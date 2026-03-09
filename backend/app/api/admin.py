"""
Admin trigger endpoints — replaces Celery on free deploy platforms.
Allows triggering data ingestion and report generation via API calls.
"""

import logging
import traceback
from datetime import date
from fastapi import APIRouter

from app.database.connection import async_session_factory

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/trigger/ingest")
async def trigger_ingest():
    """Trigger data collection from all sources (runs synchronously for error visibility)."""
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
    results = {}
    errors = {}

    async with async_session_factory() as session:
        pipeline = DataPipeline(session)
        for collector, source_name in collectors:
            try:
                logger.info(f"Collecting from {source_name}...")
                items = await collector.collect()
                if not items:
                    results[source_name] = {"collected": 0, "processed": 0}
                    continue

                if source_name == "RSS Feeds":
                    feed_groups = defaultdict(list)
                    for item in items:
                        feed = item.get("metadata", {}).get("feed", "OpenAI Blog")
                        feed_groups[feed].append(item)
                    source_total = 0
                    for feed_name, feed_items in feed_groups.items():
                        count = await pipeline.process_items(feed_items, feed_name)
                        source_total += count
                    results[source_name] = {"collected": len(items), "processed": source_total}
                    total += source_total
                else:
                    count = await pipeline.process_items(items, source_name)
                    results[source_name] = {"collected": len(items), "processed": count}
                    total += count
            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}"
                logger.error(f"Collection error for {source_name}: {err_msg}")
                logger.error(traceback.format_exc())
                errors[source_name] = err_msg

    logger.info(f"✅ Ingestion complete: {total} items")
    return {
        "status": "done",
        "total_processed": total,
        "results": results,
        "errors": errors,
    }


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


@router.post("/trigger/seed")
async def trigger_seed():
    """Re-seed the database sources (idempotent)."""
    from app.database.init_db import seed_sources
    await seed_sources()
    return {"status": "done", "message": "Sources seeded"}
