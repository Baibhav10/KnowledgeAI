"""
Celery tasks for document processing.
Full pipeline: extract text → chunk → embed → store in pgvector.
"""
import logging
from app.worker.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.extractor import extract_text
from app.core.chunker import chunk_text
from app.core.embedder import generate_embeddings_batch
from app.models.document import Document
from app.models.chunk import Chunk

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error("Document %s not found", document_id)
            return

        document.status = "processing"
        db.commit()
        logger.info("Processing document %s (%s)", document_id, document.file_type)

        # Extract text
        text = extract_text(document.file_path, document.file_type)
        logger.info("Extracted %d characters from document %s", len(text), document_id)

        # Chunk text
        chunks = chunk_text(text)
        logger.info("Created %d chunks for document %s", len(chunks), document_id)

        # Generate embeddings in batch
        logger.info("Generating embeddings for %d chunks", len(chunks))
        embeddings = generate_embeddings_batch(chunks)
        logger.info("Embeddings generated successfully")

        # Save chunks with embeddings to database
        for index, (chunk_text_content, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = Chunk(
                document_id=document.id,
                chunk_index=index,
                text=chunk_text_content,
                embedding=embedding,
            )
            db.add(chunk)

        db.commit()

        document.status = "completed"
        db.commit()
        logger.info("Document %s completed with %d chunks and embeddings", document_id, len(chunks))

    except Exception as exc:
        document.status = "failed"
        document.error_message = str(exc)
        db.commit()
        logger.error("Document %s failed: %s", document_id, exc)
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()