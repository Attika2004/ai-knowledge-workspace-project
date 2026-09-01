"""
Evaluation endpoint: latency/citation tracking (as before) PLUS retrieval
quality metrics via RAGAS -- faithfulness (is the answer actually
grounded in the retrieved context?) and context relevancy (did we
retrieve the right chunks for the question?). This replaces the
"swap in RAGAS / LangSmith / W&B once you get there" placeholder that was
in the original version of this file.

RAGAS metrics need an LLM to act as judge -- reuses whichever provider is
already configured (LLM_PROVIDER) so no extra API key is required.
"""
import time
from collections import deque
from typing import Deque, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.db import models

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])

# in-memory ring buffer of recent request metrics (per-process; fine for a demo)
_METRICS: Deque[Dict] = deque(maxlen=200)
_RAGAS_SCORES: Deque[Dict] = deque(maxlen=50)


def log_metric(user_id: int, kind: str, latency_ms: float, num_citations: int = 0):
    _METRICS.append(
        {
            "user_id": user_id,
            "kind": kind,
            "latency_ms": round(latency_ms, 1),
            "num_citations": num_citations,
            "ts": time.time(),
        }
    )


@router.get("/summary")
def summary(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    own = [m for m in _METRICS if m["user_id"] == current_user.id]
    doc_count = (
        db.query(models.Document).filter(models.Document.owner_id == current_user.id).count()
    )
    chunk_count = (
        db.query(models.Chunk).filter(models.Chunk.owner_id == current_user.id).count()
    )
    convo_count = (
        db.query(models.Conversation).filter(models.Conversation.owner_id == current_user.id).count()
    )
    avg_latency = round(sum(m["latency_ms"] for m in own) / len(own), 1) if own else 0
    own_ragas = [r for r in _RAGAS_SCORES if r["user_id"] == current_user.id]
    avg_faithfulness = (
        round(sum(r["faithfulness"] for r in own_ragas) / len(own_ragas), 3) if own_ragas else None
    )
    avg_relevancy = (
        round(sum(r["context_relevancy"] for r in own_ragas) / len(own_ragas), 3) if own_ragas else None
    )
    return {
        "documents": doc_count,
        "chunks": chunk_count,
        "conversations": convo_count,
        "requests_tracked": len(own),
        "avg_latency_ms": avg_latency,
        "avg_faithfulness": avg_faithfulness,
        "avg_context_relevancy": avg_relevancy,
        "ragas_samples_scored": len(own_ragas),
        "recent": list(own)[-20:],
        "recent_ragas": list(own_ragas)[-10:],
    }


class RagasEvalRequest(BaseModel):
    question: str
    answer: str
    contexts: List[str]


@router.post("/ragas")
def evaluate_with_ragas(
    payload: RagasEvalRequest,
    current_user: models.User = Depends(get_current_user),
):
    """
    Scores one question/answer/context triple with RAGAS. Call this after
    a chat response if you want it logged for the dashboard above -- not
    called automatically on every request since RAGAS makes its own LLM
    calls and would double your token usage per chat message.
    """
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, context_relevancy
        from langchain_openai import ChatOpenAI
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        return {
            "error": (
                "ragas is not installed. Run: pip install ragas datasets "
                "(see backend/requirements.txt)"
            )
        }

    provider = settings.LLM_PROVIDER.lower()
    if provider in ("groq", "ollama"):
        base_url = (
            "https://api.groq.com/openai/v1"
            if provider == "groq"
            else "http://localhost:11434/v1"
        )
        api_key = settings.GROQ_API_KEY if provider == "groq" else "ollama"
        judge_llm = ChatOpenAI(model=settings.LLM_MODEL, api_key=api_key, base_url=base_url)
    else:
        judge_llm = ChatAnthropic(model=settings.LLM_MODEL, api_key=settings.ANTHROPIC_API_KEY)

    dataset = Dataset.from_dict(
        {
            "question": [payload.question],
            "answer": [payload.answer],
            "contexts": [payload.contexts],
        }
    )

    result = evaluate(dataset, metrics=[faithfulness, context_relevancy], llm=judge_llm)
    scores = result.to_pandas().iloc[0].to_dict()

    entry = {
        "user_id": current_user.id,
        "question": payload.question[:100],
        "faithfulness": round(float(scores.get("faithfulness", 0)), 3),
        "context_relevancy": round(float(scores.get("context_relevancy", 0)), 3),
        "ts": time.time(),
    }
    _RAGAS_SCORES.append(entry)
    return entry
