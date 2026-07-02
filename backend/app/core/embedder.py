"""
Generates vector embeddings using a local sentence-transformers model.
We use 'all-MiniLM-L6-v2' because it's:
- Small (~90MB download)
- Fast on CPU
- Produces 384-dimensional vectors (matches our pgvector column)
- Good enough quality for a portfolio RAG system

The model is loaded once at module level so it's not reloaded
on every task — Celery workers are long-running processes.
"""
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"

logger.info("Loading embedding model: %s", MODEL_NAME)
model = SentenceTransformer(MODEL_NAME)
logger.info("Embedding model loaded successfully")


def generate_embedding(text: str) -> list[float]:
    """
    Returns a 384-dimensional embedding vector for the given text.
    """
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generates embeddings for multiple texts at once.
    Batch processing is significantly faster than one at a time.
    """
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [e.tolist() for e in embeddings]