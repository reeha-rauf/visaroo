#!/bin/sh
# Visaroo backend container entrypoint.
# SQLite is ephemeral in the container, so seed demo data on each boot, then serve.
set -e

cd /app

echo "[visaroo] seeding demo data..."
python scripts/seed_demo.py || echo "[visaroo] seed_demo skipped"
python scripts/seed_webinars.py || echo "[visaroo] seed_webinars skipped"
python scripts/seed_creator_posts.py || echo "[visaroo] seed_creator_posts skipped"
python scripts/fetch_news.py || echo "[visaroo] fetch_news skipped (no network?)"

echo "[visaroo] starting uvicorn on :${PORT:-8080}"
cd /app/backend
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
