"""Pillar 1: Source Reputation — Placeholder for Phase 2."""

from app.core.pillars.base import BasePillar
from app.models.schemas import PillarScore


class SourceReputationPillar(BasePillar):
    name = "Source Reputation"
    name_bn = "উৎস যাচাই"
    weight = 0.20
    model_id = "gemini"

    async def analyze(self, content: str, image_url: str | None = None) -> PillarScore:
        # TODO: Phase 2 — Neo4j lookup + domain analysis via gemini
        return self._make_score(
            score=50.0,
            explanation_en="Source reputation analysis not yet active.",
            explanation_bn="উৎস সুনাম বিশ্লেষণ এখনও সক্রিয় নয়।",
            active=False,
        )
