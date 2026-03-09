"""
Data processing pipeline:
normalize → spam filter → detect language → generate embeddings → store → cluster
"""

import re
import logging
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class DataPipeline:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedding_service = EmbeddingService()

    async def process_items(
        self, items: List[Dict[str, Any]], source_name: str
    ) -> int:
        """Process a list of collected items through the full pipeline."""
        if not items:
            return 0

        # Resolve source_id
        result = await self.session.execute(
            text("SELECT id FROM sources WHERE name = :name"),
            {"name": source_name},
        )
        row = result.first()
        if not row:
            logger.error(f"Source '{source_name}' not found in DB")
            return 0
        source_id = row[0]

        processed = 0
        for item in items:
            try:
                # Step 1: Normalize text
                item = self._normalize(item)

                # Step 2: Spam check
                if self._is_spam(item["body"]):
                    continue

                # Step 3: Language detection
                lang = self._detect_language(item["body"])
                if lang not in ("en", "unknown"):
                    continue  # keep only English for now

                # Step 4: Insert content (skip duplicates)
                content_id = await self._store_content(item, source_id, lang)
                if content_id is None:
                    continue  # already exists

                # Step 5: Generate and store embedding
                embed_text = f"{item['title']} {item['body']}"
                embedding = await self.embedding_service.generate(embed_text)
                await self._store_embedding(content_id, embedding)

                processed += 1
            except Exception as e:
                logger.error(f"Pipeline error for item {item.get('external_id')}: {e}")

        await self.session.commit()
        logger.info(f"Processed {processed}/{len(items)} items from {source_name}")
        return processed

    # ── Step 1: Normalize ──
    def _normalize(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize text fields."""
        item["title"] = self._clean_text(item.get("title", ""))
        item["body"] = self._clean_text(item.get("body", ""))
        return item

    @staticmethod
    def _clean_text(text_val: str) -> str:
        if not text_val:
            return ""
        # Remove excessive whitespace
        text_val = re.sub(r"\s+", " ", text_val).strip()
        # Remove URLs from body text (we keep them in the url field)
        text_val = re.sub(r"https?://\S+", "", text_val)
        # Remove special chars (keep alphanumeric + basic punctuation)
        text_val = re.sub(r"[^\w\s.,!?;:'\"-/()\[\]{}@#$%^&*+=<>]", "", text_val)
        return text_val.strip()

    # ── Step 2: Spam filter ──
    @staticmethod
    def _is_spam(body: str) -> bool:
        if not body or len(body) < 20:
            return True
        spam_patterns = [
            r"(?i)buy now", r"(?i)click here to win",
            r"(?i)free money", r"(?i)100% guaranteed",
            r"(?i)act now", r"(?i)limited time offer",
        ]
        for pat in spam_patterns:
            if re.search(pat, body):
                return True
        return False

    # ── Step 3: Language detection ──
    @staticmethod
    def _detect_language(body: str) -> str:
        try:
            from langdetect import detect
            return detect(body)
        except Exception:
            return "unknown"

    # ── Step 4: Store content ──
    async def _store_content(
        self, item: Dict[str, Any], source_id: int, language: str
    ) -> int | None:
        """Insert content row. Returns content_id or None if duplicate."""
        try:
            import json
            result = await self.session.execute(
                text("""
                    INSERT INTO content
                        (source_id, external_id, title, body, url, author,
                         published_at, content_type, language, engagement, metadata)
                    VALUES
                        (:source_id, :external_id, :title, :body, :url, :author,
                         :published_at, :content_type, :language,
                         CAST(:engagement AS jsonb), CAST(:metadata AS jsonb))
                    ON CONFLICT (source_id, external_id) DO NOTHING
                    RETURNING id
                """),
                {
                    "source_id": source_id,
                    "external_id": item["external_id"],
                    "title": item["title"],
                    "body": item["body"],
                    "url": item["url"],
                    "author": item["author"],
                    "published_at": item["published_at"],
                    "content_type": item["content_type"],
                    "language": language,
                    "engagement": json.dumps(item.get("engagement", {})),
                    "metadata": json.dumps(item.get("metadata", {})),
                },
            )
            row = result.first()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Store content error: {e}")
            return None

    # ── Step 5: Store embedding ──
    async def _store_embedding(self, content_id: int, embedding: List[float]):
        """Insert embedding vector for a content item."""
        try:
            vec_str = "[" + ",".join(str(v) for v in embedding) + "]"
            await self.session.execute(
                text("""
                    INSERT INTO embeddings (content_id, embedding)
                    VALUES (:content_id, CAST(:embedding AS vector))
                    ON CONFLICT (content_id) DO NOTHING
                """),
                {"content_id": content_id, "embedding": vec_str},
            )
        except Exception as e:
            logger.error(f"Store embedding error: {e}")

