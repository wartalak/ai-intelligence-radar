"""
Database initialization – creates pgvector extension and all tables.
"""

import asyncio
from sqlalchemy import text
from app.database.connection import engine
from app.models.base import Base
# Import all models so Base.metadata knows about them
from app.models.models import Source, Content, Embedding, Topic, TopicContent, Trend, Report  # noqa: F401


async def init_db():
    """Create pgvector extension and all tables."""
    async with engine.begin() as conn:
        has_vector = False
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            has_vector = True
            print("✅ pgvector extension enabled.")
        except Exception as e:
            print(f"⚠️ pgvector not available: {e}")

        if has_vector:
            await conn.run_sync(Base.metadata.create_all)
        else:
            # Create all tables except the ones that need pgvector (embeddings)
            from app.models.models import Embedding
            tables_to_create = [
                t for t in Base.metadata.sorted_tables
                if t.name != Embedding.__tablename__
            ]
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables_to_create)
            )
    print("✅ Database initialized.")


async def seed_sources():
    """Insert default data sources if they don't exist."""
    from app.database.connection import async_session_factory

    default_sources = [
        # RSS feeds — names must EXACTLY match what RSSCollector uses as feed_name keys
        {"name": "OpenAI Blog", "source_type": "rss", "url": "https://openai.com/blog/rss.xml", "reliability": 0.95},
        {"name": "Anthropic Blog", "source_type": "rss", "url": "https://www.anthropic.com/feed", "reliability": 0.95},
        {"name": "Google DeepMind", "source_type": "rss", "url": "https://deepmind.google/blog/rss.xml", "reliability": 0.95},
        {"name": "Meta AI", "source_type": "rss", "url": "https://ai.meta.com/blog/rss/", "reliability": 0.9},
        {"name": "NVIDIA AI", "source_type": "rss", "url": "https://blogs.nvidia.com/feed/", "reliability": 0.9},
        {"name": "Hugging Face Blog", "source_type": "rss", "url": "https://huggingface.co/blog/feed.xml", "reliability": 0.9},
        {"name": "AI News (MIT)", "source_type": "rss", "url": "https://news.mit.edu/topic/artificial-intelligence2/feed", "reliability": 0.9},
        # Other sources
        {"name": "arXiv", "source_type": "arxiv", "url": "https://arxiv.org", "reliability": 0.99},
        {"name": "GitHub Trending", "source_type": "github", "url": "https://github.com/trending", "reliability": 0.7},
        {"name": "YouTube", "source_type": "youtube", "url": "https://youtube.com", "reliability": 0.7},
        {"name": "Twitter/X", "source_type": "twitter", "url": "https://twitter.com", "reliability": 0.6},
    ]

    async with async_session_factory() as session:
        for src in default_sources:
            existing = await session.execute(
                text("SELECT id FROM sources WHERE name = :name"),
                {"name": src["name"]},
            )
            if existing.first() is None:
                await session.execute(
                    text(
                        "INSERT INTO sources (name, source_type, url, reliability) "
                        "VALUES (:name, :source_type, :url, :reliability)"
                    ),
                    src,
                )
        await session.commit()
    print("✅ Default sources seeded.")


if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(seed_sources())
