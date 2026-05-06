#!/bin/bash
# =============================================================
# Production entrypoint:
# 1. Wait for PostgreSQL
# 2. Run Alembic migrations
# 3. Start uvicorn with multiple workers
# =============================================================
set -e

echo "[entrypoint] Waiting for database..."
until python -c "
import asyncio, asyncpg, os
async def check():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'].replace('postgresql+asyncpg', 'postgresql'))
    await conn.close()
asyncio.run(check())
" 2>/dev/null; do
  echo "[entrypoint] DB not ready, retrying in 2s..."
  sleep 2
done
echo "[entrypoint] Database is ready."

echo "[entrypoint] Running migrations..."
alembic upgrade head
echo "[entrypoint] Migrations done."

echo "[entrypoint] Running bootstrap (seed permissions + admin user)..."
python tools/bootstrap.py
echo "[entrypoint] Bootstrap done."

echo "[entrypoint] Starting API server..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --no-access-log
