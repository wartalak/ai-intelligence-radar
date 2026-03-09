"""
YouTube Data API collector for AI-related videos.
"""

import httpx
import logging
from typing import List, Dict, Any
from datetime import datetime
from app.collectors.base import BaseCollector
from app.config import get_settings

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "artificial intelligence news",
    "LLM large language model",
    "AI agents tutorial",
    "GPT latest update",
    "open source AI model",
]


class YouTubeCollector(BaseCollector):
    source_name = "YouTube"
    source_type = "youtube"

    SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
    VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

    async def collect(self) -> List[Dict[str, Any]]:
        settings = get_settings()
        if not settings.YOUTUBE_API_KEY:
            logger.warning("YouTube API key not set – skipping YouTube collection.")
            return []

        items: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=30) as client:
            for query in SEARCH_QUERIES:
                try:
                    params = {
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "order": "date",
                        "maxResults": 10,
                        "key": settings.YOUTUBE_API_KEY,
                    }
                    resp = await client.get(self.SEARCH_URL, params=params)
                    if resp.status_code != 200:
                        logger.warning(f"YouTube search error: {resp.status_code}")
                        continue

                    data = resp.json()
                    video_ids = []
                    snippets = {}

                    for item in data.get("items", []):
                        vid = item["id"].get("videoId")
                        if vid:
                            video_ids.append(vid)
                            snippets[vid] = item["snippet"]

                    # fetch stats
                    if video_ids:
                        stats_resp = await client.get(
                            self.VIDEO_URL,
                            params={
                                "part": "statistics",
                                "id": ",".join(video_ids),
                                "key": settings.YOUTUBE_API_KEY,
                            },
                        )
                        stats_map = {}
                        if stats_resp.status_code == 200:
                            for sv in stats_resp.json().get("items", []):
                                stats_map[sv["id"]] = sv.get("statistics", {})

                    for vid in video_ids:
                        snippet = snippets[vid]
                        stats = stats_map.get(vid, {})
                        items.append(
                            self.normalize_item(
                                external_id=vid,
                                title=snippet.get("title", ""),
                                body=snippet.get("description", ""),
                                url=f"https://www.youtube.com/watch?v={vid}",
                                author=snippet.get("channelTitle", ""),
                                published_at=datetime.fromisoformat(
                                    snippet["publishedAt"].replace("Z", "+00:00")
                                ),
                                content_type="video",
                                engagement={
                                    "views": int(stats.get("viewCount", 0)),
                                    "likes": int(stats.get("likeCount", 0)),
                                    "comments": int(stats.get("commentCount", 0)),
                                },
                                metadata={
                                    "channel_id": snippet.get("channelId", ""),
                                    "query": query,
                                },
                            )
                        )
                except Exception as e:
                    logger.error(f"YouTube collection error for '{query}': {e}")

        # Attempt transcript extraction
        items = await self._enrich_transcripts(items)
        logger.info(f"Collected {len(items)} YouTube videos")
        return items

    async def _enrich_transcripts(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Try to fetch transcripts for videos."""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError:
            return items

        for item in items:
            try:
                vid = item["external_id"]
                transcript_list = YouTubeTranscriptApi.get_transcript(vid)
                transcript_text = " ".join(seg["text"] for seg in transcript_list)
                item["body"] = item["body"] + "\n\nTranscript:\n" + transcript_text[:3000]
            except Exception:
                pass  # transcript not available
        return items
