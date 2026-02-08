import makeWASocket, { useMultiFileAuthState, DisconnectReason } from '@whiskeysockets/baileys';
import pino from 'pino';
import axios from 'axios';
import qrcode from 'qrcode-terminal';
import express from 'express';

// ========== CONFIGURATION ==========
const BACKEND_URL = process.env.WHATSAPP_BACKEND_URL || 'http://localhost:8000';
const PORT = process.env.WHATSAPP_PORT || 3001;
const TENANT_ID = process.env.TENANT_ID || 1;
const RECONNECT_TIMEOUT = process.env.WHATSAPP_RECONNECT_TIMEOUT || 5000;
const MAX_RETRIES = process.env.WHATSAPP_MAX_RETRIES || 5;

// Variables globales
let sock = null;
let isConnected = false;
let retryCount = 0;

// ========== EXPRESS SERVER ==========
const app = express();
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: isConnected ? 'connected' : 'disconnected',
        connected: isConnected,
        backend: BACKEND_URL,
        timestamp: new Date().toISOString()
    });
});

// Status endpoint
app.get('/status', (req, res) => {
    res.json({
        whatsapp_service: 'running',
        connected: isConnected,
        backend_url: BACKEND_URL,
        tenant_id: TENANT_ID,
        timestamp: new Date().toISOString()
    });
});

app.listen(PORT, () => {
    console.log(`✅ WhatsApp service HTTP server running on port ${PORT}`);
});

// ========== WHATSAPP CONNECTION ==========
async function connectToWhatsApp() {
    console.log(`\n🔗 Tentative de connexion à WhatsApp... (tentative ${retryCount + 1}/${MAX_RETRIES})`);
    
    if (retryCount >= MAX_RETRIES) {
        console.error(`❌ Échec: ${MAX_RETRIES} tentatives atteintes. Arrêt.`);
        process.exit(1);
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
                console.log('\n' + '='.repeat(70));
                console.log('📱 SCANNEZ CE QR CODE AVEC WHATSAPP');
                console.log('🔐 60 secondes pour scanner');
                console.log('='.repeat(70));
                qrcode.generate(qr, { small: true });
                console.log('='.repeat(70) + '\n');
            }

            // Connexion fermée
            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                isConnected = false;
                console.log(`\n🔴 Déconnecté. Code: ${statusCode}`);
                
                if (statusCode === DisconnectReason.loggedOut) {
                    console.log('❌ Déconnecté par WhatsApp. Authentification requise.');
                    retryCount = 0;
                    setTimeout(connectToWhatsApp, 3000);
                    return;
                }
                
                // Reconnexion avec backoff exponentiel
                const delay = Math.min(RECONNECT_TIMEOUT * Math.pow(2, retryCount), 30000);
                console.log(`🔄 Reconnexion dans ${delay / 1000}s...`);
                retryCount++;
                setTimeout(connectToWhatsApp, delay);
            }

            // Connexion ouverte
            if (connection === 'open') {
                isConnected = true;
                retryCount = 0;
                console.log('\n' + '✅'.repeat(35));
                console.log('🎉 CONNECTÉ À WHATSAPP AVEC SUCCÈS !');
                console.log('🤖 NéoBot opérationnel');
                console.log('📡 Backend: ' + BACKEND_URL);
                console.log('✅'.repeat(35) + '\n');
            }
        });

        // Sauvegarder credentials
        sock.ev.on('creds.update', saveCreds);

        // ========== MESSAGE HANDLER ==========
        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            if (type !== 'notify' || !isConnected) return;

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
        retryCount++;
        const delay = Math.min(RECONNECT_TIMEOUT * Math.pow(2, retryCount), 30000);
        console.log(`🔄 Nouvelle tentative dans ${delay / 1000}s...`);
        setTimeout(connectToWhatsApp, delay);
    }
}

// ========== MAIN ==========
async function main() {
    console.log('\n' + '═'.repeat(70));
    console.log('🚀 NÉOBOT - WhatsApp Service (Baileys v6.7.7)');
    console.log('═'.repeat(70));
    console.log(`Backend URL: ${BACKEND_URL}`);
    console.log(`Tenant ID: ${TENANT_ID}`);
    console.log(`HTTP Port: ${PORT}`);
    console.log(`Version: 2.0 (Cleaned & Fixed)`);
    console.log(`Date: ${new Date().toLocaleString('fr-FR')}`);
    console.log('═'.repeat(70) + '\n');
    
    // Start WhatsApp connection
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
