# 🚀 NéoBot Quick Start - 5 Minutes

## What You Need
- Linux/Mac terminal
- Node.js 20+ installed
- Python 3.10+ installed
- A WhatsApp account

## Step 1: Start WhatsApp Service (2 min)

```bash
cd /home/tim/neobot-mvp/whatsapp-service
npm start
```

You should see:
```
✅ Baileys initialized
⏳ Connecting to WhatsApp...
🚀 WhatsApp Service running on http://localhost:3001
📱 Scan QR code: http://localhost:3001/qr
```

## Step 2: Scan QR Code (2 min)

1. Open browser: **http://localhost:3001/qr**
2. Scan the QR code with your phone
3. WhatsApp → 3 dots menu → Linked devices
4. Scan the code shown on your computer

Wait 10-15 seconds for connection.

## Step 3: Test Connection (1 min)

Open new terminal:

```bash
curl http://localhost:3001/health
```

You should see:
```json
{
  "service": "WhatsApp Bot (Baileys)",
  "status": "ok",
  "isConnected": true,
  "timestamp": "2025-01-01T12:00:00.000Z"
}
```

## Done! ✅

Your WhatsApp bot is now:
- ✅ Connected to your WhatsApp account
- ✅ Receiving messages
- ✅ Ready to respond
- ✅ Auto-reconnecting if connection drops

---

## Next: Connect Backend (Optional)

When ready, integrate with backend:

```bash
# Add to /home/tim/neobot-mvp/backend/app/main.py

from app.whatsapp_webhook import router as whatsapp_router
app.include_router(whatsapp_router)
```

Then uncomment webhook call in `whatsapp-service/src/server.js` (line ~93).

---

## Troubleshooting

**"No QR code available"**
→ Reload page, service might still starting

**"Bot not connected"**
→ Scan the QR code again from `http://localhost:3001/qr`

**"Port 3001 already in use"**
→ Kill old process: `pkill -f "npm start"`

**"Module not found"**
→ Install packages: `cd whatsapp-service && npm install`

---

## Next Commands

View logs:
```bash
tail -f /home/tim/neobot-mvp/whatsapp-service/logs/service.log
```

Stop bot:
```bash
pkill -f "npm start"
```

Reset (new QR code):
```bash
rm -rf /home/tim/neobot-mvp/whatsapp-service/whatsapp_sessions/*
npm start  # in whatsapp-service folder
```

---

**Enjoy your WhatsApp bot! 🤖**
