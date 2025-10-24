// debug_baileys_allinone.js
import fs from "fs"
import path from "path"
import makeWASocket, {
    useMultiFileAuthState,
    fetchLatestBaileysVersion,
    DisconnectReason
} from "@whiskeysockets/baileys"
import P from "pino"

async function clearAuthFolder(folder) {
    const folderPath = path.resolve(folder)
    if (fs.existsSync(folderPath)) {
        console.log("🧹 Suppression du dossier de session corrompu :", folderPath)
        fs.rmSync(folderPath, { recursive: true, force: true })
    }
}

async function startAllInOne() {
    console.log("🚀 [NÉOBOT] Lancement du test complet WhatsApp...")

    const { version } = await fetchLatestBaileysVersion()
    console.log("📦 Version Baileys :", version)

    const authFolder = "./auth_info"
    await clearAuthFolder(authFolder)

    const { state, saveCreds } = await useMultiFileAuthState(authFolder)

    const sock = makeWASocket({
        logger: P({ level: "silent" }),
        printQRInTerminal: true,
        browser: ["Ubuntu", "Chrome", "22.04.4"],
        auth: state,
    })

    sock.ev.on("creds.update", saveCreds)

    sock.ev.on("connection.update", (update) => {
        const { connection, lastDisconnect } = update
        if (connection === "close") {
            const reason = lastDisconnect?.error?.output?.statusCode
            console.log(`❌ Connexion fermée. Raison : ${reason}`)
            if (reason === 401) {
                console.log("⚠️ Session expirée ou invalide. Suppression automatique...")
                clearAuthFolder(authFolder).then(() => startAllInOne())
            } else if (reason !== DisconnectReason.loggedOut) {
                console.log("🔁 Tentative de reconnexion...")
                startAllInOne()
            } else {
                console.log("🚫 Déconnexion complète. Scan du QR code requis.")
            }
        } else if (connection === "open") {
            console.log("✅ Connexion WhatsApp établie avec succès !")
            sendTestMessage(sock)
        }
    })
}

async function sendTestMessage(sock) {
    try {
        const jid = "237XXXXXXXXX@s.whatsapp.net" // ← Mets ton numéro ici
        await sock.sendMessage(jid, { text: "✅ Test NÉOBOT : connexion réussie !" })
        console.log("🎯 Message test envoyé avec succès !")
    } catch (e) {
        console.error("💥 Échec d’envoi du message test :", e.message)
    }
}

startAllInOne()

