"""
Celery application configuration.
"""

from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ai_radar",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=600,   # 10 min soft limit
    task_time_limit=900,         # 15 min hard limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# ── Scheduled tasks ──
celery_app.conf.beat_schedule = {
    "ingest-content-every-2h": {
        "task": "app.workers.tasks.ingest_all_content",
        "schedule": crontab(minute=0, hour="*/2"),  # every 2 hours
    },
    "detect-trends-every-4h": {
        "task": "app.workers.tasks.detect_trends_task",
        "schedule": crontab(minute=30, hour="*/4"),  # every 4 hours
    },
    "generate-daily-report": {
        "task": "app.workers.tasks.generate_daily_report_task",
        "schedule": crontab(minute=0, hour=8),  # every day at 08:00 UTC
    },
}
