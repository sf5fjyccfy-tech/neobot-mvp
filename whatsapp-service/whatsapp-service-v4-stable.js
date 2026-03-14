#!/usr/bin/env node

/**
 * 🚀 NEOBOT WhatsApp Service - v4 STABLE EDITION
 * 
 * ✅ FIXES APPLIQUÉES:
 * - Baileys 6.7.21 (stable, pas 7.0.0-rc.1)
 * - Meilleure détection des erreurs WebSocket
 * - Retry logic amélioré avec exponential backoff
 * - QR code correctement affiché avant crash
 * - Autocorrection des configurations
 * 
 * 📋 FEATURES:
 * - Robust Baileys integration
 * - Automatic QR code generation and display
 * - Comprehensive error logging
 * - Auto-cleanup on disconnect
 * - Session persistence
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
const RECONNECT_TIMEOUT = process.env.WHATSAPP_RECONNECT_TIMEOUT || 5000;
const MAX_RETRIES = process.env.WHATSAPP_MAX_RETRIES || 10;

const AUTH_DIR = path.join(__dirname, 'auth_info_baileys');

// ========== STATE MANAGER ==========
class WhatsAppStateManager {
    constructor() {
        this.state = 'initializing';
        this.isConnected = false;
        this.currentQR = null;
        this.retryCount = 0;
        this.connectedAt = null;
        this.lastError = null;
    }

    setState(newState) {
        if (this.state !== newState) {
            console.log(`\n📊 État: ${this.state} → ${newState}`);
            this.state = newState;
        }
    }

    setQRCode(qrCode) {
        this.currentQR = qrCode;
        this.setState('waiting_qr');
        this.displayQRInstructions();
    }

    setConnected() {
        this.isConnected = true;
        this.connectedAt = Date.now();
        this.retryCount = 0;
        this.setState('connected');
        this.displayConnectedBanner();
    }

    setDisconnected(reason) {
        this.isConnected = false;
        this.lastError = reason;
        this.setState('disconnected');
    }

    displayQRInstructions() {
        console.log('\n' + '╔' + '═'.repeat(70) + '╗');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('║  🔐 SCANNING QR CODE REQUIRED                                     ║');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('║  ✅ Instructions:                                                 ║');
        console.log('║     1. Open WhatsApp on your phone                                ║');
        console.log('║     2. Go to: Settings → Linked Devices → Link a Device          ║');
        console.log('║     3. Point your phone at the QR code below (60 seconds)        ║');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('╚' + '═'.repeat(70) + '╝\n');

        if (this.currentQR) {
            try {
                qrcode.generate(this.currentQR, { small: true });
                console.log('\n✅ QR Code displayed above - Scan it NOW!\n');
            } catch (err) {
                console.error('❌ Error displaying QR:', err.message);
            }
        }
    }

    displayConnectedBanner() {
        console.log('\n' + '╔' + '═'.repeat(70) + '╗');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('║' + '🎉 CONNECTED SUCCESSFULLY! 🎉'.padStart(47).padEnd(70) + '║');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('║  ✅ Connected to WhatsApp                                        ║');
        console.log('║  🤖 NéoBot is operational                                        ║');
        console.log('║  📡 Backend: ' + BACKEND_URL.padEnd(56) + '║');
        console.log('║  🔌 Ready for messages                                           ║');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('╚' + '═'.repeat(70) + '╝\n');
    }
}

const stateManager = new WhatsAppStateManager();

// ========== EXPRESS SERVER ==========
const app = express();
app.use(express.json());

app.get('/health', (req, res) => {
    res.json({
        status: stateManager.isConnected ? 'ok' : 'connecting',
        connected: stateManager.isConnected,
        timestamp: new Date().toISOString()
    });
});

app.get('/status', (req, res) => {
    res.json({
        service: 'running',
        connected: stateManager.isConnected,
        state: stateManager.state,
        backend: BACKEND_URL,
        tenant_id: TENANT_ID
    });
});

app.get('/api/whatsapp/status', (req, res) => {
    res.json({
        state: stateManager.state,
        connected: stateManager.isConnected,
        qr_waiting: stateManager.state === 'waiting_qr',
        retries: stateManager.retryCount,
        max_retries: MAX_RETRIES,
        error: stateManager.lastError
    });
});

app.post('/api/whatsapp/restart', (req, res) => {
    console.log('🔄 Restart requested via API');
    if (sock) {
        sock.end(new Error('Manual restart'));
        sock = null;
    }
    setTimeout(() => {
        stateManager.retryCount = 0;
        connectToWhatsApp();
    }, 2000);
    res.json({ status: 'restarting' });
});

const server = app.listen(PORT, () => {
    console.log(`✅ WhatsApp service listening on port ${PORT}`);
});

// ========== WHATSAPP CONNECTION ==========
let sock = null;

async function connectToWhatsApp() {
    stateManager.retryCount++;
    console.log(`\n🔗 Attempting connection ${stateManager.retryCount}/${MAX_RETRIES}...`);

    if (stateManager.retryCount > MAX_RETRIES) {
        console.log('\n❌ Max retries reached!');
        return;
    }

    try {
        const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

        sock = makeWASocket({
            auth: state,
            printQRInTerminal: false,
            logger: pino({ level: 'silent' }), // Suppress Baileys noise
            browser: Browsers.ubuntu('Chrome'),
            connectTimeoutMs: 60000,
            keepAliveIntervalMs: 15000,
            defaultQueryTimeoutMs: 15000,
            emitOwnEventsInAutomaticMode: true,
            syncFullHistory: false,
            maxMsToWaitForConnection: 10000,
        });

        // ========== CONNECTION UPDATE ==========
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            // QR Code
            if (qr) {
                console.log('\n\n⚠️  QR CODE READY - SCAN NOW!\n');
                stateManager.setQRCode(qr);
            }

            // Connected
            if (connection === 'open') {
                console.log('✅ WhatsApp connection opened!');
                stateManager.setConnected();
                stateManager.retryCount = 0;
            }

            // Disconnected
            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const reason = lastDisconnect?.error?.message || 'Unknown';

                console.log(`\n⚠️  WhatsApp disconnected: ${reason} (code: ${statusCode})`);
                stateManager.setDisconnected(reason);

                // Auto-reconnect logic
                if (
                    statusCode === DisconnectReason.connectionClosed ||
                    statusCode === DisconnectReason.connectionLost ||
                    statusCode === DisconnectReason.restartRequired ||
                    !statusCode
                ) {
                    if (stateManager.retryCount < MAX_RETRIES) {
                        const delay = Math.min(
                            RECONNECT_TIMEOUT * Math.pow(2, stateManager.retryCount - 1),
                            30000
                        );
                        console.log(`⏳ Reconnecting in ${delay / 1000}s...`);
                        setTimeout(connectToWhatsApp, delay);
                    }
                } else if (statusCode === DisconnectReason.loggedOut) {
                    // Session expired - clean and restart
                    console.log('🔄 Session expired - cleaning and restarting...');
                    await cleanupSession();
                    setTimeout(connectToWhatsApp, 3000);
                }
            }
        });

        // Save credentials
        sock.ev.on('creds.update', saveCreds);

        // ========== MESSAGES ==========
        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            if (type !== 'notify') return;
            if (!stateManager.isConnected) return;

            for (const msg of messages) {
                if (!msg.message || msg.key.fromMe) continue;

                try {
                    const remoteJid = msg.key.remoteJid;
                    const phone = remoteJid.replace('@s.whatsapp.net', '').replace('@g.us', '');
                    const isGroup = msg.key.remoteJid.endsWith('@g.us');

                    const messageText = msg.message.conversation || 
                                      msg.message.extendedTextMessage?.text ||
                                      '[Media message]';

                    console.log(`📨 Message from ${phone}: ${messageText}`);

                    // Send to backend
                    await axios.post(`${BACKEND_URL}/webhooks/whatsapp`, {
                        from: phone,
                        message: messageText,
                        isGroup,
                        timestamp: msg.messageTimestamp
                    }).catch(err => {
                        console.log('⚠️  Backend unreachable:', err.message);
                    });
                } catch (err) {
                    console.error('❌ Error handling message:', err.message);
                }
            }
        });

        console.log('✅ Socket initialized successfully');

    } catch (err) {
        console.error(`\n❌ Connection error (attempt ${stateManager.retryCount}/${MAX_RETRIES})`);
        console.error(`   Error: ${err.message}\n`);
        
        if (err.message.includes('ECONNREFUSED') || err.message.includes('ETIMEDOUT')) {
            console.log('🔴 Network error - check internet connection');
        } else if (err.message.includes('WebSocket')) {
            console.log('🔴 WebSocket error - WhatsApp servers may be unreachable');
        }

        // Retry
        if (stateManager.retryCount < MAX_RETRIES) {
            const delay = Math.min(
                RECONNECT_TIMEOUT * Math.pow(2, stateManager.retryCount - 1),
                30000
            );
            console.log(`⏳ Retrying in ${delay / 1000}s...\n`);
            setTimeout(connectToWhatsApp, delay);
        } else {
            console.log('\n❌ Max retries reached. Waiting 30s before restart...\n');
            setTimeout(() => {
                stateManager.retryCount = 0;
                connectToWhatsApp();
            }, 30000);
        }
    }
}

async function cleanupSession() {
    try {
        if (fs.existsSync(AUTH_DIR)) {
            fs.rmSync(AUTH_DIR, { recursive: true, force: true });
            console.log('✅ Auth directory cleaned');
        }
    } catch (err) {
        console.error('⚠️  Error cleaning auth:', err.message);
    }
}

// ========== STARTUP ==========
console.log('\n════════════════════════════════════════════════════════════════');
console.log('   🚀 NEOBOT - WhatsApp Service v4 STABLE              ');
console.log('════════════════════════════════════════════════════════════════');
console.log(`   Backend: ${BACKEND_URL}`);
console.log(`   Port: ${PORT}`);
console.log(`   Tenant: ${TENANT_ID}`);
console.log('════════════════════════════════════════════════════════════════\n');

// Handle shutdown
process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down gracefully...');
    if (sock) {
        sock.end(new Error('Process termination'));
    }
    server.close(() => {
        console.log('✅ Server closed');
        process.exit(0);
    });
});

// Start connection
connectToWhatsApp();
