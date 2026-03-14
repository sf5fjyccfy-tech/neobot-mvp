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
  Browsers,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
} from '@whiskeysockets/baileys';
import qrcodeTerminal from 'qrcode-terminal';
import QRCode from 'qrcode';
import pino from 'pino';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load local env first, then fall back to project root env.
dotenv.config({ path: path.join(__dirname, '.env') });
dotenv.config({ path: path.join(__dirname, '..', '.env') });

const BACKEND_URL = process.env.WHATSAPP_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000';
const WEBHOOK_SECRET = process.env.WHATSAPP_WEBHOOK_SECRET || process.env.WHATSAPP_SECRET_KEY || '';
const PORT = Number.parseInt(process.env.WHATSAPP_PORT || process.env.PORT || '3001', 10);
const DEFAULT_TENANT_ID = Number.parseInt(process.env.TENANT_ID || '1', 10);
const MAX_RETRIES = Number.parseInt(process.env.WHATSAPP_MAX_RETRIES || '6', 10);
const BASE_RECONNECT_DELAY_MS = Number.parseInt(process.env.WHATSAPP_RECONNECT_TIMEOUT || '3000', 10);
const MAX_RECONNECT_DELAY_MS = 60000;
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
    this.state = 'idle';
    this.connected = false;
    this.initializing = false;
    this.retryCount = 0;
    this.connectedAt = null;
    this.lastError = null;
    this.lastDisconnectCode = null;
    this.qrRaw = null;
    this.qrImageDataUrl = null;
    this.qrExpiresAt = null;
    this.scheduledReconnect = null;
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
  if (code === 401 || code === 403) {
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

  cachedBaileysVersion.version = [2, 3000, 1033846690];
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

async function notifyBackendConnection(tenantId, connected) {
  const endpoint = connected
    ? `${BACKEND_URL}/api/tenants/${tenantId}/whatsapp/session/mark-connected`
    : `${BACKEND_URL}/api/tenants/${tenantId}/whatsapp/session/mark-disconnected`;

  try {
    await axios.post(endpoint, {}, { timeout: 10_000 });
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
    await axios.post(`${BACKEND_URL}/api/v1/webhooks/whatsapp`, payloadV1, { timeout: 12_000, headers });
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
    logger.error('Max retries reached, manual reset required', {
      tenantId: session.tenantId,
      retries: session.retryCount,
      reason,
    });
    return;
  }

  session.retryCount += 1;
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
    session.connectedAt = new Date().toISOString();
    session.lastError = null;
    session.lastDisconnectCode = null;
    session.qrRaw = null;
    session.qrImageDataUrl = null;
    session.qrExpiresAt = null;

    logger.info('WhatsApp connected', { tenantId: session.tenantId });
    await notifyBackendConnection(session.tenantId, true);
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

    await notifyBackendConnection(session.tenantId, false);

    if (shouldResetAuthFromCode(statusCode)) {
      logger.warn('Disconnect requires auth reset, regenerating QR', {
        tenantId: session.tenantId,
        statusCode,
      });
      await resetTenant(session.tenantId, { keepSessionObject: true, autoReconnect: true });
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
    const authDir = tenantAuthDir(tenantId);
    const { state: authState, saveCreds } = await useMultiFileAuthState(authDir);
    const version = await getBaileysVersion();

    const socket = makeWASocket({
      version,
      auth: {
        creds: authState.creds,
        keys: makeCacheableSignalKeyStore(authState.keys, bailLogger),
      },
      browser: Browsers.macOS('Desktop'),
      printQRInTerminal: false,
      syncFullHistory: false,
      markOnlineOnConnect: false,
      connectTimeoutMs: 20_000,
      keepAliveIntervalMs: 30_000,
      defaultQueryTimeoutMs: 60_000,
      retryRequestDelayMs: 250,
      maxMsgRetryCount: 5,
      shouldSyncHistoryMessage: () => false,
      generateHighQualityLinkPreview: false,
      logger: bailLogger,
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
      const msg = event?.messages?.[0];
      if (!msg?.message || msg?.key?.fromMe) {
        return;
      }
      await forwardIncomingMessage(session.tenantId, msg);
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
  session.connectedAt = null;
  session.lastError = null;
  session.lastDisconnectCode = null;
  session.qrRaw = null;
  session.qrImageDataUrl = null;
  session.qrExpiresAt = null;

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
  const result = await session.socket.sendMessage(jid, { text: message });
  return result;
}

function buildTenantQRResponse(session) {
  return {
    tenantId: session.tenantId,
    state: session.state,
    connected: session.connected,
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

      if (session.state === 'idle' || session.state === 'disconnected' || session.state === 'error') {
        if (session.retryCount === 0 && !session.scheduledReconnect) {
          logger.info('Watchdog recovery triggered', { tenantId: session.tenantId, state: session.state });
          await connectTenant(session.tenantId, { reason: 'watchdog' });
        }
      }
    }
  }, WATCHDOG_INTERVAL_MS);
}

const app = express();
app.use(express.json());

app.get('/health', (req, res) => {
  const session = getTenantSession(DEFAULT_TENANT_ID);
  res.json({
    status: session.connected ? 'healthy' : 'degraded',
    defaultTenant: session.snapshot(),
    managedTenants: tenantSessions.size,
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

app.post('/api/whatsapp/tenants/:tenantId/send-message', async (req, res) => {
  const tenantId = Number.parseInt(req.params.tenantId, 10);
  const { to, message } = req.body || {};

  if (!Number.isInteger(tenantId) || tenantId <= 0) {
    return res.status(400).json({ error: 'Invalid tenantId' });
  }

  if (!to || !message) {
    return res.status(400).json({ error: 'Missing required fields: to, message' });
  }

  try {
    const result = await sendMessageForTenant(tenantId, to, message);
    res.json({ status: 'sent', tenantId, id: result?.key?.id || null });
  } catch (error) {
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
  logger.error('Unhandled express error', { error: err.message });
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
    logger.error('uncaughtException', { error: error.message, stack: error.stack });
  });

  process.on('unhandledRejection', (reason) => {
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
  logger.error('Fatal startup error', { error: error.message, stack: error.stack });
  process.exit(1);
});
