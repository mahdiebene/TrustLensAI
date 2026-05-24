"""Pillar 6: Author/Network Analysis — Uses gemini for account pattern and bot detection."""

import json
import logging
import re

from app.core.pillars.base import BasePillar
from app.models.schemas import PillarScore
from app.services.pollinations import get_pollinations_client
from app.services.redis_client import get_cache_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a social media forensics analyst specializing in detecting bot accounts, coordinated inauthentic behavior, and network manipulation patterns.

Analyze the following content for author/network credibility indicators:

1. **Account patterns** — Does the content show signs of being from a bot or fake account?
   - Repetitive posting patterns
   - Generic/template-like language
   - Unusual posting times
   - Copy-paste behavior

2. **Network amplification** — Signs of coordinated sharing:
   - Multiple identical posts across platforms
   - Suspicious engagement patterns
   - Astroturfing indicators

3. **Author credibility signals** (if identifiable):
   - Is the author a known journalist/expert?
   - Does the writing style match a real person?
   - Are there verifiable credentials?

4. **Platform-specific signals:**
   - Facebook: Page vs. personal account, group dynamics
   - Twitter/X: Follower/following ratio, account age
   - WhatsApp: Forward count indicators

Return a JSON object with exactly this structure:
{
  "score": <number 0-100>,
  "author_type": "verified_journalist|known_entity|anonymous|suspected_bot|unknown",
  "signals": [
    {"signal": "<signal name>", "assessment": "credible|suspicious|neutral", "detail": "<brief detail>"}
  ],
  "explanation_en": "<one paragraph English summary>",
  "explanation_bn": "<one paragraph Bengali summary>"
}

Scoring guide:
- 90-100: Verified author with strong credibility
- 70-89: Identifiable author with reasonable credibility
- 50-69: Anonymous but no strong bot/fake signals
- 30-49: Multiple suspicious signals detected
- 0-29: Strong indicators of bot/fake account or coordinated campaign"""


class AuthorNetworkPillar(BasePillar):
    name = "Author/Network"
    name_bn = "লেখক বিশ্লেষণ"
    weight = 0.10
    model_id = "gemini"

    async def analyze(self, content: str, image_url: str | None = None) -> PillarScore:
        """Analyze author/network patterns using gemini."""
        cache = get_cache_service()
        cache_key = cache.make_key("pillar_author", content)
        cached = await cache.get_cached(cache_key)
        if cached:
            return PillarScore(**cached)

        try:
            client = get_pollinations_client()
            response = await client.chat(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze the author/network credibility of this content:\n\n{content}"},
                ],
                temperature=0.2,
                timeout=90.0,
            )

            result = self._parse_response(response)

            evidence = []
            if result.get("author_type"):
                evidence.append(f"Author type: {result['author_type']}")
            for s in result.get("signals", []):
                icon = {"credible": "✅", "suspicious": "⚠️", "neutral": "➖"}.get(s.get("assessment", ""), "")
                evidence.append(f"{icon} {s['signal']}: {s.get('detail', '')}")

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
            logger.error(f"[AuthorNetwork] Analysis failed: {e}")
            return self._make_score(
                score=50.0,
                explanation_en=f"Author/network analysis encountered an error: {str(e)[:100]}",
                explanation_bn="লেখক/নেটওয়ার্ক বিশ্লেষণে একটি ত্রুটি হয়েছে।",
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
                "author_type": "unknown",
                "signals": [],
                "explanation_en": "Could not parse author analysis response.",
                "explanation_bn": "লেখক বিশ্লেষণের প্রতিক্রিয়া পার্স করা যায়নি।",
            }
