import makeWASocket, { useMultiFileAuthState, DisconnectReason } from '@whiskeysockets/baileys';
import pino from 'pino';
import axios from 'axios';
import qrcode from 'qrcode-terminal';
import express from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ========== CONFIGURATION ==========
const BACKEND_URL = process.env.WHATSAPP_BACKEND_URL || 'http://localhost:8000';
const PORT = process.env.WHATSAPP_PORT || 3001;
const TENANT_ID = process.env.TENANT_ID || 1;
const RECONNECT_TIMEOUT = 5000;
const MAX_RETRIES = 5;
const SESSION_TIMEOUT = 3600000; // 1 heure

// Chemins des sessions
const AUTH_DIR = path.join(__dirname, 'auth_info_baileys');
const BACKUP_AUTH_DIR = path.join(__dirname, '.wwebjs_auth');
const SESSION_DIR = path.join(__dirname, 'session');
const TIMEOUTS_FILE = path.join(__dirname, 'session_timeouts.json');

// Logger - Simplifié sans pino-pretty pour éviter les dépendances
const logger = pino({ level: 'error' });

// ========== DÉTECTEUR DE SESSIONS EXPIRÉES ==========
class SessionManager {
    constructor() {
        this.sessionStartTime = null;
        this.sessionTimeouts = this.loadTimeouts();
        this.isSessionExpired = false;
    }

    loadTimeouts() {
        try {
            if (fs.existsSync(TIMEOUTS_FILE)) {
                return JSON.parse(fs.readFileSync(TIMEOUTS_FILE, 'utf8'));
            }
        } catch (e) {
            // Ignorer
        }
        return {};
    }

    saveTimeouts() {
        try {
            fs.writeFileSync(TIMEOUTS_FILE, JSON.stringify(this.sessionTimeouts, null, 2));
        } catch (e) {
            // Ignorer
        }
    }

    startSession() {
        this.sessionStartTime = Date.now();
        this.sessionTimeouts[TENANT_ID] = this.sessionStartTime;
        this.isSessionExpired = false;
        this.saveTimeouts();
    }

    isExpired() {
        if (!this.sessionStartTime) return false;
        const elapsed = Date.now() - this.sessionStartTime;
        return elapsed > SESSION_TIMEOUT;
    }

    cleanup() {
        return new Promise((resolve) => {
            console.log('\n🧹 Nettoyage des sessions expirées...');
            
            const dirsToClean = [AUTH_DIR, BACKUP_AUTH_DIR, SESSION_DIR];
            let cleaned = 0;

            dirsToClean.forEach(dir => {
                if (fs.existsSync(dir)) {
                    try {
                        fs.rmSync(dir, { recursive: true, force: true });
                        console.log(`   ✅ Supprimé: ${dir}`);
                        cleaned++;
                    } catch (e) {
                        console.log(`   ⚠️  Erreur suppression ${dir}: ${e.message}`);
                    }
                }
            });

            // Réinitialiser
            this.sessionStartTime = null;
            this.sessionTimeouts[TENANT_ID] = null;
            this.isSessionExpired = false;
            this.saveTimeouts();

            console.log(`✅ Nettoyage terminé (${cleaned} dossiers)\n`);
            resolve();
        });
    }

    async resetSession() {
        console.log('🔄 Réinitialisation de la session...');
        await this.cleanup();
        console.log('💾 Session réinitialisée - Nouveau QR code en attente\n');
    }
}

// Instance du gestionnaire de sessions
const sessionManager = new SessionManager();

// ========== GESTION D'ÉTAT ==========
class WhatsAppStateManager {
    constructor() {
        this.state = 'initializing';
        this.isConnected = false;
        this.currentQR = null;
        this.lastError = null;
        this.retryCount = 0;
        this.connectedAt = null;
        this.sock = null;
    }

    setState(newState) {
        const oldState = this.state;
        this.state = newState;
        console.log(`\n📊 État: ${oldState} → ${newState}`);
    }

    setQRCode(qrCode) {
        this.currentQR = qrCode;
        this.setState('waiting_qr');
        this.displayQRBanner();
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
        this.displayDisconnectBanner(reason);
    }

    displayQRBanner() {
        console.log('\n' + '╔' + '═'.repeat(70) + '╗');
        console.log('║' + '📱 SCANNER LE CODE QR POUR CONNECTER WHATSAPP'.padStart(56).padEnd(70) + '║');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('║' + '✅ Appareil: NéoBot WhatsApp Service'.padEnd(70) + '║');
        console.log('║' + '⏱️  Valide: 60 secondes'.padEnd(70) + '║');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('║' + 'Instructions:'.padEnd(70) + '║');
        console.log('║' + '1. Ouvrez WhatsApp sur votre téléphone'.padEnd(70) + '║');
        console.log('║' + '2. Allez dans: Paramètres → Appareils connectés'.padEnd(70) + '║');
        console.log('║' + '3. Cliquez sur "Connecter un appareil"'.padEnd(70) + '║');
        console.log('║' + '4. Positionnez votre téléphone face à l\'écran'.padEnd(70) + '║');
        console.log('║' + '5. Scannez le code QR ci-dessous'.padEnd(70) + '║');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('╚' + '═'.repeat(70) + '╝\n');

        if (this.currentQR) {
            qrcode.generate(this.currentQR, { small: true });
            console.log('');
        }
    }

    displayConnectedBanner() {
        console.log('\n' + '╔' + '═'.repeat(70) + '╗');
        console.log('║' + '🎉 CONNEXION RÉUSSIE 🎉'.padStart(48).padEnd(70) + '║');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('║' + '✅ Connecté à WhatsApp'.padEnd(70) + '║');
        console.log('║' + '🤖 NéoBot est opérationnel'.padEnd(70) + '║');
        console.log('║' + `📡 Backend: ${BACKEND_URL}`.padEnd(70) + '║');
        console.log('║' + `🔌 Port: ${PORT}`.padEnd(70) + '║');
        console.log('║' + '✅ Prêt à recevoir/envoyer des messages'.padEnd(70) + '║');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('╚' + '═'.repeat(70) + '╝\n');
    }

    displayDisconnectBanner(reason) {
        console.log('\n' + '╔' + '═'.repeat(70) + '╗');
        console.log('║' + '🔴 DÉCONNECTÉ 🔴'.padStart(44).padEnd(70) + '║');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('║' + `❌ ${reason}`.padEnd(70) + '║');
        console.log('║' + '🔄 Tentative de reconnexion...'.padEnd(70) + '║');
        console.log('║' + ' '.repeat(70) + '║');
        console.log('╚' + '═'.repeat(70) + '╝\n');
    }

    getStatus() {
        return {
            state: this.state,
            isConnected: this.isConnected,
            connectedAt: this.connectedAt ? new Date(this.connectedAt).toISOString() : null,
            sessionExpired: sessionManager.isSessionExpired,
            lastError: this.lastError,
            uptime: this.connectedAt ? Date.now() - this.connectedAt : 0,
            retryCount: this.retryCount,
            maxRetries: MAX_RETRIES
        };
    }
}

const stateManager = new WhatsAppStateManager();

// ========== INITIALISATION WHATSAPP ==========
async function initializeWhatsApp() {
    try {
        // Vérifier si session est expirée
        if (sessionManager.isExpired()) {
            console.log('⚠️  Session expirée détectée, nettoyage...');
            await sessionManager.resetSession();
        }

        // Créer les dossiers s'ils n'existent pas
        [AUTH_DIR, BACKUP_AUTH_DIR, SESSION_DIR].forEach(dir => {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        });

        // Utiliser useMultiFileAuthState
        const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

        // Configuration Baileys ROBUSTE
        const sock = makeWASocket({
            auth: state,
            printQRInTerminal: false, // Gérer notre propre QR
            logger: pino({ level: 'error' }),
            browser: ['NéoBot', 'Chrome', '5.0'],
            syncFullHistory: false,
            maxMsgsInMemory: 100,
            generateHighQualityLinkPreview: false,
            shouldIgnoreJid: () => false,
            // Important: ces options préviennent les erreurs 405
            fetchLatestBaileysVersion: false,
            retryRequestDelayMs: 5000,
            getMessage: async (key) => {
                return {
                    conversation: 'Message non trouvé en cache',
                };
            },
        });

        stateManager.sock = sock;

        // ===== EVENT HANDLERS =====
        
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (connection === 'close') {
                const shouldReconnect =
                    lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;

                if (shouldReconnect) {
                    stateManager.retryCount++;
                    if (stateManager.retryCount >= MAX_RETRIES) {
                        console.log('❌ Nombre maximum de tentatives atteint');
                        console.log('🧹 Nettoyage complet et redémarrage...');
                        await sessionManager.cleanup();
                        setTimeout(() => initializeWhatsApp(), 3000);
                        stateManager.retryCount = 0;
                    } else {
                        console.log(`⏳ Tentative ${stateManager.retryCount}/${MAX_RETRIES}...`);
                        setTimeout(() => initializeWhatsApp(), RECONNECT_TIMEOUT);
                    }
                } else {
                    console.log('🔐 Session déconnectée (loggedOut)');
                    stateManager.setDisconnected('Session expirée ou supprimée');
                    await sessionManager.cleanup();
                    setTimeout(() => initializeWhatsApp(), 3000);
                }
            }

            if (connection === 'connecting') {
                stateManager.setState('initializing');
            }

            if (connection === 'open') {
                sessionManager.startSession();
                stateManager.setConnected();
            }

            // QR Code
            if (qr) {
                stateManager.setQRCode(qr);
            }
        });

        sock.ev.on('creds.update', saveCreds);

        sock.ev.on('messages.upsert', async (m) => {
            const message = m.messages[0];
            if (!message.message) return;

            console.log('📨 Message reçu:', {
                from: message.key.remoteJid,
                type: message.message?.conversation ? 'text' : 'other',
            });

            try {
                // Envoyer au backend
                await axios.post(`${BACKEND_URL}/api/whatsapp/webhook/message`, {
                    tenantId: TENANT_ID,
                    from: message.key.remoteJid,
                    message: message.message,
                    timestamp: message.messageTimestamp,
                });
            } catch (error) {
                console.error('❌ Erreur envoi au backend:', error.message);
            }
        });

        sock.ev.on('error', (err) => {
            if (err.code === 405) {
                console.log('⚠️  Erreur 405 détectée');
                stateManager.setDisconnected('Erreur 405 - Réinitialisation');
                sessionManager.cleanup();
            } else {
                console.error('❌ Erreur:', err.message);
                stateManager.setDisconnected(err.message);
            }
        });

        return sock;
    } catch (error) {
        console.error('❌ Erreur initialisation:', error.message);
        stateManager.setDisconnected(error.message);
        setTimeout(() => initializeWhatsApp(), RECONNECT_TIMEOUT);
    }
}

// ========== EXPRESS SERVER ==========
const app = express();
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: stateManager.isConnected ? 'healthy' : 'unhealthy',
        connected: stateManager.isConnected,
        timestamp: new Date().toISOString(),
    });
});

// Status détaillé
app.get('/status', (req, res) => {
    res.json(stateManager.getStatus());
});

// QR Status
app.get('/api/whatsapp/status', (req, res) => {
    res.json(stateManager.getStatus());
});

// Reset session
app.post('/api/whatsapp/reset-session', async (req, res) => {
    console.log('🔄 Reset session demandé');
    await sessionManager.cleanup();
    stateManager.sock?.end();
    setTimeout(() => initializeWhatsApp(), 2000);
    res.json({ status: 'reset_initiated', message: 'Session réinitialisée, nouveau QR en attente' });
});

// Delete tenant session
app.post('/api/whatsapp/delete-tenant/:tenantId', async (req, res) => {
    const { tenantId } = req.params;
    console.log(`🧹 Suppression session tenant ${tenantId}`);
    
    delete sessionManager.sessionTimeouts[tenantId];
    sessionManager.saveTimeouts();
    
    res.json({ status: 'deleted', tenantId, message: 'Session supprimée' });
});

// Session info
app.get('/api/whatsapp/session-info', (req, res) => {
    res.json({
        activeSessions: sessionManager.sessionTimeouts,
        currentTenant: TENANT_ID,
        sessionManager: {
            isExpired: sessionManager.isExpired(),
            started: sessionManager.sessionStartTime,
        }
    });
});

// Error handler
app.use((err, req, res, next) => {
    console.error('Erreur serveur:', err);
    res.status(500).json({ error: err.message });
});

// ========== DÉMARRAGE ==========
async function start() {
    console.log('\n' + '═'.repeat(72));
    console.log('🚀 NÉOBOT - WhatsApp Service v2.0 (ROBUSTE)'.padStart(50));
    console.log('═'.repeat(72));
    console.log(`Backend URL: ${BACKEND_URL}`);
    console.log(`Tenant ID: ${TENANT_ID}`);
    console.log(`HTTP Port: ${PORT}`);
    console.log(`Date: ${new Date().toLocaleString('fr-FR')}`);
    console.log('═'.repeat(72) + '\n');

    // Démarrer WhatsApp
    await initializeWhatsApp();

    // Démarrer serveur Express
    app.listen(PORT, () => {
        console.log(`\n✅ Serveur HTTP démarré sur le port ${PORT}`);
        console.log('Endpoint disponibles:');
        console.log(`  GET  /health                       - Health check`);
        console.log(`  GET  /status                       - État du service`);
        console.log(`  GET  /api/whatsapp/status          - Status détaillé`);
        console.log(`  POST /api/whatsapp/reset-session   - Reset complet`);
        console.log(`  GET  /api/whatsapp/session-info    - Info sessions\n`);
    });

    // Vérifier l'expiration toutes les 5 minutes
    setInterval(() => {
        if (sessionManager.isExpired() && stateManager.isConnected) {
            console.log('⚠️  Session expirée détectée, reset automatique');
            sessionManager.cleanup();
            stateManager.sock?.end();
            setTimeout(() => initializeWhatsApp(), 2000);
        }
    }, 300000);
}

start().catch(console.error);
