// index.js

import express from 'express'
import axios from 'axios'
import qrcode from 'qrcode-terminal'
import pino from 'pino'
import makeWASocket, { DisconnectReason, useMultiFileAuthState } from 'baileys'

// === CONFIG ===
const API_URL = 'http://localhost:8000'
const TENANT_ID = 1
const PORT = 3000

const logger = pino({ level: 'silent' })
const app = express()
app.use(express.json())

// === ÉTAT GLOBAL ===
let sock = null
let isConnected = false
let qrCodeValue = null

// === UTILS ===
function getMessageText(message) {
  if (!message) return null
  return (
    message.conversation ||
    message.extendedTextMessage?.text ||
    message.imageMessage?.caption ||
    message.videoMessage?.caption ||
    null
  )
}

// === FONCTION PRINCIPALE ===
async function connectToWhatsApp() {
  const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys')

  sock = makeWASocket({
    logger,
    auth: state
  })

  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr, isNewLogin, isLatest } = update

    if (qr) {
      qrCodeValue = qr
      console.clear()
      console.log('\n╔════════════════════════════════════════════════╗')
      console.log('║      ⚠️  SCANNE CE QR CODE AVEC WHATSAPP       ║')
      console.log('╚════════════════════════════════════════════════╝\n')
      console.log('📱 Sur ton téléphone WhatsApp:')
      console.log('   Menu → Appareils connectés → Connecter\n')
      qrcode.generate(qr, { small: true })
      console.log('\n⏳ En attente de scan...\n')
    }

    if (connection === 'close') {
      const code = lastDisconnect?.error?.output?.statusCode
      const reason = DisconnectReason[code]
      console.log(`⚠️  Connexion fermée. Code: ${code} (${reason})`)
      isConnected = false

      if (code === DisconnectReason.loggedOut) {
        console.log('🔴 Session expirée. Relance npm start.')
        return
      }
      
      if (code !== DisconnectReason.connectionClosed && code !== DisconnectReason.connectionLost) {
        console.log('⏳ Reconnexion dans 5s...')
        setTimeout(connectToWhatsApp, 5000)
      }
    } else if (connection === 'open') {
      isConnected = true
      qrCodeValue = null
      console.log('\n✅ WhatsApp connecté ! Prêt à recevoir des messages.\n')
    }
  })

  sock.ev.on('creds.update', saveCreds)

  sock.ev.on('messages.upsert', async ({ messages }) => {
    const msg = messages[0]
    if (!msg.message || msg.key.fromMe) return

    const from = msg.key.remoteJid.split('@')[0]
    const text = getMessageText(msg.message)

    if (!text || text.trim() === '') {
      console.log(`⚠️  Message sans texte de ${from}`)
      return
    }

    console.log(`\n📱 [${from}] ${text}`)

    try {
      const response = await axios.post(`${API_URL}/api/tenants/${TENANT_ID}/whatsapp/message`, {
        phone: from,
        message: text.trim()
      })

      const botResponse = response.data.response
      await sock.sendMessage(msg.key.remoteJid, { text: botResponse })
      console.log(`🤖 → ${botResponse}\n`)
    } catch (error) {
      console.error('❌ Erreur API:', error.response?.data || error.message)
      await sock.sendMessage(msg.key.remoteJid, { text: 'Erreur technique. Réessayez.' })
    }
  })
}

// === ROUTES EXPRESS ===

// Vérification du service
app.get('/health', (req, res) => {
  res.json({
    status: isConnected ? 'connected' : 'disconnected',
    qr_code: qrCodeValue ? 'ready' : null,
    service: 'neobot-whatsapp'
  })
})

// Générer manuellement une nouvelle session
app.post('/session/create', async (req, res) => {
  await connectToWhatsApp()
  res.json({ status: 'session_started', message: 'Scan le QR dans la console' })
})

// === LANCEMENT ===
app.listen(PORT, () => {
  console.log(`🚀 Service WhatsApp en ligne sur http://localhost:${PORT}`)
  connectToWhatsApp()
})
