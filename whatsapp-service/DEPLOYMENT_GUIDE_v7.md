# 🚀 NéoBot WhatsApp Service v7 - Professional Deployment Guide

**Status**: Production-Ready with Real-Time Monitoring & Auto-Correction  
**Created**: v7.0 - Professional Implementation  
**Author**: NéoBot Development Team  
**Last Updated**: 2026-03-13

---

## 📋 Table of Contents

1. [Architecture Overview](#-architecture-overview)
2. [Prerequisites](#-prerequisites)
3. [Installation & Setup](#-installation--setup)
4. [Running the Service](#-running-the-service)
5. [Monitoring Dashboard](#-monitoring-dashboard)
6. [Auto-Correction Engine](#-auto-correction-engine)
7. [Troubleshooting Guide](#-troubleshooting-guide)
8. [Common Issues & Solutions](#-common-issues--solutions)
9. [Production Checklist](#-production-checklist)
10. [Architecture & Technical Details](#-architecture--technical-details)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     NéoBot WhatsApp System                  │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌────────────────────┐
│  WhatsApp Users  │         │  Next.js Frontend  │
│                  │         │  (Port 3000)       │
└────────┬─────────┘         └─────────┬──────────┘
         │                             │
         │ (Messages)                  │ (Web UI)
         │                             │
         ▼                             ▼
    ┌────────────────────────────────────────────┐
    │  WhatsApp Service v7 (Node.js)             │
    │  📦 Professional Implementation            │
    │  🎯 Port: 3001                            │
    │                                            │
    │  Components:                               │
    │  ✓ ProfessionalLogger                     │
    │  ✓ HealthMonitor (Real-time Metrics)     │
    │  ✓ ExpertRetryStrategy (Smart Backoff)   │
    │  ✓ DiagnosisSystem (Self-Healing)        │
    │  ✓ ConnectionState Management            │
    │  ✓ Express API (6 Endpoints)              │
    └──────────────────┬───────────────────────┘
                       │
         ┌─────────────┼──────────────┐
         │             │              │
         ▼             ▼              ▼
    ┌─────────┐  ┌──────────┐  ┌────────────┐
    │Dashboard │  │Auto-Fix  │  │Monitoring  │
    │CLI       │  │Engine    │  │Endpoints   │
    │(3001)    │  │(Daemon)  │  │(REST API)  │
    └─────────┘  └──────────┘  └────────────┘
         │             │              │
         └─────────────┴──────────────┘
                       │
                       ▼
    ┌────────────────────────────────┐
    │  FastAPI Backend (Python)      │
    │  📦 Port: 8000                 │
    │  - Multi-tenant Architecture   │
    │  - AI Integration (DeepSeek)   │
    │  - Business Logic              │
    │  - Database Management         │
    └────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │  PostgreSQL Database    │
         │  📦 Port: 5432          │
         │  - Users, Messages      │
         │  - Subscriptions        │
         │  - Analytics            │
         │  - Business Config      │
         └─────────────────────────┘
```

---

## ✅ Prerequisites

### System Requirements
- Node.js 18+ (check: `node --version`)
- npm 9+ (check: `npm --version`)
- FastAPI Backend running on port 8000
- PostgreSQL Database accessible

### Network Requirements
- Outbound HTTPS to WhatsApp servers (port 443)
- Inbound HTTP on port 3001 (WhatsApp Service)
- Inbound HTTP on port 8000 (Backend)
- Inbound TCP on port 5432 (Database)

### Dependencies
All dependencies are automatic via `npm install`:
- `@whiskeysockets/baileys@^6.7.21` - WhatsApp library
- `express@^4.22.1` - HTTP server
- `axios@^1.13.6` - HTTP client
- `chalk@^5.3.0` - Terminal colors
- `blessed@^0.1.81` - Dashboard UI
- `pino@^8.17.2` - Logging

---

## 🔧 Installation & Setup

### Step 1: Install Dependencies

```bash
cd /home/tim/neobot-mvp/whatsapp-service

# Install all dependencies
npm install

# Verify installations
npm list --depth=0
```

**Expected output:**
```
neobot-whatsapp@3.0.0
├── @whiskeysockets/baileys@6.7.21
├── axios@1.13.6
├── blessed@0.1.81
├── chalk@5.3.0
├── dotenv@16.6.1
├── express@4.22.1
├── pino@8.17.2
├── qrcode@1.5.3
└── qrcode-terminal@0.12.0
```

### Step 2: Environment Configuration

Create or verify `.env` file:

```bash
cat > .env << 'EOF'
# WhatsApp Service Configuration
WHATSAPP_SERVICE_URL=http://localhost:3001
BACKEND_URL=http://localhost:8000
TENANT_ID=1

# Node Configuration
NODE_ENV=production
PORT=3001

# Logging
LOG_LEVEL=info

# Feature Flags
ENABLE_MOCK_MODE=false
ENABLE_MONITORING=true
ENABLE_AUTO_CORRECTION=true
EOF
```

### Step 3: Clean Previous Sessions (First Run Only)

```bash
# Remove old authentication cache
npm run clean

# Or manually:
rm -rf auth_info_baileys .wwebjs_auth session sessions.json
```

---

## ▶️ Running the Service

### Option 1: Direct Execution (Development/Testing)

```bash
# Run the professional service
npm run pro

# Expected output:
# ✓ WhatsApp Service v7 Professional Started
# 🚀 Listening on http://localhost:3001
# 📊 Health: HEALTHY (100/100)
```

### Option 2: Watch Mode (Auto-Restart on Changes)

```bash
# Run with auto-reload for development
npm run pro:watch
```

### Option 3: Production with Process Manager

**Install PM2:**
```bash
npm install -g pm2
```

**Start Service:**
```bash
pm2 start whatsapp-service-v7-professional.js \
  --name "whatsapp-service" \
  --instances max \
  --exec-mode cluster \
  --visible
```

**Auto-Start on Reboot:**
```bash
pm2 startup systemd -u $USER --hp /home/$USER
pm2 save
```

**Monitor Service:**
```bash
pm2 monitor
pm2 logs whatsapp-service
```

### Parallel Terminal Setup (Recommended)

**Terminal 1: Run WhatsApp Service**
```bash
npm run pro
```

**Terminal 2: Run Dashboard**
```bash
npm run dashboard
```

**Terminal 3: Run Auto-Correction Engine** (Optional but Recommended)
```bash
node auto-correction.js
```

---

## 📊 Monitoring Dashboard

### Launching the Dashboard

```bash
npm run dashboard
# or
npm run monitor
```

### Dashboard Features

The professional dashboard provides real-time monitoring:

#### Status Panel (Left)
- **Service Status**: Connected/Disconnected/Connecting
- **Health Score**: 0-100 (higher is better)
- **Connection Stats**: Total connections, messages processed
- **Success Rate**: Percentage of successful operations
- **Uptime**: Time since service started
- **Error Tracking**: WebSocket and API error counts
- **Last Error**: When the last error occurred

#### Metrics Panel (Right)
- **Performance**: Total transactions, failed transactions
- **QR Codes Generated**: Authentication attempts
- **Timing**: Current connection state and uptime
- **History**: Disconnection tracking

#### Logs Panel (Bottom)
- **Real-time Log Stream**: Timestamped entries
- **Color-coded Levels**: Error, Warn, Info, Success, Debug
- **Scrollable History**: Navigate through recent logs
- **Auto-scroll**: Newest entries appear at bottom

### Dashboard Commands

| Key | Action |
|-----|--------|
| **r** | Refresh data immediately |
| **d** | Run full diagnostics |
| **q** | Quit dashboard |
| **Mouse** | Scroll logs, interact with panels |

### Dashboard Interpretation

**Healthy Service** (Green)
```
Status: CONNECTED
Health Score: 95/100
Success Rate: 98%
```

**Degraded Service** (Yellow)
```
Status: CONNECTED
Health Score: 65/100
Success Rate: 73%
→ Monitor logs for issues
→ Check network connectivity
```

**Critical Service** (Red)
```
Status: DISCONNECTED
Health Score: 15/100
Success Rate: 22%
→ Check WebSocket errors
→ Verify WhatsApp account status
→ Check network connectivity
```

---

## 🔧 Auto-Correction Engine

### Launching Auto-Correction

```bash
# In a separate terminal
node auto-correction.js

# Expected output:
# 🔧 Auto-Correction Engine Started
# 
# Monitors for:
# ✓ WebSocket errors
# ✓ High error rates
# ✓ Connection drops
# ✓ Timeout issues
# ✓ Authentication failures
```

### What Auto-Correction Does

**Problem → Automatic Action**

| Issue | Detection | Automatic Action |
|-------|-----------|-----------------|
| **WebSocket Errors >5** | Counts errors | Browser agent rotation attempt |
| **Success Rate <50%** | Calculates rate | Log diagnostic, alert user |
| **Disconnection** | State change | Trigger reconnection sequence |
| **Auth Lost** | Log pattern match | Notify to require QR rescan |
| **Timeout Detected** | Log pattern match | Increase timeout recommendations |
| **Health <40/100** | Score calculation | Recovery plan suggestions |

### Auto-Correction Report

Every minute, see a summary:
```
📈 Auto-Correction Report (Last minute)
  Total: 3 | Success: 2 | Failed: 1
  Success Rate: 66.7%
```

---

## 🔍 Troubleshooting Guide

### Quick Diagnostics

#### Check Service Health
```bash
curl http://localhost:3001/health
```

**Response (Healthy):**
```json
{
  "status": "ok",
  "service": "WhatsApp Service v7",
  "timestamp": "2026-03-13T10:30:45Z"
}
```

#### Get Detailed Status
```bash
curl http://localhost:3001/status
```

#### Run Full Diagnosis
```bash
curl -X POST http://localhost:3001/diagnose
```

#### View Recent Logs
```bash
curl "http://localhost:3001/logs?limit=50" | jq .
```

### Step-by-Step Troubleshooting

#### Problem 1: "Cannot connect to service"

**Symptoms**
```
✗ Cannot connect to service
Make sure the service is running
```

**Solution**
```bash
# Step 1: Check if service is running
ps aux | grep whatsapp-service-v7

# Step 2: Check for port conflicts
netstat -tlnp | grep 3001

# Step 3: Kill any existing process
pkill -f whatsapp-service-v7

# Step 4: Start service fresh
npm run pro
```

#### Problem 2: "WebSocket Error (405)"

**Symptoms**
```
ERROR [websocket] WebSocket Error (405)
Connection Failure - incompatible protocol
```

**Explanation**  
Baileys v6.7.21 incompatibility with 2026 WhatsApp protocol.

**Solutions**
1. **Immediate** (Temporary)
   ```bash
   # Dashboard will show /diagnose details
   npm run dashboard
   # Press 'd' to run diagnostics
   ```

2. **Short-term**  
   Wait for Baileys library update from maintainers:
   ```bash
   npm update @whiskeysockets/baileys
   ```

3. **Alternative Approach**  
   Use Mock mode for testing:
   ```bash
   # In whatsapp-service/: Change ENABLE_MOCK_MODE=true
   npm run pro
   ```

#### Problem 3: "QR Code Not Displaying"

**Symptoms**
```
State: waiting_qr (but no QR visible)
Timeout waiting for QR scan
```

**Solution**
```bash
# Step 1: Check logs for QR generation
npm run logs | grep -i qr

# Step 2: Verify terminal supports colors
echo $TERM

# Step 3: Clear session and try again
npm run clean
npm run pro

# Step 4: If using SSH, ensure terminal supports:
# - ANSI colors
# - Unicode box drawing
```

#### Problem 4: "Messages Not Reaching Backend"

**Symptoms**
```
Message received but not processing
Backend returns 404
```

**Solution**
```bash
# Step 1: Verify backend is running
curl http://localhost:8000/health

# Step 2: Check endpoint exists
curl http://localhost:8000/api/v1/webhooks/whatsapp

# Step 3: Verify correct endpoint in service config
# Should be: http://localhost:8000/api/v1/webhooks/whatsapp
# NOT: http://localhost:8000/webhooks/whatsapp

# Step 4: Check service logs
npm run logs | grep 'webhook\|backend\|POST'

# Step 5: Test manually
curl -X POST http://localhost:3001/ \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'
```

#### Problem 5: "Service Keeps Disconnecting"

**Symptoms**
```
State: disconnected (repeating)
connectionClosed events in logs
```

**Solution**
```bash
# Step 1: Check network connectivity
ping -c 3 google.com

# Step 2: Verify WhatsApp account not logged in elsewhere
# Check your phone - is WhatsApp Web already connected?
# Disconnect other devices if needed

# Step 3: Run diagnostics
curl -X POST http://localhost:3001/diagnose | jq .

# Step 4: Check error logs for patterns
npm run logs | grep -E 'error|Error|ERROR'

# Step 5: If persistent, try with increased timeouts
# Edit whatsapp-service-v7-professional.js:
# connectTimeoutMs: 120000, // Double to 120s
# keepAliveIntervalMs: 60000, // Double to 60s

# Step 6: Restart with fresh session
npm run clean
npm run pro
```

### Advanced Diagnostics

#### Memory Usage
```bash
# Check process memory
ps aux | grep whatsapp-service | grep -v grep | awk '{print $6}'

# If >500MB, service might have memory leak
# Solution: Restart service
pkill -f whatsapp-service-v7
npm run pro
```

#### CPU Usage
```bash
# Monitor CPU usage
top -p $(pgrep -f whatsapp-service-v7)

# If stuck >80%, restart immediately
pkill -f whatsapp-service-v7-professional
npm run pro
```

#### Database Connection Issues
```bash
# Test database connection
psql -h localhost -U neobot -d neobot_db -c "SELECT count(*) FROM messages"

# If fails, verify:
# - PostgreSQL is running
# - Credentials correct
# - Database exists
```

---

## 🐛 Common Issues & Solutions

### Connection Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `ECONNREFUSED` | Backend not running | `uvicorn app.main:app --reload` |
| `ETIMEDOUT` | Network/firewall | Check network, increase timeout |
| `ENOTFOUND` | DNS issue | Verify hostname resolution |
| `Connection Failure` | Baileys proto | Update library or wait for fix |

### Authentication Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `loggedOut` | QR expired | Scan new QR code |
| `multideviceMismatch` | Account locked | Clear session, create new QR |
| `Unauthorized 401` | Invalid credentials | Verify WhatsApp account status |

### Performance Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Slow responses | Memory leak | Restart service |
| High CPU | Infinite loop | Check logs, restart service |
| Database slow | Connection pooling | Verify DB performance |

### Monitoring Issues

| Problem | Solution |
|---------|----------|
| Dashboard not connecting | Verify port 3001 open |
| Metrics showing old data | Press 'r' to refresh |
| Auto-correction not working | Verify auto-correction.js running |

---

## ✅ Production Checklist

Before deploying to production:

```bash
# 1. Dependencies installed
npm list --depth=0
□ All packages installed

# 2. Environment variables set
cat .env
□ BACKEND_URL correct
□ TENANT_ID correct
□ NODE_ENV=production

# 3. Database connection verified
npm run status
□ Backend responding
□ Database accessible

# 4. Service starts cleanly
npm run pro
□ No errors on startup
□ Health endpoint responds

# 5. Dashboard connects
npm run dashboard
□ Shows healthy status
□ Metrics updating

# 6. Auto-correction ready (optional)
node auto-correction.js
□ Monitoring active
□ Detection working

# 7. Process manager configured
pm2 list
□ Service registered
□ Auto-restart enabled
□ Startup hook set

# 8. Logging configured
npm run logs | head -20
□ Logs readable
□ Error tracking enabled

# 9. Backup created
cp -r auth_info_baileys auth_info_baileys.backup
□ Session backup exists

# 10. Documentation reviewed
□ Team has access to guide
□ Troubleshooting steps shared
□ Contact info for support
```

---

## 🏛️ Architecture & Technical Details

### Service Components

#### 1. ProfessionalLogger 📝
```javascript
// In-memory logging with 1000 entry limit
{
  info: (message) => logs.push({message, level: 'INFO', ...}),
  error: (message) => error tracking,
  warn: (message) => warning tracking,
  success: (message) => success counting,
  debug: (message) => debug logging,
  
  getLastLogs: (count) => retrieve(count),
  getErrorStats: () => {errors, types, recency}
}
```

**Features**
- Circular buffer (newest overwrites oldest)
- Error categorization (websocket, api, connection, processing)
- Timestamp and context tracking
- Queryable via `/logs` endpoint

#### 2. HealthMonitor 🏥
```javascript
// Real-time metrics calculation
{
  connections: number,
  disconnections: number,
  messagesProcessed: number,
  errorsEncountered: number,
  successRate: percentage,
  uptime: seconds,
  
  calculateHealthScore: () => 0-100 based on:
    - Success rate (50% weight)
    - Error recency (30% weight)
    - Uptime (20% weight)
}
```

**Health Score Formula**
```
Score = (successRate * 0.5) + 
        (errorRecencyScore * 0.3) + 
        (uptimeScore * 0.2)

Health Status:
- 80-100: HEALTHY (green)
- 50-79:  DEGRADED (yellow)
- 0-49:   CRITICAL (red)
```

#### 3. ExpertRetryStrategy 🔄
```javascript
// Exponential backoff with jitter
{
  calculateDelay: (attempt) => 
    min(initialDelay * (1.5^attempt), maxDelay) + jitter,
  
  getNextBrowser: () => rotate through [
    'ubuntu_chrome',
    'ubuntu_firefox', 
    'macos_safari',
    'windows_edge'
  ],
  
  shouldRetry: (error) => smart decision based on error type,
  
  getRecoveryStrategy: (error) => specific recovery plan
}
```

**Backoff Formula**
```
delay = min(1000 * (1.5^attempt), 30000) + random(0-5000)

Attempt Delays:
1: ~1-6 seconds
2: ~1.5-6.5 seconds  
3: ~2.25-7.25 seconds
4: ~3.38-8.38 seconds
5: ~5-10 seconds
...up to 30 second cap
```

#### 4. DiagnosisSystem 🔍
```javascript
// Self-healing diagnostics
{
  checkNetwork: () => ping test, latency measure,
  checkAuthState: () => auth validation, account check,
  checkBrowser: () => browser compatibility, agent check,
  checkTiming: () => timeout validation, interval check,
  checkWhatsAppStatus: () => server response time
}
```

**Diagnosis Output**
```json
{
  "checks": {
    "network": {
      "status": "ok",
      "message": "Connectivity good",
      "latency": 45
    },
    "authState": {
      "status": "authenticated",
      "message": "Account valid"
    },
    "timing": {
      "connectTimeout": 60000,
      "keepAliveInterval": 30000,
      "queryTimeout": 20000
    },
    "browser": {
      "availableBrowsers": 4,
      "browsers": ["ubuntu_chrome", "ubuntu_firefox", "macos_safari", "windows_edge"]
    },
    "whatsappStatus": {
      "status": "ok",
      "message": "Servers responding",
      "latency": 120
    }
  }
}
```

### API Endpoints

#### `/health` (GET)
Basic health check
```bash
curl http://localhost:3001/health
# {status: "ok", service: "WhatsApp Service v7", timestamp: "..."}
```

#### `/status` (GET)
Detailed service status
```bash
curl http://localhost:3001/status
# {status, connections, state, messages, errors, uptime, ...}
```

#### `/metrics` (GET)
Performance metrics
```bash
curl http://localhost:3001/metrics
# {connections, disconnections, messagesProcessed, successRate, ...}
```

#### `/logs` (GET)
Recent logs with filtering
```bash
curl "http://localhost:3001/logs?limit=50"
# {logs: [{timestamp, level, message, icon}, ...]}
```

#### `/diagnose` (POST)
Full system diagnostics
```bash
curl -X POST http://localhost:3001/diagnose
# {checks: {network, authState, timing, browser, whatsappStatus}}
```

#### `/health/detailed` (GET)
Comprehensive health analysis
```bash
curl http://localhost:3001/health/detailed
# {status, healthScore, metrics, lastError, timestamp, ...}
```

### Connection Lifecycle

```
[START]
  ↓
[DIAGNOSIS] ← Check network, auth, browser, timing
  ↓
[CREATE SOCKET] ← makeWASocket with browser agent
  ↓
[WAIT QR] ← Display QR code for scanning
  ↓
[CONNECTED] ← Account authenticated
  ↓
[LISTEN MESSAGES] ← Receive incoming messages
  ↓ (message received)
[PROCESS MESSAGE] → Send to backend
  ↓
[SEND RESPONSE] ← Receive from backend
  ↓
[FORWARD TO CHAT] ← Send to WhatsApp user
  │
  └──> [ERROR] → log + retry with backoff
           ↓
        [RECOVERY] → switch browser or reconnect
           ↓
        [BACK TO CONNECTED]
```

### Error Handling Strategy

```
Error Received
  ↓
[CLASSIFY] → websocket/api/connection/processing
  ↓
[LOG] → Store in memory with timestamp/context
  ↓
[TRACK] → Count errors by type
  ↓
[DECIDE] → Should retry?
  ↓
  ├─[YES] → Calculate backoff delay
  │          ↓
  │       [TRY RECOVERY] → switch browser/clear cache/etc
  │          ↓
  │       [RETRY] with exponential backoff
  │
  └─[NO] → Notify user, await manual intervention
             (loggedOut, multideviceMismatch, etc)
```

---

## 📞 Support & Contact

For issues not covered in this guide:

1. **Check Dashboard Logs** → Real-time issue visibility
2. **Run Diagnostics** → `/diagnose` endpoint analysis  
3. **Review Troubleshooting** → This guide, specific section
4. **Contact DevOps Team** → With logs and error details

---

## 📚 Quick Reference

```bash
# Service Management
npm run pro              # Start service
npm run pro:watch       # Start with auto-reload
npm run clean          # Clear old sessions
npm run full-clean     # Fresh reinstall

# Monitoring
npm run dashboard      # Launch dashboard
npm run health        # Quick health check
npm run status        # Detailed status
npm run logs          # View recent logs
npm run diagnose      # Run diagnostics

# Auto-Correction (Optional)
node auto-correction.js  # Start auto-correction engine

# Process Manager (Production)
pm2 start whatsapp-service-v7-professional.js --name "whatsapp-service"
pm2 save
pm2 startup

# Stop Service
pm2 stop whatsapp-service
npm stop               # or Ctrl+C
```

---

**Generated**: 2026-03-13  
**Version**: v7.0 - Professional Implementation  
**Status**: Production Ready ✅
