// NÉOBOT WHATSAPP - CODE CORRECT POUR BAILEYS 6.5.0 + NODE 24
// Documentation: https://github.com/WhiskeySockets/Baileys
import makeWASocket from '@whiskeysockets/baileys';
import { useMultiFileAuthState } from '@whiskeysockets/baileys';

const logger = {
    level: 'silent', // 'debug', 'info', 'warn', 'error', 'silent'
};

async function startWhatsApp() {
    console.log('🤖 NÉOBOT WHATSAPP v2.0');
    console.log('=======================\n');
    
    try {
        // 1. État d'authentification
        const { state, saveCreds } = await useMultiFileAuthState('auth_info');
        console.log('🔐 Authentification chargée');
        
        // 2. Création du socket
        const sock = makeWASocket({
            auth: state,
            logger,
            printQRInTerminal: true,
            browser: ['Ubuntu', 'Chrome', '121.0.0.0'],
        });
        
        console.log('📡 Socket initialisé - Attente QR code...\n');
        
        // 3. Gestion des événements
        sock.ev.on('connection.update', (update) => {
            const { connection, qr, lastDisconnect } = update;
            
            if (qr) {
                console.log('\n══════════════════════════════════════════════════');
                console.log('🔄 NOUVEAU QR CODE DISPONIBLE !');
                console.log('📱 Instructions:');
                console.log('1. Ouvrez WhatsApp sur votre téléphone');
                console.log('2. Menu (⋮) → Appareils connectés');
                console.log('3. Taper "Lier un appareil"');
                console.log('4. Scannez le QR code ci-dessus');
                console.log('══════════════════════════════════════════════════\n');
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
                    headers: { 'Content-Type': 'application/json' },
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
                console.log(`❌ Erreur: ${error.message}`);
                
                // Fallback
                await sock.sendMessage(jid, { 
                    text: "👋 NéoBot - Système temporairement indisponible. Réessayez plus tard." 
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
