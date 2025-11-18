# 📋 STATUT DES SERVICES NEOBOT

## Services Actifs & Exposés ✅

| Service | Statut | Endpoint | Usage |
|---------|--------|----------|-------|
| `fallback_service.py` | ✅ Actif | `/api/tenants/{id}/whatsapp/message` | Réponses par défaut |
| `closeur_pro_service.py` | ✅ Actif | `/api/tenants/{id}/closeur-pro/analyze` | Analyse persuasion |
| `ai_service.py` | ✅ Actif | Utilisé dans whatsapp_webhook | Appels DeepSeek |
| `analytics_service.py` | ✅ Intégré | `/api/analytics/*` | Analytics conversations |
| `product_service.py` | ✅ Intégré | `/api/products/*` | Gestion produits |
| `contact_filter_service.py` | ✅ Utilisé | `whatsapp_webhook.py` | Filtrage contacts |
| `whatsapp_service.py` | ✅ Intégré | Webhooks | Service WhatsApp |

## Services Ghost (Définis mais Non Exposés) ⚠️

| Service | Raison | Recommendation |
|---------|--------|-----------------|
| `order_service.py` | Pas d'endpoint | ❌ Supprimer ou créer `/api/orders/*` |
| `sales_service.py` | Pas d'endpoint | ❌ Supprimer ou intégrer analytics |
| `stock_service.py` | Pas d'endpoint | ❌ Supprimer ou créer `/api/stock/*` |
| `paysika_service.py` | Pas d'endpoint | ❌ Supprimer ou créer `/api/payments/paysika` |
| `correcteur_africain.py` | Pas d'endpoint | ❌ Supprimer ou intégrer dans IA |
| `spell_corrector.py` | Doublon? | ❌ Supprimer (doublon de correcteur_africain) |
| `whatsapp_qr_service.py` | Non utilisé | ❌ Supprimer (feature non active) |

## Fichiers À Vérifier

| Fichier | Type | Recommendation |
|---------|------|-----------------|
| `whatsapp_client.py` | Client | Garder si utilisé par whatsapp_service.py |
| `alembic/` | Migration | Archiver ou supprimer |

---

## 🎯 DÉCISION FINALE

### Option A: Nettoyer Agressivement (Recommandé)
Supprimer tous les services ghost (order, sales, stock, paysika, correcteurs)
→ Code mort qui n'apporte rien actuellement

### Option B: Préserver pour l'Avenir
Garder les services mais les documenter comme "futurs" ou "en attente d'intégration"

**CHOIX: Option A** - Supprimer le code mort pour garder le codebase propre.
