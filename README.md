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

- Backend API: http://localhost:8000/docs
- WhatsApp Simulator: http://localhost:3000/health
- Health checks: http://localhost:8000/health

## Test manuel

1. Créer un tenant via http://localhost:8000/docs
2. Simuler un message via POST http://localhost:3000/simulate
3. Voir les conversations via GET http://localhost:8000/api/conversations/1

## Structure du projet

```
neobot-mvp/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # API principale
│   │   ├── models.py       # Modèles base de données
│   │   └── database.py     # Configuration DB
│   └── whatsapp_simulator.py  # Simulateur WhatsApp
├── scripts/                # Scripts utilitaires
├── docker-compose.yml      # Services Docker
└── README.md              # Ce fichier
```

## Prochaines étapes

1. Remplacer le simulateur par vraie intégration WhatsApp
2. Ajouter interface frontend
3. Intégrer vraie IA (DeepSeek)
4. Déployer en production
