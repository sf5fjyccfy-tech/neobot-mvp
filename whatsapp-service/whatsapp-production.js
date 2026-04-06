#!/usr/bin/env node

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
import qrcodeTerminal from 'qrcode-terminal';
import QRCode from 'qrcode';
import pino from 'pino';
import * as Sentry from '@sentry/node';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load local env first, then fall back to project root env.
dotenv.config({ path: path.join(__dirname, '.env') });
dotenv.config({ path: path.join(__dirname, '..', '.env') });

// Init Sentry de secours — actif même si --import ./instrument.js est absent.
// Sentry.init() est idempotent : si instrument.js l'a déjà appelé, ceci est ignoré.
if (process.env.SENTRY_DSN && !Sentry.isInitialized()) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV || 'development',
    tracesSampleRate: 0,
    beforeSend(event, hint) {
      const err = hint?.originalException;
      if (err?.message?.includes('Connection Closed') ||
          err?.message?.includes('ECONNREFUSED') ||
          err?.message?.includes('Stream Errored')) {
        return null;
      }
      return event;
    },
  });
}

const BACKEND_URL = process.env.WHATSAPP_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000';
const WEBHOOK_SECRET = process.env.WHATSAPP_WEBHOOK_SECRET || process.env.WHATSAPP_SECRET_KEY || '';
const PORT = Number.parseInt(process.env.WHATSAPP_PORT || process.env.PORT || '3001', 10);
const DEFAULT_TENANT_ID = Number.parseInt(process.env.TENANT_ID || '1', 10);
const MAX_RETRIES = Number.parseInt(process.env.WHATSAPP_MAX_RETRIES || '10', 10);
const BASE_RECONNECT_DELAY_MS = Number.parseInt(process.env.WHATSAPP_RECONNECT_TIMEOUT || '5000', 10);
const MAX_RECONNECT_DELAY_MS = 300000; // 5min max entre retries
const ERROR_AUTORECOVERY_MS = 15 * 60 * 1000; // 15min avant auto-recovery depuis état error
// Debounce messages entrants : agréger les messages rapides d'un même expéditeur avant de les envoyer au backend
const MSG_DEBOUNCE_MS = Number(process.env.MSG_DEBOUNCE_MS) || 2500;
const QR_TTL_MS = 60_000;
const WATCHDOG_INTERVAL_MS = 30_000;
const BAILEYS_VERSION_CACHE_MS = 4 * 60 * 60 * 1000;

const ROOT_AUTH_DIR = path.join(__dirname, 'auth_info_baileys');
const PID_FILE = path.join(__dirname, 'whatsapp.pid');

const bailLogger = pino({ level: 'silent' });

class Logger {
  info(message, data = undefined) {
    this.log('INFO', message, data);
  }

  warn(message, data = undefined) {
    this.log('WARN', message, data);
  }

  error(message, data = undefined) {
    this.log('ERROR', message, data);
  }

  debug(message, data = undefined) {
    if ((process.env.LOG_LEVEL || 'info') !== 'debug') {
      return;
    }
    this.log('DEBUG', message, data);
  }

  log(level, message, data = undefined) {
    const ts = new Date().toISOString();
    if (data === undefined) {
      console.log(`[${ts}] [${level}] ${message}`);
      return;
    }
    console.log(`[${ts}] [${level}] ${message}`, data);
  }
}

const logger = new Logger();

class TenantSession {
  constructor(tenantId) {
    this.tenantId = tenantId;
    this.socket = null;
    this.messageStore = new Map(); // cache pour résoudre les retries Signal (fix "en attente")
    this.processedMsgIds = new Set(); // déduplication des messages entrants
    this.state = 'idle';
    this.connected = false;
    this.initializing = false;
    this.retryCount = 0;
    this.authResetCount = 0;
    this.connectedAt = null;
    this.lastError = null;
    this.lastDisconnectCode = null;
    this.qrRaw = null;
    this.qrImageDataUrl = null;
    this.qrExpiresAt = null;
    this.scheduledReconnect = null;
    this.connectedPhone = null; // JID extrait des creds Baileys au moment de la connexion
    // Debounce messages entrants : buffer par expéditeur, aggrège les bursts avant d'appeler le backend
    this.msgBuffers = new Map();         // phone → string[]
    this.msgDebounceTimers = new Map();  // phone → setTimeout handle
    this.msgDebounceLastMsg = new Map(); // phone → dernier objet msg Baileys brut
  }

  snapshot() {
    return {
      tenantId: this.tenantId,
      state: this.state,
      connected: this.connected,
      initializing: this.initializing,
      retryCount: this.retryCount,
      connectedAt: this.connectedAt,
      lastError: this.lastError,
      lastDisconnectCode: this.lastDisconnectCode,
      hasQR: Boolean(this.qrRaw),
      qrExpiresAt: this.qrExpiresAt,
      timestamp: new Date().toISOString(),
    };
  }
}

const tenantSessions = new Map();

const cachedBaileysVersion = {
  version: null,
  fetchedAt: 0,
};

function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

function tenantAuthDir(tenantId) {
  return path.join(ROOT_AUTH_DIR, `tenant_${tenantId}`);
}

function normalizeJid(target) {
  if (!target || typeof target !== 'string') {
    return target;
  }

  if (target.includes('@')) {
    return target;
  }

  const digitsOnly = target.replace(/\D/g, '');
  if (!digitsOnly) {
    return target;
  }

  return `${digitsOnly}@s.whatsapp.net`;
}

function extractPhoneFromJid(jid) {
  if (!jid || typeof jid !== 'string') {
    return '';
  }

  const beforeAt = jid.split('@')[0] || '';
  const withoutDevice = beforeAt.split(':')[0] || '';
  return withoutDevice.replace(/\D/g, '');
}

function extractStatusCode(lastDisconnect) {
  return (
    lastDisconnect?.error?.output?.statusCode ||
    lastDisconnect?.error?.data?.statusCode ||
    lastDisconnect?.error?.statusCode ||
    null
  );
}

function reconnectDelayMs(retryCount) {
  const exp = Math.min(retryCount, 10);
  const delay = BASE_RECONNECT_DELAY_MS * (2 ** exp);
  return Math.min(delay, MAX_RECONNECT_DELAY_MS);
}

function shouldResetAuthFromCode(code) {
  if (code === 401 || code === 403 || code === 405) {
    return true;
  }

  return (
    code === DisconnectReason.loggedOut ||
    code === DisconnectReason.connectionReplaced ||
    code === DisconnectReason.badSession
  );
}

async function getBaileysVersion() {
  const now = Date.now();
  if (cachedBaileysVersion.version && now - cachedBaileysVersion.fetchedAt < BAILEYS_VERSION_CACHE_MS) {
    return cachedBaileysVersion.version;
  }

  try {
    const result = await fetchLatestBaileysVersion();
    if (Array.isArray(result?.version) && result.version.length === 3) {
      cachedBaileysVersion.version = result.version;
      cachedBaileysVersion.fetchedAt = now;
      logger.info('Fetched latest Baileys protocol version', { version: result.version.join('.') });
      return result.version;
    }
  } catch (error) {
    logger.warn('Failed to fetch latest Baileys version, using fallback', { error: error.message });
  }

  cachedBaileysVersion.version = [2, 3000, 1040787960];
  cachedBaileysVersion.fetchedAt = now;
  return cachedBaileysVersion.version;
}

function getTenantSession(tenantId) {
  const id = Number.parseInt(String(tenantId), 10);
  if (!Number.isInteger(id) || id <= 0) {
    throw new Error(`Invalid tenantId: ${tenantId}`);
  }

  if (!tenantSessions.has(id)) {
    tenantSessions.set(id, new TenantSession(id));
  }

  return tenantSessions.get(id);
}

function clearReconnectTimer(session) {
  if (session.scheduledReconnect) {
    clearTimeout(session.scheduledReconnect);
    session.scheduledReconnect = null;
  }
}

async function notifyBackendConnection(tenantId, connected, phone = null) {
  const endpoint = connected
    ? `${BACKEND_URL}/api/tenants/${tenantId}/whatsapp/session/mark-connected`
    : `${BACKEND_URL}/api/tenants/${tenantId}/whatsapp/session/mark-disconnected`;

  const body = connected && phone ? { phone } : {};

  try {
    await axios.post(endpoint, body, {
      timeout: 10_000,
      headers: { 'x-internal-token': process.env.INTERNAL_API_KEY || '' },
    });
  } catch (error) {
    logger.warn('Failed to notify backend connection state', {
      tenantId,
      connected,
      endpoint,
      error: error.message,
    });
  }
}

async function cleanupTenantAuth(tenantId) {
  // En production : supprimer les credentials PostgreSQL
  if (process.env.DATABASE_URL) {
    await clearPgAuthState(tenantId);
    logger.info('Auth state cleared from PostgreSQL', { tenantId });
    return;
  }
  // En local : supprimer le répertoire filesystem
  const authDir = tenantAuthDir(tenantId);
  if (!fs.existsSync(authDir)) {
    return;
  }
  fs.rmSync(authDir, { recursive: true, force: true });
  logger.info('Auth directory removed', { tenantId, authDir });
}

async function forwardIncomingMessage(tenantId, msg) {
  const text =
    msg?.message?.conversation ||
    msg?.message?.extendedTextMessage?.text ||
    msg?.message?.imageMessage?.caption ||
    msg?.message?.videoMessage?.caption ||
    '';

  if (!text) {
    return;
  }

  const rawFrom = msg?.key?.remoteJid || '';
  const phone = extractPhoneFromJid(rawFrom);

  if (!phone) {
    logger.warn('Skipping inbound message: cannot extract phone from JID', {
      tenantId,
      rawFrom,
    });
    return;
  }

  const payloadV1 = {
    tenant_id: tenantId,
    from_: phone,
    reply_jid: rawFrom,   // JID exact pour répondre (peut être @lid, @s.whatsapp.net, etc.)
    text,
    senderName: msg?.pushName || 'Client',
    messageKey: msg?.key || {},
    timestamp: Number(msg?.messageTimestamp || Math.floor(Date.now() / 1000)),
    isMedia: false,
  };

  const signaturePayload = `${payloadV1.from_}|${payloadV1.text}|${payloadV1.timestamp}`;
  const signature = WEBHOOK_SECRET
    ? crypto.createHmac('sha256', WEBHOOK_SECRET).update(signaturePayload).digest('hex')
    : null;

  const headers = signature
    ? { 'x-webhook-signature': signature }
    : {};

  try {
    await axios.post(`${BACKEND_URL}/api/v1/webhooks/whatsapp`, payloadV1, { timeout: 30_000, headers });
    return;
  } catch (errorV1) {
    logger.error('Primary webhook endpoint failed', {
      tenantId,
      phone,
      status: errorV1?.response?.status,
      detail: errorV1?.response?.data || null,
      error: errorV1.message,
    });
  }
}

async function stopTenantSocket(session) {
  clearReconnectTimer(session);

  if (!session.socket) {
    return;
  }

  const socket = session.socket;
  session.socket = null;

  try {
    socket.end();
  } catch (error) {
    logger.warn('Socket close error', { tenantId: session.tenantId, error: error.message });
  }
}

function scheduleReconnect(session, reason) {
  if (session.initializing || session.connected) {
    return;
  }

  if (session.retryCount >= MAX_RETRIES) {
    session.state = 'error';
    session.lastError = `Max retries reached. Last reason: ${reason}`;
    session.errorSince = Date.now();
    logger.error('Max retries reached — auto-recovery in 15min', {
      tenantId: session.tenantId,
      retries: session.retryCount,
      reason,
    });
    // Auto-recovery : dans 15 min, on remet à zéro et on retente
    // (le rate-limit WA est typiquement levé en < 15min)
    clearReconnectTimer(session);
    session.scheduledReconnect = setTimeout(() => {
      session.scheduledReconnect = null;
      logger.info('Auto-recovery from error state', { tenantId: session.tenantId });
      session.retryCount = 0;
      session.authResetCount = 0;
      session.state = 'idle';
      session.errorSince = null;
      connectTenant(session.tenantId, { forceReset: false, reason: 'auto-recovery' });
    }, ERROR_AUTORECOVERY_MS);
    return;
  }

  session.retryCount += 1;
  // Backoff exponentiel dans tous les cas — même pour les nouvelles connexions.
  // Avant: neverConnected → 2000ms (hammering WA → rate-limit 405/503).
  // Maintenant: minimum 5s, exponentiel, pour ne pas se faire ban.
  const delay = reconnectDelayMs(session.retryCount);

  clearReconnectTimer(session);
  session.scheduledReconnect = setTimeout(() => {
    session.scheduledReconnect = null;
    connectTenant(session.tenantId, { forceReset: false, reason: `retry-${session.retryCount}` });
  }, delay);

  logger.info('Reconnect scheduled', {
    tenantId: session.tenantId,
    retryCount: session.retryCount,
    delayMs: delay,
    reason,
  });
}

async function onConnectionUpdate(session, update) {
  const { connection, lastDisconnect, qr } = update;

  if (qr) {
    session.state = 'waiting_qr';
    session.connected = false;
    session.qrRaw = qr;
    session.qrExpiresAt = new Date(Date.now() + QR_TTL_MS).toISOString();

    try {
      session.qrImageDataUrl = await QRCode.toDataURL(qr, { margin: 1, width: 320 });
    } catch (error) {
      session.qrImageDataUrl = null;
      logger.warn('Failed to generate QR image data URL', {
        tenantId: session.tenantId,
        error: error.message,
      });
    }

    console.log(`\n=== TENANT ${session.tenantId} - SCAN QR CODE ===\n`);
    qrcodeTerminal.generate(qr, { small: true });
    console.log(`\nQR valid for ${Math.floor(QR_TTL_MS / 1000)} seconds.\n`);
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
    session.consecutive405 = 0;
    session.connectedAt = new Date().toISOString();
    session.lastError = null;
    session.lastDisconnectCode = null;
    session.qrRaw = null;
    session.qrImageDataUrl = null;
    session.qrExpiresAt = null;
    session.connectedPhone = extractPhoneFromJid(session.socket?.user?.id || '');

    logger.info('WhatsApp connected', { tenantId: session.tenantId, phone: session.connectedPhone });
    await notifyBackendConnection(session.tenantId, true, session.connectedPhone);
  }

  if (connection === 'close') {
    session.connected = false;
    session.initializing = false;
    session.state = 'disconnected';

    const statusCode = extractStatusCode(lastDisconnect);
    session.lastDisconnectCode = statusCode;

    const reason = `connection closed (code=${statusCode ?? 'unknown'})`;
    session.lastError = reason;

    logger.warn('WhatsApp connection closed', {
      tenantId: session.tenantId,
      statusCode,
    });

    // 515 = transition de reconnexion après scan QR / validation pairing code.
    // Pas une vraie déconnexion — ne pas notifier le backend pour éviter
    // le flash "déconnecté" pendant les 3-5s de reconnexion.
    if (statusCode !== 515) {
      await notifyBackendConnection(session.tenantId, false);
    }

    if (shouldResetAuthFromCode(statusCode)) {
      logger.warn('Disconnect requires auth reset, regenerating QR', {
        tenantId: session.tenantId,
        statusCode,
      });

      session.authResetCount = (session.authResetCount || 0) + 1;

      if (session.authResetCount > 3) {
        logger.error('Too many consecutive auth resets — manual intervention required', {
          tenantId: session.tenantId,
          authResetCount: session.authResetCount,
        });
        // auth_failed: état ignoré par le watchdog → arrêt définitif de la boucle
        session.state = 'auth_failed';
        await resetTenant(session.tenantId, { keepSessionObject: true, autoReconnect: false });
        return;
      }

      // 405 = ban IP WA — chaque retry aggrave et repousse la levée du ban.
      // Stratégie : backoff très long dès le 1er 405, arrêt complet après 3 consécutifs.
      if (statusCode === 405) {
        session.consecutive405 = (session.consecutive405 || 0) + 1;
        session.retryCount += 1;

        if (session.consecutive405 >= 3) {
          // 3 fois de suite = le ban est sérieux. On arrête 30 min.
          // Pas de cleanupTenantAuth — inutile de supprimer l'auth à chaque 405.
          session.state = 'error';
          session.lastError = `IP rate-limited by WA (405) — ${session.consecutive405} consecutive. Waiting 30min.`;
          session.errorSince = Date.now();
          const backoff = 30 * 60 * 1000; // 30 minutes fixes
          logger.warn('IP rate-limited 3+ times in a row, stopping for 30min', {
            tenantId: session.tenantId, consecutive405: session.consecutive405, backoffMs: backoff,
          });
          clearReconnectTimer(session);
          session.scheduledReconnect = setTimeout(() => {
            session.scheduledReconnect = null;
            session.state = 'idle';
            session.consecutive405 = 0;
            session.retryCount = 0;
            connectTenant(session.tenantId, { forceReset: false, reason: 'rate-limit-30min-backoff' });
          }, backoff);
          return;
        }

        // 1er ou 2ème 405 : backoff exponentiel avec minimum 5 minutes
        await cleanupTenantAuth(session.tenantId);
        session.state = 'idle';
        const FIVE_MIN = 5 * 60 * 1000;
        const backoff = Math.min(FIVE_MIN * session.consecutive405, 15 * 60 * 1000); // 5min, 10min, max 15min
        logger.warn('Rate-limited by WA (405), long wait before retry', {
          tenantId: session.tenantId, consecutive405: session.consecutive405, backoffMs: backoff,
        });
        clearReconnectTimer(session);
        session.scheduledReconnect = setTimeout(() => {
          session.scheduledReconnect = null;
          connectTenant(session.tenantId, { forceReset: false, reason: 'rate-limit-backoff' });
        }, backoff);
        return;
      }

      await resetTenant(session.tenantId, { keepSessionObject: true, autoReconnect: true });
      return;
    }

    // 515 = DisconnectReason.restartRequired = succès scan QR ou validation pairing code.
    // Meta ferme proprement la socket pour dire "reconnecte-toi avec les nouveaux creds".
    // C'est un signal de SUCCÈS, pas une erreur. Reconnexion immédiate, retryCount reset.
    if (statusCode === 515) {
      logger.info('restartRequired (515) — reconnexion immédiate avec nouveaux creds', {
        tenantId: session.tenantId,
      });
      session.retryCount = 0;
      clearReconnectTimer(session);
      session.scheduledReconnect = setTimeout(() => {
        session.scheduledReconnect = null;
        connectTenant(session.tenantId, { forceReset: false, reason: 'restart-required-515' });
      }, 300);
      return;
    }

    scheduleReconnect(session, reason);
  }
}

async function connectTenant(tenantId, options = {}) {
  const { forceReset = false, reason = 'manual' } = options;
  const session = getTenantSession(tenantId);

  if (session.initializing) {
    return session.snapshot();
  }

  if (forceReset) {
    await resetTenant(tenantId, { keepSessionObject: true, autoReconnect: false });
  } else {
    await stopTenantSocket(session);
  }

  ensureDir(ROOT_AUTH_DIR);
  ensureDir(tenantAuthDir(tenantId));

  session.initializing = true;
  session.state = 'initializing';
  session.connected = false;
  session.lastError = null;

  try {
    // En production (DATABASE_URL défini) → persistance PostgreSQL (survit aux redémarrages Render)
    // En développement local → filesystem auth_info_baileys/ (comportement inchangé)
    const authDir = tenantAuthDir(tenantId);
    const { state: authState, saveCreds } = process.env.DATABASE_URL
      ? await usePgAuthState(tenantId)
      : await useMultiFileAuthState(authDir);
    const version = await getBaileysVersion();

    // Cache compteur de retry par message (évite boucles infinies)
    const retryCache = new Map();

    const socket = makeWASocket({
      version,
      auth: {
        creds: authState.creds,
        // Limite le cache Signal à 100 entrées (défaut Baileys = illimité) — évite l'OOM
        // progressif sur le free tier Render 512MB lors de sessions longues.
        keys: makeCacheableSignalKeyStore(authState.keys, bailLogger, 100),
      },
      // Fingerprint identique à WhatsApp Web officiel — affiche "WhatsApp Web" dans les
      // appareils liés Android. Neutre, indétectable par Meta.
      browser: Browsers.macOS('Chrome'),
      printQRInTerminal: false,
      syncFullHistory: false,
      markOnlineOnConnect: false,
      connectTimeoutMs: 30_000,
      keepAliveIntervalMs: 30_000,
      defaultQueryTimeoutMs: 60_000,
      retryRequestDelayMs: 250,
      maxMsgRetryCount: 5,
      shouldSyncHistoryMessage: () => false,
      generateHighQualityLinkPreview: false,
      logger: bailLogger,
      // Fix "message en attente" : fournir getMessage et msgRetryCounterCache
      msgRetryCounterCache: {
        get: (id) => retryCache.get(id) || 0,
        set: (id, val) => retryCache.set(id, val),
        del: (id) => retryCache.delete(id),
        flushAll: () => retryCache.clear(),
      },
      getMessage: async (key) => {
        const stored = session.messageStore?.get(key.id);
        if (stored) return stored;
        return { conversation: '' };
      },
    });

    session.socket = socket;

    socket.ev.on('creds.update', saveCreds);

    socket.ev.on('connection.update', async (update) => {
      try {
        await onConnectionUpdate(session, update);
      } catch (error) {
        session.lastError = error.message;
        logger.error('connection.update handler error', {
          tenantId: session.tenantId,
          error: error.message,
        });
      }
    });

    socket.ev.on('messages.upsert', async (event) => {
      // Ignorer les messages historiques chargés au reconnect (type='append')
      if (event?.type !== 'notify') return;

      for (const msg of event?.messages || []) {
        if (!msg?.message || msg?.key?.fromMe) {
          continue;
        }

        // Déduplication : ignorer si déjà traité (même messageId)
        const msgId = msg?.key?.id;
        if (msgId) {
          if (session.processedMsgIds.has(msgId)) {
            logger.warn('Duplicate message ignored', { tenantId: session.tenantId, msgId });
            continue;
          }
          session.processedMsgIds.add(msgId);
          // Garder max 500 IDs en mémoire
          if (session.processedMsgIds.size > 500) {
            const first = session.processedMsgIds.values().next().value;
            session.processedMsgIds.delete(first);
          }
        }

        // --- Debounce par expéditeur ---
        // Extraire le texte ici pour décider si c'est un message textuel avant de buffuriser
        const rawText =
          msg?.message?.conversation ||
          msg?.message?.extendedTextMessage?.text ||
          msg?.message?.imageMessage?.caption ||
          msg?.message?.videoMessage?.caption ||
          '';

        if (!rawText) continue; // pas de texte → on skippe (même comportement qu'avant)

        const senderJid = msg?.key?.remoteJid || '';
        const senderPhone = extractPhoneFromJid(senderJid);

        // Si on ne peut pas extraire le numéro → fallback direct sans debounce
        if (!senderPhone) {
          await forwardIncomingMessage(session.tenantId, msg);
          continue;
        }

        // Bufferiser le texte
        if (!session.msgBuffers.has(senderPhone)) {
          session.msgBuffers.set(senderPhone, []);
        }
        session.msgBuffers.get(senderPhone).push(rawText);
        session.msgDebounceLastMsg.set(senderPhone, msg);

        // Réinitialiser le timer
        clearTimeout(session.msgDebounceTimers.get(senderPhone));
        session.msgDebounceTimers.set(
          senderPhone,
          setTimeout(async () => {
            const texts = session.msgBuffers.get(senderPhone) || [];
            const lastMsg = session.msgDebounceLastMsg.get(senderPhone);

            // Nettoyer immédiatement pour éviter les fuites mémoire
            session.msgBuffers.delete(senderPhone);
            session.msgDebounceTimers.delete(senderPhone);
            session.msgDebounceLastMsg.delete(senderPhone);

            if (!lastMsg || texts.length === 0) return;

            if (texts.length === 1) {
              // Cas fréquent : 1 seul message → pas de merge inutile
              await forwardIncomingMessage(session.tenantId, lastMsg);
            } else {
              // Plusieurs messages → merger en un seul objet avec conversation concaténée
              logger.info('Debounce merge', {
                tenantId: session.tenantId,
                phone: senderPhone,
                count: texts.length,
              });
              const mergedMsg = {
                ...lastMsg,
                message: { conversation: texts.join('\n') },
              };
              await forwardIncomingMessage(session.tenantId, mergedMsg);
            }
          }, MSG_DEBOUNCE_MS)
        );
        // --- Fin debounce ---
      }
    });

    logger.info('Socket initialized', { tenantId, reason, version: version.join('.') });
  } catch (error) {
    session.state = 'error';
    session.lastError = error.message;
    logger.error('Tenant initialization failed', {
      tenantId,
      reason,
      error: error.message,
    });
    scheduleReconnect(session, error.message);
  } finally {
    session.initializing = false;
  }

  return session.snapshot();
}

async function resetTenant(tenantId, options = {}) {
  const { keepSessionObject = true, autoReconnect = true } = options;
  const session = getTenantSession(tenantId);

  clearReconnectTimer(session);
  await stopTenantSocket(session);
  await cleanupTenantAuth(tenantId);

  session.state = 'idle';
  session.connected = false;
  session.initializing = false;
  session.retryCount = 0;
  session.authResetCount = 0;
  session.connectedAt = null;
  session.connectedPhone = null;
  session.lastError = null;
  session.lastDisconnectCode = null;
  session.qrRaw = null;
  session.qrImageDataUrl = null;
  session.qrExpiresAt = null;

  // Annuler les timers de debounce en cours pour éviter les fire-after-reset
  for (const timer of session.msgDebounceTimers.values()) clearTimeout(timer);
  session.msgDebounceTimers.clear();
  session.msgBuffers.clear();
  session.msgDebounceLastMsg.clear();

  if (!keepSessionObject) {
    tenantSessions.delete(tenantId);
    return { tenantId, status: 'deleted' };
  }

  if (autoReconnect) {
    return connectTenant(tenantId, { forceReset: false, reason: 'reset' });
  }

  return session.snapshot();
}

async function sendMessageForTenant(tenantId, to, message) {
  const session = getTenantSession(tenantId);

  if (!session.socket || !session.connected) {
    throw new Error('WhatsApp not connected for this tenant');
  }

  const jid = normalizeJid(to);
  let result;
  try {
    result = await session.socket.sendMessage(jid, { text: message });
    // Si le send vers @lid ne retourne pas de clé de message, considérer comme échec
    if (jid.endsWith('@lid') && !result?.key?.id) {
      throw new Error('LID send returned no message key');
    }
  } catch (lidErr) {
    if (jid.endsWith('@lid')) {
      const phone = extractPhoneFromJid(jid);
      const fallbackJid = `${phone}@s.whatsapp.net`;
      logger.warn('LID JID send failed, fallback to @s.whatsapp.net', { jid, fallbackJid, error: lidErr.message });
      result = await session.socket.sendMessage(fallbackJid, { text: message });
    } else {
      throw lidErr;
    }
  }

  // Stocker le message envoyé pour permettre les retries Signal (fix "en attente")
  if (result?.key?.id && result?.message) {
    if (!session.messageStore) session.messageStore = new Map();
    session.messageStore.set(result.key.id, result.message);
    // Garder max 200 messages en cache
    if (session.messageStore.size > 200) {
      const firstKey = session.messageStore.keys().next().value;
      session.messageStore.delete(firstKey);
    }
  }

  return result;
}

function buildTenantQRResponse(session) {
  return {
    tenantId: session.tenantId,
    state: session.state,
    connected: session.connected,
    phone: session.connectedPhone || null,
    hasQR: Boolean(session.qrRaw),
    qrRaw: session.qrRaw,
    qrImageDataUrl: session.qrImageDataUrl,
    qrExpiresAt: session.qrExpiresAt,
    message: session.connected
      ? 'WhatsApp already connected'
      : session.qrRaw
      ? 'Scan QR code now'
      : 'No QR yet. Session is initializing or disconnected',
    timestamp: new Date().toISOString(),
  };
}

function getAllTenantSnapshots() {
  return Array.from(tenantSessions.values()).map((session) => session.snapshot());
}

function startWatchdog() {
  // Keep-alive Neon : un SELECT 1 toutes les 4min empêche Neon de suspendre
  // la connexion DB pendant les périodes sans activité WhatsApp.
  setInterval(async () => {
    if (process.env.DATABASE_URL) {
      await pingPool();
    }
  }, 4 * 60 * 1000);

  setInterval(async () => {
    for (const session of tenantSessions.values()) {
      if (session.initializing || session.connected) {
        continue;
      }

      if (session.state === 'waiting_qr' && session.qrExpiresAt) {
        const expiresAt = new Date(session.qrExpiresAt).getTime();
        if (Date.now() > expiresAt) {
          logger.warn('QR expired, forcing reconnect for fresh QR', { tenantId: session.tenantId });
          await connectTenant(session.tenantId, { reason: 'qr-expired-refresh' });
        }
        continue;
      }

      // auth_failed: stop définitif, nécessite un appel à /api/whatsapp/tenants/:id/reset
      if (session.state === 'auth_failed') {
        continue;
      }

      if (session.state === 'idle' || session.state === 'disconnected') {
        if (session.retryCount === 0 && !session.scheduledReconnect) {
          logger.info('Watchdog recovery triggered', { tenantId: session.tenantId, state: session.state });
          await connectTenant(session.tenantId, { reason: 'watchdog' });
        }
      }

      // Pour l'état 'error' : le timer d'auto-recovery dans scheduleReconnect s'en charge.
      // Le watchdog ne touche pas à 'error' pour ne pas interférer avec le backoff de 15min.
    }
  }, WATCHDOG_INTERVAL_MS);
}

const app = express();
app.use(express.json());

app.get('/health', (req, res) => {
  const session = getTenantSession(DEFAULT_TENANT_ID);
  const mem = process.memoryUsage();
  res.json({
    status: session.connected ? 'healthy' : 'degraded',
    defaultTenant: session.snapshot(),
    managedTenants: tenantSessions.size,
    memoryMB: {
      rss: Math.round(mem.rss / 1024 / 1024),
      heapUsed: Math.round(mem.heapUsed / 1024 / 1024),
      heapTotal: Math.round(mem.heapTotal / 1024 / 1024),
    },
    timestamp: new Date().toISOString(),
  });
});

app.get('/status', (req, res) => {
  res.json(getTenantSession(DEFAULT_TENANT_ID).snapshot());
});

app.get('/api/whatsapp/status', (req, res) => {
  res.json(getTenantSession(DEFAULT_TENANT_ID).snapshot());
});

app.get('/api/whatsapp/session-info', (req, res) => {
  const session = getTenantSession(DEFAULT_TENANT_ID);
  res.json({
    currentTenant: DEFAULT_TENANT_ID,
    state: session.snapshot(),
  });
});

app.get('/api/whatsapp/qr', (req, res) => {
  const session = getTenantSession(DEFAULT_TENANT_ID);
  res.json(buildTenantQRResponse(session));
});

app.post('/api/whatsapp/reset-session', async (req, res) => {
  try {
    const status = await resetTenant(DEFAULT_TENANT_ID, { keepSessionObject: true, autoReconnect: true });
    res.json({ status: 'reset_initiated', tenantId: DEFAULT_TENANT_ID, state: status });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/whatsapp/send-message', async (req, res) => {
  const { to, message } = req.body || {};
  if (!to || !message) {
    return res.status(400).json({ error: 'Missing required fields: to, message' });
  }

  try {
    const result = await sendMessageForTenant(DEFAULT_TENANT_ID, to, message);
    res.json({ status: 'sent', tenantId: DEFAULT_TENANT_ID, id: result?.key?.id || null });
  } catch (error) {
    res.status(503).json({ error: error.message });
  }
});

// Backward compatible endpoint used by legacy backend task.
app.post('/send', async (req, res) => {
  const { to, text } = req.body || {};
  if (!to || !text) {
    return res.status(400).json({ error: 'Missing required fields: to, text' });
  }

  try {
    const result = await sendMessageForTenant(DEFAULT_TENANT_ID, to, text);
    res.json({ status: 'sent', tenantId: DEFAULT_TENANT_ID, id: result?.key?.id || null });
  } catch (error) {
    res.status(503).json({ error: error.message });
  }
});

app.post('/api/whatsapp/delete-tenant/:tenantId', async (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }

  try {
    const result = await resetTenant(tenantId, { keepSessionObject: false, autoReconnect: false });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/whatsapp/tenants', (req, res) => {
  res.json({ tenants: getAllTenantSnapshots() });
});

app.post('/api/whatsapp/tenants/:tenantId/connect', async (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }

  try {
    const state = await connectTenant(tenantId, { reason: 'api-connect' });
    res.json({ status: 'initializing', state });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/whatsapp/tenants/:tenantId/status', (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }

  try {
    res.json(getTenantSession(tenantId).snapshot());
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.get('/api/whatsapp/tenants/:tenantId/qr', (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }

  try {
    res.json(buildTenantQRResponse(getTenantSession(tenantId)));
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.post('/api/whatsapp/tenants/:tenantId/reset', async (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }

  try {
    const state = await resetTenant(tenantId, { keepSessionObject: true, autoReconnect: true });
    res.json({ status: 'reset_initiated', state });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Déconnexion propre — ferme le socket sans supprimer les creds ni reconnecter.
// Le backend est notifié via l'event 'close' → mark-disconnected.
app.post('/api/whatsapp/tenants/:tenantId/disconnect', async (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }

  try {
    const session = getTenantSession(tenantId);
    clearReconnectTimer(session);
    await stopTenantSocket(session);
    session.connected = false;
    session.state = 'disconnected';
    session.connectedPhone = null;
    logger.info('Tenant disconnected by user request', { tenantId });
    res.json({ status: 'disconnected', tenantId });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ── Envoi de message pour un tenant spécifique ─────────────────────────────
// POST /api/whatsapp/tenants/:tenantId/send-message
// Body: { to: "22612345678", message: "Bonjour" }
// Utilisé par le backend pour les réponses bot ET les messages opérateur
app.post('/api/whatsapp/tenants/:tenantId/send-message', async (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }

  const { to, message } = req.body || {};
  if (!to || !message) {
    return res.status(400).json({ error: 'Missing required fields: to, message' });
  }

  try {
    const result = await sendMessageForTenant(tenantId, to, message);
    logger.info('Outgoing message sent', { tenantId, to, msgId: result?.key?.id || null });
    res.json({ status: 'sent', tenantId, id: result?.key?.id || null });
  } catch (error) {
    logger.error('Failed to send message for tenant', { tenantId, to, error: error.message });
    res.status(503).json({ error: error.message });
  }
});

// Rate limiter inter-requêtes : Meta bloque les demandes de code consécutives
// sur le même tenant en moins de ~60s ("Connection Closed" immédiat sinon).
const _pairingRateLimit = new Map(); // tenantId → { phone, ts }
const PAIRING_COOLDOWN_MS = 65_000; // 5s de marge par rapport aux 60s Meta

// ── Pairing code (alternative au QR — pas sujet au rate-limit WA) ──────────
// POST /api/whatsapp/tenants/:tenantId/request-pairing-code
// Body: { phone_number: "22612345678" }  ← sans le +
// Retourne: { code: "ABCD-1234" } à taper dans WA app Settings > Linked Devices
// Pattern officiel Baileys : appeler requestPairingCode immédiatement après makeWASocket
app.post('/api/whatsapp/tenants/:tenantId/request-pairing-code', async (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }

  const phone = String(req.body?.phone_number || '').replace(/\D/g, '');
  if (!phone || phone.length < 7 || phone.length > 15) {
    return res.status(400).json({ error: 'phone_number requis (format international sans +, ex: 22612345678)' });
  }

  // ── Rate limit : Meta refuse un 2ème code < 60s après le précédent ──
  const _rl = _pairingRateLimit.get(tenantId);
  const _now = Date.now();
  if (_rl && (_now - _rl.ts) < PAIRING_COOLDOWN_MS) {
    const waitSec = Math.ceil((PAIRING_COOLDOWN_MS - (_now - _rl.ts)) / 1000);
    logger.warn('Pairing rate limited — too soon after previous attempt', { tenantId, waitSec });
    return res.status(429).json({
      error: `Attendez encore ${waitSec}s avant de demander un nouveau code — Meta bloque les tentatives consécutives`,
      wait_seconds: waitSec,
    });
  }

  const session = getTenantSession(tenantId);

  // Si déjà connecté → déconnecter proprement d'abord pour permettre le re-jumelage
  // (changement de numéro, code expiré, ou DB désynchronisée après redémarrage Render).
  // NE PAS retourner already_connected — ça bloque la régénération.
  if (session.connected) {
    logger.info('Re-pairing requested on connected session — disconnecting first', { tenantId });
    clearReconnectTimer(session);
    await stopTenantSocket(session);
    session.connected = false;
    session.state = 'idle';
    await notifyBackendConnection(tenantId, false);
  } else {
    // Stopper toute reconnexion en cours — éviter conflits de socket
    clearReconnectTimer(session);
    if (session.socket) {
      try { session.socket.end(undefined); } catch (_) {}
      session.socket = null;
      // Laisser 300ms à Baileys pour libérer les event emitters internes
      // avant de créer un nouveau socket — évite les listeners orphelins
      await new Promise(resolve => setTimeout(resolve, 300));
    }
    session.state = 'idle';
  }
  session.initializing = false;
  session.retryCount = 0;
  session.authResetCount = 0;

  // Enregistrer la tentative AVANT l'appel Baileys
  // (même si ça échoue, Meta a comptabilisé la tentative)
  _pairingRateLimit.set(tenantId, { phone, ts: Date.now() });

  try {
    const authDir = path.join(__dirname, 'auth_info_baileys', `tenant_${tenantId}`);
    if (!fs.existsSync(authDir)) {
      fs.mkdirSync(authDir, { recursive: true });
    }

    // Helper : crée un socket + demande le code. Appelé une fois, retenté une fois
    // si Meta ferme la connexion immédiatement (transitoire sur Render).
    const attemptGetCode = async () => {
      // Effacer les creds — requestPairingCode échoue si creds.registered === true.
      if (process.env.DATABASE_URL) {
        await clearPgAuthState(tenantId);
      } else {
        for (const file of fs.readdirSync(authDir)) {
          fs.rmSync(path.join(authDir, file), { force: true });
        }
      }

      const { state, saveCreds } = process.env.DATABASE_URL
        ? await usePgAuthState(tenantId)
        : await useMultiFileAuthState(authDir);

      const version = await getBaileysVersion();

      const sock = makeWASocket({
        version,
        auth: {
          creds: state.creds,
          keys: makeCacheableSignalKeyStore(state.keys, bailLogger, 100),
        },
        usePairingCode: true,
        browser: Browsers.macOS('Chrome'),
        printQRInTerminal: false,
        logger: bailLogger,
        generateHighQualityLinkPreview: false,
        connectTimeoutMs: 60_000,
        keepAliveIntervalMs: 10_000,
        defaultQueryTimeoutMs: 0,
      });
      sock.ev.on('creds.update', saveCreds);

      let metaCode = null;
      sock.ev.on('connection.update', ({ connection, lastDisconnect }) => {
        if (connection === 'close') {
          metaCode = lastDisconnect?.error?.output?.statusCode
            ?? lastDisconnect?.error?.output?.payload?.statusCode
            ?? null;
          logger.warn('Pairing sock closed during code request', { tenantId, metaCode });
        }
      });

      // Attendre ~300ms que le handshake WS interne démarre avant d'envoyer la demande.
      // Sans ce délai, certains environnements (Render cold start) obtiennent
      // "Connection Closed" immédiat car le transport n'est pas encore prêt.
      await new Promise(r => setTimeout(r, 300));

      const raw = await Promise.race([
        sock.requestPairingCode(phone),
        new Promise((_, reject) => setTimeout(
          () => reject(new Error('Pairing code timeout (30s)')), 30_000
        )),
      ]).catch(err => {
        const suffix = metaCode ? ` [Meta code: ${metaCode}]` : '';
        // Propager le metaCode pour que le retry décide quoi faire
        const e = new Error(`${err.message}${suffix}`);
        e.metaCode = metaCode;
        throw e;
      });

      return { raw, sock, saveCreds, state, version, authDir };
    };

    // --- Tentative 1 ---
    let attempt;
    try {
      attempt = await attemptGetCode();
    } catch (err1) {
      // Retry unique : si Meta a fermé la connexion (transitoire / cold start Render),
      // on attend 8s et on réessaie. Les refus définitifs (401, 403) ne sont pas retentés.
      const isTransient = err1.message.includes('Connection Closed') && err1.metaCode !== 401 && err1.metaCode !== 403;
      if (!isTransient) throw err1;

      logger.warn('requestPairingCode transient fail — retrying in 8s', { tenantId, err: err1.message });
      await new Promise(r => setTimeout(r, 8_000));

      // Augmenter le cooldown à 120s en cas d'échec (Meta se souvient des tentatives
      // même après un restart Render — on lui laisse plus de temps pour "oublier").
      _pairingRateLimit.set(tenantId, { phone, ts: Date.now() - (PAIRING_COOLDOWN_MS - 120_000) });

      attempt = await attemptGetCode(); // laisse remonter si ça échoue encore
    }

    const { raw, sock: pairSock, saveCreds, state, version, authDir: aDir } = attempt;

    session.socket = pairSock;
    session.initializing = true;
    session.state = 'initializing';

    const formatted = raw?.match(/.{1,4}/g)?.join('-') || raw;
    logger.info('Pairing code generated successfully', { tenantId, phone, code: formatted });

    logger.info('[PAIRING] ▶ Code généré — socket active en attente de validation', { tenantId, code: formatted, phone });

    // Handler post-pairing — SANS reconnexion.
    //
    // ANALYSE DES LOGS (tenant 1) :
    //   sock1 → 408 (connectionLost, 20s) → Meta a annulé la session côté serveur
    //   sock2 → 401 (loggedOut) → session Meta morte, reconnexion impossible
    //
    // 408 = Meta ferme la session de pairing après timeout (20s sous rate-limit,
    // 2-3 min normalement). Quand le socket ferme, Meta détruit la session côté
    // serveur. Tout reconnect obtient 401 — il n'y a plus rien à rejoindre.
    //
    // LA RECONNEXION NE FONCTIONNE PAS. On gère proprement :
    //   • 'open' → pairing réussi avant expiry → lancer connectTenant
    //   • 'close' 408 → session expirée → cooldown 5min + log clair
    //   • 'close' 401 → session morte (rate-limit sévère) → cooldown 10min
    pairSock.ev.on('connection.update', ({ connection, lastDisconnect }) => {
      logger.info('[PAIRING] connection.update', { tenantId, connection });
      if (connection === 'open') {
        logger.info('[PAIRING] ✅ Code accepté par WA — session complète', { tenantId });
        session.initializing = false;
        clearReconnectTimer(session);
        session.scheduledReconnect = setTimeout(() => {
          session.scheduledReconnect = null;
          connectTenant(tenantId, { forceReset: false, reason: 'after-pairing-success' });
        }, 500);
      } else if (connection === 'close') {
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        session.socket = null;
        session.initializing = false;
        session.state = 'disconnected';

        if (statusCode === 515) {
          // Pairing code validé par le téléphone de l'utilisateur.
          // Meta ferme la socket de pairing et demande une reconnexion avec les nouveaux creds
          // (déjà sauvegardés en PG via creds.update → saveCreds).
          // C'est un SUCCÈS — reconnecter immédiatement, retryCount reset.
          logger.info('[PAIRING] ✅ 515 restartRequired — code validé, reconnexion avec nouveaux creds', { tenantId });
          session.initializing = false;
          session.retryCount = 0;
          clearReconnectTimer(session);
          session.scheduledReconnect = setTimeout(() => {
            session.scheduledReconnect = null;
            connectTenant(tenantId, { forceReset: false, reason: 'pairing-restart-515' });
          }, 300);
        } else if (statusCode === 401) {
          // Rate-limit sévère Meta — session annulée avant même que l'user puisse saisir.
          // Cooldown 10 min pour laisser Meta réinitialiser.
          logger.error('[PAIRING] ❌ Session annulée (401) — rate-limit Meta sévère', { tenantId });
          _pairingRateLimit.set(tenantId, { phone, ts: Date.now() - (PAIRING_COOLDOWN_MS - 600_000) });
        } else if (statusCode === 408) {
          // Timeout Meta — fenêtre de validation expirée (20s sous rate-limit, 2-3min normal).
          // Cooldown 5 min.
          logger.warn('[PAIRING] ⏱ Session expirée (408) — code non saisi à temps', { tenantId });
          _pairingRateLimit.set(tenantId, { phone, ts: Date.now() - (PAIRING_COOLDOWN_MS - 300_000) });
        } else {
          logger.warn('[PAIRING] Socket fermée', { tenantId, statusCode });
        }
      }
    });

    return res.json({
      status: 'code_generated',
      code: formatted,
      instructions: 'Sur votre téléphone : WA → ⋮ (menu) → Appareils connectés → Associer un appareil → Associer avec un numéro de téléphone',
      phone,
      tenantId,
    });
  } catch (error) {
    logger.error('requestPairingCode failed', { tenantId, error: error.message });
    // Réinitialiser l'état — les creds ont déjà été vidés donc on ne reconnecte
    // pas automatiquement (pas de creds valides = QR socket inutile qui spamme).
    // L'utilisateur redemandera un code après le cooldown de 65s.
    session.initializing = false;
    session.socket = null;
    session.state = 'disconnected';
    // Effacer le rate limit pour cet échec early (avant même connexion Meta)
    // seulement si l'erreur est locale (pas un refus Meta)
    const isMetaRefusal = error.message.includes('Connection Closed') || error.message.includes('Meta code');
    if (!isMetaRefusal) {
      _pairingRateLimit.delete(tenantId);
    }
    return res.status(503).json({ error: `Impossible de générer le code de couplage : ${error.message}` });
  }
});

app.post('/api/whatsapp/tenants/:tenantId/typing', async (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  const { to } = req.body || {};

  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }
  if (!to) {
    return res.status(400).json({ error: 'Missing required field: to' });
  }

  const session = getTenantSession(tenantId);
  if (!session.connected || !session.socket) {
    return res.status(503).json({ error: 'WhatsApp not connected for this tenant' });
  }

  try {
    const jid = normalizeJid(to);
    await session.socket.sendPresenceUpdate('composing', jid);
    res.json({ status: 'typing', tenantId });
  } catch (error) {
    logger.error('Failed to send typing indicator', { tenantId, to, error: error.message });
    res.status(503).json({ error: error.message });
  }
});

app.post('/api/whatsapp/tenants/:tenantId/send-message', async (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  const { to, message } = req.body || {};

  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }

  if (!to || !message) {
    logger.warn('send-message: missing fields', { tenantId, to: !!to, message: !!message });
    return res.status(400).json({ error: 'Missing required fields: to, message' });
  }

  const session = getTenantSession(tenantId);
  if (!session.connected || !session.socket) {
    logger.error('send-message: WhatsApp not connected', { tenantId, state: session.state });
    return res.status(503).json({ error: 'WhatsApp not connected for this tenant' });
  }

  logger.info('Sending outgoing message', { tenantId, to, preview: message.slice(0, 80) });

  try {
    const result = await sendMessageForTenant(tenantId, to, message);
    // Annuler l'indicateur "en train d'écrire" après envoi — comportement humain naturel
    try {
      const jid = normalizeJid(to);
      await session.socket.sendPresenceUpdate('paused', jid);
    } catch (_) { /* non bloquant */ }
    logger.info('Outgoing message sent', { tenantId, to, msgId: result?.key?.id || null });
    res.json({ status: 'sent', tenantId, id: result?.key?.id || null });
  } catch (error) {
    logger.error('Failed to send message', { tenantId, to, error: error.message });
    res.status(503).json({ error: error.message });
  }
});

app.delete('/api/whatsapp/tenants/:tenantId', async (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }

  try {
    const result = await resetTenant(tenantId, { keepSessionObject: false, autoReconnect: false });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.use((err, req, res, _next) => {
  Sentry.captureException(err);
  logger.error('Express error', { error: err.message, path: req.path, method: req.method });
  res.status(500).json({ error: 'Internal server error' });
});

function registerProcessHandlers(server) {
  const shutdown = async (signal) => {
    logger.warn(`Received ${signal}, shutting down`);

    for (const session of tenantSessions.values()) {
      clearReconnectTimer(session);
      await stopTenantSocket(session);
    }

    server.close(() => {
      process.exit(0);
    });
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));

  process.on('uncaughtException', (error) => {
    Sentry.captureException(error);
    logger.error('uncaughtException', { error: error.message, stack: error.stack });
  });

  process.on('unhandledRejection', (reason) => {
    Sentry.captureException(reason instanceof Error ? reason : new Error(String(reason)));
    logger.error('unhandledRejection', { reason: String(reason) });
  });
}

async function start() {
  ensureDir(ROOT_AUTH_DIR);
  fs.writeFileSync(PID_FILE, String(process.pid));

  const server = app.listen(PORT, async () => {
    logger.info('WhatsApp service started', {
      port: PORT,
      backend: BACKEND_URL,
      defaultTenant: DEFAULT_TENANT_ID,
      signatureEnabled: Boolean(WEBHOOK_SECRET),
    });

    console.log('\nEndpoints:');
    console.log('  GET  /health');
    console.log('  GET  /status');
    console.log('  GET  /api/whatsapp/qr');
    console.log('  POST /api/whatsapp/reset-session');
    console.log('  POST /api/whatsapp/send-message');
    console.log('  GET  /api/whatsapp/tenants');
    console.log('  POST /api/whatsapp/tenants/:tenantId/connect');
    console.log('  GET  /api/whatsapp/tenants/:tenantId/qr');
    console.log('  POST /api/whatsapp/tenants/:tenantId/reset');

    await connectTenant(DEFAULT_TENANT_ID, { reason: 'startup' });
    startWatchdog();
  });

  server.on('error', (error) => {
    if (error.code === 'EADDRINUSE') {
      logger.error(`Port ${PORT} is already in use`);
      process.exit(1);
    }

    logger.error('HTTP server error', { error: error.message });
    process.exit(1);
  });

  registerProcessHandlers(server);
}

start().catch((error) => {
  Sentry.captureException(error);
  logger.error('Fatal startup error', { error: error.message, stack: error.stack });
  process.exit(1);
});
