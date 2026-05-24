"""Pillar 5: Image Authenticity — Placeholder for Phase 2."""

from app.core.pillars.base import BasePillar
from app.models.schemas import PillarScore


class ImageAuthenticityPillar(BasePillar):
    name = "Image Authenticity"
    name_bn = "ছবি যাচাই"
    weight = 0.15
    model_id = "qwen-vision-pro"

    async def analyze(self, content: str, image_url: str | None = None) -> PillarScore:
        # TODO: Phase 2C — AI-generated/manipulated detection
        if not image_url:
            return self._make_score(
                score=50.0,
                explanation_en="No image provided for analysis.",
                explanation_bn="বিশ্লেষণের জন্য কোনো ছবি দেওয়া হয়নি।",
                active=False,
            )
        return self._make_score(
            score=50.0,
            explanation_en="Image authenticity analysis not yet active.",
            explanation_bn="ছবি যাচাই বিশ্লেষণ এখনও সক্রিয় নয়।",
            active=False,
        )
