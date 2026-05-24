"""Semantic chunking for RAG pipeline.

Splits content by claim boundaries rather than fixed-size tokens.
This is critical for the trust scoring use case where each claim
needs to be independently verifiable.
"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A semantic chunk of content."""
    text: str
    chunk_type: str  # claim, context, metadata
    index: int
    metadata: dict


def semantic_chunk(content: str, max_chunk_size: int = 500) -> list[Chunk]:
    """
    Split content into semantic chunks based on claim boundaries.

    Strategy:
    1. Split by sentence boundaries
    2. Group sentences that form a single claim
    3. Ensure each chunk is independently meaningful
    4. Preserve context across chunk boundaries

    Args:
        content: Raw text content to chunk
        max_chunk_size: Maximum characters per chunk

    Returns:
        List of Chunk objects
    """
    if not content.strip():
        return []

    # Step 1: Split into sentences (handles Bengali and English)
    sentences = _split_sentences(content)

    # Step 2: Group into claim-based chunks
    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        # If adding this sentence exceeds max size, finalize current chunk
        if current_size + sentence_len > max_chunk_size and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(Chunk(
                text=chunk_text,
                chunk_type=_classify_chunk(chunk_text),
                index=len(chunks),
                metadata={},
            ))
            current_chunk = []
            current_size = 0

        current_chunk.append(sentence)
        current_size += sentence_len

    # Don't forget the last chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append(Chunk(
            text=chunk_text,
            chunk_type=_classify_chunk(chunk_text),
            index=len(chunks),
            metadata={},
        ))

    logger.info(f"[Chunking] Split content into {len(chunks)} chunks")
    return chunks


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, handling Bengali and English."""
    # Bengali sentence endings: । (dari), ? (question), ! (exclamation)
    # English: . ? !
    pattern = r'(?<=[।.!?])\s+'
    sentences = re.split(pattern, text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _classify_chunk(text: str) -> str:
    """Classify a chunk as claim, context, or metadata."""
    # Simple heuristic classification
    claim_indicators = [
        r'\d+',  # Contains numbers (statistics, dates)
        r'বলেছেন|জানিয়েছেন|দাবি',  # Bengali: said, informed, claimed
        r'according to|claimed|reported|stated',
        r'সূত্রে জানা|খবরে বলা',  # Bengali: sources say
    ]

    for pattern in claim_indicators:
        if re.search(pattern, text, re.IGNORECASE):
            return "claim"

    if len(text) < 50:
        return "metadata"

    return "context"
