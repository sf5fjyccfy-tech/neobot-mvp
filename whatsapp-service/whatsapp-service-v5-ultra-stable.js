#!/usr/bin/env node

/**
 * 🚀 NEOBOT WhatsApp Service - v5 ULTRA STABLE
 * 
 * FIXES:
 * - Baileys 6.7.21 stable with enhanced error handling
 * - Alternative socket creation with proper configuration
 * - Better browser detection
 * - Automatic fallback strategies
 * - QR code display on first attempt
 * - Detailed error logging for debugging
 */

import makeWASocket, { 
    useMultiFileAuthState, 
    DisconnectReason,
    Browsers
} from '@whiskeysockets/baileys';
import pino from 'pino';
import axios from 'axios';
import express from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import qrcode from 'qrcode-terminal';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ========== CONFIGURATION ==========
const BACKEND_URL = process.env.WHATSAPP_BACKEND_URL || 'http://localhost:8000';
const PORT = process.env.WHATSAPP_PORT || 3001;
const TENANT_ID = process.env.TENANT_ID || 1;

const AUTH_DIR = path.join(__dirname, 'auth_info_baileys');

// ========== LOGGER ==========
class Logger {
    log(level, msg, data = {}) {
        const icons = { error: '❌', warn: '⚠️ ', info: 'ℹ️ ', success: '✅' };
        const timestamp = new Date().toISOString();
        console.log(`${icons[level] || '•'} [${timestamp}] ${msg}`, 
            Object.keys(data).length ? JSON.stringify(data) : '');
    }
    error(msg, data) { this.log('error', msg, data); }
    warn(msg, data) { this.log('warn', msg, data); }
    info(msg, data) { this.log('info', msg, data); }
    success(msg, data) { this.log('success', msg, data); }
}

const logger = new Logger();

// ========== STATE MANAGER ==========
class StateManager {
    constructor() {
        this.state = 'initializing';
        this.isConnected = false;
        this.qr = null;
        this.retries = 0;
        this.lastError = null;
    }

    setQR(qr) {
        this.state = 'waiting_qr';
        this.qr = qr;
        this.displayQRCode();
    }

    setConnected() {
        this.isConnected = true;
        this.state = 'connected';
        this.retries = 0;
        this.displaySuccess();
    }

    setDisconnected(error) {
        this.isConnected = false;
        this.state = 'disconnected';
        this.lastError = error;
    }

    displayQRCode() {
        console.log('\n' + '╔' + '═'.repeat(72) + '╗');
        console.log('║' + ' '.repeat(72) + '║');
        console.log('║' + '🔐 SCAN QR CODE WITH YOUR PHONE'.padStart(41).padEnd(72) + '║');
        console.log('║' + ' '.repeat(72) + '║');
        console.log('║' + 'Steps:                                                                ║');
        console.log('║' + '  1. Open WhatsApp → Settings → Linked Devices                       ║');
        console.log('║' + '  2. Click "Link a Device"                                           ║');
        console.log('║' + '  3. Scan the QR code below with your phone camera                   ║');
        console.log('║' + '  4. Confirm on your phone                                           ║');
        console.log('║' + ' '.repeat(72) + '║');
        console.log('╚' + '═'.repeat(72) + '╝\n');

        if (this.qr) {
            try {
                qrcode.generate(this.qr, { small: true });
                console.log('\n✅ QR Code displayed above.\n⏳ Waiting for scan (60 seconds timeout)...\n');
            } catch (e) {
                logger.error('Failed to display QR', { error: e.message });
            }
        }
    }

    displaySuccess() {
        console.log('\n' + '╔' + '═'.repeat(72) + '╗');
        console.log('║' + ' '.repeat(72) + '║');
        console.log('║' + '🎉 WHATSAPP CONNECTED SUCCESSFULLY! 🎉'.padStart(51).padEnd(72) + '║');
        console.log('║' + ' '.repeat(72) + '║');
        console.log('║' + '  ✅ Connection established                                          ║');
        console.log('║' + '  🤖 NéoBot is now operational                                       ║');
        console.log('║' + '  📡 Ready to receive messages                                       ║');
        console.log('║' + '  🔌 Backend: ' + BACKEND_URL.slice(0, 55).padEnd(65) + '║');
        console.log('║' + ' '.repeat(72) + '║');
        console.log('╚' + '═'.repeat(72) + '╝\n');
    }
}

const state = new StateManager();

// ========== EXPRESS SERVER ==========
const app = express();
app.use(express.json());

app.get('/health', (req, res) => {
    res.json({ status: state.isConnected ? 'ok' : 'connecting', connected: state.isConnected });
});

app.get('/status', (req, res) => {
    res.json({ 
        connected: state.isConnected, 
        state: state.state,
        backend: BACKEND_URL
    });
});

app.post('/api/whatsapp/restart', (req, res) => {
    logger.info('Restart requested via API');
    if (sock) {
        sock.end(new Error('User restart'));
        sock = null;
        state.state = 'initializing';
        state.retries = 0;
        setTimeout(connect, 2000);
    }
    res.json({ status: 'restarting' });
});

const server = app.listen(PORT, () => {
    logger.success(`WhatsApp service listening on port ${PORT}`);
});

// ========== CONNECTION ==========
let sock = null;
let connectionTimeout = null;

async function connect() {
    state.retries++;
    logger.info(`Attempting connection (${state.retries}/15)...`);

    // Circuit breaker after too many retries
    if (state.retries > 15) {
        logger.error('Max retries exceeded. Entering cool-down for 60s...');
        state.state = 'error';
        setTimeout(() => {
            state.retries = 0;
            connect();
        }, 60000);
        return;
    }

    try {
        // Load auth state
        const { state: authState, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

        logger.info('Creating Socket connection...');

        // Socket configuration with enhanced stability
        sock = makeWASocket({
            auth: authState,
            printQRInTerminal: false,
            logger: pino({ level: 'silent' }), // Suppress Baileys noise
            browser: Browsers.ubuntu('Chrome'),
            
            // Connection parameters
            connectTimeoutMs: 60000,
            keepAliveIntervalMs: 30000,
            defaultQueryTimeoutMs: 20000,
            maxMsToWaitForConnection: 10000,
            
            // Optimizations
            syncFullHistory: false,
            markOnlineOnConnect: true,
            shouldSyncHistoryMessage: false,
            shouldCatchupOnMiss: false,
            emitOwnEventsInAutomaticMode: true,
            shouldIgnoreJids: [],
        });

        logger.success('Socket created successfully');

        // ========== CONNECTION EVENTS ==========
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            // QR Code - Display immediately
            if (qr) {
                logger.success('QR Code generated - awaiting scan');
                state.setQR(qr);
            }

            // Connected
            if (connection === 'open') {
                logger.success('Connected to WhatsApp servers!');
                state.setConnected();
                clearTimeout(connectionTimeout);
            }

            // Disconnected
            if (connection === 'close') {
                const code = lastDisconnect?.error?.output?.statusCode;
                const reason = lastDisconnect?.error?.message || 'Unknown';

                logger.warn(`Disconnected`, { code, reason });
                state.setDisconnected(reason);

                // Determine if we should reconnect
                const shouldReconnect = (
                    !code ||
                    code === DisconnectReason.connectionClosed ||
                    code === DisconnectReason.connectionLost ||
                    code === DisconnectReason.restartRequired ||
                    code === DisconnectReason.timedOut
                );

                if (shouldReconnect && state.retries < 15) {
                    const delay = Math.min(1000 + (state.retries * 2000), 30000);
                    logger.info(`Reconnecting in ${delay / 1000}s...`);
                    setTimeout(connect, delay);
                }
            }
        });

        // Save credentials
        sock.ev.on('creds.update', saveCreds);

        // Messages
        sock.ev.on('messages.upsert', async ({ messages }) => {
            if (!state.isConnected) return;

            for (const msg of messages) {
                if (msg.key.fromMe || !msg.message) continue;
                try {
                    const phone = msg.key.remoteJid.replace(/[^0-9]/g, '').slice(-12);
                    const text = msg.message.conversation || 
                               msg.message.extendedTextMessage?.text ||
                               '[Non-text message]';
                    logger.info(`Message from ${phone}`, { text: text.slice(0, 50) });
                } catch (e) {
                    logger.warn('Error processing message', { error: e.message });
                }
            }
        });

        // Connection timeout watchdog
        clearTimeout(connectionTimeout);
        connectionTimeout = setTimeout(() => {
            if (!state.isConnected && sock) {
                logger.warn('Connection timeout - reconnecting');
                sock.end(new Error('Timeout'));
            }
        }, 120000);

    } catch (error) {
        logger.error('Connection error', { 
            message: error.message,
            attempt: state.retries
        });

        // Determine retry delay based on error type
        let delay = 5000;
        if (error.message.includes('ECONNREFUSED')) {
            delay = 10000;
            logger.warn('Connection refused - backend may be down');
        } else if (error.message.includes('WebSocket')) {
            delay = 15000;
            logger.warn('WebSocket error - network or server issue');
        }

        if (state.retries < 15) {
            const nextDelay = Math.min(delay + (state.retries * 1000), 30000);
            logger.info(`Retrying in ${nextDelay / 1000}s...`);
            setTimeout(connect, nextDelay);
        }
    }
}

// ========== STARTUP ==========
console.log(`
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║  🚀  NEOBOT WhatsApp Service v5 ULTRA STABLE                         ║
║                                                                        ║
║  Backend: ${BACKEND_URL.padEnd(63)}║
║  Port: ${String(PORT).padEnd(68)}║
║  Baileys: 6.7.21 (Stable)                                              ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
`);

// Cleanup on exit
process.on('SIGINT', () => {
    logger.info('Shutting down...');
    if (sock) sock.end(new Error('Shutdown'));
    server.close(() => process.exit(0));
});

// Start
connect();
