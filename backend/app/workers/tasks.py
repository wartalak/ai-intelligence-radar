"""
Celery task definitions for background processing.
"""

import asyncio
import logging
from datetime import date
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper to run an async function in a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.tasks.ingest_all_content")
def ingest_all_content():
    """Collect content from all sources and run through the pipeline."""
    _run_async(_ingest_all())


async def _ingest_all():
    from app.database.connection import create_fresh_session
    from app.services.pipeline import DataPipeline
    from app.collectors.twitter_collector import TwitterCollector
    from app.collectors.youtube_collector import YouTubeCollector
    from app.collectors.rss_collector import RSSCollector
    from app.collectors.arxiv_collector import ArxivCollector
    from app.collectors.github_collector import GitHubCollector

    collectors = [
        (TwitterCollector(), "Twitter/X"),
        (YouTubeCollector(), "YouTube"),
        (RSSCollector(), "RSS Feeds"),
        (ArxivCollector(), "arXiv"),
        (GitHubCollector(), "GitHub Trending"),
    ]

    total = 0
    async with create_fresh_session() as session:
        pipeline = DataPipeline(session)
        for collector, source_name in collectors:
            try:
                logger.info(f"Collecting from {source_name}...")

                items = await collector.collect()
                if not items:
                    continue

                # For RSS, group by feed name
                if source_name == "RSS Feeds":
                    from collections import defaultdict
                    feed_groups = defaultdict(list)
                    for item in items:
                        feed = item.get("metadata", {}).get("feed", "OpenAI Blog")
                        feed_groups[feed].append(item)
                    for feed_name, feed_items in feed_groups.items():
                        try:
                            count = await pipeline.process_items(feed_items, feed_name)
                            total += count
                        except Exception as e:
                            logger.error(f"Pipeline error for feed {feed_name}: {e}")
                else:
                    count = await pipeline.process_items(items, source_name)
                    total += count
            except Exception as e:
                logger.error(f"Collection error for {source_name}: {e}")

    logger.info(f"✅ Ingestion complete. Processed {total} items total.")
    return total


@celery_app.task(name="app.workers.tasks.detect_trends_task")
def detect_trends_task():
    """Run trend detection on collected content."""
    return _run_async(_detect_trends())


async def _detect_trends():
    from app.database.connection import create_fresh_session
    from app.services.trends import TrendDetector

    async with create_fresh_session() as session:
        detector = TrendDetector(session)
        trends = await detector.detect_trends()
        logger.info(f"✅ Trend detection complete. Found {len(trends)} trends.")
        return len(trends)


@celery_app.task(name="app.workers.tasks.generate_daily_report_task")
def generate_daily_report_task():
    """Generate today's intelligence report."""
    return _run_async(_generate_report())


async def _generate_report():
    from app.database.connection import create_fresh_session
    from app.analysis.report_generator import ReportGenerator

    async with create_fresh_session() as session:
        generator = ReportGenerator(session)
        report = await generator.generate_daily_report(date.today())
        logger.info(f"✅ Daily report generated: {report.get('title', 'N/A')}")
        return report.get("title", "Done")


@celery_app.task(name="app.workers.tasks.ingest_single_source")
def ingest_single_source(source_type: str):
    """Ingest content from a single source type."""
    return _run_async(_ingest_single(source_type))


async def _ingest_single(source_type: str):
    from app.database.connection import create_fresh_session
    from app.services.pipeline import DataPipeline

    collector_map = {
        "twitter": ("app.collectors.twitter_collector", "TwitterCollector", "Twitter/X"),
        "youtube": ("app.collectors.youtube_collector", "YouTubeCollector", "YouTube"),
        "rss": ("app.collectors.rss_collector", "RSSCollector", "OpenAI Blog"),
        "arxiv": ("app.collectors.arxiv_collector", "ArxivCollector", "arXiv"),
        "github": ("app.collectors.github_collector", "GitHubCollector", "GitHub Trending"),
    }

    if source_type not in collector_map:
        logger.error(f"Unknown source type: {source_type}")
        return 0

    module_path, class_name, source_name = collector_map[source_type]
    import importlib
    module = importlib.import_module(module_path)
    collector_class = getattr(module, class_name)
    collector = collector_class()

    async with create_fresh_session() as session:
        pipeline = DataPipeline(session)
        items = await collector.collect()
        count = await pipeline.process_items(items, source_name)
        logger.info(f"✅ Ingested {count} items from {source_name}")
        return count
