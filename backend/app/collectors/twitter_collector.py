"""
Twitter / X collector using the v2 API.
"""

import httpx
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from app.collectors.base import BaseCollector
from app.config import get_settings

logger = logging.getLogger(__name__)

AI_KEYWORDS = [
    "artificial intelligence",
    "LLM",
    "GPT",
    "Claude",
    "AI agents",
    "transformers",
    "open source model",
    "machine learning",
    "neural network",
    "generative AI",
]


class TwitterCollector(BaseCollector):
    source_name = "Twitter/X"
    source_type = "twitter"

    SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

    async def collect(self) -> List[Dict[str, Any]]:
        settings = get_settings()
        if not settings.TWITTER_BEARER_TOKEN:
            logger.warning("Twitter bearer token not set – skipping Twitter collection.")
            return []

        headers = {"Authorization": f"Bearer {settings.TWITTER_BEARER_TOKEN}"}
        items: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for keyword in AI_KEYWORDS[:5]:  # limit to avoid rate limits
                try:
                    params = {
                        "query": f"{keyword} -is:retweet lang:en",
                        "max_results": 20,
                        "tweet.fields": "created_at,public_metrics,author_id",
                    }
                    resp = await client.get(self.SEARCH_URL, headers=headers, params=params)
                    if resp.status_code != 200:
                        logger.warning(f"Twitter API error {resp.status_code}: {resp.text[:200]}")
                        continue

                    data = resp.json()
                    for tweet in data.get("data", []):
                        metrics = tweet.get("public_metrics", {})
                        items.append(
                            self.normalize_item(
                                external_id=tweet["id"],
                                title="",
                                body=tweet["text"],
                                url=f"https://twitter.com/i/status/{tweet['id']}",
                                author=tweet.get("author_id", ""),
                                published_at=datetime.fromisoformat(
                                    tweet["created_at"].replace("Z", "+00:00")
                                ),
                                content_type="tweet",
                                engagement={
                                    "likes": metrics.get("like_count", 0),
                                    "retweets": metrics.get("retweet_count", 0),
                                    "replies": metrics.get("reply_count", 0),
                                    "impressions": metrics.get("impression_count", 0),
                                },
                                metadata={"keyword": keyword},
                            )
                        )
                except Exception as e:
                    logger.error(f"Twitter collection error for '{keyword}': {e}")

        logger.info(f"Collected {len(items)} tweets")
        return items
