"""
Trend detection engine.

trend_score = content_velocity × engagement_weight × source_authority

Uses HDBSCAN for embedding clustering to discover topic groups.
"""

import logging
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TrendDetector:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def detect_trends(self) -> List[Dict[str, Any]]:
        """Run full trend detection pipeline."""
        # 1) Cluster recent embeddings
        clusters = await self._cluster_embeddings()

        # 2) For each cluster, compute trend score
        trends = []
        for cluster_id, content_ids in clusters.items():
            if cluster_id == -1:
                continue  # noise cluster

            velocity = await self._content_velocity(content_ids)
            engagement = await self._engagement_weight(content_ids)
            authority = await self._source_authority(content_ids)

            score = velocity * engagement * authority

            # Get representative titles for the cluster
            keywords = await self._extract_keywords(content_ids)
            cluster_name = keywords[0] if keywords else f"Cluster {cluster_id}"

            # Upsert topic
            topic_id = await self._upsert_topic(cluster_name, keywords, len(content_ids), score, cluster_id)

            # Store trend snapshot
            await self.session.execute(
                text("""
                    INSERT INTO trends (topic_id, trend_score, content_velocity, engagement_weight, source_authority)
                    VALUES (:topic_id, :score, :velocity, :engagement, :authority)
                """),
                {
                    "topic_id": topic_id,
                    "score": round(score, 4),
                    "velocity": round(velocity, 4),
                    "engagement": round(engagement, 4),
                    "authority": round(authority, 4),
                },
            )

            trends.append({
                "topic_id": topic_id,
                "name": cluster_name,
                "score": round(score, 4),
                "content_count": len(content_ids),
                "keywords": keywords,
            })

        await self.session.commit()
        trends.sort(key=lambda x: x["score"], reverse=True)
        logger.info(f"Detected {len(trends)} trend clusters")
        return trends

    async def _cluster_embeddings(self) -> Dict[int, List[int]]:
        """Cluster recent content embeddings with HDBSCAN."""
        cutoff = datetime.utcnow() - timedelta(days=3)
        result = await self.session.execute(
            text("""
                SELECT e.content_id, e.embedding::text
                FROM embeddings e
                JOIN content c ON c.id = e.content_id
                WHERE c.collected_at > :cutoff AND c.is_spam = false
                ORDER BY c.collected_at DESC
                LIMIT 2000
            """),
            {"cutoff": cutoff},
        )
        rows = result.fetchall()
        if len(rows) < 10:
            logger.info("Not enough embeddings for clustering")
            return {}

        content_ids = [r[0] for r in rows]
        vectors = []
        for r in rows:
            vec_str = r[1].strip("[]")
            vectors.append([float(v) for v in vec_str.split(",")])

        X = np.array(vectors)

        try:
            import hdbscan
            clusterer = hdbscan.HDBSCAN(min_cluster_size=5, min_samples=3, metric="euclidean")
            labels = clusterer.fit_predict(X)
        except Exception as e:
            logger.error(f"HDBSCAN clustering failed: {e}")
            return {}

        clusters: Dict[int, List[int]] = {}
        for idx, label in enumerate(labels):
            label = int(label)
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(content_ids[idx])

        return clusters

    async def _content_velocity(self, content_ids: List[int]) -> float:
        """Ratio of recent items to total, capped at 10."""
        if not content_ids:
            return 0.0
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        result = await self.session.execute(
            text("""
                SELECT COUNT(*) FROM content
                WHERE id = ANY(:ids) AND collected_at > :cutoff
            """),
            {"ids": content_ids, "cutoff": recent_cutoff},
        )
        recent = result.scalar() or 0
        return min(recent / max(len(content_ids), 1) * 10, 10.0)

    async def _engagement_weight(self, content_ids: List[int]) -> float:
        """Average engagement score across content items."""
        result = await self.session.execute(
            text("""
                SELECT engagement FROM content WHERE id = ANY(:ids)
            """),
            {"ids": content_ids},
        )
        rows = result.fetchall()
        total = 0.0
        for row in rows:
            eng = row[0] or {}
            total += (
                eng.get("likes", 0) * 1
                + eng.get("retweets", 0) * 2
                + eng.get("views", 0) * 0.01
                + eng.get("stars", 0) * 3
                + eng.get("comments", 0) * 1.5
            )
        avg = total / max(len(rows), 1)
        # Normalize to 0-10 range
        return min(avg / 100, 10.0) + 1.0

    async def _source_authority(self, content_ids: List[int]) -> float:
        """Average reliability of the sources contributing to this cluster."""
        result = await self.session.execute(
            text("""
                SELECT AVG(s.reliability)
                FROM content c
                JOIN sources s ON s.id = c.source_id
                WHERE c.id = ANY(:ids)
            """),
            {"ids": content_ids},
        )
        avg = result.scalar()
        return float(avg) if avg else 0.5

    async def _extract_keywords(self, content_ids: List[int]) -> List[str]:
        """Extract top keywords from the cluster content titles."""
        result = await self.session.execute(
            text("""
                SELECT title FROM content WHERE id = ANY(:ids) AND title IS NOT NULL
                LIMIT 20
            """),
            {"ids": content_ids},
        )
        titles = [r[0] for r in result.fetchall() if r[0]]
        if not titles:
            return []

        # Simple word frequency
        from collections import Counter
        import re
        stop_words = {
            "the", "a", "an", "is", "it", "of", "in", "to", "for", "on",
            "with", "and", "or", "by", "at", "from", "as", "be", "was",
            "are", "this", "that", "we", "our", "how", "what", "new",
            "has", "have", "not", "can", "will", "its", "all", "but",
        }
        words = []
        for title in titles:
            tokens = re.findall(r"\b[a-zA-Z]{3,}\b", title.lower())
            words.extend(t for t in tokens if t not in stop_words)

        common = Counter(words).most_common(5)
        return [w for w, _ in common]

    async def _upsert_topic(
        self, name: str, keywords: List[str], content_count: int, score: float, cluster_id: int
    ) -> int:
        """Insert or update a topic."""
        import json
        result = await self.session.execute(
            text("""
                INSERT INTO topics (name, keywords, content_count, trend_score, cluster_id, last_seen)
                VALUES (:name, CAST(:keywords AS jsonb), :count, :score, :cluster_id, NOW())
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """),
            {
                "name": name,
                "keywords": json.dumps(keywords),
                "count": content_count,
                "score": score,
                "cluster_id": cluster_id,
            },
        )
        row = result.first()
        if row:
            return row[0]
        # fallback: query existing
        result = await self.session.execute(
            text("SELECT id FROM topics WHERE cluster_id = :cid ORDER BY id DESC LIMIT 1"),
            {"cid": cluster_id},
        )
        row = result.first()
        return row[0] if row else 1
