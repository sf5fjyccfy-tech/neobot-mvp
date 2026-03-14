# 🚀 NEOBOT WhatsApp Service - v4.0 Optimized Edition

**Status: Production Ready**

## ✨ What's New in v4.0

### 🔧 Core Fixes
- **✅ No more infinite loops** - Service stops after max retries
- **✅ Stable Baileys** - Using latest stable instead of RC  
- **✅ Smart QR handling** - Auto-expires after 60 seconds
- **✅ Proper retry logic** - Max 3 retries, then STOP
- **✅ Better error messages** - Clear API error responses

### 📊 Production Features
- **Health Check** - Monitors connection every 30s
- **Graceful Shutdown** - Proper cleanup on SIGTERM/SIGINT
- **Session Persistence** - Credentials saved securely
- **Comprehensive Logging** - Debug-level logs available
- **API Monitoring** - Track all webhook failures

### 🛡️ Prevention Features
- **Port Lock** - Prevents multiple instances
- **Memory Protection** - Limits in-memory messages
- **Connection Timeout** - 120s transaction timeout
- **Disk Space Check** - Diagnostic alerts for low space

---

## 📦 Installation

### Option A: Fresh Install
```bash
cd /home/tim/neobot-mvp/whatsapp-service

# Clean old files
bash start-optimized.sh --clean

# Service starts automatically
```

### Option B: Update Existing
```bash
cd /home/tim/neobot-mvp/whatsapp-service

# Kill old service
pkill -9 -f "whatsapp-production.js" || true

# Update dependencies
npm install

# Start optimized version
bash start-optimized.sh
```

---

## 🎯 Using the Service

### 1. **Start Service**
```bash
bash start-optimized.sh
```

### 2. **Wait for QR Code**
Service will display:
```
📱 SCANNER LE QR CODE
...instructions...
```

You have **60 seconds** to scan the QR code with your WhatsApp phone.

### 3. **Scan with WhatsApp**
1. Open WhatsApp on your phone
2. Go to: Settings → Linked Devices → Connect Device
3. Point camera at the QR code
4. Confirm

### ✅ Once Connected
```
✅ WhatsApp CONNECTÉ ✅
🎉 Connexion réussie!
```

Service is ready to send/receive messages.

---

## 📡 API Endpoints

### Health Check
```bash
curl http://localhost:3001/health
```

Response:
```json
{
  "status": "healthy",
  "connected": true,
  "timestamp": "2026-03-13T00:00:00.000Z"
}
```

### Get Status
```bash
curl http://localhost:3001/status
```

Response:
```json
{
  "connected": true,
  "state": "connected",
  "uptime_ms": 123456,
  "tenant_id": 1,
  "hasQR": false,
  "error": null
}
```

### Get QR Code Data
```bash
curl http://localhost:3001/api/whatsapp/qr
```

Response:
```json
{
  "has_qr": true,
  "qr_data": "data:image/png;base64,...",
  "state": "waiting_auth",
  "message": "Waiting for QR scan"
}
```

### Reset/Logout
```bash
curl -X POST http://localhost:3001/api/whatsapp/reset
```

Response:
```json
{
  "status": "reset_initiated",
  "message": "Waiting for new QR code"
}
```

### Send Message
```bash
curl -X POST http://localhost:3001/api/whatsapp/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "to": "33612345678@s.whatsapp.net",
    "message": "Hello from NéoBot!"
  }'
```

Response:
```json
{
  "status": "sent",
  "id": "message-id-xyz",
  "timestamp": "2026-03-13T00:00:00.000Z"
}
```

---

## 🔍 Debugging

### Check Service Status
```bash
curl -s http://localhost:3001/status | json_pp
```

### View Real-time Logs
```bash
# Service logs are printed to console
# For file logging, redirect stdout:
# node whatsapp-optimized.js > logs/whatsapp.log 2>&1 &
```

### Run Diagnostic
```bash
bash diagnostic-system.sh
```

### Kill Service
```bash
pkill -9 -f "whatsapp-optimized.js"
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Backend API URL
BACKEND_URL=http://localhost:8000

# Service Port
PORT=3001

# Tenant ID
TENANT_ID=1

# Log Level (debug, info, warn, error)
LOG_LEVEL=info

# Session Timeout (ms, default: 72 hours)
SESSION_TIMEOUT=259200000
```

### Advanced Configuration

Edit `whatsapp-optimized.js` to customize:
- `QR_TIMEOUT`: 60000 ms (60 seconds)
- `RECONNECT_DELAY`: 5000 ms (5 seconds)
- `MAX_RETRIES`: 3 attempts
- `HEALTH_CHECK_INTERVAL`: 30000 ms (30 seconds)

---

## 🐛 Troubleshooting

### Problem: Service starts but no QR code appears
**Solution:** Check if port 3001 is blocked
```bash
ss -tlnp | grep 3001
# If active, kill it: sudo fuser -k 3001/tcp
```

### Problem: QR code expires (60s timeout)
**Solution:** Call reset endpoint
```bash
curl -X POST http://localhost:3001/api/whatsapp/reset
```

### Problem: "Connection Failure" errors
**Solution:** 
1. Check internet connection
2. Verify WhatsApp servers are accessible
3. Try `--clean` restart: `bash start-optimized.sh --clean`

### Problem: "Max retries exceeded"
**Solution:**
1. Reset the service: `curl -X POST http://localhost:3001/api/whatsapp/reset`
2. Scan new QR code within 60 seconds
3. Wait for "✅ WhatsApp CONNECTÉ"

### Problem: Old process still running
**Solution:**
```bash
# Force kill all node processes
killall -9 node
# Or specifically:
pkill -9 -f "whatsapp"
```

---

## 📊 Service States

| State | Meaning | Action |
|-------|---------|--------|
| `initializing` | Starting up | Wait... |
| `waiting_auth` | Waiting for QR scan | Scan the QR code |
| `connected` | ✅ Ready | Send messages! |
| `disconnected` | Lost connection | Service will retry |
| `error` | Fatal error | Call `/reset` endpoint |

---

## 🚀 Production Recommendations

1. **Run in background:**
   ```bash
   nohup bash start-optimized.sh > logs/whatsapp.log 2>&1 &
   ```

2. **Use process manager (PM2):**
   ```bash
   npm install -g pm2
   pm2 start whatsapp-optimized.js --name whatsapp
   pm2 save
   pm2 startup
   ```

3. **Monitor health:**
   ```bash
   # Add to crontab (every 5 minutes)
   */5 * * * * curl -s http://localhost:3001/health > /dev/null || systemctl restart whatsapp
   ```

4. **Log rotation:**
   ```bash
   # Redirect to file with rotation
   node whatsapp-optimized.js | logrotate
   ```

5. **Enable HTTPS proxy:**
   ```bash
   # Use nginx/Apache to proxy port 3001
   # Recommended for production
   ```

---

## 📝 Version History

### v4.0 (Current)
- Completely rewritten for stability
- Removed all infinite loops
- Added QR timeout (60s)
- Smart health checking
- Better error handling
- Production-ready

### v3.0 (Previous)
- Initial optimized version
- Had retry loop issues

---

## 💡 Tips & Tricks

### Automatic QR Code Display (Web Interface)
Create a simple web page that calls `/api/whatsapp/qr` to display the QR code:
```html
<img id="qr" />
<script>
  setInterval(() => {
    fetch('/api/whatsapp/qr')
      .then(r => r.json())
      .then(d => {
        if (d.has_qr) {
          document.getElementById('qr').src = d.qr_data;
        }
      });
  }, 1000);
</script>
```

### Webhook Integration
The service sends messages to your backend:
```bash
POST /api/whatsapp/webhook/message
{
  "tenant_id": 1,
  "from": "33612345678@s.whatsapp.net",
  "message": {...},
  "timestamp": 1234567890
}
```

Make sure your backend endpoint is configured at `BACKEND_URL`.

---

## 🤝 Support

If you encounter issues:
1. Run: `bash diagnostic-system.sh`
2. Check logs for error messages
3. Try: `bash start-optimized.sh --clean`
4. Review troubleshooting section above

---

**Happy messaging! 🚀**
