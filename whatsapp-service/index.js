import makeWASocket, { DisconnectReason, useMultiFileAuthState } from '@whiskeysockets/baileys'
import qrcode from 'qrcode-terminal'
import { writeFileSync } from 'fs'
import pino from 'pino'
import axios from 'axios'

const logger = pino({ level: 'silent' })
const API_URL = 'http://localhost:8000'
const TENANT_ID = 3

function getMessageText(message) {
    if (!message) return null
    return message.conversation || message.extendedTextMessage?.text || message.imageMessage?.caption || null
}

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys')
    
    const sock = makeWASocket({
        logger,
        auth: state,
        browser: ['NeoBot', 'Safari', '15.0']
    })

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update
        
        if(qr) {
            console.log('\n╔════════════════════════════════════╗')
            console.log('║   SCANNE CE QR CODE MAINTENANT!   ║')
            console.log('╚════════════════════════════════════╝\n')
            
            // Afficher dans terminal
            qrcode.generate(qr, { small: true })
            
            // Sauvegarder en PNG (optionnel)
            try {
                const QRCode = (await import('qrcode')).default
                await QRCode.toFile('qr.png', qr)
                console.log('\n✅ QR code sauvegardé: qr.png')
                console.log('Tu peux aussi l\'ouvrir avec: xdg-open qr.png\n')
            } catch(e) {}
            
            console.log('📱 WhatsApp → Menu (⋮) → Appareils connectés → Lier un appareil\n')
        }
        
        if(connection === 'close') {
            const statusCode = lastDisconnect?.error?.output?.statusCode
            console.log('❌ Déconnecté. Code:', statusCode)
            
            if(statusCode === DisconnectReason.loggedOut) {
                console.log('Session expirée. Supprime auth_info_baileys/ et relance.')
            } else if(statusCode === 405) {
                console.log('⏳ Bloqué temporairement. Attends 30 min.')
            } else {
                console.log('🔄 Reconnexion dans 5s...')
                setTimeout(connectToWhatsApp, 5000)
            }
        } else if(connection === 'open') {
            console.log('\n✅✅✅ WHATSAPP CONNECTÉ ! ✅✅✅\n')
            
            // Message test
            const myNumber = sock.user.id.split(':')[0] + '@s.whatsapp.net'
            await sock.sendMessage(myNumber, { text: '🤖 NeoBot activé ! Envoie un message pour tester.' })
        }
    })

    sock.ev.on('creds.update', saveCreds)

    sock.ev.on('messages.upsert', async ({ messages }) => {
        const msg = messages[0]
        if (!msg.message || msg.key.fromMe) return

        const from = msg.key.remoteJid.split('@')[0]
        const text = getMessageText(msg.message)
        if (!text?.trim()) return

        console.log(`\n📱 Message de ${from}: ${text}`)

        try {
            const response = await axios.post(`${API_URL}/api/tenants/${TENANT_ID}/whatsapp/message`, {
                phone: from,
                message: text.trim()
            })

            const botResponse = response.data.response
            
            // Délai humain
            await new Promise(r => setTimeout(r, 1500))
            
            await sock.sendMessage(msg.key.remoteJid, { text: botResponse })
            console.log(`🤖 Réponse: ${botResponse}\n`)
        } catch (error) {
            console.error('Erreur API:', error.message)
        }
    })
}

console.log('🚀 Démarrage service WhatsApp...\n')
connectToWhatsApp()
