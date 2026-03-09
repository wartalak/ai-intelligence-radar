"""
GitHub trending AI repositories collector.
"""

import httpx
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.config import get_settings

logger = logging.getLogger(__name__)

AI_TOPICS = [
    "artificial-intelligence",
    "machine-learning",
    "deep-learning",
    "large-language-models",
    "generative-ai",
]


class GitHubCollector(BaseCollector):
    source_name = "GitHub Trending"
    source_type = "github"

    TRENDING_URL = "https://github.com/trending"
    SEARCH_API = "https://api.github.com/search/repositories"

    async def collect(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        settings = get_settings()
        headers = {"Accept": "application/vnd.github+json"}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            # Method 1: GitHub Search API for AI repos created/pushed recently
            since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
            for topic in AI_TOPICS:
                try:
                    params = {
                        "q": f"topic:{topic} pushed:>{since}",
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 10,
                    }
                    resp = await client.get(self.SEARCH_API, params=params)
                    if resp.status_code != 200:
                        logger.warning(f"GitHub API error: {resp.status_code}")
                        continue

                    data = resp.json()
                    for repo in data.get("items", []):
                        items.append(
                            self.normalize_item(
                                external_id=str(repo["id"]),
                                title=repo["full_name"],
                                body=(repo.get("description") or "") + "\n\n" + (repo.get("topics", []) and ", ".join(repo["topics"]) or ""),
                                url=repo["html_url"],
                                author=repo["owner"]["login"],
                                published_at=datetime.fromisoformat(
                                    repo["created_at"].replace("Z", "+00:00")
                                ),
                                content_type="repo",
                                engagement={
                                    "stars": repo.get("stargazers_count", 0),
                                    "forks": repo.get("forks_count", 0),
                                    "watchers": repo.get("watchers_count", 0),
                                    "open_issues": repo.get("open_issues_count", 0),
                                },
                                metadata={
                                    "language": repo.get("language", ""),
                                    "topics": repo.get("topics", []),
                                    "license": (repo.get("license") or {}).get("spdx_id", ""),
                                },
                            )
                        )
                except Exception as e:
                    logger.error(f"GitHub collection error for topic '{topic}': {e}")

            # Method 2: Scrape trending page
            try:
                resp = await client.get(f"{self.TRENDING_URL}?since=daily&spoken_language_code=en")
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for article in soup.select("article.Box-row")[:15]:
                        h2 = article.select_one("h2 a")
                        if not h2:
                            continue
                        repo_path = h2.get("href", "").strip("/")
                        desc_p = article.select_one("p")
                        description = desc_p.text.strip() if desc_p else ""
                        stars_el = article.select_one("span.d-inline-block.float-sm-right")
                        stars_text = stars_el.text.strip().replace(",", "") if stars_el else "0"

                        items.append(
                            self.normalize_item(
                                external_id=f"trending-{repo_path}",
                                title=repo_path,
                                body=description,
                                url=f"https://github.com/{repo_path}",
                                author=repo_path.split("/")[0] if "/" in repo_path else "",
                                published_at=datetime.utcnow(),
                                content_type="repo",
                                engagement={"stars_today": int(stars_text) if stars_text.isdigit() else 0},
                                metadata={"source": "trending_page"},
                            )
                        )
            except Exception as e:
                logger.error(f"GitHub trending page scrape error: {e}")

        # Deduplicate by URL
        seen = set()
        unique = []
        for item in items:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique.append(item)

        logger.info(f"Collected {len(unique)} GitHub repos")
        return unique
