from pydantic import BaseModel
from typing import Optional


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    messages: list[ChatMessage] = []
    limit: int = 5
    conversation_id: Optional[str] = None