"""
Conversation management endpoints.
Each conversation is scoped to one document and one user.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document
from app.schemas.conversation import ConversationCreate, ConversationResponse, MessageResponse

router = APIRouter()


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify document belongs to user's org
    document = db.query(Document).filter(
        Document.id == payload.document_id,
        Document.organization_id == current_user.organization_id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    conversation = Conversation(
        title=payload.title,
        document_id=payload.document_id,
        user_id=current_user.id,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        document_id=str(conversation.document_id),
        document_name=document.name,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[],
    )


@router.get("/", response_model=list[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id,
    ).order_by(Conversation.updated_at.desc()).all()

    return [
        ConversationResponse(
            id=str(c.id),
            title=c.title,
            document_id=str(c.document_id),
            document_name=c.document.name,
            created_at=c.created_at,
            updated_at=c.updated_at,
            messages=[
                MessageResponse(
                    id=str(m.id),
                    role=m.role,
                    content=m.content,
                    created_at=m.created_at,
                )
                for m in c.messages
            ],
        )
        for c in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        document_id=str(conversation.document_id),
        document_name=conversation.document.name,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageResponse(
                id=str(m.id),
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in conversation.messages
        ],
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.query(Message).filter(Message.conversation_id == conversation.id).delete()
    db.delete(conversation)
    db.commit()