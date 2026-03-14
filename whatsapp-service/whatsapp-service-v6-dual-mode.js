#!/usr/bin/env node

/**
 * 🚀 NEOBOT WhatsApp Service - v6 MOCK + PRODUCTION MODE
 * 
 * DUAL MODE:
 * - MOCK MODE: Simule WhatsApp pour tests (fonctionne maintenant)
 * - PRODUCTION MODE: Utilise API WhatsApp Official (à configurer)
 * 
 * Pour switcher entre les modes:
 * export WHATSAPP_MODE=mock      # Mode test (défaut)
 * export WHATSAPP_MODE=official  # Mode production (après setup Meta)
 * export WHATSAPP_MODE=twilio    # Twilio API (optionnel)
 */

import express from 'express';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ========== CONFIGURATION ==========
const BACKEND_URL = process.env.WHATSAPP_BACKEND_URL || 'http://localhost:8000';
const PORT = process.env.WHATSAPP_PORT || 3001;
const TENANT_ID = process.env.TENANT_ID || 1;
const WHATSAPP_MODE = process.env.WHATSAPP_MODE || 'mock'; // mock | official | twilio

// ========== LOGGER ==========
const logger = {
    error: (msg, data = {}) => console.log(`❌ ${msg}`, data),
    warn: (msg, data = {}) => console.log(`⚠️  ${msg}`, data),
    info: (msg, data = {}) => console.log(`ℹ️  ${msg}`, data),
    success: (msg, data = {}) => console.log(`✅ ${msg}`, data),
};

// ========== STATE ==========
let state = {
    connected: false,
    mode: WHATSAPP_MODE,
    qr: null,
    connectedAt: null,
    messagesReceived: 0,
};

// ========== MOCK WHATSAPP SERVICE ==========
class MockWhatsAppService {
    constructor() {
        this.connected = false;
        logger.info('MockWhatsApp service initialized');
    }

    async connect() {
        logger.info('MockWhatsApp: Simulating connection...');
        
        // Simulate QR code generation
        await this.simulateQRDisplay();
        
        // Simulate connection after 5 seconds
        setTimeout(() => {
            this.connected = true;
            state.connected = true;
            state.connectedAt = Date.now();
            logger.success('MockWhatsApp: Connected!');
        }, 5000);
    }

    simulateQRDisplay() {
        return new Promise((resolve) => {
            // Simulate QR code
            const mockQR = `
╔══════════════════════════════════════════╗
║        📱 MOCK QR CODE (Test Mode)       ║
║                                          ║
║  This is a SIMULATED QR code for         ║
║  testing purposes. All messages will     ║
║  be mocked. No real WhatsApp connection. ║
║                                          ║
║  To use REAL WhatsApp:                   ║
║  1. Set WHATSAPP_MODE=official           ║
║  2. Configure Meta API credentials       ║
║  3. Restart the service                  ║
║                                          ║
╚══════════════════════════════════════════╝
            `;
            
            console.log(mockQR);
            logger.success('MockWhatsApp: QR displayed (simulated)');
            
            state.qr = 'MOCK_QR_CODE_FOR_TESTING';
            resolve();
        });
    }

    // Simulate receiving messages
    async simulateIncomingMessage() {
        const mockMessages = [
            { phone: '5521987654321', text: 'Olá! Testando o NéoBot 🤖' },
            { phone: '5521987654322', text: 'Como você está?' },
            { phone: '5521987654323', text: 'Pode responder?' },
        ];

        const randomMsg = mockMessages[Math.floor(Math.random() * mockMessages.length)];
        
        logger.info('MockWhatsApp: Simulated incoming message', { 
            from: randomMsg.phone, 
            text: randomMsg.text 
        });

        // Send to backend
        try {
            await axios.post(`${BACKEND_URL}/webhooks/whatsapp`, {
                from: randomMsg.phone,
                message: randomMsg.text,
                timestamp: Date.now(),
                isGroup: false,
                isMock: true
            });
            
            state.messagesReceived++;
            logger.success('Message sent to backend', { count: state.messagesReceived });
        } catch (err) {
            logger.warn('Backend unreachable', { error: err.message });
        }
    }

    disconnect() {
        this.connected = false;
        state.connected = false;
        logger.info('MockWhatsApp: Disconnected');
    }
}

// ========== OFFICIAL WHATSAPP API SERVICE ==========
class OfficialWhatsAppService {
    constructor() {
        this.phoneNumberId = process.env.WHATSAPP_PHONE_NUMBER_ID;
        this.accessToken = process.env.WHATSAPP_ACCESS_TOKEN;
        this.connected = false;

        if (!this.phoneNumberId || !this.accessToken) {
            logger.error('Official WhatsApp API credentials not set!');
            logger.info('Please set:', {
                WHATSAPP_PHONE_NUMBER_ID: 'your-phone-number-id',
                WHATSAPP_ACCESS_TOKEN: 'your-access-token'
            });
        }
    }

    async connect() {
        if (!this.phoneNumberId || !this.accessToken) {
            logger.error('Cannot connect: Missing credentials');
            return;
        }

        logger.info('Official WhatsApp API: Connecting...');
        
        try {
            // Verify token
            const response = await axios.get(
                `https://graph.instagram.com/v20.0/${this.phoneNumberId}`,
                { headers: { Authorization: `Bearer ${this.accessToken}` } }
            );

            this.connected = true;
            state.connected = true;
            state.connectedAt = Date.now();
            logger.success('Official WhatsApp API: Connected!');
        } catch (err) {
            logger.error('Official WhatsApp API connection failed', { 
                error: err.response?.data?.error?.message || err.message 
            });
        }
    }

    disconnect() {
        this.connected = false;
        state.connected = false;
        logger.info('Official WhatsApp API: Disconnected');
    }

    async sendMessage(to, message) {
        if (!this.connected) {
            logger.error('Not connected to Official API');
            return;
        }

        try {
            await axios.post(
                `https://graph.instagram.com/v20.0/${this.phoneNumberId}/messages`,
                {
                    messaging_product: 'whatsapp',
                    to: to,
                    type: 'text',
                    text: { body: message }
                },
                { headers: { Authorization: `Bearer ${this.accessToken}` } }
            );
            
            logger.success('Message sent via Official API', { to });
        } catch (err) {
            logger.error('Failed to send message', { error: err.message });
        }
    }
}

// ========== EXPRESS APP ==========
const app = express();
app.use(express.json());

// Select service based on mode
let whatsappService;
if (WHATSAPP_MODE === 'mock') {
    whatsappService = new MockWhatsAppService();
    logger.warn('Using MOCK WhatsApp (for testing only)');
} else if (WHATSAPP_MODE === 'official') {
    whatsappService = new OfficialWhatsAppService();
} else {
    logger.error(`Unknown mode: ${WHATSAPP_MODE}`);
    process.exit(1);
}

// ========== ENDPOINTS ==========
app.get('/health', (req, res) => {
    res.json({
        status: state.connected ? 'ok' : 'connecting',
        mode: state.mode,
        connected: state.connected
    });
});

app.get('/status', (req, res) => {
    res.json({
        service: 'running',
        mode: state.mode,
        connected: state.connected,
        connectedAt: state.connectedAt ? new Date(state.connectedAt).toISOString() : null,
        messagesReceived: state.messagesReceived
    });
});

app.post('/test/receive-message', (req, res) => {
    // Test endpoint to simulate incoming messages
    if (whatsappService instanceof MockWhatsAppService) {
        whatsappService.simulateIncomingMessage();
        res.json({ success: true, message: 'Simulated message sent to backend' });
    } else {
        res.status(400).json({ error: 'Only available in mock mode' });
    }
});

app.post('/send-message', async (req, res) => {
    const { to, message } = req.body;
    
    if (!to || !message) {
        return res.status(400).json({ error: 'Missing to or message' });
    }

    if (whatsappService instanceof OfficialWhatsAppService) {
        await whatsappService.sendMessage(to, message);
        res.json({ success: true });
    } else {
        logger.info('MockWhatsApp: Would send', { to, message });
        res.json({ success: true, mock: true });
    }
});

// ========== STARTUP ==========
const server = app.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║  🚀  NEOBOT WhatsApp Service v6 (${WHATSAPP_MODE.toUpperCase()})                     ║
║                                                                    ║
║  Mode: ${state.mode === 'mock' ? '🧪 MOCK (Testing)' : '📱 OFFICIAL (Production)'}                                       ║
║  Backend: ${BACKEND_URL.padEnd(53)}║
║  Port: ${String(PORT).padEnd(56)}║
║                                                                    ║
║  Endpoints:                                                        ║
║    GET  /health                - Health check                     ║
║    GET  /status                - Service status                   ║
║    POST /send-message          - Send message                     ║
║                                                                    ║
${state.mode === 'mock' ? `║    POST /test/receive-message  - Simulate incoming message (mock only)     ║` : `║                                                                    ║`}
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    `);
});

// Connect to WhatsApp service
whatsappService.connect();

// If mock mode, simulate incoming messages every 30 seconds
if (WHATSAPP_MODE === 'mock') {
    setInterval(() => {
        if (state.connected) {
            whatsappService.simulateIncomingMessage();
        }
    }, 30000);
}

// Graceful shutdown
process.on('SIGINT', () => {
    logger.info('Shutting down...');
    whatsappService.disconnect();
    server.close(() => process.exit(0));
});
