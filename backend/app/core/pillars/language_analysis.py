"""Pillar 3: Language Analysis — Uses claude model to detect manipulation patterns."""

import json
import logging
import re

from app.core.pillars.base import BasePillar
from app.models.schemas import PillarScore
from app.services.pollinations import get_pollinations_client
from app.services.redis_client import get_cache_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a linguistic analysis expert specializing in detecting manipulation, propaganda, and misinformation patterns in Bengali and English text.

CRITICAL: Do NOT hallucinate or make up information. If you cannot determine something from the provided content, explicitly state 'Cannot determine from available information' and give a neutral score of 50. Never invent source names, author names, or facts that are not explicitly present in the content.

Analyze the following content for:
1. Emotional manipulation / sensationalism
2. Clickbait patterns (exaggerated claims, urgency)
3. Logical fallacies (ad hominem, straw man, false dichotomy)
4. Propaganda techniques (bandwagon, fear appeal, loaded language)
5. Urgency/fear language designed to bypass critical thinking
6. Bengali-specific patterns:
   - Communal tension triggers
   - Political bias markers
   - Rumor language patterns
   - Sensationalist Bengali news patterns

Return a JSON object with exactly this structure:
{
  "score": <number 0-100>,
  "patterns_found": [
    {"pattern": "<pattern name>", "severity": "high|medium|low", "example": "<quote from text>"}
  ],
  "explanation_en": "<one paragraph English summary>",
  "explanation_bn": "<one paragraph Bengali summary>"
}

Scoring guide:
- 90-100: Neutral, factual language with no manipulation detected
- 70-89: Mostly factual with minor emotional language (normal for opinion pieces)
- 50-69: Notable manipulation patterns present
- 30-49: Heavy use of manipulation techniques
- 0-29: Extreme propaganda/manipulation — designed to deceive"""


class LanguageAnalysisPillar(BasePillar):
    name = "Language Analysis"
    name_bn = "ভাষা বিশ্লেষণ"
    weight = 0.20
    model_id = "claude"

    async def analyze(self, content: str, image_url: str | None = None) -> PillarScore:
        """Analyze language patterns for manipulation detection."""
        # Check cache
        cache = get_cache_service()
        cache_key = cache.make_key("pillar_language", content)
        cached = await cache.get_cached(cache_key)
        if cached:
            return PillarScore(**cached)

        try:
            client = get_pollinations_client()
            response = await client.chat(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this content for manipulation patterns:\n\n{content[:3000]}"},
                ],
                temperature=0.2,
                timeout=12.0,
            )

            # Parse JSON response
            result = self._parse_response(response)

            evidence = []
            for p in result.get("patterns_found", []):
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(p.get("severity", ""), "")
                evidence.append(f"{severity_icon} {p['pattern']}: \"{p.get('example', '')}\"")

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

            # Cache result
            await cache.set_cached(cache_key, score.model_dump(), ttl=86400)
            return score

        except Exception as e:
            logger.error(f"[LanguageAnalysis] Analysis failed: {e}")
            return self._make_score(
                score=50.0,
                explanation_en=f"Language analysis encountered an error: {str(e)[:100]}",
                explanation_bn="ভাষা বিশ্লেষণে একটি ত্রুটি হয়েছে।",
                active=False,
            )

    def _parse_response(self, response: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
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
                "patterns_found": [],
                "explanation_en": "Could not parse analysis response.",
                "explanation_bn": "বিশ্লেষণের প্রতিক্রিয়া পার্স করা যায়নি।",
            }
