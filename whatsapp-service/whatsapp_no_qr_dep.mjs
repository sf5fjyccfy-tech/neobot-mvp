// NÉOBOT WHATSAPP - SANS qrcode-terminal
// Affiche juste le texte du QR code
import makeWASocket from '@whiskeysockets/baileys';
import { useMultiFileAuthState } from '@whiskeysockets/baileys';

async function startWhatsApp() {
    console.log('🤖 NÉOBOT WHATSAPP SIMPLE');
    console.log('==========================\n');
    
    try {
        // 1. État d'authentification
        const { state, saveCreds } = await useMultiFileAuthState('auth_info');
        console.log('🔐 Authentification chargée');
        
        // 2. Création du socket
        const sock = makeWASocket({
            auth: state,
            browser: ['Ubuntu', 'Chrome', '121.0.0.0'],
        });
        
        console.log('📡 Socket initialisé - Attente QR code...\n');
        
        // 3. Gestion des événements
        sock.ev.on('connection.update', (update) => {
            const { connection, qr, lastDisconnect } = update;
            
            if (qr) {
                console.log('\n' + '═'.repeat(60));
                console.log('🔄 QR CODE DISPONIBLE !');
                console.log('═'.repeat(60));
                console.log('\n📋 Copiez ce lien dans un générateur de QR code:');
                console.log('https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + encodeURIComponent(qr));
                console.log('\n📱 OU scannez directement avec WhatsApp:');
                console.log('1. Ouvrez WhatsApp → Menu → Appareils connectés');
                console.log('2. → Lier un appareil');
                console.log('3. Scannez le QR code généré');
                console.log('═'.repeat(60) + '\n');
            }
            
            if (connection === 'open') {
                console.log('✅ CONNECTÉ À WHATSAPP !');
                console.log('📱 Prêt à recevoir des messages...\n');
            }
            
            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                console.log(`🔌 Déconnecté (Code: ${statusCode || 'inconnu'})`);
                console.log('🔄 Reconnexion dans 5s...\n');
                setTimeout(startWhatsApp, 5000);
            }
        });
        
        // 4. Sauvegarde
        sock.ev.on('creds.update', saveCreds);
        
        // 5. Messages
        sock.ev.on('messages.upsert', async ({ messages }) => {
            const msg = messages[0];
            if (!msg.message || msg.key.fromMe) return;
            
            const jid = msg.key.remoteJid;
            const phone = jid.split('@')[0];
            const text = msg.message.conversation || 
                         msg.message.extendedTextMessage?.text || 
                         '[Media]';
            
            console.log(`📨 ${phone}: ${text.substring(0, 60)}...`);
            
            try {
                const response = await fetch('http://localhost:8000/api/tenants/1/whatsapp/message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone, message: text })
                });
                
                let reply = "👋 NéoBot en ligne ! Envoyez 'aide' pour menu.";
                
                if (response.ok) {
                    const data = await response.json();
                    reply = data.response || reply;
                }
                
                await sock.sendMessage(jid, { text: reply });
                console.log(`✅ Réponse envoyée\n`);
                
            } catch (error) {
                console.log(`❌ Erreur: ${error.message}`);
                await sock.sendMessage(jid, { 
                    text: "👋 NéoBot - Maintenance. Réessayez plus tard." 
                });
            }
        });
        
    } catch (error) {
        console.error('💥 ERREUR:', error.message);
        console.log('🔄 Redémarrage dans 10s...\n');
        setTimeout(startWhatsApp, 10000);
    }
}

// Démarrer
startWhatsApp();
