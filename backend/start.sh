#!/bin/bash
if [ -f "alembic.ini" ]; then
  alembic upgrade head || echo "No alembic migrations or alembic not configured"
fi
exec uvicorn app.main:app --host 0.0.0.0 --port \${PORT:-8000}
