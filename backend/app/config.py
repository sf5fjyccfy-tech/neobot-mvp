import os

# Fichier de configuration NéoBot (config.py)
NEOBOT_TENANT_ID = 1
# Clé secrète partagée entre le service Node.js et FastAPI (à mettre dans .env en prod)
WHATSAPP_SECRET_KEY = os.getenv("WHATSAPP_WEBHOOK_SECRET") or os.getenv("WHATSAPP_SECRET_KEY") or ""
