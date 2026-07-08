"""
RAG chat endpoint with streaming responses and conversation memory.
Full pipeline:
1. Convert question to embedding
2. Find top N relevant chunks from pgvector
3. Check similarity threshold — refuse if no good matches
4. Build system prompt with retrieved context
5. Append full conversation history
6. Stream Llama 3.2 response token by token
7. Send citations as first SSE event
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
from app.models.conversation import Conversation
from app.models.message import Message
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.3
MAX_HISTORY_TOKENS = 80000  # ~80k tokens, leave room for context and response
APPROX_TOKENS_PER_CHAR = 0.25  # rough estimate: 1 token ≈ 4 chars


def retrieve_chunks(query: str, org_id: str, limit: int, db: Session, previous_answer: str = "") -> list[dict]:
    # If the question is short/vague, enrich it with the previous answer for better retrieval
    search_query = query
    if len(query.split()) < 8 and previous_answer:
        search_query = f"{query} {previous_answer[:300]}"

    query_embedding = generate_embedding(search_query)
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

def estimate_tokens(messages: list[dict]) -> int:
    """Rough token estimate based on character count."""
    total_chars = sum(len(m.get("content", "")) for m in messages)
    return int(total_chars * APPROX_TOKENS_PER_CHAR)


def trim_history(messages: list[dict]) -> tuple[list[dict], bool]:
    """
    Trims oldest messages if approaching token limit.
    Returns (trimmed_messages, was_trimmed).
    Always keeps the system prompt (first message).
    """
    if estimate_tokens(messages) <= MAX_HISTORY_TOKENS:
        return messages, False

    system = messages[0]
    history = messages[1:]

    while len(history) > 2 and estimate_tokens([system] + history) > MAX_HISTORY_TOKENS:
        history = history[2:]  # remove oldest user+assistant pair

    return [system] + history, True


def build_system_prompt(chunks: list[dict]) -> str:
    if not chunks:
        return """You are a helpful assistant for a knowledge base system.
No relevant documents were found for this question.
Tell the user clearly that you couldn't find relevant information in their knowledge base.
Do not make up information."""

    context = "\n\n".join([
        f"[Source: {c['document_name']}, chunk {c['chunk_index']}]\n{c['text']}"
        for c in chunks
    ])

    return f"""You are a helpful assistant for a knowledge base system.
Answer questions using ONLY the document excerpts provided below.
If the answer isn't in the documents, say so clearly — do not make up information.
At the end of your answer, list the sources you used.

Document excerpts:
{context}"""


@router.post("/")
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    def stream():
        # Get previous answer for context-enriched retrieval
        previous_answer = ""
        if payload.messages:
            for msg in reversed(payload.messages):
                if msg.role == "assistant":
                    previous_answer = msg.content
                    break

        # Retrieve relevant chunks
        chunks = retrieve_chunks(
            query=payload.question,
            org_id=str(current_user.organization_id),
            limit=payload.limit,
            db=db,
            previous_answer=previous_answer,
        )
        logger.info("Retrieved %d chunks for question: %s", len(chunks), payload.question)

        # Similarity threshold check
        if chunks and chunks[0]["similarity"] < SIMILARITY_THRESHOLD:
            logger.info("Best similarity %.4f below threshold", chunks[0]["similarity"])
            chunks = []

        # Send citations
        citations = [
            {"document_name": c["document_name"], "similarity": c["similarity"]}
            for c in chunks
        ]
        yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"

        # Build messages for Ollama
        system_prompt = build_system_prompt(chunks)
        messages = [{"role": "system", "content": system_prompt}]
        for msg in payload.messages:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": payload.question})

        # Trim if approaching token limit
        messages, was_trimmed = trim_history(messages)
        if was_trimmed:
            yield f"data: {json.dumps({'type': 'trimmed'})}\n\n"

        current_tokens = estimate_tokens(messages)
        if current_tokens > (MAX_HISTORY_TOKENS * 0.8):
            yield f"data: {json.dumps({'type': 'approaching_limit'})}\n\n"

        # Stream response
        full_response = ""
        for chunk in ollama.chat(
            model="llama3.2",
            messages=messages,
            stream=True,
        ):
            content = chunk["message"]["content"]
            full_response += content
            yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

        # Save messages to database if conversation_id provided
        if payload.conversation_id:
            try:
                conversation = db.query(Conversation).filter(
                    Conversation.id == payload.conversation_id,
                    Conversation.user_id == current_user.id,
                ).first()
                if conversation:
                    db.add(Message(
                        conversation_id=conversation.id,
                        role="user",
                        content=payload.question,
                    ))
                    db.add(Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=full_response,
                    ))
                    conversation.updated_at = datetime.utcnow()
                    db.commit()
            except Exception as e:
                logger.error("Failed to save messages: %s", e)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")