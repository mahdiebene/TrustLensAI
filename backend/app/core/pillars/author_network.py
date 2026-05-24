"""Pillar 6: Author/Network Analysis — Placeholder for Phase 2."""

from app.core.pillars.base import BasePillar
from app.models.schemas import PillarScore


class AuthorNetworkPillar(BasePillar):
    name = "Author/Network"
    name_bn = "লেখক বিশ্লেষণ"
    weight = 0.10
    model_id = "gemini"

    async def analyze(self, content: str, image_url: str | None = None) -> PillarScore:
        # TODO: Phase 2D — Account patterns, bot detection
        return self._make_score(
            score=50.0,
            explanation_en="Author/network analysis not yet active.",
            explanation_bn="লেখক/নেটওয়ার্ক বিশ্লেষণ এখনও সক্রিয় নয়।",
            active=False,
        )
