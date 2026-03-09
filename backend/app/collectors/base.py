"""
Abstract base collector.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Base class for all data collectors."""

    source_name: str = ""
    source_type: str = ""

    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect data from the source.
        Returns a list of normalized content dicts with keys:
            external_id, title, body, url, author, published_at,
            content_type, engagement, metadata
        """
        pass

    def normalize_item(
        self,
        external_id: str,
        title: str,
        body: str,
        url: str = "",
        author: str = "",
        published_at: datetime | None = None,
        content_type: str = "",
        engagement: dict | None = None,
        metadata: dict | None = None,
    ) -> Dict[str, Any]:
        """Return a consistently-structured content dict."""
        return {
            "external_id": str(external_id),
            "title": (title or "")[:500],
            "body": body or "",
            "url": url or "",
            "author": (author or "")[:255],
            "published_at": published_at or datetime.utcnow(),
            "content_type": content_type or self.source_type,
            "engagement": engagement or {},
            "metadata": metadata or {},
        }
