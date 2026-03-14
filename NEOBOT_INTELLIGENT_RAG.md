# NEOBOT INTELLIGENT - Système RAG (Retrieval Augmented Generation)
## Comment le bot devient intelligent avec les vraies données

---

## 🎯 LE PROBLÈME RÉSOLU

**Avant**: Le bot inventait les réponses
- "On va lancer un plan à 123 FCFA" (inexact)
- "Notre tarif est secret" (confus)
- Pas de cohérence avec le profil réel

**Maintenant**: Le bot utilise les VRAIES données du business
- Tarifs corrects (20K, 50K, 90K FCFA)
- Descriptions de produits exactes
- Ton et style cohérents avec le profil
- Réponses basées sur des faits, pas sur l'hallucination

---

## 🏗️ ARCHITECTURE NOUVELLE

```
Message → WhatsApp Webhook
    ↓
BrainOrchestrator.process()
    ↓
generate_ai_response_with_db()  ← NOUVEAU: RAG-enabled
    ├─ KnowledgeBaseService.get_tenant_profile()
    │   └─ Récupère données réelles de TenantBusinessConfig
    ├─ KnowledgeBaseService.format_profile_for_prompt()  
    │   └─ Formate données pour prompt système
    ├─ Construit prompt système ENRICHI avec donnéesréelles
    └─ Appel DeepSeek (avec vrai contexte métier)
        └─ Réponse intelligente basée sur FAITS
Response → Utilisateur
```

---

## 📊 DONNÉES UTILISÉES (RAG Context)

### Pour NéoBot (tenant 1):
```
PROFIL MÉTIER:
- Entreprise: NéoBot
- Type: neobot
- Ton: Professional, Friendly, Expert, Persuasif
- Focus: Efficacité, Scaling, Support client
- Description: Plateforme d'automatisation WhatsApp avec IA

PRODUITS/SERVICES:
- Basique: 20000 FCFA (2000 messages/mois)
- Standard: 50000 FCFA (illimité + IA avancée)
- Pro: 90000 FCFA (4000 messages + canaux illimités)
```

### Pour clients (restaurant, ecommerce, etc.):
```
PROFIL MÉTIER:
- Entreprise: [Nom du client]
- Type: [restaurant/ecommerce/...]
- Ton: [Friendly/Professional/...]
- Focus: [Quality/Price/Service/...]
- Produits/Services: [Liste exacte avec prix]
```

---

## 🚀 UTILISATION

### 1. Initialiser le profil NéoBot
```bash
curl -X POST http://localhost:8000/api/v1/setup/init-neobot-profile

# Réponse:
{
  "status": "success",
  "message": "NéoBot profile initialized for tenant 1",
  "profile": {
    "name": "NéoBot",
    "business_type": "neobot",
    "tone": "Professional, Friendly, Expert, Persuasif",
    "selling_focus": "Efficacité, Scaling, Support client",
    "products_count": 3
  }
}
```

### 2. Vérifier le profil
```bash
curl http://localhost:8000/api/v1/setup/profile/1

# Obtient le profil complet du tenant
```

### 3. Voir le contexte RAG (ce que l'IA verra)
```bash
curl http://localhost:8000/api/v1/setup/profile/1/formatted

# Retourne le texte exact fourni au prompt système
```

### 4. Envoyer un message via WhatsApp
```
Message: "Quel est votre tarif?"

AVANT (sans RAG):
- Bot: "On vend des services, mais je sais pas les prix"

APRÈS (avec RAG):
- Bot: "💰 Nos plans:
  - Basique: 20,000 FCFA/mois
  - Standard: 50,000 FCFA/mois
  - Pro: 90,000 FCFA/mois
  Lequel vous intéresse?"
```

---

## 📋 COMMENT ÇA MARCHE TECHNIQUEMENT

### Étape 1: Récupérer le profil réel
```python
profile = KnowledgeBaseService.get_tenant_profile(db, tenant_id=1)
# Retourne dict avec: name, business_type, tone, products_services, etc.
```

### Étape 2: Formater pour le prompt
```python
rag_context = KnowledgeBaseService.format_profile_for_prompt(profile)
# Retourne string lisible pour l'IA:
# "PROFIL MÉTIER: NéoBot
#  PRODUITS/SERVICES:
#  - Basique: 20000 FCFA..."
```

### Étape 3: Construire le prompt système RICHE
```python
system_prompt = f"""Tu es NéoBot, assistant d'automatisation WhatsApp.

{rag_context}  ← Les vraies données du business sont ICI!

INSTRUCTIONS:
- Réponds avec les tarifs ci-dessus
- Mentionne les produits réels
- Sois persuasif et professionnel
"""
```

### Étape 4: Appel API avec contexte réel
```python
response = await DeepSeekClient.call(
    messages=[
        {"role": "system", "content": system_prompt},  ← Contient données réelles
        {"role": "user", "content": "Quel est votre tarif?"}
    ]
)
```

### Résultat: Réponse intelligente basée sur FAITS ✅

---

## 🎨 CUSTOMISER LE PROFIL

### Pour un restaurant:
```python
profile = {
    "company_name": "La Saveur Restaurant",
    "business_type": "restaurant",
    "tone": "Warm, Friendly, Inviting",
    "selling_focus": "Quality, Taste, Service",
    "products_services": [
        {"name": "Pizza Margherita", "price": 5000, "description": "Fromage, tomate, basilic"},
        {"name": "Pâtes à la Crème", "price": 6500, "description": "Sauce maison, crème fraîche"},
        {"name": "Dessert Chocolat", "price": 3000}
    ]
}
```

Le bot répondra:
- Question "Vous avez une pizza?": "Oui! Notre Pizza Margherita (5000 FCFA) est délicieuse!"
- Question "Prix?": "Nos plats vont de 3000 à 6500 FCFA avec des saveurs exceptionnelles"

### Pour un ecommerce:
```python
profile = {
    "company_name": "TechShop",
    "business_type": "ecommerce",
    "tone": "Professional, Modern, Helpful",
    "selling_focus": "Innovation, Value for Money",
    "products_services": [
        {"name": "Smartphone XYZ", "price": 180000, "description": "5G, 128GB"},
        {"name": "Laptop ABC", "price": 450000, "description": "Intel i7, 16GB RAM"},
    ]
}
```

---

## ✅ VÉRIFIER QUE ÇA MARCHE

### Test 1: Profil créé?
```bash
curl http://localhost:8000/api/v1/setup/profile/1
# Doit retourner les données NéoBot
```

### Test 2: Contexte RAG formaté?
```bash
curl http://localhost:8000/api/v1/setup/profile/1/formatted
# Doit afficher "PROFIL MÉTIER: NéoBot..." dans rag_context
```

### Test 3: Bot répond intelligemment?
Envoyez un message via WhatsApp:
- "Quel est votre tarif?" → Doit lister 20K, 50K, 90K
- "Vous faites quoi?" → Doit parler d'automatisation WhatsApp
- "Essai gratuit?" → Doit mentionner 7 jours gratuit

---

## 🔧 DÉBOGUER SI ÇA NE MARCHE PAS

### Problème: Bot invente toujours les réponses
**Cause**: Profil non créé ou pas chargé  
**Solution**:
```bash
# 1. Créer le profil
curl -X POST http://localhost:8000/api/v1/setup/init-neobot-profile

# 2. Vérifier qu'il est créé
curl http://localhost:8000/api/v1/setup/profile/1

# 3. Regarder les logs
tail -f /home/tim/neobot-mvp/logs/app.log | grep "RAG\|profile"
```

### Problème: Erreur "Profile not found"
**Cause**: Table tenant_business_config vide  
**Solution**:
- Le profil devrait être créé automatiquement au startup
- Sinon, appeler l'endpoint `/init-neobot-profile` manuellement

### Problème: Bot ignore les produits dans la liste
**Cause**: Format JSON incorrect dans products_services  
**Solution**:
```python
# Vérifier que c'est correct:
products_services = [
    {
        "name": "Basique",
        "price": 20000,
        "description": "...",
        "features": [...]
    }
]
# NOT: "products_services": "string literal"
```

---

## 📈 AMÉLIORATIONS FUTURES

1. **Cache RAG**: Cacher les profils pour réduire latence
2. **Semantic Search**: Chercher info pertinente si question spécifique
3. **Dynamic Prompts**: Adapter prompt selon le type de question
4. **Multi-language**: Support français/anglais/autres
5. **Custom Templates**: Templates personnalisées par tenant

---

## 📚 FICHIERS CLÉS

- `app/services/knowledge_base_service.py` - Service RAG principal
- `app/services/ai_service_rag.py` - Logique IA avec RAG
- `app/routers/setup.py` - Endpoints pour gérer les profils
- `app/whatsapp_webhook.py` - Webhook qui utilise RAG
- `backend/app/database.py` - Tables (tenant_business_config)

---

**Résultante**: Bot intelligent qui répond avec VRAI DONNÉES ✅ 
Au lieu d'inventer! 🎉
