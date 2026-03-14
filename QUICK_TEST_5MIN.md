# ⚡ QUICK TEST - 5 MINUTES

**Goal**: Validate RAG system works  
**Time**: 5 minutes max  
**Level**: Non-technical OK

---

## DO THIS NOW (in order)

### 1️⃣ Terminal 1: Start Backend (1 min)
```bash
cd /home/tim/neobot-mvp/backend
python -m uvicorn app.main:app --reload

# Wait for: "Uvicorn running on http://127.0.0.1:8000"
```

### 2️⃣ Terminal 2: Run Tests (2 min)
```bash
cd /home/tim/neobot-mvp
./test_rag_system.sh

# Should show all ✅
```

### 3️⃣ Terminal 2: Send Test Message (2 min)
```bash
# Test 1: Init profile
curl -X POST http://localhost:8000/api/v1/setup/init-neobot-profile

# Test 2: Get profile (check for "NéoBot" and "50000" FCFA)
curl http://localhost:8000/api/v1/setup/profile/1 | jq '.products_services[1]'

# Test 3: See RAG context
curl http://localhost:8000/api/v1/setup/profile/1/formatted | jq '.rag_context'
```

---

## ✅ EXPECTED RESULTS

### If you see these → WORKING ✅
```json
{
  "status": "success",
  "message": "NéoBot profile initialized"
}

{
  "company_name": "NéoBot",
  "business_type": "neobot",
  "tone": "Professional, Friendly, Expert, Persuasif"
}

{
  "name": "Standard",
  "price": 50000,
  "description": "Illimité, IA Avancée, Support prioritaire"
}

"PROFIL MÉTIER: NéoBot..."
```

### If you see errors → See [TEST_GUIDE_FINAL.md](./TEST_GUIDE_FINAL.md) Troubleshooting

---

## 🎯 THAT'S IT!

If all ✅ then system is **production ready**! 🚀

For full details see: [TEST_GUIDE_FINAL.md](./TEST_GUIDE_FINAL.md)

---

**Next**: Send real WhatsApp messages and verify bot responds with correct prices/products!
