"""
arXiv API collector for latest AI/ML/NLP research papers.
"""

import httpx
import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Any
from datetime import datetime
from app.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG"]
ARXIV_API = "http://export.arxiv.org/api/query"


class ArxivCollector(BaseCollector):
    source_name = "arXiv"
    source_type = "arxiv"

    async def collect(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for category in ARXIV_CATEGORIES:
                try:
                    params = {
                        "search_query": f"cat:{category}",
                        "sortBy": "submittedDate",
                        "sortOrder": "descending",
                        "max_results": 25,
                    }
                    resp = await client.get(ARXIV_API, params=params)
                    if resp.status_code != 200:
                        logger.warning(f"arXiv API error for {category}: {resp.status_code}")
                        continue

                    root = ET.fromstring(resp.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

                    for entry in root.findall("atom:entry", ns):
                        arxiv_id = entry.find("atom:id", ns).text.strip()
                        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                        summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
                        published = entry.find("atom:published", ns).text.strip()

                        authors = []
                        for author_el in entry.findall("atom:author", ns):
                            name_el = author_el.find("atom:name", ns)
                            if name_el is not None:
                                authors.append(name_el.text.strip())

                        # Get PDF link
                        pdf_url = ""
                        for link in entry.findall("atom:link", ns):
                            if link.get("title") == "pdf":
                                pdf_url = link.get("href", "")
                                break

                        categories = [
                            cat.get("term", "")
                            for cat in entry.findall("atom:category", ns)
                        ]

                        items.append(
                            self.normalize_item(
                                external_id=arxiv_id,
                                title=title,
                                body=summary,
                                url=pdf_url or arxiv_id,
                                author=", ".join(authors[:5]),
                                published_at=datetime.fromisoformat(
                                    published.replace("Z", "+00:00")
                                ),
                                content_type="paper",
                                engagement={},
                                metadata={
                                    "categories": categories,
                                    "primary_category": category,
                                    "arxiv_id": arxiv_id.split("/")[-1],
                                },
                            )
                        )
                except Exception as e:
                    logger.error(f"arXiv collection error for '{category}': {e}")

        logger.info(f"Collected {len(items)} arXiv papers")
        return items
