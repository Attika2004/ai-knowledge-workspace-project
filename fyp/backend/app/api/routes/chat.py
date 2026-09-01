import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.db import models
from app.schemas.schemas import ChatRequest, ChatResponse, Citation
from app.services import vector_store
from app.services.langchain_rag import rag_answer  # was: app.services.llm
from app.services.langgraph_agent import run_agent  # was: app.services.agent
from app.api.routes.evaluation import log_metric

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _get_or_create_conversation(db: Session, user_id: int, conversation_id, first_message: str):
    if conversation_id:
        convo = (
            db.query(models.Conversation)
            .filter(models.Conversation.id == conversation_id, models.Conversation.owner_id == user_id)
            .first()
        )
        if convo:
            return convo
    convo = models.Conversation(owner_id=user_id, title=first_message[:60])
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def _history_for_anthropic(db: Session, conversation_id: int, limit: int = 10):
    msgs = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.created_at.asc())
        .limit(limit)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in msgs]


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    start = time.perf_counter()
    convo = _get_or_create_conversation(db, current_user.id, payload.conversation_id, payload.message)
    history = _history_for_anthropic(db, convo.id)

    db.add(models.Message(conversation_id=convo.id, role="user", content=payload.message))
    db.commit()

    tool_calls: list[str] = []

    try:
        if payload.use_agent:
            answer, tool_calls = run_agent(db, current_user.id, payload.message, history)
            citations: list[Citation] = []
        else:
            results = vector_store.search(
                db,
                current_user.id,
                payload.message,
                top_k=settings.TOP_K,
                mode="hybrid",
                document_ids=payload.document_ids,
            )
            context_chunks = []
            citations = []
            for chunk_id, score in results:
                chunk = db.query(models.Chunk).get(chunk_id)
                if not chunk:
                    continue
                doc = db.query(models.Document).get(chunk.document_id)
                context_chunks.append(chunk.content)
                citations.append(
                    Citation(
                        document_id=chunk.document_id,
                        filename=doc.filename if doc else "unknown",
                        chunk_index=chunk.chunk_index,
                        snippet=chunk.content[:200],
                        score=round(score, 3),
                    )
                )
            answer = rag_answer(payload.message, context_chunks, history)
    except RuntimeError as e:
        # missing/misconfigured API key -- surface a clean message
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # network errors, rate limits, provider outages, etc.
        raise HTTPException(
            status_code=502,
            detail=f"The language model provider returned an error: {e}",
        )

    db.add(models.Message(conversation_id=convo.id, role="assistant", content=answer))
    db.commit()

    elapsed_ms = (time.perf_counter() - start) * 1000
    log_metric(current_user.id, "agent" if payload.use_agent else "rag", elapsed_ms, len(citations))

    return ChatResponse(
        conversation_id=convo.id, answer=answer, citations=citations, tool_calls=tool_calls
    )