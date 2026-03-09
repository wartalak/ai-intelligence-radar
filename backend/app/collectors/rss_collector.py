"""
RSS/Atom feed collector for AI company blogs.
"""

import feedparser
import httpx
import logging
from typing import List, Dict, Any
from datetime import datetime
from email.utils import parsedate_to_datetime
from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "OpenAI Blog": "https://openai.com/blog/rss.xml",
    "Anthropic Blog": "https://www.anthropic.com/feed",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Meta AI": "https://ai.meta.com/blog/rss/",
    "NVIDIA AI": "https://blogs.nvidia.com/feed/",
    "Hugging Face Blog": "https://huggingface.co/blog/feed.xml",
    "AI News (MIT)": "https://news.mit.edu/topic/artificial-intelligence2/feed",
}


class RSSCollector(BaseCollector):
    source_name = "RSS Feeds"
    source_type = "rss"

    async def collect(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            for feed_name, feed_url in RSS_FEEDS.items():
                try:
                    resp = await client.get(feed_url)
                    if resp.status_code != 200:
                        logger.warning(f"RSS fetch failed for {feed_name}: {resp.status_code}")
                        continue

                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries[:15]:
                        pub_date = self._parse_date(entry)
                        body = entry.get("summary", "") or entry.get("description", "")
                        # Strip HTML tags for clean text
                        import re
                        clean_body = re.sub(r"<[^>]+>", " ", body).strip()

                        items.append(
                            self.normalize_item(
                                external_id=entry.get("id", entry.get("link", "")),
                                title=entry.get("title", ""),
                                body=clean_body,
                                url=entry.get("link", ""),
                                author=entry.get("author", feed_name),
                                published_at=pub_date,
                                content_type="article",
                                engagement={},
                                metadata={"feed": feed_name, "feed_url": feed_url},
                            )
                        )
                except Exception as e:
                    logger.error(f"RSS collection error for '{feed_name}': {e}")

        logger.info(f"Collected {len(items)} RSS articles")
        return items

    @staticmethod
    def _parse_date(entry) -> datetime:
        """Try to parse the publication date from various feed formats."""
        for field in ("published", "updated", "created"):
            raw = entry.get(field)
            if raw:
                try:
                    return parsedate_to_datetime(raw)
                except Exception:
                    try:
                        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    except Exception:
                        pass
        return datetime.utcnow()
