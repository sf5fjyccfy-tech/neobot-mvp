import makeWASocket, { 
    DisconnectReason, 
    useMultiFileAuthState, 
    makeInMemoryStore,
    isJidBroadcast,
    isJidStatusBroadcast
} from '@whiskeysockets/baileys'
import qrcode from 'qrcode-terminal'
import express from 'express'
import axios from 'axios'
import cors from 'cors'
import fs from 'fs'
import { WebSocketServer } from 'ws'

const app = express()
app.use(cors())
app.use(express.json())

// Configuration
const PORT = 3001
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
const WS_PORT = 3002

// WebSocket pour QR codes temps réel
const wss = new WebSocketServer({ port: WS_PORT })

// Stockage des sessions multi-tenant
const sessions = new Map()
const qrCodes = new Map()

// Store pour gérer les données hors ligne
const store = makeInMemoryStore({})
store.readFromFile('./baileys_store.json')
setInterval(() => {
    store.writeToFile('./baileys_store.json')
}, 10_000)

class WhatsAppSession {
    constructor(tenantId, businessName = 'Business') {
        this.tenantId = tenantId
        this.businessName = businessName
        this.sock = null
        this.qr = null
        this.isConnected = false
        this.messageQueue = []
        this.retryCount = 0
        this.maxRetries = 3
    }

    async initialize() {
        try {
            const authDir = `./auth_sessions/${this.tenantId}`
            if (!fs.existsSync(authDir)) {
                fs.mkdirSync(authDir, { recursive: true })
            }

            const { state, saveCreds } = await useMultiFileAuthState(authDir)

            this.sock = makeWASocket({
                auth: {
                    creds: state.creds,
                    keys: state.keys,
                },
                printQRInTerminal: false,
                browser: ["NeoBot", "Chrome", "4.0.0"],
                generateHighQualityLinkPreview: true,
                markOnlineOnConnect: false,
                defaultQueryTimeoutMs: 60000,
                keepAliveIntervalMs: 25000,
                retryRequestDelayMs: 2000,
                maxMsgRetryCount: 3,
                msgRetryCounterCache: {},
                connectTimeoutMs: 60000,
                logger: {
                    level: 'error',
                    log: () => {}
                }
            })

            store.bind(this.sock.ev)

            // Gestion des événements de connexion
            this.sock.ev.on('connection.update', (update) => {
                this.handleConnectionUpdate(update)
            })

            // Sauvegarde automatique des credentials
            this.sock.ev.on('creds.update', saveCreds)

            // Gestion des messages entrants
            this.sock.ev.on('messages.upsert', async (m) => {
                await this.handleIncomingMessages(m)
            })

            console.log(`Session initialisée pour tenant: ${this.tenantId}`)
            return true

        } catch (error) {
            console.error(`Erreur initialisation session ${this.tenantId}:`, error)
            return false
        }
    }

    handleConnectionUpdate(update) {
        const { connection, lastDisconnect, qr } = update

        if (qr) {
            this.qr = qr
            qrCodes.set(this.tenantId, qr)
            
            // Afficher QR en terminal
            qrcode.generate(qr, { small: true })
            console.log(`QR Code généré pour ${this.businessName} (${this.tenantId})`)
            
            // Envoyer QR via WebSocket
            this.broadcastQR(qr)
        }

        if (connection === 'close') {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut
            
            console.log(`Connexion fermée pour ${this.tenantId}, reconnexion:`, shouldReconnect)

            if (shouldReconnect && this.retryCount < this.maxRetries) {
                this.retryCount++
                setTimeout(() => {
                    console.log(`Tentative de reconnexion ${this.retryCount}/${this.maxRetries} pour ${this.tenantId}`)
                    this.initialize()
                }, 5000 * this.retryCount)
            }
        } else if (connection === 'open') {
            this.isConnected = true
            this.retryCount = 0
            qrCodes.delete(this.tenantId)
            
            console.log(`Connexion établie pour ${this.businessName} (${this.tenantId})`)
            
            // Traiter la queue des messages en attente
            this.processMessageQueue()
        }
    }

    async handleIncomingMessages(m) {
        const messages = m.messages
        
        for (const message of messages) {
            // Ignorer messages de groupes, status et nos propres messages
            if (
                message.key.fromMe ||
                isJidBroadcast(message.key.remoteJid) ||
                isJidStatusBroadcast(message.key.remoteJid) ||
                message.key.remoteJid.includes('@g.us')
            ) continue

            try {
                await this.processIncomingMessage(message)
            } catch (error) {
                console.error(`Erreur traitement message pour ${this.tenantId}:`, error)
            }
        }
    }

    async processIncomingMessage(message) {
        const from = message.key.remoteJid
        const messageContent = this.extractMessageContent(message)
        
        if (!messageContent) return

        console.log(`Message reçu [${this.tenantId}] de ${from}: ${messageContent.substring(0, 50)}...`)

        // Envoyer au backend pour traitement IA
        try {
            const response = await axios.post(`${BACKEND_URL}/api/process-message`, {
                tenant_id: parseInt(this.tenantId),
                customer_phone: from.split('@')[0],
                message: messageContent,
                message_type: 'text'
            }, { timeout: 15000 })

            // Réponse IA reçue, l'envoyer
            if (response.data?.ai_response) {
                await this.sendMessage(from, response.data.ai_response)
            }

        } catch (error) {
            console.error(`Erreur appel backend pour ${this.tenantId}:`, error.message)
            
            // Message d'erreur générique
            await this.sendMessage(from, 
                "Désolé, je rencontre un problème technique temporaire. Un de nos conseillers va vous répondre rapidement."
            )
        }
    }

    extractMessageContent(message) {
        // Extraire le contenu selon le type de message
        if (message.message?.conversation) {
            return message.message.conversation
        }
        
        if (message.message?.extendedTextMessage?.text) {
            return message.message.extendedTextMessage.text
        }
        
        if (message.message?.imageMessage?.caption) {
            return `[Image] ${message.message.imageMessage.caption}`
        }
        
        if (message.message?.videoMessage?.caption) {
            return `[Vidéo] ${message.message.videoMessage.caption}`
        }
        
        if (message.message?.audioMessage) {
            return '[Message vocal reçu]'
        }

        return null
    }

    async sendMessage(to, text, options = {}) {
        if (!this.isConnected || !this.sock) {
            console.warn(`Session ${this.tenantId} non connectée, message en queue`)
            this.messageQueue.push({ to, text, options })
            return false
        }

        try {
            // Simuler indicateur de frappe
            await this.sock.sendPresenceUpdate('composing', to)
            await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))
            
            // Envoyer le message
            await this.sock.sendMessage(to, { text })
            
            // Arrêter l'indicateur
            await this.sock.sendPresenceUpdate('paused', to)
            
            console.log(`Message envoyé [${this.tenantId}] vers ${to}: ${text.substring(0, 30)}...`)
            return true

        } catch (error) {
            console.error(`Erreur envoi message ${this.tenantId}:`, error)
            return false
        }
    }

    async processMessageQueue() {
        if (this.messageQueue.length === 0) return

        console.log(`Traitement queue ${this.tenantId}: ${this.messageQueue.length} messages`)

        for (const msg of this.messageQueue) {
            await this.sendMessage(msg.to, msg.text, msg.options)
            await new Promise(resolve => setTimeout(resolve, 1000)) // Délai entre messages
        }

        this.messageQueue = []
    }

    broadcastQR(qr) {
        wss.clients.forEach(client => {
            if (client.readyState === 1) { // WebSocket.OPEN
                client.send(JSON.stringify({
                    type: 'qr',
                    tenantId: this.tenantId,
                    businessName: this.businessName,
                    qr: qr
                }))
            }
        })
    }

    async disconnect() {
        if (this.sock) {
            await this.sock.logout()
            this.sock = null
            this.isConnected = false
        }
        sessions.delete(this.tenantId)
        console.log(`Session ${this.tenantId} déconnectée`)
    }
}

// API Routes
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'neobot-whatsapp-real',
        active_sessions: sessions.size,
        backend_url: BACKEND_URL
    })
})

app.post('/session/create', async (req, res) => {
    const { tenantId, businessName } = req.body

    if (!tenantId) {
        return res.status(400).json({ error: 'tenantId requis' })
    }

    if (sessions.has(tenantId.toString())) {
        return res.json({ 
            status: 'exists', 
            message: 'Session déjà active',
            connected: sessions.get(tenantId.toString()).isConnected
        })
    }

    const session = new WhatsAppSession(tenantId.toString(), businessName || `Business ${tenantId}`)
    sessions.set(tenantId.toString(), session)

    const initialized = await session.initialize()

    if (initialized) {
        res.json({
            status: 'created',
            tenantId: tenantId,
            message: 'Session créée, scannez le QR code'
        })
    } else {
        sessions.delete(tenantId.toString())
        res.status(500).json({ error: 'Échec initialisation session' })
    }
})

app.get('/session/qr/:tenantId', (req, res) => {
    const tenantId = req.params.tenantId
    const qr = qrCodes.get(tenantId)
    const session = sessions.get(tenantId)

    if (!session) {
        return res.status(404).json({ error: 'Session non trouvée' })
    }

    if (session.isConnected) {
        return res.json({ status: 'connected', message: 'WhatsApp déjà connecté' })
    }

    if (qr) {
        return res.json({ status: 'qr_ready', qr: qr })
    }

    res.json({ status: 'initializing', message: 'QR en génération...' })
})

app.post('/session/disconnect/:tenantId', async (req, res) => {
    const tenantId = req.params.tenantId
    const session = sessions.get(tenantId)

    if (!session) {
        return res.status(404).json({ error: 'Session non trouvée' })
    }

    await session.disconnect()
    res.json({ status: 'disconnected', tenantId: tenantId })
})

app.get('/sessions', (req, res) => {
    const sessionList = Array.from(sessions.entries()).map(([id, session]) => ({
        tenantId: id,
        businessName: session.businessName,
        connected: session.isConnected,
        queueLength: session.messageQueue.length
    }))

    res.json({
        total: sessions.size,
        sessions: sessionList
    })
})

// Démarrage des services
const server = app.listen(PORT, () => {
    console.log('='.repeat(50))
    console.log('🤖 NéoBot WhatsApp Service RÉEL')
    console.log('='.repeat(50))
    console.log(`📱 API: http://localhost:${PORT}`)
    console.log(`🔌 WebSocket: ws://localhost:${WS_PORT}`)
    console.log(`🌐 Backend: ${BACKEND_URL}`)
    console.log('='.repeat(50))
})

// WebSocket pour communication temps réel
wss.on('connection', (ws) => {
    console.log('Nouvelle connexion WebSocket')
    
    ws.on('message', (data) => {
        try {
            const message = JSON.parse(data)
            console.log('Message WebSocket reçu:', message)
        } catch (error) {
            console.error('Erreur parsing WebSocket:', error)
        }
    })
})

// Nettoyage gracieux
process.on('SIGINT', async () => {
    console.log('\nArrêt en cours...')
    
    // Déconnecter toutes les sessions
    for (const [tenantId, session] of sessions) {
        console.log(`Déconnexion session ${tenantId}`)
        await session.disconnect()
    }
    
    server.close()
    process.exit(0)
})
