"""Base class for all trust scoring pillars."""

from abc import ABC, abstractmethod
from app.models.schemas import PillarScore


class BasePillar(ABC):
    """Abstract base class for trust scoring pillars."""

    name: str = ""
    name_bn: str = ""
    weight: float = 0.0
    model_id: str = ""

    @abstractmethod
    async def analyze(self, content: str, image_url: str | None = None) -> PillarScore:
        """
        Analyze content and return a pillar score.

        Args:
            content: The text content or URL to analyze
            image_url: Optional image URL for image-based analysis

        Returns:
            PillarScore with score, explanation, and evidence
        """
        ...

    def _make_score(
        self,
        score: float,
        explanation_en: str,
        explanation_bn: str,
        evidence: list[str] | None = None,
        active: bool = True,
    ) -> PillarScore:
        """Helper to construct a PillarScore."""
        return PillarScore(
            name=self.name,
            name_bn=self.name_bn,
            score=score,
            weight=self.weight,
            explanation_en=explanation_en,
            explanation_bn=explanation_bn,
            evidence=evidence or [],
            model_used=self.model_id,
            active=active,
        )
