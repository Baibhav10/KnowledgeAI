"""
RAG chat endpoint with streaming responses.
Flow:
1. Convert question to embedding
2. Find top N relevant chunks from pgvector
3. Build a prompt with those chunks as context
4. Stream Llama 3.2's response back to the client via SSE
5. Include citations showing which documents were used
"""
import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.embedder import generate_embedding
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest
import ollama

router = APIRouter()
logger = logging.getLogger(__name__)


def retrieve_chunks(query: str, org_id: str, limit: int, db: Session) -> list[dict]:
    """Find the most relevant chunks for a query using vector similarity."""
    query_embedding = generate_embedding(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

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
            "org_id": org_id,
            "limit": limit,
        }
    ).fetchall()

    return [
        {
            "chunk_id": str(row.chunk_id),
            "document_id": str(row.document_id),
            "document_name": row.document_name,
            "chunk_index": row.chunk_index,
            "text": row.text,
            "similarity": round(float(row.similarity), 4),
        }
        for row in results
    ]


def build_prompt(question: str, chunks: list[dict]) -> str:
    """Build a RAG prompt with retrieved context."""
    if not chunks:
        return f"""You are a helpful assistant. No relevant documents were found for this question.
Please let the user know you couldn't find relevant information in their knowledge base.

Question: {question}"""

    context = "\n\n".join([
        f"[Source: {c['document_name']}, chunk {c['chunk_index']}]\n{c['text']}"
        for c in chunks
    ])

    return f"""You are a helpful assistant that answers questions based on the provided documents.
Use ONLY the information from the documents below to answer the question.
If the answer isn't in the documents, say so clearly.
At the end of your answer, list the sources you used.

Documents:
{context}

Question: {question}

Answer:"""


@router.post("/")
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    def stream():
        # Retrieve relevant chunks
        chunks = retrieve_chunks(
            query=payload.question,
            org_id=str(current_user.organization_id),
            limit=payload.limit,
            db=db,
        )
        logger.info(
            "Retrieved %d chunks for question: %s",
            len(chunks), payload.question
        )

        # Send citations first as a structured JSON event
        citations = [
            {"document_name": c["document_name"], "similarity": c["similarity"]}
            for c in chunks
        ]
        yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"

        # Build prompt and stream LLM response
        prompt = build_prompt(payload.question, chunks)

        for chunk in ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        ):
            content = chunk["message"]["content"]
            yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")