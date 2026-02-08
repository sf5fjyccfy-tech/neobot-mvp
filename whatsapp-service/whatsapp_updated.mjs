// NÉOBOT WHATSAPP - MISE À JOUR POUR BAILEYS 6.5.0+
// Corrections pour les changements d'API
import makeWASocket from '@whiskeysockets/baileys';
import { useMultiFileAuthState } from '@whiskeysockets/baileys';
import qrcode from 'qrcode-terminal';

async function startWhatsApp() {
    console.log('🤖 NÉOBOT WHATSAPP UPDATED');
    console.log('===========================\n');
    
    try {
        // 1. État d'authentification
        const { state, saveCreds } = await useMultiFileAuthState('auth_info');
        console.log('🔐 Authentification chargée');
        
        // 2. Création du socket SANS printQRInTerminal
        const sock = makeWASocket({
            auth: state,
            // logger: undefined, // Pas de logger personnalisé pour éviter les erreurs
            browser: ['Ubuntu', 'Chrome', '121.0.0.0'],
            connectTimeoutMs: 60000,
        });
        
        console.log('📡 Socket initialisé\n');
        
        // 3. Gestion MANUELLE du QR code (printQRInTerminal est déprécié)
        sock.ev.on('connection.update', (update) => {
            const { connection, qr, lastDisconnect } = update;
            
            // AFFICHAGE MANUEL DU QR CODE
            if (qr) {
                console.log('\n' + '═'.repeat(60));
                console.log('🔄 QR CODE DISPONIBLE - Scannez avec WhatsApp:');
                console.log('═'.repeat(60));
                
                // Afficher le QR code dans le terminal
                qrcode.generate(qr, { small: true }, (qrcodeStr) => {
                    console.log(qrcodeStr);
                });
                
                console.log('\n📱 Instructions:');
                console.log('1. Ouvrez WhatsApp sur votre téléphone');
                console.log('2. Menu (⋮) → Appareils connectés');
                console.log('3. → Lier un appareil');
                console.log('4. Scannez le QR code ci-dessus');
                console.log('═'.repeat(60) + '\n');
                
                // Timer expiration QR (2 minutes)
                setTimeout(() => {
                    if (!sock.user) {
                        console.log('⏰ QR code expiré. Nouvelle génération...');
                        sock.ws.close();
                    }
                }, 120000);
            }
            
            if (connection === 'open') {
                console.log('✅ CONNECTÉ À WHATSAPP !');
                console.log('👤 Utilisateur:', sock.user?.id?.split(':')[0] || 'N/A');
                console.log('📱 Prêt à recevoir des messages...\n');
            }
            
            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                console.log(`🔌 Déconnecté (Code: ${statusCode || 'inconnu'})`);
                
                // Reconnexion automatique
                console.log('🔄 Reconnexion dans 5s...\n');
                setTimeout(startWhatsApp, 5000);
            }
        });
        
        // 4. Sauvegarde des credentials
        sock.ev.on('creds.update', saveCreds);
        
        // 5. Gestion des messages
        sock.ev.on('messages.upsert', async ({ messages }) => {
            const msg = messages[0];
            if (!msg.message || msg.key.fromMe) return;
            
            const jid = msg.key.remoteJid;
            const phone = jid.split('@')[0];
            const text = msg.message.conversation || 
                         msg.message.extendedTextMessage?.text || 
                         '[Media]';
            
            console.log(`📨 ${phone}: ${text.substring(0, 60)}${text.length > 60 ? '...' : ''}`);
            
            try {
                // Appel au backend NéoBot
                const response = await fetch('http://localhost:8000/api/tenants/1/whatsapp/message', {
                    method: 'POST',
                    headers: { 'Content-Type: 'application/json' },
                    body: JSON.stringify({ phone, message: text })
                });
                
                let reply = "👋 NéoBot en ligne !";
                
                if (response.ok) {
                    const data = await response.json();
                    reply = data.response || reply;
                }
                
                await sock.sendMessage(jid, { text: reply });
                console.log(`✅ Réponse envoyée\n`);
                
            } catch (error) {
                console.log(`❌ Erreur backend: ${error.message}`);
                
                // Fallback
                await sock.sendMessage(jid, { 
                    text: "👋 NéoBot - Service temporairement indisponible. Réessayez." 
                });
            }
        });
        
    } catch (error) {
        console.error('💥 ERREUR INITIALISATION:', error.message);
        console.log('🔄 Redémarrage dans 10s...\n');
        setTimeout(startWhatsApp, 10000);
    }
}

// Gestion des signaux
process.on('SIGINT', () => {
    console.log('\n🛑 Arrêt propre...');
    process.exit(0);
});

// Démarrer
startWhatsApp();
