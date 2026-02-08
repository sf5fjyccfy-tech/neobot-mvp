// NÉOBOT WHATSAPP - VERSION ULTRA STABLE (ES Module)
import makeWASocket from '@whiskeysockets/baileys';
import { useMultiFileAuthState } from '@whiskeysockets/baileys';
import qrcode from 'qrcode-terminal';
import axios from 'axios';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { rmSync } from 'fs';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const TENANT_ID = process.env.TENANT_ID || 1;

console.log('🚀' + '='.repeat(50));
console.log('     NÉOBOT WHATSAPP - CONNEXION STABLE');
console.log('🚀' + '='.repeat(50));

let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;

async function connectToWhatsApp() {
    reconnectAttempts++;
    
    if (reconnectAttempts > MAX_RECONNECT_ATTEMPTS) {
        console.log('❌ Trop de tentatives échouées. Arrêt.');
        return;
    }
    
    console.log(`\n🔗 Tentative de connexion #${reconnectAttempts}...`);
    
    try {
        const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');
        console.log('✅ Session initialisée');
        
        const sock = makeWASocket({
            auth: state,
            printQRInTerminal: false,
            logger: undefined,
            browser: ["Ubuntu", "Chrome", "120.0.0.0"],
            connectTimeoutMs: 60000,
            keepAliveIntervalMs: 30000,
            defaultQueryTimeoutMs: 60000,
            emitOwnEvents: true,
            retryRequestDelayMs: 2000
        });

        sock.ev.on('connection.update', (update) => {
            const { connection, lastDisconnect, qr } = update;
            
            if (qr) {
                console.log('\n' + '='.repeat(60));
                console.log('📱 SCANNEZ CE QR CODE AVEC WHATSAPP :');
                console.log('1. OUVREZ WHATSAPP sur votre téléphone');
                console.log('2. ALLEZ DANS : Paramètres → Appareils connectés');
                console.log('3. TAPPEZ : "Connecter un appareil"');
                console.log('4. SCANNEZ le code ci-dessous');
                console.log('='.repeat(60) + '\n');
                
                qrcode.generate(qr, { small: true });
                console.log('\n📱 Si le QR ne fonctionne pas, vérifiez que :');
                console.log('   • Votre téléphone a INTERNET');
                console.log('   • WhatsApp est à jour');
                console.log('   • Vous êtes sur le même réseau WiFi');
                console.log('');
            }
            
            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                console.log(`🔴 Connexion fermée (code: ${statusCode})`);
                
                if (statusCode === 401 || statusCode === 403) {
                    console.log('🔄 Session expirée, création nouvelle session...');
                    rmSync('auth_info_baileys', { recursive: true, force: true });
                    reconnectAttempts = 0;
                }
                
                setTimeout(connectToWhatsApp, 5000);
            }
            
            if (connection === 'open') {
                console.log('\n' + '🎉'.repeat(30));
                console.log('✅ SUCCÈS : CONNECTÉ À WHATSAPP !');
                console.log('🤖 NÉOBOT EST MAINTENANT ACTIF');
                console.log('📡 Messages relayés vers : ' + BACKEND_URL);
                console.log('🎉'.repeat(30) + '\n');
                reconnectAttempts = 0;
            }
        });

        sock.ev.on('creds.update', saveCreds);

        sock.ev.on('messages.upsert', async ({ messages }) => {
            for (const msg of messages) {
                if (msg.key.fromMe) continue;
                
                const remoteJid = msg.key.remoteJid;
                const text = msg.message?.conversation || 
                            msg.message?.extendedTextMessage?.text || '';
                
                if (!text) continue;
                
                const senderName = msg.pushName || "Client";
                const phone = remoteJid.replace('@s.whatsapp.net', '');
                
                console.log(`\n📨 [${new Date().toLocaleTimeString()}] ${senderName}: ${text.substring(0, 50)}`);
                
                try {
                    const response = await axios.post(
                        `${BACKEND_URL}/api/tenants/${TENANT_ID}/whatsapp/message`,
                        {
                            phone: phone,
                            message: text,
                            name: senderName
                        },
                        { timeout: 10000 }
                    );
                    
                    const botResponse = response.data.response || "👋 NéoBot à votre service !";
                    await sock.sendMessage(remoteJid, { text: botResponse });
                    
                    console.log(`🤖 Réponse envoyée: ${botResponse.substring(0, 50)}`);
                    
                } catch (error) {
                    console.error(`❌ Erreur backend: ${error.message}`);
                    const fallback = "👋 NéoBot - Service momentanément indisponible. Réessayez plus tard.";
                    await sock.sendMessage(remoteJid, { text: fallback });
                }
            }
        });

    } catch (error) {
        console.error(`💥 Erreur initialisation: ${error.message}`);
        
        if (error.message.includes('timeout') || error.message.includes('408')) {
            console.log('🕐 Timeout détecté - vérifiez votre connexion Internet');
            console.log('📶 Essayez:');
            console.log('   1. Redémarrez votre box WiFi');
            console.log('   2. Vérifiez les pare-feux (port 443)');
            console.log('   3. Essayez avec un autre réseau');
        }
        
        setTimeout(connectToWhatsApp, 10000);
    }
}

// Démarrer
connectToWhatsApp();

// Gestion des signaux
process.on('SIGINT', () => {
    console.log('\n🛑 Arrêt propre du service...');
    process.exit(0);
});
