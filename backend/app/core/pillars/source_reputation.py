"""Pillar 1: Source Reputation — Uses gemini for domain analysis + Neo4j lookup."""

import json
import logging
import re

from app.core.pillars.base import BasePillar
from app.models.schemas import PillarScore
from app.services.pollinations import get_pollinations_client
from app.services.redis_client import get_cache_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a media source credibility analyst specializing in South Asian news sources.
Analyze the source/domain of the following content for reputation and reliability.

CRITICAL: Do NOT hallucinate or make up information. If you cannot determine something from the provided content, explicitly state 'Cannot determine from available information' and give a neutral score of 50. Never invent source names, author names, or facts that are not explicitly present in the content.

Your task:
1. Identify the source (domain, publication, or platform)
2. Assess the source's credibility based on:
   - Known reputation of the publication
   - Domain age and authority indicators
   - Whether it's a known news outlet vs. anonymous blog
   - History of accuracy (if known)
   - Presence of editorial standards
3. For Bangladeshi sources, consider:
   - Prothom Alo, Daily Star, BD News 24 = high reliability
   - Government sources = moderate (may have bias)
   - Unknown Facebook pages/groups = low reliability
   - WhatsApp forwards = very low reliability

Return a JSON object with exactly this structure:
{
  "score": <number 0-100>,
  "source_identified": "<name of source or 'Unknown'>",
  "source_type": "mainstream_news|government|blog|social_media|unknown",
  "factors": [
    {"factor": "<factor name>", "assessment": "positive|negative|neutral", "detail": "<brief detail>"}
  ],
  "explanation_en": "<one paragraph English summary>",
  "explanation_bn": "<one paragraph Bengali summary>"
}

Scoring guide:
- 90-100: Major verified news outlet with strong editorial standards
- 70-89: Known reliable source with minor concerns
- 50-69: Source has mixed reputation or limited track record
- 30-49: Source has known credibility issues
- 0-29: Anonymous, unverifiable, or known misinformation source"""


class SourceReputationPillar(BasePillar):
    name = "Source Reputation"
    name_bn = "উৎস যাচাই"
    weight = 0.20
    model_id = "gemini"

    async def analyze(self, content: str, image_url: str | None = None) -> PillarScore:
        """Analyze source reputation using gemini + domain knowledge."""
        cache = get_cache_service()
        cache_key = cache.make_key("pillar_source", content)
        cached = await cache.get_cached(cache_key)
        if cached:
            return PillarScore(**cached)

        try:
            # Extract URL if present
            url_match = re.search(r'https?://[^\s]+', content)
            url_context = f"\nURL found: {url_match.group()}" if url_match else "\nNo URL found in content."

            client = get_pollinations_client()
            response = await client.chat(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze the source reputation of this content:{url_context}\n\n{content[:3000]}"},
                ],
                temperature=0.2,
                timeout=18.0,
            )

            result = self._parse_response(response)

            evidence = []
            for f in result.get("factors", []):
                icon = {"positive": "✅", "negative": "❌", "neutral": "➖"}.get(f.get("assessment", ""), "")
                evidence.append(f"{icon} {f['factor']}: {f.get('detail', '')}")

            if result.get("source_identified"):
                evidence.insert(0, f"Source: {result['source_identified']} ({result.get('source_type', 'unknown')})")

            score = PillarScore(
                name=self.name,
                name_bn=self.name_bn,
                score=result["score"],
                weight=self.weight,
                explanation_en=result["explanation_en"],
                explanation_bn=result["explanation_bn"],
                evidence=evidence,
                model_used=self.model_id,
                active=True,
            )

            await cache.set_cached(cache_key, score.model_dump(), ttl=86400)
            return score

        except Exception as e:
            logger.error(f"[SourceReputation] Analysis failed: {e}")
            return self._make_score(
                score=50.0,
                explanation_en=f"Source reputation analysis encountered an error: {str(e)[:100]}",
                explanation_bn="উৎস সুনাম বিশ্লেষণে একটি ত্রুটি হয়েছে।",
                active=False,
            )

    def _parse_response(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return {
                "score": 50,
                "source_identified": "Unknown",
                "source_type": "unknown",
                "factors": [],
                "explanation_en": "Could not parse source analysis response.",
                "explanation_bn": "উৎস বিশ্লেষণের প্রতিক্রিয়া পার্স করা যায়নি।",
            }
