// debug_baileys.js
// Script de test complet pour diagnostiquer Baileys

import makeWASocket, {
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion
} from '@whiskeysockets/baileys'

import pino from 'pino'

const logger = pino({ level: 'info' })

async function connectTest() {
  try {
    logger.info('🚀 Démarrage du test de connexion WhatsApp...')

    // 1️⃣ Auth state
    const { state, saveCreds } = await useMultiFileAuthState('./auth_info_baileys')

    // 2️⃣ Version Baileys
    const { version, isLatest } = await fetchLatestBaileysVersion()
    logger.info(`📦 Version Baileys: ${version.join('.')}, dernière version: ${isLatest}`)

    // 3️⃣ Connexion
    const sock = makeWASocket({
      logger,
      printQRInTerminal: true,
      auth: state,
      version,
      syncFullHistory: false,
    })

    // 4️⃣ Sauvegarde automatique
    sock.ev.on('creds.update', saveCreds)

    // 5️⃣ Log complet sur chaque update
    sock.ev.on('connection.update', (update) => {
      const { connection, lastDisconnect, qr } = update

      if (qr) logger.info('📱 QR code généré — scanne-le rapidement avec ton WhatsApp !')

      if (connection === 'open') {
        logger.info('✅ Connexion WhatsApp établie avec succès !')
      } else if (connection === 'close') {
        const reason = lastDisconnect?.error?.output?.statusCode
        logger.error(`❌ Connexion fermée — Code: ${reason}`)

        if (reason === DisconnectReason.loggedOut) {
          logger.warn('⚠️ Session expirée ou supprimée. Supprime auth_info_baileys et reconnecte.')
        } else if (reason === 405) {
          logger.error('🚫 Erreur 405: méthode interdite — version Baileys/WhatsApp peut être obsolète.')
        } else {
          logger.error('🔍 Détail erreur:', lastDisconnect?.error)
        }
      }
    })

    // 6️⃣ Test envoi message (optionnel)
    setTimeout(async () => {
      try {
        const jid = '237XXXXXXXXXX@s.whatsapp.net' // ⚠️ remplace par ton numéro test
        await sock.sendMessage(jid, { text: '✅ Test de connexion réussi via debug_baileys.js' })
        logger.info('📤 Message test envoyé avec succès.')
      } catch (e) {
        logger.error('💥 Échec d’envoi de message test:', e)
      }
    }, 10000)

  } catch (err) {
    logger.error('💀 Erreur critique:', err)
  }
}

connectTest()
