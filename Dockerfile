# Visaroo backend — FastAPI on AWS App Runner.
# Build context is the REPO ROOT so both backend/ and scripts/ are available.
#   docker build -t visaroo-backend .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    PYTHONPATH=/app/backend

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY corpus/ ./corpus/
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8080

ENTRYPOINT ["sh", "docker-entrypoint.sh"]
