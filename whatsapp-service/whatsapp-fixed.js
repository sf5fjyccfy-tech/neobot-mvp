#!/usr/bin/env node

/**
 * 🚀 NEOBOT WhatsApp Service - v5.0 FIXED
 * 
 * BREAKTHROUGH FIX (GitHub Issue #2377, Feb 26, 2026):
 * ✅ Platform.WEB → Platform.MACOS (WhatsApp rejected WEB)
 * ✅ fetchLatestBaileysVersion() for dynamic version sync
 * ✅ Proper auth state with makeCacheableSignalKeyStore
 * ✅ Optimized timeout configuration
 * ✅ No infinite loops, proper retry logic
 */

import express from 'express';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============================================================
// CONFIGURATION
// ============================================================

const CONFIG = {
    backend_url: process.env.BACKEND_URL || 'http://localhost:8000',
    port: parseInt(process.env.PORT || 3001),
    tenant_id: parseInt(process.env.TENANT_ID || 1),
    session_timeout: parseInt(process.env.SESSION_TIMEOUT || 259200000),
    log_level: process.env.LOG_LEVEL || 'info',
    qr_timeout: 60000,
    reconnect_delay: 5000,
    max_retries: 3,
    health_check_interval: 30000,
    auth_dir: path.join(__dirname, 'auth_info_baileys'),
    session_file: path.join(__dirname, 'sessions.json'),
    pid_file: path.join(__dirname, 'whatsapp.pid'),
};

// ============================================================
// LOGGER
// ============================================================

class Logger {
    constructor(level = 'info') {
        this.level = level;
        this.levels = { error: 0, warn: 1, info: 2, debug: 3 };
    }

    log(lvl, msg, data = {}) {
        if (this.levels[lvl] > this.levels[this.level]) return;
        const ts = new Date().toISOString();
        const icon = { error: '❌', warn: '⚠️', info: 'ℹ️', debug: '🔍' }[lvl];
        if (Object.keys(data).length > 0) {
            console.log(`${icon} [${ts}] ${msg}`, JSON.stringify(data));
        } else {
            console.log(`${icon} [${ts}] ${msg}`);
        }
    }

    error(msg, data) { this.log('error', msg, data); }
    warn(msg, data) { this.log('warn', msg, data); }
    info(msg, data) { this.log('info', msg, data); }
    debug(msg, data) { this.log('debug', msg, data); }
}

const logger = new Logger(CONFIG.log_level);

// ============================================================
// STATE & SESSION
// ============================================================

class SessionState {
    constructor() {
        this.connected = false;
        this.state = 'initializing';
        this.qr_code = null;
        this.error_msg = null;
        this.retry_count = 0;
        this.connected_at = null;
        this.last_activity = Date.now();
    }

    setConnected() {
        this.connected = true;
        this.state = 'connected';
        this.connected_at = Date.now();
        this.retry_count = 0;
        this.qr_code = null;
        this.error_msg = null;
        logger.info('✅ WhatsApp CONNECTED');
    }

    setError(msg, state = 'error') {
        this.connected = false;
        this.state = state;
        this.error_msg = msg;
        this.qr_code = null;
        logger.warn('❌ State Error', { msg, state });
    }

    setWaitingQR(qr) {
        this.state = 'waiting_auth';
        this.qr_code = qr;
        logger.info('📱 New QR Code Generated');
    }

    getStatus() {
        return {
            connected: this.connected,
            state: this.state,
            tenant_id: CONFIG.tenant_id,
            connected_at: this.connected_at ? new Date(this.connected_at) : null,
            uptime_ms: this.connected_at ? Date.now() - this.connected_at : 0,
            last_activity: new Date(this.last_activity),
            retry_count: this.retry_count,
            error: this.error_msg,
            hasQR: !!this.qr_code,
            timestamp: new Date().toISOString(),
        };
    }
}

const state = new SessionState();

// ============================================================
// BAILEYS - FIXED VERSION (Feb 26 2026 Solution)
// ============================================================

let globalSocket = null;
let initLock = false;
let qrTimeout = null;

async function initializeBaileys() {
    if (initLock) {
        logger.warn('Init already in progress, skipping');
        return;
    }

    initLock = true;
    state.retry_count++;

    try {
        if (!fs.existsSync(CONFIG.auth_dir)) {
            fs.mkdirSync(CONFIG.auth_dir, { recursive: true });
        }

        state.state = 'initializing';
        logger.info('🔄 Loading Baileys...');

        // Load Baileys
        let Baileys;
        try {
            Baileys = await import('@whiskeysockets/baileys');
        } catch (e) {
            logger.error('Failed to load @whiskeysockets/baileys', { error: e.message });
            throw e;
        }

        const { 
            makeWASocket, 
            useMultiFileAuthState, 
            DisconnectReason, 
            Browsers,
            fetchLatestBaileysVersion,
            makeCacheableSignalKeyStore
        } = Baileys;

        if (!makeWASocket || !useMultiFileAuthState) {
            throw new Error('Required Baileys exports not found');
        }

        logger.info('📁 Loading auth state...');
        const { state: authState, saveCreds } = await useMultiFileAuthState(CONFIG.auth_dir);

        // ⭐ KEY FIX #1: Fetch latest WhatsApp protocol version
        logger.info('🔍 Fetching latest WhatsApp protocol version...');
        let version;
        try {
            const versionData = await fetchLatestBaileysVersion();
            version = versionData.version;
            logger.info('✅ Version fetched', { version: version.join('.') });
        } catch (err) {
            logger.warn('Could not fetch version, using fallback', { error: err.message });
            version = [2, 3000, 1033846690];
        }

        // ⭐ KEY FIX #2: Use macOS browser (NOT WEB, ubuntu, or generic string)
        // Solution: GitHub Issue #2377 (Feb 26, 2026)
        // WhatsApp servers reject Platform.WEB during device pairing
        const socketConfig = {
            version: version,  // Dynamic version from WhatsApp
            auth: {
                creds: authState.creds,
                keys: makeCacheableSignalKeyStore(authState.keys, logger)
            },
            browser: Browsers.macOS('Chrome'),  // ⭐ FIX: macOS (not WEB or ubuntu)
            printQRInTerminal: false,
            syncFullHistory: false,
            maxMsgsInMemory: 50,
            generateHighQualityLinkPreview: false,
            shouldSyncHistoryMessage: () => false,
            markOnlineOnConnect: true,
            // ⭐ KEY FIX #3: Optimized timeout configuration
            connectTimeoutMs: 20_000,           // Time to establish socket
            keepAliveIntervalMs: 30_000,        // Heartbeat interval
            defaultQueryTimeoutMs: 60_000,      // Query timeout
            retryRequestDelayMs: 250,           // Retry delay
            maxMsgRetryCount: 5,                // Max message retries
        };

        logger.info('Creating socket with fixed configuration', { 
            version: version.join('.'),
            browser: 'macOS' 
        });

        const socket = makeWASocket(socketConfig);
        globalSocket = socket;

        // ========== EVENTS ==========

        socket.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            try {
                if (qr) {
                    state.setWaitingQR(qr);

                    if (qrTimeout) clearTimeout(qrTimeout);
                    qrTimeout = setTimeout(() => {
                        logger.warn('⏰ QR Code expired (60s timeout)');
                        state.setError('QR Code expired - Please call POST /api/whatsapp/reset');
                        if (globalSocket) {
                            globalSocket.end(() => {
                                globalSocket = null;
                            });
                        }
                        initLock = false;
                    }, CONFIG.qr_timeout);
                }

                if (connection === 'connecting') {
                    state.state = 'initializing';
                    logger.info('🔗 Connecting...');
                }

                if (connection === 'open') {
                    if (qrTimeout) clearTimeout(qrTimeout);
                    state.setConnected();
                    initLock = false;
                }

                if (connection === 'close') {
                    const statusCode = lastDisconnect?.error?.output?.statusCode;
                    const reason = DisconnectReason[statusCode] || `Unknown (${statusCode})`;

                    logger.warn('🔌 Connection closed', { 
                        statusCode, 
                        reason,
                        retry: state.retry_count 
                    });

                    if (statusCode === DisconnectReason.loggedOut) {
                        logger.info('👤 User logged out');
                        state.setError('User logged out - Call POST /api/whatsapp/reset');
                        initLock = false;
                        return;
                    }

                    if (statusCode === DisconnectReason.connectionReplaced) {
                        logger.info('Another device connected');
                        state.setError('Connection replaced by another device');
                        initLock = false;
                        return;
                    }

                    if (state.retry_count < CONFIG.max_retries) {
                        logger.info('🔄 Retrying...', { 
                            attempt: state.retry_count, 
                            max: CONFIG.max_retries 
                        });
                        state.state = 'disconnected';
                        setTimeout(() => {
                            initLock = false;
                            initializeBaileys();
                        }, CONFIG.reconnect_delay);
                    } else {
                        logger.error('❌ Max retries exceeded');
                        state.setError('Max retries exceeded - Manual reset required', 'error');
                        initLock = false;
                    }
                }
            } catch (err) {
                logger.error('Error in connection.update', { error: err.message });
                state.setError(err.message);
                initLock = false;
            }
        });

        socket.ev.on('creds.update', () => {
            logger.debug('💾 Credentials updated');
            saveCreds();
        });

        socket.ev.on('messages.upsert', async (m) => {
            if (!m?.messages?.[0]) return;

            const msg = m.messages[0];
            if (!msg?.message) return;

            state.last_activity = Date.now();
            logger.info('💬 Message received', { from: msg.key.remoteJid });

            try {
                await axios.post(`${CONFIG.backend_url}/api/whatsapp/webhook/message`, {
                    tenant_id: CONFIG.tenant_id,
                    from: msg.key.remoteJid,
                    message: msg.message,
                    timestamp: msg.messageTimestamp,
                }, { timeout: 10000 });
            } catch (err) {
                logger.error('Failed to send message to backend', { error: err.message });
            }
        });

        socket.ev.on('error', (err) => {
            logger.error('Socket error', { code: err?.code, message: err?.message });
            state.setError(`Socket error: ${err?.message}`);
        });

        logger.info('✅ Socket initialized successfully');
        initLock = false;

    } catch (err) {
        logger.error('❌ Baileys initialization failed', { 
            error: err.message,
            stack: err.stack 
        });
        state.setError(err.message, 'error');

        if (state.retry_count < 1) {
            logger.info('Retrying initialization...');
            initLock = false;
            setTimeout(() => initializeBaileys(), CONFIG.reconnect_delay);
        } else {
            logger.error('Init failed after retry');
            state.setError('Initialization failed - Call POST /api/whatsapp/reset', 'error');
            initLock = false;
        }
    }
}

// ============================================================
// EXPRESS API
// ============================================================

const app = express();
app.use(express.json());

app.get('/health', (req, res) => {
    res.json({
        status: state.connected ? 'healthy' : 'unhealthy',
        connected: state.connected,
        timestamp: new Date().toISOString(),
    });
});

app.get('/status', (req, res) => {
    res.json(state.getStatus());
});

app.get('/api/whatsapp/status', (req, res) => {
    res.json(state.getStatus());
});

app.get('/api/whatsapp/qr', (req, res) => {
    res.json({
        has_qr: !!state.qr_code,
        qr_data: state.qr_code,
        state: state.state,
        message: state.connected ? 'Already connected' : 'Waiting for QR scan',
    });
});

app.post('/api/whatsapp/reset', async (req, res) => {
    try {
        logger.info('🔄 Reset requested');

        if (qrTimeout) clearTimeout(qrTimeout);
        
        if (globalSocket) {
            await new Promise(resolve => {
                globalSocket.end((err) => {
                    if (err) logger.error('Socket close error', { error: err.message });
                    globalSocket = null;
                    resolve();
                });
            });
        }

        if (fs.existsSync(CONFIG.auth_dir)) {
            fs.rmSync(CONFIG.auth_dir, { recursive: true, force: true });
            logger.info('Auth directory cleared');
        }

        state.retry_count = 0;
        state.state = 'initializing';
        state.qr_code = null;
        state.error_msg = null;

        initLock = false;
        setTimeout(() => initializeBaileys(), 1000);

        res.json({ status: 'reset_initiated', message: 'Waiting for new QR code' });
    } catch (err) {
        logger.error('Reset failed', { error: err.message });
        res.status(500).json({ error: err.message });
    }
});

app.post('/api/whatsapp/send-message', async (req, res) => {
    const { to, message } = req.body;

    if (!globalSocket || !state.connected) {
        return res.status(503).json({ error: 'WhatsApp not connected' });
    }

    if (!to || !message) {
        return res.status(400).json({ error: 'Missing: to, message' });
    }

    try {
        const result = await globalSocket.sendMessage(to, { text: message });
        res.json({ 
            status: 'sent',
            id: result.key.id,
            timestamp: new Date().toISOString(),
        });
    } catch (err) {
        logger.error('Send message failed', { error: err.message });
        res.status(500).json({ error: err.message });
    }
});

app.use((err, req, res, next) => {
    logger.error('Express error', { error: err.message });
    res.status(500).json({ error: 'Internal error' });
});

// ============================================================
// HEALTH CHECK & MONITORING
// ============================================================

function startHealthCheck() {
    setInterval(() => {
        const uptime = state.connected_at ? Date.now() - state.connected_at : 0;
        
        logger.debug('Health check', {
            connected: state.connected,
            state: state.state,
            uptime_min: Math.floor(uptime / 60000),
        });

        if (!state.connected && 
            state.state !== 'initializing' && 
            state.state !== 'waiting_auth' &&
            !initLock &&
            state.retry_count === 0) {
            
            logger.warn('Health check: Service not responding - attempting recovery');
            initializeBaileys();
        }
    }, CONFIG.health_check_interval);
}

// ============================================================
// STARTUP
// ============================================================

async function start() {
    console.log('\n╔' + '═'.repeat(70) + '╗');
    console.log('║' + '🚀 NEOBOT WhatsApp Service v5.0 (FIXED)'.padStart(55).padEnd(70) + '║');
    console.log('║' + ' '.repeat(70) + '║');
    console.log('║' + `Backend: ${CONFIG.backend_url}`.padEnd(70) + '║');
    console.log('║' + `Port: ${CONFIG.port}`.padEnd(70) + '║');
    console.log('║' + `Tenant: ${CONFIG.tenant_id}`.padEnd(70) + '║');
    console.log('║' + ` Started: ${new Date().toLocaleString('fr-FR')}`.padEnd(70) + '║');
    console.log('║' + ' '.repeat(70) + '║');
    console.log('║' + '⭐ FIXES: macOS browser, dynamic version, optimized timeouts'.padEnd(70) + '║');
    console.log('╚' + '═'.repeat(70) + '╝\n');

    fs.writeFileSync(CONFIG.pid_file, process.pid.toString());

    const server = app.listen(CONFIG.port, () => {
        logger.info(`✅ Server listening on port ${CONFIG.port}`);
        console.log('📡 API Endpoints:');
        console.log(`  GET  /health`);
        console.log(`  GET  /status`);
        console.log(`  GET  /api/whatsapp/status`);
        console.log(`  GET  /api/whatsapp/qr`);
        console.log(`  POST /api/whatsapp/reset`);
        console.log(`  POST /api/whatsapp/send-message\n`);
    });

    server.on('error', (err) => {
        if (err.code === 'EADDRINUSE') {
            logger.error(`Port ${CONFIG.port} already in use`);
            process.exit(1);
        }
        logger.error('Server error', { error: err.message });
        process.exit(1);
    });

    await initializeBaileys();
    startHealthCheck();

    const shutdown = (sig) => {
        logger.info(`${sig} received - shutting down gracefully`);
        
        if (qrTimeout) clearTimeout(qrTimeout);
        
        if (globalSocket) {
            globalSocket.end(() => {
                logger.info('Socket closed');
                process.exit(0);
            });
        } else {
            process.exit(0);
        }
    };

    process.on('SIGTERM', () => shutdown('SIGTERM'));
    process.on('SIGINT', () => shutdown('SIGINT'));

    process.on('uncaughtException', (err) => {
        logger.error('Uncaught exception', { error: err.message });
    });

    process.on('unhandledRejection', (err) => {
        logger.error('Unhandled rejection', { error: String(err) });
    });
}

start().catch(err => {
    logger.error('Fatal error', { error: err.message });
    process.exit(1);
});
