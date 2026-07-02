"""
Splits extracted text into overlapping chunks for embedding.

CHUNK_SIZE: max number of words per chunk.
CHUNK_OVERLAP: how many words to repeat between consecutive chunks.

Why overlap? If a key sentence falls at the boundary between two chunks,
overlap ensures it appears fully in at least one of them, so it won't
be missed during vector search.
"""
import logging

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500    # words
CHUNK_OVERLAP = 50  # words


def chunk_text(text: str) -> list[str]:
    """
    Splits text into overlapping word-based chunks.
    Returns a list of chunk strings.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP

    logger.info("Split text into %d chunks (%d words total)", len(chunks), len(words))
    return chunks