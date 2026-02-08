import os

print("🎯 SERVICES NÉOBOT - INVENTAIRE COMPLET")
print("=" * 50)

services = {
    "fallback_service.py": "Service de fallback intelligent (réponses automatiques)",
    "closeur_pro_service.py": "Système de persuasion et anti-abandon", 
    "ai_service.py": "Ancien service IA (maintenant intégré dans main.py)",
    "whatsapp_qr_service.py": "Gestion QR Code WhatsApp",
    "contact_filter_service.py": "Filtrage des contacts professionnels/personnels"
}

# Vérifier l'existence de chaque service
for service, description in services.items():
    path = f"app/services/{service}"
    if os.path.exists(path):
        print(f"✅ {service:25} - {description}")
    else:
        print(f"❌ {service:25} - NON TROUVÉ")

print("\n📊 MODÈLES DE BASE DE DONNÉES :")
models = ["Tenant", "Conversation", "Message", "TenantSector", "PendingMessage"]
for model in models:
    print(f"   🗃️  {model}")

print("\n🎯 ENDPOINTS API PRINCIPAUX :")
endpoints = [
    "POST /api/tenants/{id}/whatsapp/message",
    "GET /api/tenants/{id}/analytics", 
    "GET /api/tenants/{id}/analytics/monthly",
    "POST /api/tenants",
    "GET /api/tenants/{id}"
]
for endpoint in endpoints:
    print(f"   🌐 {endpoint}")

print("\n🔧 FONCTIONNALITÉS ACTIVÉES :")
features = [
    "🤖 IA DeepSeek (prioritaire)",
    "🔧 Fallback intelligent (secours)",
    "💬 WhatsApp Baileys",
    "📊 Analytics et statistiques",
    "🎯 Closeur Pro (persuasion éthique)",
    "🗂️  Gestion multi-tenants"
]
for feature in features:
    print(f"   {feature}")
