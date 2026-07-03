from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    limit: int = 5  # number of chunks to retrieve