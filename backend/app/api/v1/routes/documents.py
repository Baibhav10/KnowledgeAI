"""
Document upload endpoint.
Accepts a file, saves it to disk, creates a DB record with
status='pending', then hands off to Celery for processing.
Returns immediately — the user doesn't wait for processing to finish.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import save_upload
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.worker.tasks import process_document

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate file type
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save file to disk
    file_path, file_type = save_upload(file)

    # Create DB record
    document = Document(
        name=file.filename,
        file_path=file_path,
        file_type=file_type,
        status="pending",
        organization_id=current_user.organization_id,
        uploaded_by=current_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    process_document.delay(str(document.id))

    return DocumentResponse(
        id=str(document.id),
        name=document.name,
        file_type=document.file_type,
        status=document.status,
        created_at=document.created_at,
    )

@router.get("/", response_model=list[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs = db.query(Document)\
        .filter(Document.organization_id == current_user.organization_id)\
        .order_by(Document.created_at.desc())\
        .all()
    return [
        DocumentResponse(
            id=str(d.id),
            name=d.name,
            file_type=d.file_type,
            status=d.status,
            created_at=d.created_at,
        )
        for d in docs
    ]