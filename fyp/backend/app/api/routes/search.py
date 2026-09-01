from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db import models
from app.schemas.schemas import SearchRequest, SearchResultItem
from app.services import vector_store

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=list[SearchResultItem])
def search(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    results = vector_store.search(
        db, current_user.id, payload.query, top_k=payload.top_k, mode=payload.mode
    )
    items = []
    for chunk_id, score in results:
        chunk = db.query(models.Chunk).get(chunk_id)
        if not chunk:
            continue
        doc = db.query(models.Document).get(chunk.document_id)
        items.append(
            SearchResultItem(
                document_id=chunk.document_id,
                filename=doc.filename if doc else "unknown",
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=round(score, 3),
            )
        )
    return items
