"""Contextual RAG enrichment.

For each chunk, an LLM generates metadata:
- Topic classification
- Key claims extracted
- Source attribution
- Language detection
- Relevance scoring
"""

import json
import logging
import re
import asyncio
from dataclasses import dataclass

from app.core.rag.chunking import Chunk
from app.services.pollinations import get_pollinations_client

logger = logging.getLogger(__name__)

ENRICHMENT_PROMPT = """Analyze this text chunk and extract structured metadata.

Text: "{chunk_text}"

Return JSON:
{{"topic": "<main topic>", "claims": ["<claim 1>"], "source_mentioned": "<source or null>", "language": "bn|en|mixed", "sentiment": "positive|negative|neutral", "keywords": ["<kw1>", "<kw2>"]}}"""


@dataclass
class EnrichedChunk:
    """A chunk with LLM-generated metadata."""
    text: str
    chunk_type: str
    index: int
    topic: str
    claims: list[str]
    source_mentioned: str | None
    language: str
    sentiment: str
    keywords: list[str]
    embedding: list[float] | None = None


async def enrich_chunk(chunk: Chunk) -> EnrichedChunk:
    """Enrich a single chunk with LLM-generated metadata."""
    try:
        client = get_pollinations_client()
        response = await client.chat(
            model="gemini",
            messages=[
                {"role": "system", "content": "Extract metadata. Return only valid JSON."},
                {"role": "user", "content": ENRICHMENT_PROMPT.format(chunk_text=chunk.text[:400])},
            ],
            temperature=0.1,
            timeout=15.0,
        )

        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        json_match = re.search(r'\{[\s\S]*\}', text)
        metadata = json.loads(json_match.group()) if json_match else json.loads(text)

        return EnrichedChunk(
            text=chunk.text,
            chunk_type=chunk.chunk_type,
            index=chunk.index,
            topic=metadata.get("topic", "unknown"),
            claims=metadata.get("claims", []),
            source_mentioned=metadata.get("source_mentioned"),
            language=metadata.get("language", "mixed"),
            sentiment=metadata.get("sentiment", "neutral"),
            keywords=metadata.get("keywords", []),
        )

    except Exception as e:
        logger.warning(f"[Contextual] Enrichment failed for chunk {chunk.index}: {e}")
        return EnrichedChunk(
            text=chunk.text,
            chunk_type=chunk.chunk_type,
            index=chunk.index,
            topic="unknown",
            claims=[],
            source_mentioned=None,
            language="mixed",
            sentiment="neutral",
            keywords=[],
        )


async def enrich_chunks(chunks: list[Chunk]) -> list[EnrichedChunk]:
    """Enrich multiple chunks in parallel."""
    return await asyncio.gather(*[enrich_chunk(c) for c in chunks])
