const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const express = require('express');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const PORT = 3001;
const BACKEND_URL = 'http://localhost:8000';

const sessions = new Map();
const qrCodes = new Map();

async function createWhatsAppSession(tenantId) {
    console.log(`🔄 Création session WhatsApp tenant ${tenantId}`);
    
    const authDir = path.join(__dirname, 'auth', `tenant_${tenantId}`);
    if (!fs.existsSync(authDir)) {
        fs.mkdirSync(authDir, { recursive: true });
    }
    
    const { state, saveCreds } = await useMultiFileAuthState(authDir);
    
    const sock = makeWASocket({
        auth: state,
        printQRInTerminal: false,
        browser: ['NeoBot', 'Chrome', '1.0.0']
    });
    
    sock.ev.on('creds.update', saveCreds);
    
    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            console.log(`📱 QR Code généré pour tenant ${tenantId}`);
            qrCodes.set(tenantId, qr);
        }
        
        if (connection === 'close') {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log(`❌ Connexion fermée tenant ${tenantId}, reconnexion: ${shouldReconnect}`);
            
            if (shouldReconnect) {
                sessions.delete(tenantId);
                setTimeout(() => createWhatsAppSession(tenantId), 3000);
            }
        } else if (connection === 'open') {
            console.log(`✅ WhatsApp connecté pour tenant ${tenantId}`);
            qrCodes.delete(tenantId);
            
            try {
                await axios.post(`${BACKEND_URL}/webhook/whatsapp/connected`, {
                    tenant_id: tenantId,
                    phone_number: sock.user.id.split(':')[0]
                });
            } catch (err) {
                console.error('Erreur notification backend:', err.message);
            }
        }
    });
    
    sock.ev.on('messages.upsert', async ({ messages }) => {
        for (const msg of messages) {
            if (!msg.message || msg.key.fromMe) continue;
            
            const from = msg.key.remoteJid;
            const text = msg.message.conversation || 
                        msg.message.extendedTextMessage?.text || '';
            
            if (!text) continue;
            
            console.log(`📱 Message reçu de ${from}: ${text.substring(0, 50)}`);
            
            try {
                const response = await axios.post(`${BACKEND_URL}/webhook/whatsapp`, {
                    tenant_id: tenantId,
                    from_number: from.replace('@s.whatsapp.net', ''),
                    message: text
                });
                
                const aiResponse = response.data.response;
                await sock.sendMessage(from, { text: aiResponse });
                console.log(`🤖 Réponse envoyée: ${aiResponse.substring(0, 50)}`);
                
            } catch (err) {
                console.error('Erreur traitement message:', err.message);
            }
        }
    });
    
    sessions.set(tenantId, sock);
    return sock;
}

app.post('/connect', async (req, res) => {
    const { tenant_id } = req.body;
    
    if (!tenant_id) {
        return res.status(400).json({ error: 'tenant_id requis' });
    }
    
    try {
        await createWhatsAppSession(tenant_id);
        
        let attempts = 0;
        while (!qrCodes.has(tenant_id) && attempts < 30) {
            await new Promise(resolve => setTimeout(resolve, 500));
            attempts++;
        }
        
        const qr = qrCodes.get(tenant_id);
        
        if (qr) {
            res.json({
                success: true,
                qr_code: qr,
                message: 'Scannez le QR code avec WhatsApp'
            });
        } else {
            res.json({
                success: false,
                message: 'Timeout - QR non généré'
            });
        }
        
    } catch (err) {
        console.error('Erreur connexion:', err);
        res.status(500).json({ error: err.message });
    }
});

app.get('/status/:tenant_id', (req, res) => {
    const tenantId = parseInt(req.params.tenant_id);
    const sock = sessions.get(tenantId);
    
    res.json({
        connected: sock?.user ? true : false,
        phone_number: sock?.user ? sock.user.id.split(':')[0] : null,
        qr_pending: qrCodes.has(tenantId)
    });
});

app.listen(PORT, () => {
    console.log(`🚀 Service WhatsApp démarré sur port ${PORT}`);
    console.log(`📡 Backend API: ${BACKEND_URL}`);
});
