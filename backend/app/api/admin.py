"""
Admin trigger endpoints — replaces Celery on free deploy platforms.
Allows triggering data ingestion and report generation via API calls.
"""

import logging
from datetime import date
from fastapi import APIRouter, BackgroundTasks

from app.database.connection import async_session_factory

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_ingestion():
    """Run data ingestion from all sources with its own DB session."""
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
    async with async_session_factory() as session:
        pipeline = DataPipeline(session)
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
async def trigger_ingest(background_tasks: BackgroundTasks):
    """Trigger data collection from all sources (runs in background)."""
    background_tasks.add_task(_run_ingestion)
    return {"status": "started", "message": "Veri toplama başlatıldı"}


@router.post("/trigger/report")
async def trigger_report():
    """Generate today's AI intelligence report."""
    from app.analysis.report_generator import ReportGenerator
    async with async_session_factory() as session:
        generator = ReportGenerator(session)
        report = await generator.generate_daily_report(date.today())
        return {"status": "done", "title": report.get("title", "N/A")}


@router.post("/trigger/trends")
async def trigger_trends():
    """Run trend detection on current content."""
    from app.services.trends import TrendDetector
    async with async_session_factory() as session:
        detector = TrendDetector(session)
        trends = await detector.detect_trends()
        return {"status": "done", "trend_count": len(trends)}
