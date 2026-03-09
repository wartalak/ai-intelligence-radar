"""
Trends API endpoint.
Falls back to keyword-frequency based trends if the topics/trends tables are empty.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db

router = APIRouter()


@router.get("/trends")
async def get_trends(limit: int = Query(20, le=50), db: AsyncSession = Depends(get_db)):
    """Return current trending AI topics.
    If no HDBSCAN-detected trends exist, falls back to keyword frequency analysis.
    """
    # First try the topics table
    result = await db.execute(
        text("""
            SELECT t.id, t.name, t.description, t.keywords, t.content_count,
                   t.trend_score, t.first_seen, t.last_seen,
                   tr.content_velocity, tr.engagement_weight, tr.source_authority
            FROM topics t
            LEFT JOIN LATERAL (
                SELECT content_velocity, engagement_weight, source_authority
                FROM trends
                WHERE topic_id = t.id
                ORDER BY snapshot_at DESC
                LIMIT 1
            ) tr ON true
            ORDER BY t.trend_score DESC
            LIMIT :limit
        """),
        {"limit": limit},
    )
    rows = result.fetchall()

    if rows:
        return {
            "trends": [
                {
                    "id": r[0],
                    "name": r[1],
                    "description": r[2],
                    "keywords": r[3] or [],
                    "content_count": r[4],
                    "trend_score": round(r[5], 2),
                    "first_seen": str(r[6]) if r[6] else None,
                    "last_seen": str(r[7]) if r[7] else None,
                    "velocity": round(r[8], 2) if r[8] else 0,
                    "engagement": round(r[9], 2) if r[9] else 0,
                    "authority": round(r[10], 2) if r[10] else 0,
                }
                for r in rows
            ]
        }

    # Fallback: compute trending keywords from content titles
    return await _keyword_trends(db, limit)


async def _keyword_trends(db: AsyncSession, limit: int) -> dict:
    """Extract trending topics by keyword frequency from recent content titles."""
    result = await db.execute(
        text("""
            SELECT c.title, c.content_type, c.engagement
            FROM content c
            WHERE c.is_spam = false AND c.title IS NOT NULL AND c.title != ''
            ORDER BY c.collected_at DESC
            LIMIT 500
        """)
    )
    rows = result.fetchall()

    if not rows:
        return {"trends": []}

    import re
    from collections import Counter

    stop_words = {
        "the", "a", "an", "is", "it", "of", "in", "to", "for", "on",
        "with", "and", "or", "by", "at", "from", "as", "be", "was",
        "are", "this", "that", "we", "our", "how", "what", "new",
        "has", "have", "not", "can", "will", "its", "all", "but",
        "use", "using", "get", "just", "now", "you", "your", "more",
        "like", "than", "been", "about", "also", "into", "most", "other",
        "over", "such", "only", "some", "very", "does", "did", "do",
    }

    # Extract keywords from bigrams and individual words
    word_counter = Counter()
    bigram_counter = Counter()

    for row in rows:
        title = row[0] or ""
        tokens = re.findall(r"\b[a-zA-Z]{2,}\b", title.lower())
        filtered = [t for t in tokens if t not in stop_words]
        word_counter.update(filtered)

        # Bigrams for multi-word concepts
        for i in range(len(filtered) - 1):
            bigram = f"{filtered[i]} {filtered[i+1]}"
            bigram_counter.update([bigram])

    # Combine top bigrams and words
    trends = []
    trend_id = 1

    # Add top bigrams first (more specific)
    for phrase, count in bigram_counter.most_common(min(limit, 10)):
        if count >= 2:
            trends.append({
                "id": trend_id,
                "name": phrase.title(),
                "description": f"'{phrase}' kelimesi {count} farklı içerikte geçiyor",
                "keywords": phrase.split(),
                "content_count": count,
                "trend_score": round(count * 1.5, 2),
                "first_seen": None,
                "last_seen": None,
                "velocity": round(count / max(len(rows), 1) * 10, 2),
                "engagement": 0,
                "authority": 0,
            })
            trend_id += 1

    # Add top single words
    for word, count in word_counter.most_common(limit * 2):
        if count >= 3 and len(trends) < limit:
            # Skip if already covered by a bigram
            if any(word in t["name"].lower() for t in trends):
                continue
            trends.append({
                "id": trend_id,
                "name": word.title(),
                "description": f"'{word}' kelimesi {count} farklı içerikte geçiyor",
                "keywords": [word],
                "content_count": count,
                "trend_score": round(count * 1.0, 2),
                "first_seen": None,
                "last_seen": None,
                "velocity": round(count / max(len(rows), 1) * 10, 2),
                "engagement": 0,
                "authority": 0,
            })
            trend_id += 1

    trends.sort(key=lambda t: t["trend_score"], reverse=True)
    return {"trends": trends[:limit]}
