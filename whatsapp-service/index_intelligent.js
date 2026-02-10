import makeWASocket, { useMultiFileAuthState, DisconnectReason } from '@whiskeysockets/baileys';
import pino from 'pino';
import axios from 'axios';
import qrcode from 'qrcode-terminal';
import express from 'express';
import fs from 'fs';
import path from 'path';

// ========== CONFIGURATION ==========
const BACKEND_URL = process.env.WHATSAPP_BACKEND_URL || 'http://localhost:8000';
const PORT = process.env.WHATSAPP_PORT || 3001;
const TENANT_ID = process.env.TENANT_ID || 1;
const RECONNECT_TIMEOUT = process.env.WHATSAPP_RECONNECT_TIMEOUT || 5000;
const MAX_RETRIES = process.env.WHATSAPP_MAX_RETRIES || 5;

// ========== GESTION D'ÉTAT INTELLIGENTE ==========
class WhatsAppStateManager {
    constructor() {
        this.state = 'initializing'; // initializing, waiting_qr, connected, disconnected, error
        this.isConnected = false;
        this.currentQR = null;
        this.qrExpiry = null;
        this.lastError = null;
        this.retryCount = 0;
        this.connectedAt = null;
        this.disconnectReason = null;
        this.sessionExpired = false;
    }

    setState(newState) {
        const oldState = this.state;
        this.state = newState;
        console.log(`\n📊 État: ${oldState} → ${newState}`);
    }

    setQRCode(qrCode) {
        this.currentQR = qrCode;
        this.qrExpiry = Date.now() + (60 * 1000); // 60 secondes avant expiration
        this.setState('waiting_qr');
        this.displayQRInstructions();
    }

    setConnected() {
        this.isConnected = true;
        this.connectedAt = Date.now();
        this.retryCount = 0;
        this.sessionExpired = false;
        this.setState('connected');
        this.displayConnectedBanner();
    }

    setDisconnected(reason, code) {
        this.isConnected = false;
        this.disconnectReason = reason;
        this.lastError = `Code: ${code}`;
        this.setState('disconnected');
        this.displayDisconnectMessage(reason, code);
    }

    displayQRInstructions() {
        console.log('\n' + '╔' + '═'.repeat(68) + '╗');
        console.log('║ 📱 VEUILLEZ SCANNER LE CODE QR CI-DESSOUS                     ║');
        console.log('║ 🔐 avec votre appareil WhatsApp                                 ║');
        console.log('║ ⏱️  Valide pendant 60 secondes                                  ║');
        console.log('║                                                                  ║');
        console.log('║ 💡 Instructions:                                                 ║');
        console.log('║ 1. Ouvrez WhatsApp sur votre téléphone                          ║');
        console.log('║ 2. Allez dans: Paramètres → Appareils connectés                ║');
        console.log('║ 3. Cliquez sur "Connecter un appareil"                          ║');
        console.log('║ 4. Positionnez votre téléphone face à l\'écran                   ║');
        console.log('║ 5. Scannez le code QR below                                      ║');
        console.log('║                                                                  ║');
        console.log('╚' + '═'.repeat(68) + '╝\n');

        if (this.currentQR) {
            qrcode.generate(this.currentQR, { small: true });
        }

        console.log('\n' + '─'.repeat(70));
        console.log('⏳ En attente de scan... (60s)');
        console.log('─'.repeat(70) + '\n');
    }

    displayConnectedBanner() {
        console.log('\n' + '╔' + '═'.repeat(68) + '╗');
        console.log('║' + ' '.repeat(68) + '║');
        console.log('║' + '🎉 CONNEXION RÉUSSIE! 🎉'.padStart(45).padEnd(68) + '║');
        console.log('║' + ' '.repeat(68) + '║');
        console.log('║  ✅ Connecté à WhatsApp                                         ║');
        console.log('║  🤖 NéoBot est opérationnel                                     ║');
        console.log('║  📡 Backend:', `${BACKEND_URL}`.padEnd(48) + '║');
        console.log('║  🔌 Prêt à recevoir des messages                                ║');
        console.log('║' + ' '.repeat(68) + '║');
        console.log('╚' + '═'.repeat(68) + '╝\n');
    }

    displayDisconnectMessage(reason, code) {
        console.log('\n' + '╔' + '═'.repeat(68) + '╗');
        console.log('║' + ' '.repeat(68) + '║');
        console.log('║' + '🔴 DÉCONNECTÉ 🔴'.padStart(42).padEnd(68) + '║');
        console.log('║' + ' '.repeat(68) + '║');

        // Messages intelligents par code d'erreur
        const messages = this.getDisconnectMessages(code, reason);
        messages.forEach(msg => {
            console.log('║  ' + msg.padEnd(66) + '║');
        });

        console.log('║' + ' '.repeat(68) + '║');
        console.log('╚' + '═'.repeat(68) + '╝\n');
    }

    getDisconnectMessages(code, reason) {
        const messages = [];

        switch (code) {
            case DisconnectReason.connectionClosed:
                messages.push('❌ Connexion fermée par le serveur WhatsApp');
                messages.push('💡 Action: Relancement automatique du service');
                messages.push('⏳ Reconnexion dans 5 secondes...');
                break;

            case DisconnectReason.connectionLost:
                messages.push('❌ Connexion perdue (timeout)');
                messages.push('💡 Action: Vérification de la connexion réseau');
                messages.push('⏳ Tentative de reconnexion...');
                break;

            case DisconnectReason.connectionReplaced:
                messages.push('⚠️  Session remplacée (connectée ailleurs)');
                messages.push('💡 Action: Une autre session WhatsApp a pris le contrôle');
                messages.push('📱 À rescanner depuis ce terminal');
                messages.push('⏳ Redémarrage nécessaire...');
                this.sessionExpired = true;
                break;

            case DisconnectReason.loggedOut:
                messages.push('🔐 Session expirée ou supprimée');
                messages.push('💡 Action: Authentification WhatsApp requise');
                messages.push('📱 Veuillez scanner le nouveau code QR');
                this.sessionExpired = true;
                break;

            case DisconnectReason.restartRequired:
                messages.push('🔄 Redémarrage requis par WhatsApp');
                messages.push('💡 Action: Service en redémarrage automatique');
                messages.push('⏳ Relancement du service...');
                break;

            case DisconnectReason.multideviceMismatch:
                messages.push('⚠️  Incompatibilité multi-appareil détectée');
                messages.push('💡 Action: Vérification des paramètres WhatsApp');
                messages.push('📱 Resscan peut être nécessaire');
                break;

            case 408:
                messages.push('⏱️  Timeout: Le serveur WhatsApp ne répond pas');
                messages.push('💡 Action: Vérification de la connexion internet');
                messages.push('🌐 Assurez-vous d\'avoir une connexion internet stable');
                break;

            case 405:
                messages.push('❌ Erreur 405: Méthode non autorisée');
                messages.push('💡 Action: Version de Baileys incompatible?');
                messages.push('🔄 Tentative de reconnexion...');
                break;

            default:
                messages.push(`❌ Erreur: ${reason || code}`);
                messages.push('💡 Action: Reconnexion automatique');
                messages.push('⏳ Nouvelle tentative en cours...');
        }

        return messages;
    }

    getDetailedStatus() {
        return {
            state: this.state,
            isConnected: this.isConnected,
            retryCount: this.retryCount,
            maxRetries: MAX_RETRIES,
            connectedAt: this.connectedAt ? new Date(this.connectedAt).toISOString() : null,
            sessionExpired: this.sessionExpired,
            lastError: this.lastError,
            disconnectReason: this.disconnectReason,
            qrActive: this.state === 'waiting_qr',
            qrExpiry: this.qrExpiry ? new Date(this.qrExpiry).toISOString() : null,
            messages: {
                en: this.getStatusMessageEn(),
                fr: this.getStatusMessageFr()
            }
        };
    }

    getStatusMessageFr() {
        switch (this.state) {
            case 'initializing':
                return 'Initialisation en cours...';
            case 'waiting_qr':
                return 'En attente de scan du code QR';
            case 'connected':
                return '✅ Connecté et opérationnel';
            case 'disconnected':
                return '🔴 Déconnecté - Reconnexion...';
            case 'error':
                return '❌ Erreur - Vérification en cours';
            default:
                return 'État inconnu';
        }
    }

    getStatusMessageEn() {
        switch (this.state) {
            case 'initializing':
                return 'Initializing...';
            case 'waiting_qr':
                return 'Waiting for QR scan';
            case 'connected':
                return '✅ Connected and operational';
            case 'disconnected':
                return '🔴 Disconnected - Reconnecting...';
            case 'error':
                return '❌ Error - Checking...';
            default:
                return 'Unknown state';
        }
    }
}

// Instance globale
const stateManager = new WhatsAppStateManager();

// ========== EXPRESS SERVER ==========
const app = express();
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: stateManager.isConnected ? 'connected' : 'disconnected',
        connected: stateManager.isConnected,
        backend: BACKEND_URL,
        timestamp: new Date().toISOString()
    });
});

// Status endpoint
app.get('/status', (req, res) => {
    res.json({
        whatsapp_service: 'running',
        connected: stateManager.isConnected,
        state: stateManager.state,
        backend_url: BACKEND_URL,
        tenant_id: TENANT_ID,
        timestamp: new Date().toISOString()
    });
});

// Detailed status endpoint
app.get('/api/whatsapp/status', (req, res) => {
    res.json(stateManager.getDetailedStatus());
});

// QR Status endpoint (pour voir l'état du QR spécifiquement)
app.get('/api/whatsapp/qr-status', (req, res) => {
    res.json({
        qr_active: stateManager.state === 'waiting_qr',
        state: stateManager.state,
        message: stateManager.state === 'waiting_qr'
            ? 'QR code en attente - Scannez avec votre téléphone'
            : `État actuel: ${stateManager.getStatusMessageFr()}`,
        instruction_fr: stateManager.state === 'waiting_qr'
            ? 'Ouvrez WhatsApp → Paramètres → Appareils connectés → Scannez le code QR'
            : 'Service déjà connecté',
        instruction_en: stateManager.state === 'waiting_qr'
            ? 'Open WhatsApp → Settings → Linked Devices → Scan QR Code'
            : 'Service already connected',
        timestamp: new Date().toISOString()
    });
});

// Restart connection endpoint
app.post('/api/whatsapp/restart', (req, res) => {
    console.log('🔄 Redémarrage demandé via API');
    if (sock) {
        sock.end(new Error('Manual restart'));
    }
    setTimeout(() => {
        connectToWhatsApp();
    }, 2000);
    res.json({
        status: 'restarting',
        message: 'Service en redémarrage...'
    });
});

app.listen(PORT, () => {
    console.log(`✅ WhatsApp service HTTP server running on port ${PORT}`);
    console.log(`📊 Endpoints disponibles:`);
    console.log(`   GET  /health                    - Health check simple`);
    console.log(`   GET  /status                    - État du service`);
    console.log(`   GET  /api/whatsapp/status       - État détaillé`);
    console.log(`   GET  /api/whatsapp/qr-status    - État du QR code`);
    console.log(`   POST /api/whatsapp/restart      - Redémarrer`);
});

// ========== WHATSAPP CONNECTION ==========
let sock = null;

async function connectToWhatsApp() {
    stateManager.retryCount++;
    console.log(`\n🔗 Tentative de connexion ${stateManager.retryCount}/${MAX_RETRIES}...`);

    if (stateManager.retryCount > MAX_RETRIES) {
        stateManager.setState('error');
        console.log('\n' + '╔' + '═'.repeat(68) + '╗');
        console.log('║' + ' '.repeat(68) + '║');
        console.log('║' + '❌ ERREUR CRITIQUE ❌'.padStart(44).padEnd(68) + '║');
        console.log('║' + ' '.repeat(68) + '║');
        console.log('║  Impossible de se connecter après ' + `${MAX_RETRIES}`.padEnd(33) + '║');
        console.log('║  tentatives.                                                    ║');
        console.log('║                                                                  ║');
        console.log('║  Solutions:                                                      ║');
        console.log('║  1. Vérifiez votre connexion internet                           ║');
        console.log('║  2. Vérifiez que le backend est actif                           ║');
        console.log('║  3. Redémarrez le service                                       ║');
        console.log('║  4. Connectez-vous à WhatsApp sur votre téléphone               ║');
        console.log('║                                                                  ║');
        console.log('╚' + '═'.repeat(68) + '╝\n');
        
        // Redémarrage automatique après 30 secondes
        console.log('🔄 Redémarrage automatique dans 30 secondes...\n');
        setTimeout(() => {
            stateManager.retryCount = 0;
            connectToWhatsApp();
        }, 30000);
        return;
    }

    try {
        const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');

        sock = makeWASocket({
            auth: state,
            printQRInTerminal: false,
            logger: pino({ level: 'error' }),
            browser: ["Ubuntu", "Chrome", "110.0"],
            connectTimeoutMs: 30000,
            keepAliveIntervalMs: 15000,
            defaultQueryTimeoutMs: 10000,
        });

        // ========== CONNECTION UPDATE EVENT ==========
        sock.ev.on('connection.update', (update) => {
            const { connection, lastDisconnect, qr } = update;

            // Afficher QR code
            if (qr) {
                stateManager.setQRCode(qr);
            }

            // Connexion ouverte
            if (connection === 'open') {
                stateManager.setConnected();
            }

            // Connexion fermée
            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = 
                    statusCode === DisconnectReason.connectionClosed ||
                    statusCode === DisconnectReason.connectionLost ||
                    statusCode === DisconnectReason.restartRequired;

                stateManager.setDisconnected(lastDisconnect?.error?.message, statusCode);

                if (shouldReconnect) {
                    if (stateManager.retryCount < MAX_RETRIES) {
                        const delay = Math.min(RECONNECT_TIMEOUT * Math.pow(2, stateManager.retryCount - 1), 30000);
                        console.log(`⏳ Nouvelle tentative dans ${delay / 1000}s...\n`);
                        setTimeout(connectToWhatsApp, delay);
                    }
                }
            }
        });

        // Sauvegarder credentials
        sock.ev.on('creds.update', saveCreds);

        // ========== MESSAGE HANDLER ==========
        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            if (type !== 'notify' || !stateManager.isConnected) return;

            for (const msg of messages) {
                // Ignorer les messages envoyés par le bot
                if (!msg.message || msg.key.fromMe) continue;

                const remoteJid = msg.key.remoteJid;
                const phone = remoteJid.replace('@s.whatsapp.net', '');
                const text = msg.message.conversation || msg.message.extendedTextMessage?.text || '';
                const senderName = msg.pushName || `Client ${phone.slice(-4)}`;

                if (!text.trim()) continue;

                console.log(`\n📱 Message de ${senderName}:`);
                console.log(`   Texte: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"`);

                try {
                    // Envoyer au backend
                    console.log(`   📤 Envoi au backend...`);
                    const response = await axios.post(
                        `${BACKEND_URL}/api/whatsapp/message`,
                        {
                            from: phone,
                            message: text,
                            tenant_id: TENANT_ID,
                            timestamp: new Date().toISOString()
                        },
                        { timeout: 30000 }
                    );

                    const botResponse = response.data?.response;

                    if (!botResponse) {
                        console.log(`   ⚠️ Pas de réponse du backend`);
                        return;
                    }

                    console.log(`   🤖 Réponse: "${botResponse.substring(0, 50)}${botResponse.length > 50 ? '...' : ''}"`);

                    // Envoyer la réponse via WhatsApp
                    await sock.sendMessage(remoteJid, { text: botResponse });
                    console.log(`   ✅ Réponse envoyée\n`);

                } catch (error) {
                    console.error(`   ❌ Erreur: ${error.message}`);
                    console.log('');
                }
            }
        });

        return sock;

    } catch (error) {
        console.error(`❌ Erreur connexion: ${error.message}`);
        const delay = Math.min(RECONNECT_TIMEOUT * Math.pow(2, stateManager.retryCount - 1), 30000);
        console.log(`⏳ Nouvelle tentative dans ${delay / 1000}s...\n`);
        setTimeout(connectToWhatsApp, delay);
    }
}

// ========== MAIN ==========
async function main() {
    console.log('\n' + '═'.repeat(70));
    console.log('🚀 NÉOBOT - WhatsApp Service (Version Intelligente)');
    console.log('═'.repeat(70));
    console.log(`Backend URL: ${BACKEND_URL}`);
    console.log(`Tenant ID: ${TENANT_ID}`);
    console.log(`HTTP Port: ${PORT}`);
    console.log(`Version: 3.0 (Gestion d'état intelligente)`);
    console.log(`Date: ${new Date().toLocaleString('fr-FR')}`);
    console.log('═'.repeat(70));

    stateManager.setState('initializing');
    await connectToWhatsApp();
}

// Gestion des signaux
process.on('SIGINT', () => {
    console.log('\n🛑 Arrêt du service...');
    if (sock) {
        sock.end(new Error('Client disconnect'));
    }
    process.exit(0);
});

// Démarrage
main().catch(console.error);
