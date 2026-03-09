"""
Twitter / X collector for corporate AI accounts.

Uses multiple free methods to collect tweets without paid API:
1. Twitter syndication timeline endpoint (embedded timeline HTML)
2. Nitter RSS feeds (public Twitter proxies)
3. Direct scraping fallback

Targets official AI company accounts for the latest announcements.
"""

import re
import httpx
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.config import get_settings

logger = logging.getLogger(__name__)

# ── Corporate AI accounts to track ──
AI_ACCOUNTS = [
    # Company → handle (without @)
    ("Anthropic", "AnthropicAI"),
    ("OpenAI", "OpenAI"),
    ("Google DeepMind", "GoogleDeepMind"),
    ("Meta AI", "MetaAI"),
    ("xAI (Grok)", "xaborai"),
    ("NVIDIA AI", "NVIDIAAI"),
    ("Hugging Face", "huggingface"),
    ("Mistral AI", "MistralAI"),
    ("Cohere", "CohereForAI"),
    ("Stability AI", "StabilityAI"),
    ("Microsoft AI", "MSFTResearch"),
    ("Apple ML", "AppleMLResearch"),
    ("LangChain", "LangChainAI"),
    ("LlamaIndex", "llaborai_index"),
    ("Weights & Biases", "weights_biases"),
]

# ── Nitter instances (public Twitter proxies) ──
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.woodland.cafe",
    "https://nitter.net",
]


class TwitterCollector(BaseCollector):
    source_name = "Twitter/X"
    source_type = "twitter"

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect tweets from corporate AI accounts using free methods."""
        settings = get_settings()
        items: List[Dict[str, Any]] = []

        # Method 1: Try Twitter API if token is available
        if settings.TWITTER_BEARER_TOKEN:
            api_items = await self._collect_via_api(settings.TWITTER_BEARER_TOKEN)
            items.extend(api_items)

        # Method 2: Scrape via Nitter RSS (free, no API key needed)
        nitter_items = await self._collect_via_nitter()
        items.extend(nitter_items)

        # Method 3: Twitter syndication endpoint (embedded timelines)
        if not nitter_items:
            syndication_items = await self._collect_via_syndication()
            items.extend(syndication_items)

        # Deduplicate by external_id
        seen = set()
        unique = []
        for item in items:
            if item["external_id"] not in seen:
                seen.add(item["external_id"])
                unique.append(item)

        logger.info(f"Collected {len(unique)} tweets from corporate AI accounts")
        return unique

    # ─────────────────────────────────────────────────
    # Method 1: Official Twitter API v2 (if token available)
    # ─────────────────────────────────────────────────
    async def _collect_via_api(self, bearer_token: str) -> List[Dict[str, Any]]:
        """Use Twitter API v2 to fetch recent tweets from AI accounts."""
        items: List[Dict[str, Any]] = []
        headers = {"Authorization": f"Bearer {bearer_token}"}
        handles = [h for _, h in AI_ACCOUNTS]

        async with httpx.AsyncClient(timeout=30) as client:
            # Build query: from:handle1 OR from:handle2 ...
            query_parts = [f"from:{h}" for h in handles[:10]]  # API limit
            query = " OR ".join(query_parts) + " -is:retweet"

            try:
                params = {
                    "query": query,
                    "max_results": 50,
                    "tweet.fields": "created_at,public_metrics,author_id",
                    "expansions": "author_id",
                    "user.fields": "username,name",
                }
                resp = await client.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    headers=headers,
                    params=params,
                )
                if resp.status_code != 200:
                    logger.warning(f"Twitter API error {resp.status_code}: {resp.text[:200]}")
                    return items

                data = resp.json()
                # Build author lookup
                users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

                for tweet in data.get("data", []):
                    metrics = tweet.get("public_metrics", {})
                    author = users.get(tweet.get("author_id"), {})
                    username = author.get("username", "")
                    display_name = author.get("name", username)

                    items.append(
                        self.normalize_item(
                            external_id=tweet["id"],
                            title=f"@{username}" if username else "",
                            body=tweet["text"],
                            url=f"https://x.com/{username}/status/{tweet['id']}",
                            author=display_name,
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
                            metadata={"account": username, "source_method": "api"},
                        )
                    )
            except Exception as e:
                logger.error(f"Twitter API collection error: {e}")

        return items

    # ─────────────────────────────────────────────────
    # Method 2: Nitter RSS (free, no API key)
    # ─────────────────────────────────────────────────
    async def _collect_via_nitter(self) -> List[Dict[str, Any]]:
        """Scrape tweets via Nitter RSS feeds — free public Twitter proxies."""
        items: List[Dict[str, Any]] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=3)

        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AIRadar/1.0)"},
        ) as client:
            working_instance = None

            for instance in NITTER_INSTANCES:
                try:
                    test = await client.get(f"{instance}/OpenAI/rss", timeout=8)
                    if test.status_code == 200 and "<rss" in test.text[:200].lower():
                        working_instance = instance
                        logger.info(f"Using Nitter instance: {instance}")
                        break
                except Exception:
                    continue

            if not working_instance:
                logger.warning("No working Nitter instance found")
                return items

            for company, handle in AI_ACCOUNTS:
                try:
                    resp = await client.get(f"{working_instance}/{handle}/rss")
                    if resp.status_code != 200:
                        continue

                    # Parse RSS
                    import feedparser
                    feed = feedparser.parse(resp.text)

                    for entry in feed.entries[:20]:
                        # Parse date
                        pub_date = datetime.now(timezone.utc)
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            from calendar import timegm
                            pub_date = datetime.fromtimestamp(
                                timegm(entry.published_parsed), tz=timezone.utc
                            )

                        # Only last 3 days
                        if pub_date < cutoff:
                            continue

                        # Extract tweet text from HTML
                        body = entry.get("summary", "") or entry.get("description", "")
                        clean = BeautifulSoup(body, "html.parser").get_text(separator=" ").strip()

                        # Skip retweets
                        if clean.startswith("RT @"):
                            continue

                        # Extract tweet ID from link
                        link = entry.get("link", "")
                        tweet_id = link.rstrip("/").split("/")[-1] if link else ""

                        items.append(
                            self.normalize_item(
                                external_id=f"tw-{handle}-{tweet_id}" if tweet_id else f"tw-{handle}-{hash(clean)}",
                                title=f"@{handle}",
                                body=clean,
                                url=f"https://x.com/{handle}/status/{tweet_id}" if tweet_id else link,
                                author=company,
                                published_at=pub_date,
                                content_type="tweet",
                                engagement={},
                                metadata={
                                    "account": handle,
                                    "company": company,
                                    "source_method": "nitter_rss",
                                },
                            )
                        )
                except Exception as e:
                    logger.error(f"Nitter collection error for @{handle}: {e}")

        logger.info(f"Collected {len(items)} tweets via Nitter RSS")
        return items

    # ─────────────────────────────────────────────────
    # Method 3: Twitter syndication (embedded timelines)
    # ─────────────────────────────────────────────────
    async def _collect_via_syndication(self) -> List[Dict[str, Any]]:
        """Scrape tweets via Twitter's syndication/embed endpoint."""
        items: List[Dict[str, Any]] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=3)

        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
        ) as client:
            for company, handle in AI_ACCOUNTS:
                try:
                    # Twitter syndication timeline
                    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{handle}"
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")

                    # Find tweet containers
                    for tweet_div in soup.select("[data-tweet-id], .timeline-Tweet"):
                        tweet_id = tweet_div.get("data-tweet-id", "")
                        text_el = tweet_div.select_one(
                            ".timeline-Tweet-text, .tweet-text, [data-testid='tweetText']"
                        )
                        if not text_el:
                            continue

                        tweet_text = text_el.get_text(separator=" ").strip()
                        if not tweet_text or tweet_text.startswith("RT @"):
                            continue

                        # Try to get timestamp
                        time_el = tweet_div.select_one("time")
                        pub_date = datetime.now(timezone.utc)
                        if time_el and time_el.get("datetime"):
                            try:
                                pub_date = datetime.fromisoformat(
                                    time_el["datetime"].replace("Z", "+00:00")
                                )
                            except Exception:
                                pass

                        if pub_date < cutoff:
                            continue

                        items.append(
                            self.normalize_item(
                                external_id=f"tw-synd-{handle}-{tweet_id or hash(tweet_text)}",
                                title=f"@{handle}",
                                body=tweet_text,
                                url=f"https://x.com/{handle}/status/{tweet_id}" if tweet_id else f"https://x.com/{handle}",
                                author=company,
                                published_at=pub_date,
                                content_type="tweet",
                                engagement={},
                                metadata={
                                    "account": handle,
                                    "company": company,
                                    "source_method": "syndication",
                                },
                            )
                        )
                except Exception as e:
                    logger.error(f"Syndication collection error for @{handle}: {e}")

        logger.info(f"Collected {len(items)} tweets via syndication")
        return items
