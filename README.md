# AI Intelligence Radar 🛰️

Automated AI ecosystem intelligence platform. Collects real-time data from social media, research papers, blogs, videos, and developer communities — then generates daily AI intelligence reports and custom topic analysis using LLMs.

![Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Stack](https://img.shields.io/badge/Next.js-000?style=flat&logo=nextdotjs&logoColor=white)
![Stack](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Stack](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white)
![Stack](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)

---

## Features

- **Daily Intelligence Reports** — AI-generated briefings with Major Announcements, Research Breakthroughs, New Tools, Trending Discussions, and Strategic Insights
- **Custom Topic Analysis** — Search any AI topic and receive a deep-dive analysis powered by vector similarity search + GPT-4o
- **Multi-Source Data Collection** — Twitter/X, YouTube, RSS feeds (OpenAI, Anthropic, DeepMind, Meta AI, NVIDIA), arXiv research papers, GitHub trending repos
- **Trend Detection** — HDBSCAN clustering + multi-factor trend scoring (velocity × engagement × authority)
- **Beautiful Dashboard** — Dark glassmorphism UI with real-time updates

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Next.js    │────▶│  FastAPI     │────▶│ PostgreSQL  │
│  Frontend   │     │  Backend     │     │ + pgvector  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │   Celery    │────▶ Redis
                    │  Workers    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Twitter/X    YouTube      arXiv
         RSS Feeds    GitHub    (collectors)
```

---

## Quick Start (Docker)

### 1. Clone and configure

```bash
cd ai-intelligence-radar
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
OPENAI_API_KEY=sk-your-key        # Required for embeddings + reports
YOUTUBE_API_KEY=your-key           # Required for YouTube collection
TWITTER_BEARER_TOKEN=your-token   # Optional
GITHUB_TOKEN=your-token           # Optional (increases rate limit)
```

### 2. Start all services

```bash
docker compose up --build
```

This starts:
- **PostgreSQL** (with pgvector) on port 5432
- **Redis** on port 6379
- **FastAPI Backend** on port 8000
- **Celery Worker** for background processing
- **Celery Beat** for scheduled tasks
- **Next.js Frontend** on port 3000

### 3. Open the dashboard

Navigate to [http://localhost:3000](http://localhost:3000)

### 4. Trigger initial data collection

```bash
# Run content ingestion manually
docker exec radar-celery-worker celery -A app.workers.celery_app call app.workers.tasks.ingest_all_content

# Generate today's report
docker exec radar-celery-worker celery -A app.workers.celery_app call app.workers.tasks.generate_daily_report_task

# Detect trends
docker exec radar-celery-worker celery -A app.workers.celery_app call app.workers.tasks.detect_trends_task
```

---

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Needs PostgreSQL (with pgvector) and Redis running locally
cp ../.env.example .env
# Edit .env with your local DB/Redis URLs

uvicorn app.main:app --reload --port 8000
```

### Celery Worker

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

### Celery Beat (scheduler)

```bash
cd backend
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/report/today` | Today's AI intelligence report |
| `GET` | `/api/report/{date}` | Report for a specific date |
| `POST` | `/api/analysis/topic` | Custom topic analysis (body: `{"query": "..."}`) |
| `GET` | `/api/trends` | Current trending topics |
| `GET` | `/api/content/latest` | Latest collected content |
| `GET` | `/health` | Health check |

---

## Data Sources

| Source | Type | What's Collected |
|--------|------|-----------------|
| Twitter/X | API v2 | AI-related tweets, engagement metrics |
| YouTube | Data API | AI videos, metadata, transcripts |
| RSS Feeds | feedparser | Blog posts from OpenAI, Anthropic, DeepMind, Meta, NVIDIA |
| arXiv | API | Papers in cs.AI, cs.CL, cs.LG |
| GitHub | API + Scrape | Trending AI repositories |

---

## Scheduled Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| Content Ingestion | Every 2 hours | Collects from all sources |
| Trend Detection | Every 4 hours | Clusters & scores trends |
| Daily Report | 08:00 UTC | Generates the daily briefing |

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (async), Celery
- **Database**: PostgreSQL 16 + pgvector
- **Cache/Broker**: Redis 7
- **AI**: OpenAI (text-embedding-3-small, GPT-4o)
- **ML**: HDBSCAN, scikit-learn, NumPy
- **Frontend**: Next.js 15, TailwindCSS v4, TypeScript
- **Deployment**: Docker Compose

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key for embeddings + LLM |
| `YOUTUBE_API_KEY` | ⬜ | YouTube Data API key |
| `TWITTER_BEARER_TOKEN` | ⬜ | Twitter/X API bearer token |
| `GITHUB_TOKEN` | ⬜ | GitHub token (higher rate limits) |
| `DATABASE_URL` | ✅ | PostgreSQL async connection string |
| `REDIS_URL` | ✅ | Redis connection string |

---

## Cloud Deployment

### Backend (Railway / AWS)

1. Push the `backend/` directory to a Git repo
2. Connect to Railway or AWS App Runner
3. Set environment variables
4. Use `docker/Dockerfile.backend` as the Dockerfile

### Frontend (Vercel)

1. Push the `frontend/` directory to a Git repo
2. Connect to Vercel
3. Set `NEXT_PUBLIC_API_URL` to your backend URL
4. Deploy

---

## License

MIT
