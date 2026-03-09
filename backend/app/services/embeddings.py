"""
OpenAI embedding generation service.
"""

import logging
from typing import List
from openai import AsyncOpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS

    async def generate(self, text: str) -> List[float]:
        """Generate embedding vector for a single text."""
        if not text.strip():
            return [0.0] * self.dimensions

        # Truncate to ~8000 tokens worth of text
        text = text[:30000]

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return [0.0] * self.dimensions

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts (max 2048 per call)."""
        if not texts:
            return []

        # Clean and truncate
        cleaned = [(t[:30000] if t.strip() else "empty") for t in texts]

        results = []
        batch_size = 100  # stay within limits
        for i in range(0, len(cleaned), batch_size):
            batch = cleaned[i : i + batch_size]
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                results.extend([d.embedding for d in response.data])
            except Exception as e:
                logger.error(f"Batch embedding error: {e}")
                results.extend([[0.0] * self.dimensions] * len(batch))

        return results
