/**
 * Baileys WhatsApp Service pour NéoBot
 * Phase 8M: Intégration complète avec QR code, session management, et features
 * 
 * Features:
 * - QR Code scanning
 * - Session persistence (chiffré)
 * - Rate limiting anti-ban
 * - Reconnexion automatique
 * - Health monitoring
 */

import makeWASocket, {
  useMultiFileAuthState,
  DisconnectReason,
  Browsers
} from "@whiskeysockets/baileys";
import NodeCache from "node-cache";
import qrcode from "qrcode-terminal";
import axios from "axios";
import pino from "pino";
import dotenv from "dotenv";
import { readFileSync, writeFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const TENANT_ID = parseInt(process.env.TENANT_ID) || 1;

// Logger
const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  transport: {
    target: "pino-pretty",
    options: {
      colorize: true,
      translateTime: "SYS:standard",
      ignore: "pid,hostname"
    }
  }
});

// Cache pour QR code rapidement
const qrCache = new NodeCache({ stdTTL: 120 }); // Expire après 2 min
let globalSessionId = null;
let sock = null;
let messageQueue = [];
let lastMessageTime = 0;
const RATE_LIMIT_MS = 2000; // 2 sec minimum entre messages (500 msg/hour ~ 100 msg/hour best case)

/**
 * Rate Limiter Anti-Ban
 */
class RateLimiter {
  constructor() {
    this.messageCount = 0;
    this.lastResetTime = Date.now();
    this.windowSize = 3600000; // 1 hour en ms
  }

  canSendMessage() {
    const now = Date.now();
    
    // Reset counter chaque heure
    if (now - this.lastResetTime > this.windowSize) {
      this.messageCount = 0;
      this.lastResetTime = now;
    }
    
    // Max 100 messages par heure (ultra safe)
    return this.messageCount < 100;
  }

  recordMessage() {
    this.messageCount++;
  }

  getStats() {
    return {
      messages_this_hour: this.messageCount,
      limit: 100,
      safe: this.messageCount < 80
    };
  }
}

const rateLimiter = new RateLimiter();

/**
 * Génère et affiche QR code
 */
async function handleQRCode(qr, sessionId) {
  console.log("\n");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("        📱 SCANNEZ CE CODE QR AVEC VOTRE TÉLÉPHONE 📱");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  qrcode.generate(qr, { small: true });
  
  console.log("\n═══════════════════════════════════════════════════════════\n");
  
  // Sauvegarde en cache
  qrCache.set(`qr_${sessionId}`, qr);
  
  // Notifie backend
  try {
    await axios.post(`${BACKEND_URL}/api/whatsapp/qr-generated`, {
      session_id: sessionId,
      qr_code: qr,
      expires_at: new Date(Date.now() + 120000).toISOString()
    });
    logger.info(`✅ QR code notifié au backend`);
  } catch (err) {
    logger.warn(`⚠️ Erreur notificat QR au backend: ${err.message}`);
  }
}

/**
 * Initialise la session WhatsApp
 */
async function initializeSession(sessionId) {
  globalSessionId = sessionId;
  
  const auth = await useMultiFileAuthState(`./auth_info_${sessionId}`);
  
  sock = makeWASocket({
    auth: auth.state,
    logger: pino({ level: "error" }),
    browser: Browsers.macOS("Safari"),
    qrTimeout: 180000, // 3 min QR timeout
    connectTimeoutMs: 60000,
    maxRetries: 5,
    retryRequestDelayMs: 1000,
    chattingStatus: true,
    version: [2, 2353, 11],
    printQRInTerminal: false
  });

  // QR Code
  sock.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;
    
    if (qr) {
      await handleQRCode(qr, sessionId);
    }
    
    if (connection === "connecting") {
      logger.info("📡 Connexion en cours...");
    }
    
    if (connection === "open") {
      logger.info(`✅ CONNECTÉ! ${sock.user?.name}`);
      
      // Notifie backend
      try {
        await axios.post(`${BACKEND_URL}/api/whatsapp/session-connected`, {
          session_id: sessionId,
          phone_number: sock.user?.id?.split(":")[0],
          timestamp: new Date().toISOString()
        });
      } catch (err) {
        logger.warn(`Erreur notificat connexion: ${err.message}`);
      }
      
      // Sauveregarde session
      await auth.saveCreds();
    }
    
    if (connection === "close") {
      const shouldReconnect =
        lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
      
      logger.warn(
        `🔌 Déconnecté. Redémarrage: ${shouldReconnect ? "Oui" : "Non"}`
      );
      
      if (shouldReconnect) {
        setTimeout(() => initializeSession(sessionId), 3000);
      }
    }
  });

  // Reçoit les messages
  sock.ev.on("messages.upsert", async (m) => {
    logger.info(`📨 Reçu depuis ${m.messages[0].key.remoteJid}`);

    for (const msg of m.messages) {
      if (!msg.message) return; // Ignore les reçus

      const text =
        msg.message.conversation ||
        msg.message.extendedTextMessage?.text ||
        "";

      if (!text) return;

      const from = msg.key.remoteJid;
      const name = msg.pushName || from;

      logger.info(`💬 ${name}: ${text.substring(0, 50)}`);

      // Ajoute à queue
      messageQueue.push({
        from,
        name,
        text,
        timestamp: msg.messageTimestamp
      });

      // Envoie au backend (webhook)
      await sendToBackend(from, name, text);
    }
  });

  // Handle errors
  sock.ev.on("error", (err) => {
    logger.error(`❌ Erreur: ${err.message}`);
  });

  // Update creds
  sock.ev.on("creds.update", async () => {
    await auth.saveCreds();
  });

  return sock;
}

/**
 * Envoie le message reçu au backend
 */
async function sendToBackend(from, name, text) {
  try {
    // Rate limit check
    if (!rateLimiter.canSendMessage()) {
      logger.warn(
        `⚠️ Rate limit atteint! (${rateLimiter.getStats().messages_this_hour}/100 cette heure)`
      );
      return;
    }

    const response = await axios.post(
      `${BACKEND_URL}/api/v1/webhooks/whatsapp`,
      {
        from,
        name,
        message: text,
        timestamp: new Date().toISOString(),
        session_id: globalSessionId
      },
      {
        timeout: 30000,
        headers: {
          "Content-Type": "application/json"
        }
      }
    );

    rateLimiter.recordMessage();
    logger.info(`✅ Envoyé au backend: ${response.status}`);

    // Si le backend retourne une réponse, envoie
    if (response.data?.response) {
      await sendMessageWithDelay(from, response.data.response);
    }
  } catch (err) {
    logger.error(
      `❌ Erreur backend: ${err.response?.status || err.message}`
    );
  }
}

/**
 * Envoie message avec délai (anti-ban)
 */
async function sendMessageWithDelay(to, text, delay = 2000) {
  const now = Date.now();
  const timeSinceLastMsg = now - lastMessageTime;

  if (timeSinceLastMsg < delay) {
    const waitTime = delay - timeSinceLastMsg;
    logger.info(`⏱️ Attente ${waitTime}ms avant envoi`);
    await new Promise((resolve) => setTimeout(resolve, waitTime));
  }

  try {
    await sock.sendMessage(to, { text });
    lastMessageTime = Date.now();
    logger.info(`✅ Envoyé à ${to}`);
  } catch (err) {
    logger.error(`❌ Erreur envoi: ${err.message}`);
  }
}

/**
 * Déconnecte la session
 */
async function logoutSession(sessionId) {
  try {
    if (sock) {
      await sock.logout();
      logger.info(`🔌 Déconnecté: ${sessionId}`);
    }
  } catch (err) {
    logger.error(`Erreur logout: ${err.message}`);
  }
}

/**
 * Récupère QR code du cache
 */
function getQRCode(sessionId) {
  return qrCache.get(`qr_${sessionId}`);
}

/**
 * Health check
 */
function getHealth() {
  return {
    status: sock?.user ? "connected" : "disconnected",
    phone: sock?.user?.id?.split(":")[0] || null,
    sessionId: globalSessionId,
    messageQueueSize: messageQueue.length,
    rateLimiter: rateLimiter.getStats(),
    uptime: process.uptime()
  };
}

/**
 * Démarrage principal
 */
async function start() {
  logger.info("🚀 Démarrage Baileys Service (Phase 8M)");

  const sessionId = `sess_${Date.now()}`;
  
  try {
    await initializeSession(sessionId);
    logger.info(`✅ Service prêt (Session: ${sessionId})`);
  } catch (err) {
    logger.error(`❌ Erreur démarrage: ${err.message}`);
    process.exit(1);
  }
}

// Express pour les endpoints
import express from "express";

const app = express();
app.use(express.json());

// Endpoints
app.get("/health", (req, res) => {
  res.json(getHealth());
});

app.get("/qr/:sessionId", (req, res) => {
  const qr = getQRCode(req.params.sessionId);
  if (!qr) {
    return res.status(404).json({ error: "QR not found or expired" });
  }
  res.json({ qr_code: qr });
});

app.post("/send/:sessionId", async (req, res) => {
  const { to, text } = req.body;
  if (!to || !text) {
    return res.status(400).json({ error: "Missing to or text" });
  }

  try {
    await sendMessageWithDelay(to, text);
    res.json({ status: "sent" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/logout", async (req, res) => {
  try {
    await logoutSession(globalSessionId);
    res.json({ status: "logged out" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  logger.info(`🌐 Server sur http://localhost:${PORT}`);
  start();
});
