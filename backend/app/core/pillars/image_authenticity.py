"""Pillar 5: Image Authenticity — Uses qwen-vision-pro for AI-generated/manipulated detection."""

import json
import logging
import re

from app.core.pillars.base import BasePillar
from app.models.schemas import PillarScore
from app.services.pollinations import get_pollinations_client
from app.services.redis_client import get_cache_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an image forensics expert specializing in detecting AI-generated and manipulated images.

CRITICAL: Do NOT hallucinate or make up information. If you cannot determine something from the provided image, explicitly state 'Cannot determine from available information' and give a neutral score of 50. Never invent details that are not visible in the image.

Analyze the provided image for signs of:
1. **AI generation** — Artifacts from DALL-E, Midjourney, Stable Diffusion (unnatural hands, text errors, impossible geometry)
2. **Photo manipulation** — Signs of Photoshop/editing (clone stamping, inconsistent lighting, edge artifacts)
3. **Context manipulation** — Real image used out of context (old image presented as new, different location claimed)
4. **Deepfake indicators** — Face swapping artifacts, unnatural skin texture, inconsistent reflections
5. **Metadata inconsistencies** — If visible, note any EXIF data concerns

Return a JSON object with exactly this structure:
{
  "score": <number 0-100>,
  "image_type": "authentic|ai_generated|manipulated|out_of_context|uncertain",
  "indicators": [
    {"indicator": "<what was found>", "severity": "high|medium|low", "detail": "<specific detail>"}
  ],
  "explanation_en": "<one paragraph English summary>",
  "explanation_bn": "<one paragraph Bengali summary>"
}

Scoring guide:
- 90-100: Image appears authentic with no manipulation indicators
- 70-89: Minor concerns but likely authentic
- 50-69: Some indicators of manipulation or AI generation
- 30-49: Strong indicators of manipulation
- 0-29: Clearly AI-generated or heavily manipulated"""

SYSTEM_PROMPT_NO_IMAGE = """You are an image forensics expert. The user has submitted content for analysis but no image was provided.

CRITICAL: Do NOT hallucinate or make up information. Simply report that no image was available for analysis.

Analyze the text content to determine if it references or describes images that might be manipulated.
Look for:
- Claims about photos/videos that sound sensational
- References to "leaked" images or videos
- Descriptions that suggest AI-generated content

Return a JSON object:
{
  "score": 50,
  "image_type": "no_image_provided",
  "indicators": [],
  "explanation_en": "No image was provided for analysis. Text-only content was submitted.",
  "explanation_bn": "বিশ্লেষণের জন্য কোনো ছবি দেওয়া হয়নি। শুধুমাত্র টেক্সট জমা দেওয়া হয়েছে।"
}"""


class ImageAuthenticityPillar(BasePillar):
    name = "Image Authenticity"
    name_bn = "ছবি যাচাই"
    weight = 0.15
    model_id = "qwen-vision-pro"

    async def analyze(self, content: str, image_url: str | None = None) -> PillarScore:
        """Analyze image authenticity using vision model."""
        cache = get_cache_service()
        cache_key = cache.make_key("pillar_image", content + (image_url or ""))
        cached = await cache.get_cached(cache_key)
        if cached:
            return PillarScore(**cached)

        try:
            client = get_pollinations_client()

            if image_url:
                # Use vision model with image
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "text", "text": f"Analyze this image for authenticity. Context: {content[:500]}"},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ]},
                ]
            else:
                # No image — analyze text for image-related claims
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT_NO_IMAGE},
                    {"role": "user", "content": f"No image provided. Analyze this text for image-related claims:\n\n{content[:500]}"},
                ]

            response = await client.chat(
                model=self.model_id if image_url else "gemini",
                messages=messages,
                temperature=0.2,
                timeout=18.0,
            )

            result = self._parse_response(response)

            evidence = []
            if result.get("image_type") and result["image_type"] != "no_image_provided":
                evidence.append(f"Type: {result['image_type']}")
            for ind in result.get("indicators", []):
                sev_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(ind.get("severity", ""), "")
                evidence.append(f"{sev_icon} {ind['indicator']}: {ind.get('detail', '')}")

            score = PillarScore(
                name=self.name,
                name_bn=self.name_bn,
                score=result["score"],
                weight=self.weight,
                explanation_en=result["explanation_en"],
                explanation_bn=result["explanation_bn"],
                evidence=evidence,
                model_used=self.model_id if image_url else "gemini",
                active=bool(image_url),
            )

            await cache.set_cached(cache_key, score.model_dump(), ttl=86400)
            return score

        except Exception as e:
            logger.error(f"[ImageAuthenticity] Analysis failed: {e}")
            return self._make_score(
                score=50.0,
                explanation_en=f"Image analysis encountered an error: {str(e)[:100]}",
                explanation_bn="ছবি বিশ্লেষণে একটি ত্রুটি হয়েছে।",
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
                "image_type": "uncertain",
                "indicators": [],
                "explanation_en": "Could not parse image analysis response.",
                "explanation_bn": "ছবি বিশ্লেষণের প্রতিক্রিয়া পার্স করা যায়নি।",
            }
