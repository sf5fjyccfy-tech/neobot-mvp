# Deprecated API Layer (`app/api`)

This directory contains legacy route modules kept only for historical reference.

Status:
- Not mounted in `backend/app/main.py`
- Not part of the active runtime API surface
- Active endpoints are implemented in `backend/app/routers/`

Guidelines:
- Do not add new features in `app/api`
- Implement and mount routes from `app/routers/*`
- If legacy files are needed, migrate logic into active routers before removal
