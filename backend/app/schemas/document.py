from pydantic import BaseModel
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    name: str
    file_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True