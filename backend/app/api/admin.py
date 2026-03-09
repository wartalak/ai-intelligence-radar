"""
Admin trigger endpoints — replaces Celery on free deploy platforms.
Allows triggering data ingestion and report generation via API calls.
"""

import asyncio
import logging
from datetime import date
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_ingestion(db: AsyncSession):
    """Run data ingestion from all sources."""
    from app.services.pipeline import DataPipeline
    from app.collectors.rss_collector import RSSCollector
    from app.collectors.arxiv_collector import ArxivCollector
    from app.collectors.github_collector import GitHubCollector
    from app.collectors.youtube_collector import YouTubeCollector
    from app.collectors.twitter_collector import TwitterCollector
    from collections import defaultdict

    collectors = [
        (RSSCollector(), "RSS Feeds"),
        (ArxivCollector(), "arXiv"),
        (GitHubCollector(), "GitHub Trending"),
        (YouTubeCollector(), "YouTube"),
        (TwitterCollector(), "Twitter/X"),
    ]

    total = 0
    pipeline = DataPipeline(db)
    for collector, source_name in collectors:
        try:
            logger.info(f"Collecting from {source_name}...")
            items = await collector.collect()
            if not items:
                continue
            if source_name == "RSS Feeds":
                feed_groups = defaultdict(list)
                for item in items:
                    feed = item.get("metadata", {}).get("feed", "OpenAI Blog")
                    feed_groups[feed].append(item)
                for feed_name, feed_items in feed_groups.items():
                    count = await pipeline.process_items(feed_items, feed_name)
                    total += count
            else:
                count = await pipeline.process_items(items, source_name)
                total += count
        except Exception as e:
            logger.error(f"Collection error for {source_name}: {e}")
    logger.info(f"✅ Ingestion complete: {total} items")
    return total


@router.post("/trigger/ingest")
async def trigger_ingest(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Trigger data collection from all sources (runs in background)."""
    background_tasks.add_task(_run_ingestion, db)
    return {"status": "started", "message": "Veri toplama başlatıldı"}


@router.post("/trigger/report")
async def trigger_report(db: AsyncSession = Depends(get_db)):
    """Generate today's AI intelligence report."""
    from app.analysis.report_generator import ReportGenerator
    generator = ReportGenerator(db)
    report = await generator.generate_daily_report(date.today())
    return {"status": "done", "title": report.get("title", "N/A")}


@router.post("/trigger/trends")
async def trigger_trends(db: AsyncSession = Depends(get_db)):
    """Run trend detection on current content."""
    from app.services.trends import TrendDetector
    detector = TrendDetector(db)
    trends = await detector.detect_trends()
    return {"status": "done", "trend_count": len(trends)}
