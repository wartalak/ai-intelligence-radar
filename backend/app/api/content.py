"""
Content feed API endpoint.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db

router = APIRouter()


@router.get("/content/latest")
async def get_latest_content(
    content_type: str = Query(None, description="Filter by type: tweet, video, article, paper, repo"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Return latest collected content items."""
    if content_type:
        result = await db.execute(
            text("""
                SELECT c.id, c.title, c.body, c.url, c.author, c.published_at,
                       c.content_type, c.engagement, c.metadata, s.name AS source_name
                FROM content c
                JOIN sources s ON s.id = c.source_id
                WHERE c.is_spam = false AND c.content_type = :ctype
                ORDER BY c.collected_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"ctype": content_type, "limit": limit, "offset": offset},
        )
    else:
        result = await db.execute(
            text("""
                SELECT c.id, c.title, c.body, c.url, c.author, c.published_at,
                       c.content_type, c.engagement, c.metadata, s.name AS source_name
                FROM content c
                JOIN sources s ON s.id = c.source_id
                WHERE c.is_spam = false
                ORDER BY c.collected_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset},
        )

    rows = result.fetchall()

    return {
        "items": [
            {
                "id": r[0],
                "title": r[1],
                "body": (r[2] or "")[:500],
                "url": r[3],
                "author": r[4],
                "published_at": str(r[5]) if r[5] else None,
                "content_type": r[6],
                "engagement": r[7] or {},
                "metadata": r[8] or {},
                "source": r[9],
            }
            for r in rows
        ],
        "count": len(rows),
    }
