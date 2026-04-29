#!/usr/bin/env node

/**
 * NeoBot WhatsApp Service v4.0
 * Production-ready Baileys service for multi-tenant WhatsApp automation
 * Fixes: auth persistence, QR field names, session isolation, reconnection logic
 */

import express from 'express';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import makeWASocket, {
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
  Browsers,
} from '@whiskeysockets/baileys';
import { usePgAuthState, clearPgAuthState, pingPool } from './pg-auth-state.js';
import NodeCache from '@cacheable/node-cache';
import QRCode from 'qrcode';
import pino from 'pino';
import * as Sentry from '@sentry/node';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '.env') });
dotenv.config({ path: path.join(__dirname, '..', '.env') });

// ── Sentry ────────────────────────────────────────────────────────────────────
if (process.env.SENTRY_DSN && !Sentry.isInitialized()) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV || 'production',
    tracesSampleRate: 0,
    beforeSend(event, hint) {
      const msg = hint?.originalException?.message || '';
      if (
        msg.includes('Connection Closed') ||
        msg.includes('ECONNREFUSED') ||
        msg.includes('Stream Errored') ||
        msg.includes('Socket connection timeout')
      ) return null;
      return event;
    },
  });
}

// ── Config ────────────────────────────────────────────────────────────────────
const BACKEND_URL =
  process.env.WHATSAPP_BACKEND_URL ||
  process.env.BACKEND_URL ||
  'http://localhost:8000';
const WEBHOOK_SECRET =
  process.env.WHATSAPP_WEBHOOK_SECRET ||
  process.env.WHATSAPP_SECRET_KEY ||
  '';
const PORT = parseInt(process.env.PORT || '3001', 10);
const DEFAULT_TENANT_ID = parseInt(process.env.TENANT_ID || '1', 10);
const INTERNAL_API_KEY = (process.env.INTERNAL_API_KEY || '').trim();

// Reconnection
const MAX_RETRIES = 8;
const BASE_RECONNECT_MS = 5_000;
const MAX_RECONNECT_MS = 300_000;   // 5 min
const ERROR_RECOVERY_MS = 15 * 60_000; // 15 min

// Messages
const MSG_DEBOUNCE_MS = parseInt(process.env.MSG_DEBOUNCE_MS || '2500', 10);

// QR
const QR_TTL_MS = 60_000; // 60s — Meta QR expires ~20-30s, we refresh proactively

// Baileys version cache
const BAILEYS_VERSION_CACHE_MS = 4 * 60 * 60_000;

// Pairing code rate limit
const PAIRING_COOLDOWN_MS = 65_000;

const ROOT_AUTH_DIR = path.join(__dirname, 'auth_info_baileys');
const bailLogger = pino({ level: 'silent' });

// ── Logger ────────────────────────────────────────────────────────────────────
const logger = {
  _log(level, message, data) {
    const ts = new Date().toISOString();
    const line = data !== undefined
      ? `[${ts}] [${level}] ${message} ${JSON.stringify(data)}`
      : `[${ts}] [${level}] ${message}`;
    console.log(line);
  },
  info: (m, d) => logger._log('INFO', m, d),
  warn: (m, d) => logger._log('WARN', m, d),
  error: (m, d) => logger._log('ERROR', m, d),
  debug: (m, d) => {
    if (process.env.LOG_LEVEL === 'debug') logger._log('DEBUG', m, d);
  },
};

// ── Browser profiles ──────────────────────────────────────────────────────────
// Each tenant gets a different fingerprint to reduce detection surface.
// Pairing code always uses macOS+Chrome (Meta validates this server-side).
const BROWSER_PROFILES = [
  Browsers.macOS('Safari'),
  Browsers.ubuntu('Chrome'),
  Browsers.windows('Firefox'),
  Browsers.macOS('Firefox'),
  Browsers.ubuntu('Firefox'),
];

function getBrowserForTenant(tenantId) {
  return BROWSER_PROFILES[tenantId % BROWSER_PROFILES.length];
}

// ── Baileys version cache ─────────────────────────────────────────────────────
const baileysVersionCache = { version: null, fetchedAt: 0 };

async function getBaileysVersion() {
  const now = Date.now();
  if (
    baileysVersionCache.version &&
    now - baileysVersionCache.fetchedAt < BAILEYS_VERSION_CACHE_MS
  ) {
    return baileysVersionCache.version;
  }
  try {
    const result = await fetchLatestBaileysVersion();
    if (Array.isArray(result?.version) && result.version.length === 3) {
      baileysVersionCache.version = result.version;
      baileysVersionCache.fetchedAt = now;
      logger.info('Baileys version fetched', { version: result.version.join('.') });
      return result.version;
    }
  } catch (e) {
    logger.warn('Failed to fetch Baileys version, using fallback', { error: e.message });
  }
  // Stable fallback version
  baileysVersionCache.version = [2, 3000, 1040787960];
  baileysVersionCache.fetchedAt = now;
  return baileysVersionCache.version;
}

// ── TenantSession ─────────────────────────────────────────────────────────────
class TenantSession {
  constructor(tenantId) {
    this.tenantId = tenantId;
    this.socket = null;
    this.messageStore = new Map();
    this.processedMsgIds = new Set();
    this.state = 'idle';
    this.connected = false;
    this.initializing = false;
    this.retryCount = 0;
    this.authResetCount = 0;
    this.consecutive405 = 0;
    this.connectedAt = null;
    this.lastError = null;
    this.lastDisconnectCode = null;
    this.qrRaw = null;
    this.qr_image = null;       // ← field name aligned with frontend
    this.qrExpiresAt = null;
    this.scheduledReconnect = null;
    this.connectedPhone = null;
    this.errorSince = null;
    this.autoConnectEnabled = false;
    // Message debounce
    this.msgBuffers = new Map();
    this.msgDebounceTimers = new Map();
    this.msgDebounceLastMsg = new Map();
  }

  snapshot() {
    return {
      tenantId: this.tenantId,
      state: this.state,
      connected: this.connected,
      phone: this.connectedPhone || null,
      initializing: this.initializing,
      retryCount: this.retryCount,
      connectedAt: this.connectedAt,
      lastError: this.lastError,
      lastDisconnectCode: this.lastDisconnectCode,
      // QR fields — consistent naming for frontend
      has_qr_code: Boolean(this.qrRaw),
      qr_image: this.qr_image,
      qrExpiresAt: this.qrExpiresAt,
      timestamp: new Date().toISOString(),
    };
  }
}

// ── Session store ─────────────────────────────────────────────────────────────
const tenantSessions = new Map();
const _pairingRateLimit = new Map();

function getTenantSession(tenantId) {
  const id = parseInt(String(tenantId), 10);
  if (!Number.isInteger(id) || id <= 0) throw new Error(`Invalid tenantId: ${tenantId}`);
  if (!tenantSessions.has(id)) tenantSessions.set(id, new TenantSession(id));
  return tenantSessions.get(id);
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

function tenantAuthDir(tenantId) {
  return path.join(ROOT_AUTH_DIR, `tenant_${tenantId}`);
}

function normalizeJid(target) {
  if (!target || typeof target !== 'string') return target;
  if (target.includes('@')) return target;
  const digits = target.replace(/\D/g, '');
  return digits ? `${digits}@s.whatsapp.net` : target;
}

function extractPhone(jid) {
  if (!jid || typeof jid !== 'string') return '';
  return (jid.split('@')[0] || '').split(':')[0].replace(/\D/g, '');
}

function extractStatusCode(lastDisconnect) {
  return (
    lastDisconnect?.error?.output?.statusCode ||
    lastDisconnect?.error?.data?.statusCode ||
    lastDisconnect?.error?.statusCode ||
    null
  );
}

function reconnectDelay(retryCount) {
  return Math.min(BASE_RECONNECT_MS * 2 ** Math.min(retryCount, 10), MAX_RECONNECT_MS);
}

function shouldResetAuth(code) {
  return (
    code === 401 || code === 403 || code === 405 ||
    code === DisconnectReason.loggedOut ||
    code === DisconnectReason.connectionReplaced ||
    code === DisconnectReason.badSession
  );
}

function clearReconnectTimer(session) {
  if (session.scheduledReconnect) {
    clearTimeout(session.scheduledReconnect);
    session.scheduledReconnect = null;
  }
}

// ── Auth helpers ──────────────────────────────────────────────────────────────
async function getAuthState(tenantId) {
  if (process.env.DATABASE_URL) {
    return usePgAuthState(tenantId);
  }
  ensureDir(tenantAuthDir(tenantId));
  return useMultiFileAuthState(tenantAuthDir(tenantId));
}

async function cleanupAuth(tenantId) {
  if (process.env.DATABASE_URL) {
    await clearPgAuthState(tenantId);
    logger.info('Auth cleared from DB', { tenantId });
  } else {
    const dir = tenantAuthDir(tenantId);
    if (fs.existsSync(dir)) fs.rmSync(dir, { recursive: true, force: true });
    logger.info('Auth directory removed', { tenantId });
  }
}

// ── Backend notification ──────────────────────────────────────────────────────
async function notifyBackend(tenantId, connected, phone = null) {
  const path = connected
    ? `/api/tenants/${tenantId}/whatsapp/session/mark-connected`
    : `/api/tenants/${tenantId}/whatsapp/session/mark-disconnected`;
  try {
    await axios.post(
      `${BACKEND_URL}${path}`,
      connected && phone ? { phone } : {},
      {
        timeout: 10_000,
        headers: { 'x-internal-token': INTERNAL_API_KEY },
      }
    );
  } catch (e) {
    logger.warn('Backend notification failed', { tenantId, connected, error: e.message });
  }
}

// ── Message forwarding ────────────────────────────────────────────────────────
async function forwardMessage(tenantId, msg) {
  const text =
    msg?.message?.conversation ||
    msg?.message?.extendedTextMessage?.text ||
    msg?.message?.imageMessage?.caption ||
    msg?.message?.videoMessage?.caption || '';

  if (!text) return;

  const rawFrom = msg?.key?.remoteJid || '';
  const phone = extractPhone(rawFrom);
  if (!phone) return;

  const payload = {
    tenant_id: tenantId,
    from_: phone,
    reply_jid: rawFrom,
    text,
    senderName: msg?.pushName || 'Client',
    messageKey: msg?.key || {},
    timestamp: Number(msg?.messageTimestamp || Math.floor(Date.now() / 1000)),
    isMedia: false,
  };

  const sigPayload = `${payload.from_}|${payload.text}|${payload.timestamp}`;
  const signature = WEBHOOK_SECRET
    ? crypto.createHmac('sha256', WEBHOOK_SECRET).update(sigPayload).digest('hex')
    : null;

  const headers = signature ? { 'x-webhook-signature': signature } : {};

  // Retry logic — 3 attempts with 2s delay
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      await axios.post(
        `${BACKEND_URL}/api/v1/webhooks/whatsapp`,
        payload,
        { timeout: 30_000, headers }
      );
      return;
    } catch (e) {
      logger.warn('Webhook attempt failed', { tenantId, attempt, error: e.message });
      if (attempt < 3) await new Promise(r => setTimeout(r, 2000));
    }
  }
  logger.error('All webhook attempts failed', { tenantId, phone });
}

// ── Socket management ─────────────────────────────────────────────────────────
async function stopSocket(session) {
  clearReconnectTimer(session);
  if (!session.socket) return;
  const sock = session.socket;
  session.socket = null;
  try { sock.end(); } catch (_) { }
}

// ── Connection update handler ─────────────────────────────────────────────────
async function onConnectionUpdate(session, update) {
  const { connection, lastDisconnect, qr } = update;

  // New QR received
  if (qr) {
    session.state = 'waiting_qr';
    session.connected = false;
    session.qrRaw = qr;
    session.qrExpiresAt = new Date(Date.now() + QR_TTL_MS).toISOString();
    try {
      // Generate base64 image — field name 'qr_image' aligned with frontend
      session.qr_image = await QRCode.toDataURL(qr, { margin: 2, width: 300 });
    } catch (e) {
      session.qr_image = null;
      logger.warn('QR image generation failed', { tenantId: session.tenantId, error: e.message });
    }
    logger.info('QR code ready', { tenantId: session.tenantId, expiresAt: session.qrExpiresAt });
  }

  if (connection === 'connecting') {
    session.state = 'initializing';
  }

  if (connection === 'open') {
    clearReconnectTimer(session);
    session.connected = true;
    session.initializing = false;
    session.state = 'connected';
    session.retryCount = 0;
    session.authResetCount = 0;
    session.consecutive405 = 0;
    session.errorSince = null;
    session.connectedAt = new Date().toISOString();
    session.lastError = null;
    session.lastDisconnectCode = null;
    session.qrRaw = null;
    session.qr_image = null;
    session.qrExpiresAt = null;
    session.connectedPhone = extractPhone(session.socket?.user?.id || '');
    logger.info('WhatsApp connected', {
      tenantId: session.tenantId,
      phone: session.connectedPhone,
    });
    await notifyBackend(session.tenantId, true, session.connectedPhone);
  }

  if (connection === 'close') {
    session.connected = false;
    session.initializing = false;
    session.state = 'disconnected';
    const code = extractStatusCode(lastDisconnect);
    session.lastDisconnectCode = code;
    session.lastError = `connection closed (code=${code ?? 'unknown'})`;
    logger.warn('WhatsApp disconnected', { tenantId: session.tenantId, code });

    if (code !== 515) await notifyBackend(session.tenantId, false);

    // 515 = pairing success, Meta asks to reconnect with new creds
    if (code === 515) {
      session.retryCount = 0;
      clearReconnectTimer(session);
      session.scheduledReconnect = setTimeout(() => {
        session.scheduledReconnect = null;
        connectTenant(session.tenantId, { reason: 'restart-515' });
      }, 500);
      return;
    }

    if (shouldResetAuth(code)) {
      session.authResetCount = (session.authResetCount || 0) + 1;

      if (session.authResetCount > 3) {
        logger.error('Too many auth resets — pausing 10min', { tenantId: session.tenantId });
        session.state = 'auth_failed';
        await cleanupAuth(session.tenantId);
        clearReconnectTimer(session);
        session.scheduledReconnect = setTimeout(() => {
          session.scheduledReconnect = null;
          session.state = 'idle';
          session.authResetCount = 0;
          session.retryCount = 0;
          logger.info('Auth reset recovery', { tenantId: session.tenantId });
        }, 10 * 60_000);
        return;
      }

      // 405 — IP rate limit by Meta
      if (code === 405) {
        session.consecutive405 = (session.consecutive405 || 0) + 1;
        session.retryCount += 1;
        if (session.consecutive405 >= 3) {
          session.state = 'error';
          session.lastError = `IP rate-limited (405) x${session.consecutive405}`;
          session.errorSince = Date.now();
          clearReconnectTimer(session);
          session.scheduledReconnect = setTimeout(() => {
            session.scheduledReconnect = null;
            session.state = 'idle';
            session.consecutive405 = 0;
            session.retryCount = 0;
            connectTenant(session.tenantId, { reason: '405-backoff-30min' });
          }, 30 * 60_000);
          return;
        }
        await cleanupAuth(session.tenantId);
        session.state = 'idle';
        const backoff = Math.min(5 * 60_000 * session.consecutive405, 15 * 60_000);
        clearReconnectTimer(session);
        session.scheduledReconnect = setTimeout(() => {
          session.scheduledReconnect = null;
          connectTenant(session.tenantId, { reason: '405-backoff' });
        }, backoff);
        return;
      }

      await resetTenant(session.tenantId, { keepSession: true, reconnect: true });
      return;
    }

    scheduleReconnect(session, session.lastError);
  }
}

function scheduleReconnect(session, reason) {
  if (session.initializing || session.connected) return;
  if (!session.autoConnectEnabled) return;

  if (session.retryCount >= MAX_RETRIES) {
    session.state = 'error';
    session.lastError = `Max retries (${MAX_RETRIES}). Last: ${reason}`;
    session.errorSince = Date.now();
    logger.error('Max retries reached, auto-recovery in 15min', { tenantId: session.tenantId });
    clearReconnectTimer(session);
    session.scheduledReconnect = setTimeout(() => {
      session.scheduledReconnect = null;
      session.retryCount = 0;
      session.authResetCount = 0;
      session.state = 'idle';
      session.errorSince = null;
      connectTenant(session.tenantId, { reason: 'auto-recovery' });
    }, ERROR_RECOVERY_MS);
    return;
  }

  session.retryCount += 1;
  const delay = reconnectDelay(session.retryCount);
  clearReconnectTimer(session);
  session.scheduledReconnect = setTimeout(() => {
    session.scheduledReconnect = null;
    connectTenant(session.tenantId, { reason: `retry-${session.retryCount}` });
  }, delay);

  logger.info('Reconnect scheduled', {
    tenantId: session.tenantId,
    retry: session.retryCount,
    delayMs: delay,
  });
}

// ── Connect tenant ────────────────────────────────────────────────────────────
async function connectTenant(tenantId, options = {}) {
  const { reason = 'manual' } = options;
  const session = getTenantSession(tenantId);

  if (session.initializing) return session.snapshot();

  await stopSocket(session);
  ensureDir(ROOT_AUTH_DIR);
  ensureDir(tenantAuthDir(tenantId));

  session.initializing = true;
  session.state = 'initializing';
  session.connected = false;
  session.lastError = null;

  try {
    // Load auth — DO NOT clear before connecting (preserve valid sessions)
    const { state: authState, saveCreds } = await getAuthState(tenantId);
    const version = await getBaileysVersion();
    const retryCache = new Map();

    const socket = makeWASocket({
      version,
      auth: {
        creds: authState.creds,
        keys: makeCacheableSignalKeyStore(
          authState.keys,
          bailLogger,
          new NodeCache({ maxKeys: 100, stdTTL: 30, useClones: false })
        ),
      },
      browser: getBrowserForTenant(tenantId),
      printQRInTerminal: false,
      syncFullHistory: false,
      markOnlineOnConnect: false,
      connectTimeoutMs: 90_000,
      keepAliveIntervalMs: 15_000,
      defaultQueryTimeoutMs: 0,
      retryRequestDelayMs: 500,
      maxMsgRetryCount: 5,
      shouldSyncHistoryMessage: () => false,
      generateHighQualityLinkPreview: false,
      logger: bailLogger,
      msgRetryCounterCache: {
        get: (id) => retryCache.get(id) || 0,
        set: (id, val) => retryCache.set(id, val),
        del: (id) => retryCache.delete(id),
        flushAll: () => retryCache.clear(),
      },
      getMessage: async (key) => {
        return session.messageStore?.get(key.id) || { conversation: '' };
      },
    });

    session.socket = socket;
    await new Promise(r => setTimeout(r, 300));

    socket.ev.on('creds.update', saveCreds);

    socket.ev.on('connection.update', async (update) => {
      try {
        await onConnectionUpdate(session, update);
      } catch (e) {
        session.lastError = e.message;
        logger.error('connection.update error', { tenantId, error: e.message });
      }
    });

    socket.ev.on('messages.upsert', async (event) => {
      if (event?.type !== 'notify') return;

      for (const msg of event?.messages || []) {
        if (!msg?.message || msg?.key?.fromMe) continue;

        // Deduplication
        const msgId = msg?.key?.id;
        if (msgId) {
          if (session.processedMsgIds.has(msgId)) continue;
          session.processedMsgIds.add(msgId);
          if (session.processedMsgIds.size > 500) {
            session.processedMsgIds.delete(session.processedMsgIds.values().next().value);
          }
        }

        const rawText =
          msg?.message?.conversation ||
          msg?.message?.extendedTextMessage?.text ||
          msg?.message?.imageMessage?.caption ||
          msg?.message?.videoMessage?.caption || '';

        if (!rawText) continue;

        const senderJid = msg?.key?.remoteJid || '';
        const senderPhone = extractPhone(senderJid);

        if (!senderPhone) {
          await forwardMessage(session.tenantId, msg);
          continue;
        }

        // Debounce — aggregate rapid messages from same sender
        if (!session.msgBuffers.has(senderPhone)) session.msgBuffers.set(senderPhone, []);
        session.msgBuffers.get(senderPhone).push(rawText);
        session.msgDebounceLastMsg.set(senderPhone, msg);

        clearTimeout(session.msgDebounceTimers.get(senderPhone));
        session.msgDebounceTimers.set(
          senderPhone,
          setTimeout(async () => {
            const texts = session.msgBuffers.get(senderPhone) || [];
            const lastMsg = session.msgDebounceLastMsg.get(senderPhone);
            session.msgBuffers.delete(senderPhone);
            session.msgDebounceTimers.delete(senderPhone);
            session.msgDebounceLastMsg.delete(senderPhone);

            if (!lastMsg || !texts.length) return;

            const finalMsg = texts.length === 1
              ? lastMsg
              : { ...lastMsg, message: { conversation: texts.join('\n') } };

            await forwardMessage(session.tenantId, finalMsg);
          }, MSG_DEBOUNCE_MS)
        );
      }
    });

    logger.info('Socket initialized', { tenantId, reason, version: version.join('.') });
  } catch (e) {
    session.state = 'error';
    session.lastError = e.message;
    logger.error('Connect failed', { tenantId, error: e.message });
    scheduleReconnect(session, e.message);
  } finally {
    session.initializing = false;
  }

  return session.snapshot();
}

// ── Reset tenant ──────────────────────────────────────────────────────────────
async function resetTenant(tenantId, options = {}) {
  const { keepSession = true, reconnect = true } = options;
  const session = getTenantSession(tenantId);

  clearReconnectTimer(session);
  await stopSocket(session);
  await cleanupAuth(tenantId);

  Object.assign(session, {
    state: 'idle',
    connected: false,
    initializing: false,
    retryCount: 0,
    authResetCount: 0,
    consecutive405: 0,
    errorSince: null,
    connectedAt: null,
    connectedPhone: null,
    lastError: null,
    lastDisconnectCode: null,
    qrRaw: null,
    qr_image: null,
    qrExpiresAt: null,
  });

  for (const t of session.msgDebounceTimers.values()) clearTimeout(t);
  session.msgDebounceTimers.clear();
  session.msgBuffers.clear();
  session.msgDebounceLastMsg.clear();

  if (!keepSession) {
    tenantSessions.delete(tenantId);
    return { tenantId, status: 'deleted' };
  }

  if (reconnect) {
    return connectTenant(tenantId, { reason: 'reset' });
  }

  return session.snapshot();
}

// ── Send message ──────────────────────────────────────────────────────────────
async function sendMessage(tenantId, to, message) {
  const session = getTenantSession(tenantId);
  if (!session.socket || !session.connected) {
    throw new Error('WhatsApp not connected');
  }

  const jid = normalizeJid(to);
  let result;

  try {
    result = await session.socket.sendMessage(jid, { text: message });
    if (jid.endsWith('@lid') && !result?.key?.id) throw new Error('LID send failed');
  } catch (e) {
    if (jid.endsWith('@lid')) {
      const fallback = `${extractPhone(jid)}@s.whatsapp.net`;
      result = await session.socket.sendMessage(fallback, { text: message });
    } else {
      throw e;
    }
  }

  // Cache for Signal retry resolution
  if (result?.key?.id && result?.message) {
    if (!session.messageStore) session.messageStore = new Map();
    session.messageStore.set(result.key.id, result.message);
    if (session.messageStore.size > 200) {
      session.messageStore.delete(session.messageStore.keys().next().value);
    }
  }

  return result;
}

// ── QR response builder ───────────────────────────────────────────────────────
function buildQRResponse(session) {
  return {
    tenantId: session.tenantId,
    status: session.state,
    connected: session.connected,
    phone: session.connectedPhone || null,
    // Consistent field names for frontend
    has_qr_code: Boolean(session.qrRaw),
    qr_image: session.qr_image,         // base64 data URL
    qrExpiresAt: session.qrExpiresAt,
    expires_in: session.qrExpiresAt
      ? Math.max(0, Math.round((new Date(session.qrExpiresAt) - Date.now()) / 1000))
      : null,
    message: session.connected
      ? 'Already connected'
      : session.qrRaw
        ? 'Scan QR code now'
        : 'No QR available — trigger connection first',
    timestamp: new Date().toISOString(),
  };
}

// ── Watchdog ──────────────────────────────────────────────────────────────────
function startWatchdog() {
  // DB keepalive
  setInterval(async () => {
    if (process.env.DATABASE_URL) {
      try { await pingPool(); } catch (_) { }
    }
  }, 4 * 60_000);

  // Backend keepalive (prevent Render sleep)
  if (BACKEND_URL && !BACKEND_URL.includes('localhost')) {
    setInterval(async () => {
      try { await axios.get(`${BACKEND_URL}/health`, { timeout: 10_000 }); } catch (_) { }
    }, 14 * 60_000);
  }

  // Self keepalive
  const SELF_URL = process.env.WHATSAPP_SERVICE_URL;
  if (SELF_URL && !SELF_URL.includes('localhost')) {
    setInterval(async () => {
      try { await axios.get(`${SELF_URL}/health`, { timeout: 8_000 }); } catch (_) { }
    }, 10 * 60_000);
  }

  // Session watchdog
  setInterval(async () => {
    for (const session of tenantSessions.values()) {
      if (session.initializing || session.connected) continue;
      if (!session.autoConnectEnabled) continue;
      if (session.state === 'auth_failed') continue;

      // Refresh expired QR
      if (session.state === 'waiting_qr' && session.qrExpiresAt) {
        if (Date.now() > new Date(session.qrExpiresAt).getTime()) {
          logger.warn('QR expired, refreshing', { tenantId: session.tenantId });
          await connectTenant(session.tenantId, { reason: 'qr-refresh' });
        }
        continue;
      }

      if (
        (session.state === 'idle' || session.state === 'disconnected') &&
        session.retryCount === 0 &&
        !session.scheduledReconnect
      ) {
        logger.info('Watchdog recovery', { tenantId: session.tenantId });
        await connectTenant(session.tenantId, { reason: 'watchdog' });
      }
    }
  }, 30_000);
}

// ── Express app ───────────────────────────────────────────────────────────────
const app = express();
app.use(express.json({ limit: '10mb' }));

// Health
app.get('/health', (req, res) => {
  const session = getTenantSession(DEFAULT_TENANT_ID);
  const mem = process.memoryUsage();
  const connected = [...tenantSessions.values()].filter(s => s.connected).length;
  res.json({
    status: session.connected ? 'healthy' : 'degraded',
    tenants_connected: connected,
    tenants_total: tenantSessions.size,
    defaultTenant: session.snapshot(),
    memoryMB: {
      rss: Math.round(mem.rss / 1024 / 1024),
      heap: Math.round(mem.heapUsed / 1024 / 1024),
    },
    timestamp: new Date().toISOString(),
  });
});

// Status
app.get('/status', (req, res) => res.json(getTenantSession(DEFAULT_TENANT_ID).snapshot()));
app.get('/api/whatsapp/status', (req, res) => res.json(getTenantSession(DEFAULT_TENANT_ID).snapshot()));

// QR (default tenant)
app.get('/api/whatsapp/qr', async (req, res) => {
  const session = getTenantSession(DEFAULT_TENANT_ID);
  if (!session.socket && session.state === 'idle') {
    session.autoConnectEnabled = true;
    connectTenant(DEFAULT_TENANT_ID, { reason: 'qr-trigger' }).catch(() => { });
  }
  res.json(buildQRResponse(session));
});

// Reset (default tenant)
app.post('/api/whatsapp/reset-session', async (req, res) => {
  try {
    const state = await resetTenant(DEFAULT_TENANT_ID, { keepSession: true, reconnect: true });
    res.json({ status: 'reset_initiated', state });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Send message (default tenant)
app.post('/api/whatsapp/send-message', async (req, res) => {
  const { to, message } = req.body || {};
  if (!to || !message) return res.status(400).json({ error: 'Missing: to, message' });
  try {
    const result = await sendMessage(DEFAULT_TENANT_ID, to, message);
    res.json({ status: 'sent', id: result?.key?.id || null });
  } catch (e) {
    res.status(503).json({ error: e.message });
  }
});

// Legacy send
app.post('/send', async (req, res) => {
  const { to, text } = req.body || {};
  if (!to || !text) return res.status(400).json({ error: 'Missing: to, text' });
  try {
    const result = await sendMessage(DEFAULT_TENANT_ID, to, text);
    res.json({ status: 'sent', id: result?.key?.id || null });
  } catch (e) {
    res.status(503).json({ error: e.message });
  }
});

// All tenants
app.get('/api/whatsapp/tenants', (req, res) => {
  res.json({ tenants: [...tenantSessions.values()].map(s => s.snapshot()) });
});

// Per-tenant endpoints
app.post('/api/whatsapp/tenants/:id/connect', async (req, res) => {
  const tenantId = parseInt(req.params.id, 10);
  if (!tenantId || tenantId <= 0) return res.status(400).json({ error: 'Invalid tenantId' });
  try {
    getTenantSession(tenantId).autoConnectEnabled = true;
    const state = await connectTenant(tenantId, { reason: 'api-connect' });
    res.json({ status: 'initializing', state });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/whatsapp/tenants/:id/status', (req, res) => {
  const tenantId = parseInt(req.params.id, 10);
  if (!tenantId || tenantId <= 0) return res.status(400).json({ error: 'Invalid tenantId' });
  try {
    res.json(getTenantSession(tenantId).snapshot());
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

app.get('/api/whatsapp/tenants/:id/qr', async (req, res) => {
  const tenantId = parseInt(req.params.id, 10);
  if (!tenantId || tenantId <= 0) return res.status(400).json({ error: 'Invalid tenantId' });
  try {
    const session = getTenantSession(tenantId);
    if (!session.socket && session.state === 'idle') {
      session.autoConnectEnabled = true;
      connectTenant(tenantId, { reason: 'qr-trigger' }).catch(() => { });
    }
    res.json(buildQRResponse(session));
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

app.post('/api/whatsapp/tenants/:id/reset', async (req, res) => {
  const tenantId = parseInt(req.params.id, 10);
  if (!tenantId || tenantId <= 0) return res.status(400).json({ error: 'Invalid tenantId' });
  try {
    const state = await resetTenant(tenantId, { keepSession: true, reconnect: true });
    res.json({ status: 'reset_initiated', state });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/whatsapp/tenants/:id/disconnect', async (req, res) => {
  const tenantId = parseInt(req.params.id, 10);
  if (!tenantId || tenantId <= 0) return res.status(400).json({ error: 'Invalid tenantId' });
  try {
    const session = getTenantSession(tenantId);
    clearReconnectTimer(session);
    await stopSocket(session);
    session.connected = false;
    session.state = 'disconnected';
    session.connectedPhone = null;
    session.autoConnectEnabled = false;
    await notifyBackend(tenantId, false);
    res.json({ status: 'disconnected', tenantId });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.delete('/api/whatsapp/tenants/:id', async (req, res) => {
  const tenantId = parseInt(req.params.id, 10);
  if (!tenantId || tenantId <= 0) return res.status(400).json({ error: 'Invalid tenantId' });
  try {
    const result = await resetTenant(tenantId, { keepSession: false, reconnect: false });
    res.json(result);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/whatsapp/tenants/:id/send-message', async (req, res) => {
  const tenantId = parseInt(req.params.id, 10);
  const { to, message } = req.body || {};
  if (!tenantId || tenantId <= 0) return res.status(400).json({ error: 'Invalid tenantId' });
  if (!to || !message) return res.status(400).json({ error: 'Missing: to, message' });
  try {
    const result = await sendMessage(tenantId, to, message);
    try {
      await getTenantSession(tenantId).socket?.sendPresenceUpdate('paused', normalizeJid(to));
    } catch (_) { }
    res.json({ status: 'sent', tenantId, id: result?.key?.id || null });
  } catch (e) {
    res.status(503).json({ error: e.message });
  }
});

app.post('/api/whatsapp/tenants/:id/send-image', async (req, res) => {
  const tenantId = parseInt(req.params.id, 10);
  const { to, imageBase64, caption = '', mimetype = 'image/jpeg' } = req.body || {};
  if (!tenantId || tenantId <= 0) return res.status(400).json({ error: 'Invalid tenantId' });
  if (!to || !imageBase64) return res.status(400).json({ error: 'Missing: to, imageBase64' });
  const session = getTenantSession(tenantId);
  if (!session.connected || !session.socket) return res.status(503).json({ error: 'Not connected' });
  try {
    const jid = normalizeJid(to);
    const buffer = Buffer.from(
      imageBase64.replace(/^data:[^;]+;base64,/, ''),
      'base64'
    );
    const result = await session.socket.sendMessage(jid, {
      image: buffer,
      caption,
      mimetype,
    });
    res.json({ status: 'sent', tenantId, id: result?.key?.id || null });
  } catch (e) {
    logger.error('send-image failed', { tenantId, error: e.message });
    res.status(503).json({ error: e.message });
  }
});

app.post('/api/whatsapp/tenants/:id/typing', async (req, res) => {
  const tenantId = parseInt(req.params.id, 10);
  const { to } = req.body || {};
  if (!tenantId || tenantId <= 0) return res.status(400).json({ error: 'Invalid tenantId' });
  if (!to) return res.status(400).json({ error: 'Missing: to' });
  const session = getTenantSession(tenantId);
  if (!session.connected || !session.socket) return res.status(503).json({ error: 'Not connected' });
  try {
    await session.socket.sendPresenceUpdate('composing', normalizeJid(to));
    res.json({ status: 'typing', tenantId });
  } catch (e) {
    res.status(503).json({ error: e.message });
  }
});

// ── Pairing code ──────────────────────────────────────────────────────────────
app.post('/api/whatsapp/tenants/:id/request-pairing-code', async (req, res) => {
  const tenantId = parseInt(req.params.id, 10);
  if (!tenantId || tenantId <= 0) return res.status(400).json({ error: 'Invalid tenantId' });

  const phone = String(req.body?.phone_number || '').replace(/\D/g, '');
  if (!phone || phone.length < 7 || phone.length > 15) {
    return res.status(400).json({ error: 'phone_number required (international format without +)' });
  }

  // Rate limit check
  const rl = _pairingRateLimit.get(tenantId);
  const now = Date.now();
  if (rl && now - rl.ts < PAIRING_COOLDOWN_MS) {
    const wait = Math.ceil((PAIRING_COOLDOWN_MS - (now - rl.ts)) / 1000);
    return res.status(429).json({
      error: `Wait ${wait}s before next attempt (Meta rate limit)`,
      wait_seconds: wait,
    });
  }

  const session = getTenantSession(tenantId);

  // Stop any existing connection
  clearReconnectTimer(session);
  if (session.socket) {
    session.initializing = true;
    try { session.socket.end(undefined); } catch (_) { }
    session.socket = null;
    await new Promise(r => setTimeout(r, 500));
    clearReconnectTimer(session);
  }
  session.connected = false;
  session.state = 'idle';
  session.initializing = false;
  session.retryCount = 0;
  session.authResetCount = 0;

  _pairingRateLimit.set(tenantId, { phone, ts: Date.now() });

  const attemptCode = async () => {
    // Clear old credentials — required for pairing code to work
    await cleanupAuth(tenantId);
    await new Promise(r => setTimeout(r, 1000));

    const { state, saveCreds } = await getAuthState(tenantId);
    const version = await getBaileysVersion();

    const sock = makeWASocket({
      version,
      auth: {
        creds: state.creds,
        keys: makeCacheableSignalKeyStore(
          state.keys,
          bailLogger,
          new NodeCache({ maxKeys: 100, stdTTL: 30, useClones: false })
        ),
      },
      usePairingCode: true,
      // Must be macOS+Chrome for pairing code (Meta validates server-side)
      browser: Browsers.macOS('Google Chrome'),
      printQRInTerminal: false,
      logger: bailLogger,
      generateHighQualityLinkPreview: false,
      connectTimeoutMs: 60_000,
      keepAliveIntervalMs: 10_000,
      defaultQueryTimeoutMs: 0,
    });

    sock.ev.on('creds.update', saveCreds);

    let metaCode = null;
    sock.ev.on('connection.update', ({ connection, lastDisconnect: ld }) => {
      if (connection === 'close') {
        metaCode = ld?.error?.output?.statusCode ?? null;
      }
    });

    await new Promise(r => setTimeout(r, 500));

    const raw = await Promise.race([
      sock.requestPairingCode(phone),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout 30s')), 30_000)),
    ]).catch(err => {
      const e = new Error(`${err.message}${metaCode ? ` [Meta:${metaCode}]` : ''}`);
      e.metaCode = metaCode;
      throw e;
    });

    return { raw, sock, saveCreds };
  };

  try {
    let attempt;
    try {
      attempt = await attemptCode();
    } catch (err1) {
      const transient =
        err1.message.includes('Connection Closed') &&
        err1.metaCode !== 401 &&
        err1.metaCode !== 403;

      if (!transient) throw err1;

      logger.warn('Pairing code transient fail, retrying in 8s', { tenantId, error: err1.message });
      await new Promise(r => setTimeout(r, 8_000));
      attempt = await attemptCode();
    }

    const { raw, sock: pairSock } = attempt;
    const formatted = raw?.match(/.{1,4}/g)?.join('-') || raw;

    session.socket = pairSock;
    session.initializing = true;
    session.state = 'initializing';

    logger.info('Pairing code generated', { tenantId, phone, code: formatted });

    // Handle post-pairing events
    pairSock.ev.on('connection.update', ({ connection, lastDisconnect: ld }) => {
      const code = ld?.error?.output?.statusCode ?? null;

      if (connection === 'open') {
        logger.info('Pairing accepted', { tenantId });
        session.autoConnectEnabled = true;
        session.initializing = false;
        clearReconnectTimer(session);
        session.scheduledReconnect = setTimeout(() => {
          session.scheduledReconnect = null;
          connectTenant(tenantId, { reason: 'post-pairing' });
        }, 500);
        return;
      }

      if (connection === 'close') {
        session.socket = null;
        session.initializing = false;

        if (code === 515) {
          logger.info('Pairing 515 — reconnecting with new creds', { tenantId });
          session.autoConnectEnabled = true;
          session.retryCount = 0;
          clearReconnectTimer(session);
          session.scheduledReconnect = setTimeout(() => {
            session.scheduledReconnect = null;
            connectTenant(tenantId, { reason: 'pairing-515' });
          }, 300);
          return;
        }

        if (code === 401) {
          logger.error('Pairing 401 — rate-limited by Meta, wait 10min', { tenantId });
          session.state = 'error';
          session.lastError = 'Meta 401 — cooldown 10min';
          session.errorSince = Date.now();
          _pairingRateLimit.set(tenantId, { phone, ts: Date.now() + 600_000 - PAIRING_COOLDOWN_MS });
          clearReconnectTimer(session);
          session.scheduledReconnect = setTimeout(() => {
            session.scheduledReconnect = null;
            session.state = 'idle';
            session.errorSince = null;
            session.authResetCount = 0;
          }, 600_000);
          return;
        }

        if (code === 408) {
          logger.warn('Pairing 408 — expired, wait 5min', { tenantId });
          session.state = 'error';
          session.lastError = 'Pairing expired 408 — cooldown 5min';
          session.errorSince = Date.now();
          clearReconnectTimer(session);
          session.scheduledReconnect = setTimeout(() => {
            session.scheduledReconnect = null;
            session.state = 'idle';
            session.errorSince = null;
          }, 300_000);
          return;
        }

        logger.warn('Pairing socket closed', { tenantId, code });
        session.state = 'disconnected';
      }
    });

    return res.json({
      status: 'code_generated',
      code: formatted,
      phone,
      tenantId,
      instructions: 'WhatsApp → Settings → Linked Devices → Link with phone number → Enter code',
    });
  } catch (e) {
    logger.error('Pairing code failed', { tenantId, error: e.message });
    session.initializing = false;
    session.socket = null;
    session.state = 'disconnected';
    if (!e.message.includes('Connection Closed') && !e.message.includes('Meta')) {
      _pairingRateLimit.delete(tenantId);
    }
    return res.status(503).json({ error: `Pairing failed: ${e.message}` });
  }
});

// ── Error handler ─────────────────────────────────────────────────────────────
app.use((err, req, res, _next) => {
  Sentry.captureException(err);
  logger.error('Express error', { error: err.message, path: req.path });
  res.status(500).json({ error: 'Internal server error' });
});

// ── Process handlers ──────────────────────────────────────────────────────────
function registerHandlers(server) {
  const shutdown = async (signal) => {
    logger.warn(`Shutdown: ${signal}`);
    for (const session of tenantSessions.values()) {
      clearReconnectTimer(session);
      await stopSocket(session);
    }
    server.close(() => process.exit(0));
    setTimeout(() => process.exit(1), 10_000);
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('uncaughtException', (e) => {
    Sentry.captureException(e);
    logger.error('uncaughtException', { error: e.message });
  });
  process.on('unhandledRejection', (r) => {
    Sentry.captureException(r instanceof Error ? r : new Error(String(r)));
    logger.error('unhandledRejection', { reason: String(r) });
  });
}

// ── Startup ───────────────────────────────────────────────────────────────────
async function start() {
  ensureDir(ROOT_AUTH_DIR);

  const server = app.listen(PORT, async () => {
    logger.info('NeoBot WhatsApp Service v4.0 started', {
      port: PORT,
      backend: BACKEND_URL,
      defaultTenant: DEFAULT_TENANT_ID,
      db: process.env.DATABASE_URL ? 'postgresql' : 'filesystem',
    });

    // Check for existing valid session on startup
    try {
      const { state } = await getAuthState(DEFAULT_TENANT_ID);
      if (state.creds?.registered) {
        logger.info('Valid session found — auto-connecting', { tenantId: DEFAULT_TENANT_ID });
        getTenantSession(DEFAULT_TENANT_ID).autoConnectEnabled = true;
        await connectTenant(DEFAULT_TENANT_ID, { reason: 'startup' });
      } else {
        logger.info('No session — waiting for user action (QR or pairing code)', {
          tenantId: DEFAULT_TENANT_ID,
        });
      }
    } catch (e) {
      logger.warn('Startup session check failed', { error: e.message });
    }

    startWatchdog();
  });

  server.on('error', (e) => {
    if (e.code === 'EADDRINUSE') {
      logger.error(`Port ${PORT} already in use`);
    } else {
      logger.error('Server error', { error: e.message });
    }
    process.exit(1);
  });

  registerHandlers(server);
}

start().catch((e) => {
  Sentry.captureException(e);
  logger.error('Fatal startup error', { error: e.message });
  process.exit(1);
});