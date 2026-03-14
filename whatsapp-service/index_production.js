import makeWASocket, { useMultiFileAuthState, DisconnectReason } from '@whiskeysockets/baileys';
import pino from 'pino';
import axios from 'axios';
import qrcode from 'qrcode-terminal';
import express from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { EventEmitter } from 'events';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ========== CONFIGURATION ==========
const BACKEND_URL = process.env.WHATSAPP_BACKEND_URL || 'http://localhost:8000';
const PORT = process.env.WHATSAPP_PORT || 3001;
const TENANT_ID = process.env.TENANT_ID || 1;

const AUTH_DIR = path.join(__dirname, 'auth_info_baileys');
const BACKUP_AUTH_DIR = path.join(__dirname, '.wwebjs_auth');
const SESSION_DIR = path.join(__dirname, 'session');

// Logger basique
const logger = pino({ level: 'error' });

// ========== GESTION DE SESSION GLOB ALE ==========
const sessionManager = {
    isConnected: false,
    lastQR: null,
    retryCount: 0,
    maxRetries: 5,
    socket: null,
    state: 'initializing',
    connectedAt: null,
    lastError: null
};

// ========== INITIALISATION BAILEYS ==========
async function startWhatsApp() {
    try {
        // Créer les dossiers
        [AUTH_DIR, BACKUP_AUTH_DIR, SESSION_DIR].forEach(dir => {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        });

        const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

        // Configuration MINIMALE de Baileys pour forcer QR
        const sock = makeWASocket({
            auth: state,
            printQRInTerminal: true, // On veut que Baileys affiche aussi c'est OK
            logger: pino({ level: 'warn' }),
            browser: ['NéoBot', 'Chrome', '5.0'],
            syncFullHistory: false,
            maxMsgsInMemory: 100,
            generateHighQualityLinkPreview: false,
        });

        sessionManager.socket = sock;

        // ===== GESTION DES ÉVÉNEMENTS =====
        
        let qrCodeReceived = false;
        let connectionTimeout = null;

        // Timeout pour attendre le QR
        const settQRTimeout = () => {
            connectionTimeout = setTimeout(() => {
                if (!qrCodeReceived && !sessionManager.isConnected && sessionManager.retryCount < sessionManager.maxRetries) {
                    sessionManager.retryCount++;
                    console.log(`\n⏳ Tentative ${sessionManager.retryCount}/${sessionManager.maxRetries}...`);
                    
                    if (sessionManager.retryCount >= sessionManager.maxRetries) {
                        console.log('❌ Max retries atteint - Reset complet');
                        cleanupAndRestart();
                    } else {
                        settQRTimeout();
                    }
                }
            }, 8000);
        };

        settQRTimeout();

        // Event: connection update
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            // QR Code
            if (qr) {
                qrCodeReceived = true;
                sessionManager.lastQR = qr;
                sessionManager.state = 'waiting_qr';
                clearTimeout(connectionTimeout);
                
                console.log('\n' + '═'.repeat(72));
                console.log('╔' + '═'.repeat(70) + '╗');
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
                
                // Afficher le QR code en ASCII
                qrcode.generate(qr, { small: true });
                console.log('');
            }

            // Connection states
            if (connection === 'connecting') {
                sessionManager.state = 'connecting';
                console.log('🔗 Connexion en cours...');
            } else if (connection === 'open') {
                qrCodeReceived = true;
                sessionManager.isConnected = true;
                sessionManager.connectedAt = Date.now();
                sessionManager.state = 'connected';
                sessionManager.retryCount = 0;
                clearTimeout(connectionTimeout);
                
                console.log('\n' + '═'.repeat(72));
                console.log('╔' + '═'.repeat(70) + '╗');
                console.log('║' + '🎉 CONNEXION RÉUSSIE 🎉'.padStart(48).padEnd(70) + '║');
                console.log('║' + ' '.repeat(70) + '║');
                console.log('║' + '✅ Connecté à WhatsApp'.padEnd(70) + '║');
                console.log('║' + '🤖 NéoBot est opérationnel'.padEnd(70) + '║');
                console.log('║' + `📡 Backend: ${BACKEND_URL}`.padEnd(70) + '║');
                console.log('║' + `🔌 Port: ${PORT}`.padEnd(70) + '║');
                console.log('║' + '✅ Prêt à recevoir/envoyer des messages'.padEnd(70) + '║');
                console.log('║' + ' '.repeat(70) + '║');
                console.log('╚' + '═'.repeat(70) + '╝\n');
            } else if (connection === 'close') {
                const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
                
                if (shouldReconnect && !qrCodeReceived) {
                    // Pas encore de QR reçu, réessayer
                    console.log('⚠️  Déconnexion avant QR - Nouvelle tentative');
                    settQRTimeout();
                } else if (shouldReconnect) {
                    sessionManager.isConnected = false;
                    sessionManager.state = 'disconnected';
                    console.log('🔴 Déconnecté - Tentative de reconnexion');
                    setTimeout(() => startWhatsApp(), 3000);
                } else {
                    // Logged out
                    sessionManager.state = 'logged_out';
                    console.log('🔐 Session expirée - Reset et nouveau QR');
                    cleanupAndRestart();
                }
            }
        });

        // Credentials updated
        sock.ev.on('creds.update', saveCreds);

        // Messages
        sock.ev.on('messages.upsert', async (m) => {
            const message = m.messages[0];
            if (!message.message) return;

            console.log('📨 Message reçu');
            try {
                await axios.post(`${BACKEND_URL}/api/whatsapp/webhook/message`, {
                    tenantId: TENANT_ID,
                    message: message.message,
                    timestamp: message.messageTimestamp,
                });
            } catch (err) {
                console.error('❌ Erreur webhook backend');
            }
        });

        return sock;

    } catch (error) {
        console.error('❌ Erreur initialisation:', error.message);
        sessionManager.state = 'error';
        sessionManager.lastError = error.message;
        setTimeout(() => startWhatsApp(), 3000);
    }
}

// ========== CLEANUP ET RESTART ==========
async function cleanupAndRestart() {
    console.log('\n🧹 Nettoyage et redémarrage...');
    
    try {
        if (sessionManager.socket) {
            await sessionManager.socket.end().catch(() => {});
        }

        [AUTH_DIR, BACKUP_AUTH_DIR, SESSION_DIR].forEach(dir => {
            if (fs.existsSync(dir)) {
                fs.rmSync(dir, { recursive: true, force: true });
                console.log(`   ✅ Supprimé: ${dir}`);
            }
        });

        SessionManager.isConnected = false;
        sessionManager.retryCount = 0;
        sessionManager.state = 'initializing';

        setTimeout(() => {
            console.log('\n🚀 Redémarrage avec nouvelle session...\n');
            startWhatsApp();
        }, 2000);
    } catch (err) {
        console.error('❌ Erreur cleanup:', err.message);
    }
}

// ========== EXPRESS SERVER ==========
const app = express();
app.use(express.json());

app.get('/health', (req, res) => {
    res.json({
        status: sessionManager.isConnected ? 'healthy' : 'unhealthy',
        connected: sessionManager.isConnected,
        state: sessionManager.state,
        timestamp: new Date().toISOString(),
    });
});

app.get('/status', (req, res) => {
    res.json({
        state: sessionManager.state,
        isConnected: sessionManager.isConnected,
        uptime: sessionManager.connectedAt ? Date.now() - sessionManager.connectedAt : 0,
        lastError: sessionManager.lastError,
        retryCount: sessionManager.retryCount,
    });
});

app.post('/api/whatsapp/reset-session', async (req, res) => {
    console.log('🔄 Reset demandé via API');
    await cleanupAndRestart();
    res.json({ status: 'reset_initiated' });
});

// ========== DÉMARRAGE ==========
async function start() {
    console.log('\n' + '═'.repeat(72));
    console.log('🚀 NÉOBOT - WhatsApp Service v2.1 (PRODUCTION)'.padStart(58));
    console.log('═'.repeat(72));
    console.log(`Backend URL: ${BACKEND_URL}`);
    console.log(`HTTP Port: ${PORT}`);
    console.log(`Date: ${new Date().toLocaleString('fr-FR')}`);
    console.log('═'.repeat(72) + '\n');

    // Démarrer WhatsApp
    await startWhatsApp();

    // Serveur Express
    app.listen(PORT, () => {
        console.log(`\n✅ API HTTP disponible sur le port ${PORT}`);
    });
}

start().catch(console.error);
