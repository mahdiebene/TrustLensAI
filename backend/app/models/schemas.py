"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request body for the /api/analyze endpoint."""

    content: str = Field(..., min_length=1, max_length=10000, description="Text content or URL to analyze")
    image_url: str | None = Field(None, description="Optional image URL for image authenticity analysis")


class PillarScore(BaseModel):
    """Individual pillar scoring result."""

    name: str = Field(..., description="Pillar name")
    name_bn: str = Field(..., description="Pillar name in Bengali")
    score: float = Field(..., ge=0, le=100, description="Pillar score 0-100")
    weight: float = Field(..., ge=0, le=1, description="Pillar weight in final score")
    explanation_en: str = Field(..., description="English explanation")
    explanation_bn: str = Field(..., description="Bengali explanation")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence")
    model_used: str = Field("", description="AI model used for this pillar")
    active: bool = Field(True, description="Whether this pillar was actively analyzed")


class AnalyzeResponse(BaseModel):
    """Response body for the /api/analyze endpoint."""

    trust_score: float = Field(..., ge=0, le=100, description="Weighted trust score 0-100")
    verdict: str = Field(..., description="Human-readable verdict in English")
    verdict_bn: str = Field(..., description="Human-readable verdict in Bengali")
    pillars: list[PillarScore] = Field(..., description="Individual pillar scores")
    explanation_en: str = Field(..., description="Overall English explanation")
    explanation_bn: str = Field(..., description="Overall Bengali explanation")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level 0-1")
    cached: bool = Field(False, description="Whether result was served from cache")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")

    # Scrape-failure signaling (when a URL could not be retrieved)
    scrape_failed: bool = Field(False, description="True when the URL could not be scraped — frontend should prompt user for text/image")
    scrape_reason_en: str = Field("", description="Human-readable failure reason (English)")
    scrape_reason_bn: str = Field("", description="Human-readable failure reason (Bengali)")
    needs_user_input: bool = Field(False, description="True if the frontend should ask the user to paste the post content or upload a screenshot")
    original_url: str = Field("", description="The URL the user submitted (echoed back when scrape_failed)")


class HealthResponse(BaseModel):
    """Response body for the /api/health endpoint."""

    status: str = "ok"
    version: str = "0.1.0"
    services: dict[str, str] = Field(default_factory=dict)
