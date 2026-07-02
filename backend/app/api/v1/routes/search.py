"""
Vector similarity search endpoint.
Takes a query string, converts it to an embedding,
and returns the most semantically similar chunks from pgvector.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_db
from app.core.embedder import generate_embedding
from app.api.v1.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class ChunkResult(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    chunk_index: int
    text: str
    similarity: float


class SearchResponse(BaseModel):
    query: str
    results: list[ChunkResult]


@router.post("", response_model=SearchResponse)
def search(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Generate embedding for the query
    query_embedding = generate_embedding(payload.query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # Vector similarity search scoped to the user's organization
    # <=> is pgvector's cosine distance operator (lower = more similar)
    # 1 - distance = similarity score
    results = db.execute(
        text("""
            SELECT
                c.id AS chunk_id,
                c.document_id,
                d.name AS document_name,
                c.chunk_index,
                c.text,
                1 - (c.embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.organization_id = :org_id
              AND d.status = 'completed'
              AND c.embedding IS NOT NULL
            ORDER BY c.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """),
        {
            "embedding": embedding_str,
            "org_id": str(current_user.organization_id),
            "limit": payload.limit,
        }
    ).fetchall()

    return SearchResponse(
        query=payload.query,
        results=[
            ChunkResult(
                chunk_id=str(row.chunk_id),
                document_id=str(row.document_id),
                document_name=row.document_name,
                chunk_index=row.chunk_index,
                text=row.text,
                similarity=round(float(row.similarity), 4),
            )
            for row in results
        ]
    )