"""Pillar 4: Bengali Context — Placeholder for Phase 2."""

from app.core.pillars.base import BasePillar
from app.models.schemas import PillarScore


class BengaliContextPillar(BasePillar):
    name = "Bengali Context"
    name_bn = "বাংলা প্রসঙ্গ"
    weight = 0.15
    model_id = "qwen-large"

    async def analyze(self, content: str, image_url: str | None = None) -> PillarScore:
        # TODO: Phase 2B — BD-specific misinformation patterns
        return self._make_score(
            score=50.0,
            explanation_en="Bengali context analysis not yet active.",
            explanation_bn="বাংলা প্রসঙ্গ বিশ্লেষণ এখনও সক্রিয় নয়।",
            active=False,
        )
