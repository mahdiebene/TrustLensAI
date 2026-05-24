"""Pillar 2: Content Consistency — Uses perplexity-reasoning for web search cross-referencing."""

import json
import logging

from app.core.pillars.base import BasePillar
from app.models.schemas import PillarScore
from app.services.pollinations import get_pollinations_client
from app.services.redis_client import get_cache_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a fact-checking analyst specializing in South Asian media and Bengali content.
Analyze the following content for factual consistency by cross-referencing with known information.

Your task:
1. Identify the key claims made in the content
2. Assess whether these claims are consistent with known facts
3. Look for contradictions, exaggerations, or unverifiable statements
4. Consider the Bangladeshi context for political, social, and cultural claims

Return a JSON object with exactly this structure:
{
  "score": <number 0-100>,
  "findings": [
    {"claim": "<extracted claim>", "status": "verified|contradicted|unverifiable", "reason": "<brief reason>"}
  ],
  "explanation_en": "<one paragraph English summary of consistency analysis>",
  "explanation_bn": "<one paragraph Bengali summary>"
}

Scoring guide:
- 90-100: All claims verified by multiple reliable sources
- 70-89: Most claims verified, minor inconsistencies
- 50-69: Mixed — some claims verified, some unverifiable
- 30-49: Significant contradictions found
- 0-29: Major claims contradicted by reliable sources"""


class ContentConsistencyPillar(BasePillar):
    name = "Content Consistency"
    name_bn = "বিষয়বস্তু সামঞ্জস্য"
    weight = 0.20
    model_id = "perplexity-reasoning"

    async def analyze(self, content: str, image_url: str | None = None) -> PillarScore:
        """Analyze content consistency using perplexity-reasoning with web search."""
        # Check cache
        cache = get_cache_service()
        cache_key = cache.make_key("pillar_consistency", content)
        cached = await cache.get_cached(cache_key)
        if cached:
            return PillarScore(**cached)

        try:
            client = get_pollinations_client()
            response = await client.chat(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this content for factual consistency:\n\n{content}"},
                ],
                temperature=0.2,
                timeout=90.0,
            )

            # Parse JSON response
            result = self._parse_response(response)

            score = PillarScore(
                name=self.name,
                name_bn=self.name_bn,
                score=result["score"],
                weight=self.weight,
                explanation_en=result["explanation_en"],
                explanation_bn=result["explanation_bn"],
                evidence=[f"{f['claim']} — {f['status']}" for f in result.get("findings", [])],
                model_used=self.model_id,
                active=True,
            )

            # Cache result
            await cache.set_cached(cache_key, score.model_dump(), ttl=86400)
            return score

        except Exception as e:
            logger.error(f"[ContentConsistency] Analysis failed: {e}")
            return self._make_score(
                score=50.0,
                explanation_en=f"Content consistency analysis encountered an error: {str(e)[:100]}",
                explanation_bn="বিষয়বস্তু সামঞ্জস্য বিশ্লেষণে একটি ত্রুটি হয়েছে।",
                active=False,
            )

    def _parse_response(self, response: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Strip markdown code blocks if present
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # Fallback
            return {
                "score": 50,
                "findings": [],
                "explanation_en": "Could not parse analysis response.",
                "explanation_bn": "বিশ্লেষণের প্রতিক্রিয়া পার্স করা যায়নি।",
            }
