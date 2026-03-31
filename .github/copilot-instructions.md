# NeoBot — Contexte projet

## Stack
- Backend : FastAPI (Python) — port 8000
- Frontend : Next.js (React/TypeScript) — port 3002
- Service WhatsApp : Node.js / Baileys — port 3001
- Base de données : PostgreSQL (`neobot_db`)
- Monitoring : Grafana Cloud + Sentry
- Paiements : Korapay (Mobile Money + cartes, API Payout pour reversements marchands)
- CDN/HTTPS : Cloudflare
- Email transactionnel : Brevo

## Produit
SaaS d'agents IA conversationnels sur WhatsApp. Les clients configurent un agent via un dashboard, l'agent répond automatiquement à leurs clients sur WhatsApp. 5 types d'agents : Libre, RDV & Suivi, Support & FAQ, Vente, Qualification.

## Architecture clés
- `backend/app/` : FastAPI — routers, models SQLAlchemy, services, dependencies
- `frontend/src/` : Next.js App Router — `app/`, `components/`, `lib/api.ts`
- `whatsapp-service/` : Node.js Baileys — `whatsapp-production.js` comme entry point
- Superadmin : `users.is_superadmin = TRUE` (user id=8, timpatrick561@gmail.com)
- Tenant actif dev : id=13
- Auth : JWT dans localStorage, impersonation dans sessionStorage (token 1h)

## Règles absolues
- Toutes les clés API en variables d'environnement, jamais dans le code
- Signature HMAC obligatoire sur tous les webhooks Korapay
- Les prompts système des agents ne sont jamais exposés côté client ni loggés en clair
- Gestion d'erreurs explicite partout — pas de crash silencieux
- Mobile-first — utilisateurs finaux majoritairement sur mobile en Afrique
- Les routes `/api/admin/*` utilisent `Depends(get_superadmin_user)` — vérification en DB, jamais côté client seul
- ALTER TABLE via `psql -U postgres` (socket Unix) — user `neobot` n'a pas les droits DDL

## NeoCaisse
Système de paiement intégré : paiement reçu sur compte NeoBot Korapay → commission NeoBot déduite → reversement automatique au marchand via Payout API vers son Mobile Money.

## Commandes utiles
```bash
# Backend
source /home/tim/neobot-mvp/.venv/bin/activate
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend && npm run dev -- --port 3002

# WhatsApp service
cd whatsapp-service && node whatsapp-production.js

# DB (admin)
psql -U postgres -d neobot_db
```
