# NéoBot MVP - Assistant IA pour PME Africaines

## Démarrage rapide

### 1. Services Docker (base de données)

```bash
docker-compose up -d
```

### 2. Backend FastAPI

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 3. Simulateur WhatsApp

```bash
cd backend
source venv/bin/activate
python whatsapp_simulator.py
```

## Ou utiliser les scripts

### Démarrage

```bash
./scripts/start_backend.sh    # Terminal 1
./scripts/start_whatsapp.sh   # Terminal 2
```

### Test du système

```bash
./scripts/test_system.sh
```

## Endpoints principaux

- Backend API : [http://localhost:8000/docs](http://localhost:8000/docs)
- WhatsApp Simulator : [http://localhost:3000/health](http://localhost:3000/health)
- Health checks : [http://localhost:8000/health](http://localhost:8000/health)

## Test manuel

1. Créer un tenant via l'interface API : [Backend API](http://localhost:8000/docs)

   Exemple JSON pour la création d'un tenant :

   ```json
   {
     "name": "Test Tenant",
     "email": "test@example.com",
     "phone": "+22500000000",
     "business_type": "restaurant"
   }
   ```

2. Simuler un message via POST vers le simulateur WhatsApp.
3. Voir les conversations via GET sur l'API.

## Configuration rapide

- Assurez-vous que PostgreSQL écoute sur le port standard 5432.
- Exemple de variable d'environnement pour la base de données :

```bash
export DATABASE_URL="postgresql://neobot:azerty2007@localhost:5432/neobot"
```

## Structure du projet

```
neobot-mvp/
├── backend/                 
│   ├── app/
│   │   ├── main.py         # API principale + routes
│   │   ├── models.py       # Modèles DB (Tenant, Message, etc.)
│   │   ├── database.py     # Config PostgreSQL
│   │   └── services/       # Services métier
│   │       └── ai_service.py # Service IA DeepSeek
├── docker-compose.yml      # PostgreSQL config
└── README.md              
```

## Fonctionnalités actives

- Connexion PostgreSQL (port 5432)
- Health check avec logging
- Intégration DeepSeek AI
- Gestion des tenants
- Quota messages (vérification à ajouter avant traitement)

## Problèmes connus

- Période d'essai à activer automatiquement (trial_ends_at)
- Tests de charge non implémentés
- Simulateur WhatsApp à ré-intégrer si besoin

## Prochaines étapes

1. Implémenter l'activation automatique de la période d'essai
2. Intégrer l'API WhatsApp Business
3. Ajouter interface frontend
4. Configurer les tests de charge
5. Déployer en production
