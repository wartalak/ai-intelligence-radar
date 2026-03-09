#!/bin/bash
# ──────────────────────────────────────────────
# AI Intelligence Radar — First Run Script
# ──────────────────────────────────────────────

set -e

echo "🛰️  AI Intelligence Radar — First Run Setup"
echo "============================================="

# Check .env
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys, then run this script again."
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first."
    exit 1
fi

echo "🐳 Starting all services..."
docker compose up -d --build

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

echo ""
echo "🔄 Running initial content ingestion..."
docker exec radar-celery-worker celery -A app.workers.celery_app call app.workers.tasks.ingest_all_content || true

echo ""
echo "📊 Generating initial report..."
docker exec radar-celery-worker celery -A app.workers.celery_app call app.workers.tasks.generate_daily_report_task || true

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Dashboard:  http://localhost:3000"
echo "🔌 API:        http://localhost:8000"
echo "📚 API Docs:   http://localhost:8000/docs"
echo ""
echo "📡 Data will auto-refresh every 2 hours via Celery Beat."
