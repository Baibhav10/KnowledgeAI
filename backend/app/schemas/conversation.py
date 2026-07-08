from pydantic import BaseModel
from datetime import datetime


class ConversationCreate(BaseModel):
    document_id: str
    title: str = "New conversation"


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    id: str
    title: str
    document_id: str
    document_name: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []