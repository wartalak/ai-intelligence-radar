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
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized with pgvector extension and all tables.")


async def seed_sources():
    """Insert default data sources if they don't exist."""
    from app.database.connection import async_session_factory

    default_sources = [
        {"name": "Twitter/X", "source_type": "twitter", "url": "https://twitter.com", "reliability": 0.6},
        {"name": "YouTube", "source_type": "youtube", "url": "https://youtube.com", "reliability": 0.7},
        {"name": "OpenAI Blog", "source_type": "rss", "url": "https://openai.com/blog/rss.xml", "reliability": 0.95},
        {"name": "Anthropic Blog", "source_type": "rss", "url": "https://www.anthropic.com/feed", "reliability": 0.95},
        {"name": "Google DeepMind Blog", "source_type": "rss", "url": "https://deepmind.google/blog/rss.xml", "reliability": 0.95},
        {"name": "Meta AI Blog", "source_type": "rss", "url": "https://ai.meta.com/blog/rss/", "reliability": 0.9},
        {"name": "NVIDIA AI Blog", "source_type": "rss", "url": "https://blogs.nvidia.com/feed/", "reliability": 0.9},
        {"name": "arXiv", "source_type": "arxiv", "url": "https://arxiv.org", "reliability": 0.99},
        {"name": "GitHub Trending", "source_type": "github", "url": "https://github.com/trending", "reliability": 0.7},
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
