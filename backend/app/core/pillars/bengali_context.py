"""Pillar 4: Bengali Context — Uses qwen-large for BD-specific misinformation patterns."""

import json
import logging
import re

from app.core.pillars.base import BasePillar
from app.models.schemas import PillarScore
from app.services.pollinations import get_pollinations_client
from app.services.redis_client import get_cache_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert on Bangladeshi social media misinformation patterns.
You understand the cultural, political, and social context of Bangladesh deeply.

Analyze the following content for Bangladesh-specific misinformation patterns:

1. **Communal tension narratives** — Content designed to inflame Hindu-Muslim tensions
2. **Political misinformation** — False claims about political parties (AL, BNP, JP), elections, or leaders
3. **Disaster/crisis rumors** — False claims during floods, cyclones, or political unrest
4. **Celebrity death hoaxes** — False reports of deaths of Bangladeshi celebrities
5. **Price manipulation rumors** — False claims about commodity prices to cause panic buying
6. **Anti-minority narratives** — Content targeting religious or ethnic minorities
7. **Foreign conspiracy theories** — Claims about India, Pakistan, or Myanmar plotting against BD
8. **Fake government announcements** — Fabricated policy changes or official statements
9. **Historical revisionism** — Distortion of Liberation War history or national events
10. **Health misinformation** — False medical claims specific to BD context

Also check for:
- Known viral misinformation patterns that have circulated in Bangladesh
- Content that matches templates commonly used by BD misinformation networks
- Seasonal patterns (election season, religious holidays, national days)

Return a JSON object with exactly this structure:
{
  "score": <number 0-100>,
  "patterns_detected": [
    {"pattern": "<pattern name>", "confidence": "high|medium|low", "detail": "<specific detail>"}
  ],
  "cultural_context": "<brief note on relevant BD context>",
  "explanation_en": "<one paragraph English summary>",
  "explanation_bn": "<one paragraph Bengali summary>"
}

Scoring guide:
- 90-100: No BD-specific misinformation patterns detected
- 70-89: Minor patterns but likely legitimate content
- 50-69: Some concerning patterns that warrant caution
- 30-49: Multiple misinformation patterns detected
- 0-29: Matches known BD misinformation templates"""


class BengaliContextPillar(BasePillar):
    name = "Bengali Context"
    name_bn = "বাংলা প্রসঙ্গ"
    weight = 0.15
    model_id = "qwen-large"

    async def analyze(self, content: str, image_url: str | None = None) -> PillarScore:
        """Analyze content for Bangladesh-specific misinformation patterns."""
        cache = get_cache_service()
        cache_key = cache.make_key("pillar_bengali", content)
        cached = await cache.get_cached(cache_key)
        if cached:
            return PillarScore(**cached)

        try:
            client = get_pollinations_client()
            response = await client.chat(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this content for Bangladesh-specific misinformation patterns:\n\n{content}"},
                ],
                temperature=0.2,
                timeout=90.0,
            )

            result = self._parse_response(response)

            evidence = []
            for p in result.get("patterns_detected", []):
                conf_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(p.get("confidence", ""), "")
                evidence.append(f"{conf_icon} {p['pattern']}: {p.get('detail', '')}")

            if result.get("cultural_context"):
                evidence.append(f"Context: {result['cultural_context']}")

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
            logger.error(f"[BengaliContext] Analysis failed: {e}")
            return self._make_score(
                score=50.0,
                explanation_en=f"Bengali context analysis encountered an error: {str(e)[:100]}",
                explanation_bn="বাংলা প্রসঙ্গ বিশ্লেষণে একটি ত্রুটি হয়েছে।",
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
                "patterns_detected": [],
                "cultural_context": "",
                "explanation_en": "Could not parse Bengali context analysis.",
                "explanation_bn": "বাংলা প্রসঙ্গ বিশ্লেষণ পার্স করা যায়নি।",
            }
