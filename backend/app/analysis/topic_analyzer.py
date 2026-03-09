"""
Custom topic analysis — text search + Google Gemini analysis.
Falls back to text-based search when vector embeddings are unavailable.
"""

import json
import logging
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import google.generativeai as genai
from app.config import get_settings

logger = logging.getLogger(__name__)

TOPIC_SYSTEM_PROMPT = """Sen bir AI İstihbarat Analistisin. Kullanıcı belirli bir konu hakkında
derinlemesine analiz istedi. Sana verilen içerik öğelerini ve kendi bilgini kullanarak analiz üret.

Şu yapıda bir analiz üret:
1. **Genel Bakış** - Bu konu nedir ve neden önemli
2. **Önemli Gelişmeler** - Son olaylar, çıkışlar ve değişiklikler
3. **Önemli Oyuncular** - İlgili şirketler, araştırmacılar ve projeler
4. **Teknik Detaylar** - Önemli teknik yönler
5. **Pazar Etkisi** - İş dünyası ve sektör etkileri
6. **Gelecek Görünümü** - Gelecek tahminleri ve beklenen gelişmeler

Kurallar:
- Spesifik ve veri odaklı ol.
- Sağlanan kaynaklara atıfta bulun.
- TÜM METİNLER TÜRKÇE OLACAK.
- Geçerli JSON çıktısı ver. Anahtarlar: title, overview, developments (liste), players (liste), technical (liste), impact (liste), outlook (liste)
- Her liste öğesi şu anahtarlara sahip obje olacak: point, detail, source (opsiyonel string)
"""


class TopicAnalyzer:
    def __init__(self, session: AsyncSession):
        settings = get_settings()
        self.session = session
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.LLM_MODEL)

    async def analyze(self, query: str) -> Dict[str, Any]:
        """Analyze a user-provided topic using text search + Gemini LLM."""
        # 1) Text-based search across content
        rows = await self._text_search(query)

        # 2) Build context from found items
        context_items = []
        sources: List[Dict[str, str]] = []
        for r in rows:
            context_items.append(
                f"[{r[5].upper()}] {r[1] or 'Untitled'}\n"
                f"Source: {r[7]} | Author: {r[4] or 'Unknown'}\n"
                f"URL: {r[3] or 'N/A'}\n"
                f"Content: {(r[2] or '')[:400]}\n"
            )
            if r[3]:
                sources.append({"title": r[1] or "Untitled", "url": r[3], "type": r[5]})

        context = "\n---\n".join(context_items) if context_items else "Veritabanında bu konuyla ilgili spesifik veri bulunamadı."

        # 3) Gemini analysis (always works, even without local data)
        user_prompt = (
            f"{TOPIC_SYSTEM_PROMPT}\n\n"
            f"Kullanıcı sorgusu: {query}\n\n"
            f"Veritabanından bulunan ilgili içerikler:\n\n{context}\n\n"
            f"Bu konu hakkında derinlemesine bir analiz üret. Eğer veritabanında yeterli veri yoksa, "
            f"kendi bilgini kullanarak kapsamlı bir analiz yap. Sadece geçerli JSON çıktısı ver, markdown formatı kullanma."
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
            data["query"] = query
            data["sources"] = sources[:10]
            return data
        except Exception as e:
            logger.error(f"Topic analysis Gemini error: {e}")
            return {
                "query": query,
                "title": f"Analiz: {query}",
                "overview": f"Analiz üretilirken hata oluştu: {str(e)}",
                "developments": [],
                "players": [],
                "technical": [],
                "impact": [],
                "outlook": [],
                "sources": sources[:10],
            }

    async def _text_search(self, query: str) -> list:
        """Search content using text matching (ILIKE) — no embeddings needed."""
        # Split query into words for broader matching
        words = [w.strip() for w in query.split() if len(w.strip()) >= 2]
        if not words:
            return []

        # Build ILIKE conditions for each word
        conditions = []
        params = {}
        for i, word in enumerate(words[:5]):  # max 5 words
            key = f"w{i}"
            conditions.append(f"(c.title ILIKE :{key} OR c.body ILIKE :{key})")
            params[key] = f"%{word}%"

        where_clause = " OR ".join(conditions)

        result = await self.session.execute(
            text(f"""
                SELECT c.id, c.title, c.body, c.url, c.author, c.content_type,
                       c.engagement, s.name as source_name
                FROM content c
                JOIN sources s ON s.id = c.source_id
                WHERE c.is_spam = false AND ({where_clause})
                ORDER BY c.collected_at DESC
                LIMIT 30
            """),
            params,
        )
        return result.fetchall()

    @staticmethod
    def _parse_json_safe(raw: str) -> dict:
        """Parse JSON with repair for common LLM formatting issues."""
        import re
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        cleaned = re.sub(r',\s*([}\]])', r'\1', raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
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
        return {"title": "Analiz", "overview": raw[:2000], "developments": [], "players": [], "technical": [], "impact": [], "outlook": []}
