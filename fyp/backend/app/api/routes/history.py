from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db import models
from app.schemas.schemas import ConversationOut, ConversationDetail

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.Conversation)
        .filter(models.Conversation.owner_id == current_user.id)
        .order_by(models.Conversation.created_at.desc())
        .all()
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    convo = (
        db.query(models.Conversation)
        .filter(models.Conversation.id == conversation_id, models.Conversation.owner_id == current_user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    convo = (
        db.query(models.Conversation)
        .filter(models.Conversation.id == conversation_id, models.Conversation.owner_id == current_user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(convo)
    db.commit()
    return {"ok": True}
