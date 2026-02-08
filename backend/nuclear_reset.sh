#!/bin/bash
echo "💥 RÉINITIALISATION NUCLÉAIRE"
echo "============================="

cd ~/neobot-mvp/backend

# 1. Tout arrêter
echo "🛑 Arrêt total..."
pkill -9 -f "python" 2>/dev/null || true
sleep 2

# 2. Recréer un main.py ULTRA SIMPLE
echo "📝 Recréation main.py..."
cat > app/main.py << 'MAIN_EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/")
def root():
    return {"message": "NéoBot TEST", "status": "OK"}

@app.get("/health")
def health():
    return {"status": "healthy", "test": "simple"}

@app.post("/api/auth/login")
def login(data: LoginRequest):
    if data.email == "admin@neobot.ai" and data.password == "admin123":
        return {
            "access_token": "test_token_123",
            "token_type": "bearer",
            "user_id": 1,
            "tenant_id": 1
        }
    raise HTTPException(status_code=401, detail="Bad credentials")

@app.get("/api/test")
def test():
    return {"message": "Test OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
MAIN_EOF

# 3. Démarrer
echo "🚀 Démarrage..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
sleep 3

# 4. Tester
echo "🧪 Test basique..."
curl -s http://localhost:8000/health
echo ""
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@neobot.ai","password":"admin123"}' \
  -s | python3 -m json.tool

echo ""
echo "✅ Si ça marche, le problème est dans votre code complexe"
