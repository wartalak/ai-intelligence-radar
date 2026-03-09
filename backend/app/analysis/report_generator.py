"""
AI-powered daily intelligence report generator — Google Gemini Pro.
"""

import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import google.generativeai as genai
from app.config import get_settings

logger = logging.getLogger(__name__)


REPORT_SYSTEM_PROMPT = """Sen global Yapay Zeka ekosistemini analiz eden bir AI İstihbarat Analistisin.
Sosyal medya, araştırma makaleleri, bloglar, videolar ve kod depolarından toplanan verileri analiz ederek
günlük istihbarat brifingleri üretiyorsun.

Raporun şu bölümlerden oluşmalıdır:
1. **Önemli Duyurular** - Öne çıkan ürün lansmanları, ortaklıklar, politika değişiklikleri
2. **Araştırma Atılımları** - Dikkat çekici makaleler ve bilimsel gelişmeler
3. **Yeni AI Araçları** - Yeni çıkan veya trend olan araçlar, kütüphaneler, modeller
4. **Gündem Tartışmaları** - AI topluluğundaki sıcak konular
5. **Stratejik Değerlendirmeler** - Ortaya çıkan kalıplar ve etkilere dair analizin

Kurallar:
- Spesifik ol ve mümkünse kaynak göster.
- Somut detaylar ver: isimler, sayılar, tarihler.
- Her bölümde 3-5 madde olsun.
- Profesyonel bir istihbarat brifing tarzında yaz.
- TÜM METİNLER TÜRKÇE OLACAK.
- Geçerli JSON çıktısı ver. Anahtarlar: title, summary, sections (announcements, breakthroughs, tools, discussions, insights anahtarlarına sahip obje)
- Her bölüm değeri, şu anahtarlara sahip obje listesi olacak: headline, detail, sources (string listesi)
"""


class ReportGenerator:
    def __init__(self, session: AsyncSession):
        settings = get_settings()
        self.session = session
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.LLM_MODEL)

    async def generate_daily_report(self, report_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate or retrieve the daily intelligence report."""
        target_date = report_date or date.today()

        # Check if report already exists
        existing = await self.session.execute(
            text("SELECT id, title, summary, sections, source_refs FROM reports WHERE report_date = :d"),
            {"d": target_date},
        )
        row = existing.first()
        if row:
            return {
                "id": row[0],
                "date": str(target_date),
                "title": row[1],
                "summary": row[2],
                "sections": row[3],
                "source_refs": row[4],
            }

        # Gather recent content for context
        context = await self._gather_context(target_date)

        if not context:
            return self._empty_report(target_date)

        # Generate report via Gemini
        report = await self._call_gemini(context, target_date)

        # Store report
        await self._store_report(target_date, report)

        return report

    async def _gather_context(self, target_date: date) -> str:
        """Collect recent content items as context for the LLM."""
        since = datetime.combine(target_date - timedelta(days=2), datetime.min.time())

        result = await self.session.execute(
            text("""
                SELECT c.title, c.body, c.content_type, c.url, c.author,
                       c.engagement, s.name as source_name
                FROM content c
                JOIN sources s ON s.id = c.source_id
                WHERE c.collected_at > :since AND c.is_spam = false
                ORDER BY c.collected_at DESC
                LIMIT 100
            """),
            {"since": since},
        )
        rows = result.fetchall()
        if not rows:
            return ""

        items = []
        for r in rows:
            eng = r[5] or {}
            eng_str = ", ".join(f"{k}: {v}" for k, v in eng.items()) if eng else "N/A"
            items.append(
                f"[{r[2].upper()}] {r[0] or 'Untitled'}\n"
                f"Source: {r[6]} | Author: {r[4] or 'Unknown'}\n"
                f"Engagement: {eng_str}\n"
                f"URL: {r[3] or 'N/A'}\n"
                f"Content: {(r[1] or '')[:500]}\n"
            )

        return "\n---\n".join(items)

    async def _call_gemini(self, context: str, target_date: date) -> Dict[str, Any]:
        """Call Google Gemini to generate the report."""
        user_prompt = (
            f"{REPORT_SYSTEM_PROMPT}\n\n"
            f"Today's date: {target_date}\n\n"
            f"Here are the latest AI-related content items collected from multiple sources:\n\n"
            f"{context}\n\n"
            f"Based on this data, produce a comprehensive AI Intelligence Report for today. "
            f"Output as valid JSON only, no markdown formatting."
        )

        try:
            response = self.model.generate_content(
                user_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                    max_output_tokens=8192,
                ),
            )
            raw = response.text
            data = self._parse_json_safe(raw)

            return {
                "date": str(target_date),
                "title": data.get("title", f"AI Intelligence Report — {target_date}"),
                "summary": data.get("summary", ""),
                "sections": data.get("sections", {}),
                "source_refs": [],
            }
        except Exception as e:
            logger.error(f"Gemini report generation error: {e}")
            return self._empty_report(target_date)

    @staticmethod
    def _parse_json_safe(raw: str) -> dict:
        """Parse JSON with repair for common LLM formatting issues."""
        import re
        # Try strict parse first
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Remove trailing commas before } or ]
        cleaned = re.sub(r',\s*([}\]])', r'\1', raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        # Try to extract the first valid JSON object
        brace_count = 0
        start = raw.find('{')
        if start == -1:
            return {}
        for i in range(start, len(raw)):
            if raw[i] == '{':
                brace_count += 1
            elif raw[i] == '}':
                brace_count -= 1
            if brace_count == 0:
                snippet = raw[start:i+1]
                cleaned = re.sub(r',\s*([}\]])', r'\1', snippet)
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    break
        # Last resort: return a minimal report
        logger.warning("Could not parse Gemini JSON, returning raw as summary")
        return {"title": "AI Intelligence Report", "summary": raw[:2000], "sections": {}}

    async def _store_report(self, target_date: date, report: Dict[str, Any]):
        """Persist the generated report."""
        try:
            await self.session.execute(
                text("""
                    INSERT INTO reports (report_date, title, summary, sections, source_refs, model_used)
                    VALUES (:d, :title, :summary, CAST(:sections AS jsonb), CAST(:refs AS jsonb), :model)
                    ON CONFLICT (report_date)
                    DO UPDATE SET title = :title, summary = :summary,
                                  sections = CAST(:sections AS jsonb), source_refs = CAST(:refs AS jsonb),
                                  model_used = :model, generated_at = NOW()
                """),
                {
                    "d": target_date,
                    "title": report["title"],
                    "summary": report["summary"],
                    "sections": json.dumps(report["sections"]),
                    "refs": json.dumps(report.get("source_refs", [])),
                    "model": get_settings().LLM_MODEL,
                },
            )
            await self.session.commit()
        except Exception as e:
            logger.error(f"Store report error: {e}")

    @staticmethod
    def _empty_report(target_date: date) -> Dict[str, Any]:
        return {
            "date": str(target_date),
            "title": f"AI Intelligence Report — {target_date}",
            "summary": "No data collected yet. Reports will be generated once content is ingested.",
            "sections": {
                "announcements": [],
                "breakthroughs": [],
                "tools": [],
                "discussions": [],
                "insights": [],
            },
            "source_refs": [],
        }
