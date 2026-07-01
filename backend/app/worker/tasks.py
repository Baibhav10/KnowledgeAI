"""
Celery tasks for document processing.
Each task receives a document_id and processes it through the pipeline:
1. Extract text from the file
2. Chunk the text
3. Generate embeddings
4. Store in pgvector
Steps 2-4 are stubbed for now — we'll fill them in Phase 3c and 3d.
"""
import logging
from app.worker.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str):
    """
    Main document processing pipeline.
    bind=True gives us access to `self` so we can retry on failure.
    max_retries=3 means Celery will retry up to 3 times before marking as failed.
    """
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error("Document %s not found", document_id)
            return

        # Mark as processing
        document.status = "processing"
        db.commit()
        logger.info("Processing document %s (%s)", document_id, document.file_type)

        # TODO Phase 3c: extract text and chunk it
        # TODO Phase 3d: generate embeddings and store in pgvector

        # Mark as completed for now
        document.status = "completed"
        db.commit()
        logger.info("Document %s completed", document_id)

    except Exception as exc:
        document.status = "failed"
        document.error_message = str(exc)
        db.commit()
        logger.error("Document %s failed: %s", document_id, exc)
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()