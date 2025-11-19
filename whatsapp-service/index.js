// index.js

import express from 'express'
import axios from 'axios'
import qrcode from 'qrcode-terminal'
import pino from 'pino'
import makeWASocket, { DisconnectReason, useMultiFileAuthState } from '@whiskeysockets/baileys'

// === CONFIG ===
const API_URL = 'http://localhost:8000'
const TENANT_ID = 1
const PORT = 3001

const logger = pino({ level: 'error' })
const app = express()
app.use(express.json())

// === ÉTAT GLOBAL ===
let sock = null
let isConnected = false
let qrCodeValue = null
let reconnectAttempts = 0

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
  try {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys')

    sock = makeWASocket({
      logger,
      auth: state,
      browser: ['NéoBot', 'Chrome', '14.0']
    })

    sock.ev.on('connection.update', (update) => {
      const { connection, lastDisconnect, qr } = update

      if (qr) {
        qrCodeValue = qr
        console.clear()
        console.log('\n╔════════════════════════════════════════════════╗')
        console.log('║      ⚠️  SCANNE CE QR CODE AVEC WHATSAPP       ║')
        console.log('╚════════════════════════════════════════════════╝\n')
        console.log('📱 Sur ton téléphone WhatsApp:')
        console.log('   Menu → Appareils connectés → Connecter\n')
        console.log('🌐 Ou visite: http://localhost:3001/qr\n')
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
        
        // Reconnexion automatique
        if (code !== DisconnectReason.connectionClosed && code !== DisconnectReason.connectionLost && code !== 401) {
          const delay = Math.min(60000, 5000 * Math.pow(1.5, (reconnectAttempts || 0)))
          console.log(`⏳ Reconnexion dans ${delay / 1000}s... (Tentative ${(reconnectAttempts || 0) + 1})`)
          reconnectAttempts = (reconnectAttempts || 0) + 1
          setTimeout(() => {
            connectToWhatsApp().catch(err => console.error('Erreur:', err.message))
          }, delay)
        }
      } else if (connection === 'open') {
        isConnected = true
        qrCodeValue = null
        reconnectAttempts = 0
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
        console.error('Erreur API:', error.message)
        await sock.sendMessage(msg.key.remoteJid, { text: 'Erreur technique.' })
      }
    })
  } catch (error) {
    console.error('Erreur connexion:', error.message)
    setTimeout(() => {
      connectToWhatsApp().catch(err => console.error(err.message))
    }, 10000)
  }
}

// === ROUTES EXPRESS ===

app.get('/health', (req, res) => {
  res.json({
    status: isConnected ? 'connected' : 'disconnected',
    qr_code: qrCodeValue ? 'ready' : null,
    service: 'neobot-whatsapp'
  })
})

app.get('/qr', (req, res) => {
  if (!qrCodeValue) {
    return res.status(400).json({
      error: isConnected ? 'Already connected' : 'QR not ready',
      status: isConnected ? 'connected' : 'generating'
    })
  }
  
  res.send(`<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>NéoBot QR</title>
<script src="https://cdn.jsdelivr.net/npm/qrcode@1.5.0/build/qrcode.min.js"><\/script>
<style>body{font-family:Arial;text-align:center;padding:50px;background:#f5f5f5}
.box{background:white;padding:40px;border-radius:10px;max-width:400px;margin:auto;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
h1{color:#128c7e}#qr{margin:20px 0}</style></head>
<body><div class="box"><h1>🔗 NéoBot WhatsApp</h1>
<p>Scanne avec ton téléphone</p><div id="qr"><\/div>
<p style="font-size:12px;color:#666">Menu → Appareils connectés → Connecter</p></div>
<script>QRCode.toCanvas(document.getElementById('qr'), "${qrCodeValue}", {width:250});
setInterval(()=>location.reload(), 10000)<\/script></body></html>`)
})

app.post('/session/create', async (req, res) => {
  connectToWhatsApp().catch(e => console.error(e.message))
  res.json({ status: 'starting', message: 'Check http://localhost:3001/qr' })
})

// === DÉMARRAGE ===
app.listen(PORT, () => {
  console.log(`🚀 Service WhatsApp sur http://localhost:${PORT}`)
  console.log(`QR: http://localhost:${PORT}/qr`)
  connectToWhatsApp().catch(e => console.error(e))
})
