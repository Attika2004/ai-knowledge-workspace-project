import os
import shutil
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.db import models
from app.schemas.schemas import DocumentOut
from app.services.document_processor import extract_text, chunk_text
from app.services import vector_store

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}


def _process_document(doc_id: int, user_id: int):
    """Runs in the background: extract text, chunk it, rebuild the user's index."""
    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        doc = db.query(models.Document).get(doc_id)
        if not doc:
            return
        try:
            text = extract_text(doc.filepath, doc.filetype)
            chunks = chunk_text(text)
            if not chunks:
                doc.status = "failed"
                db.commit()
                return
            for i, content in enumerate(chunks):
                db.add(
                    models.Chunk(
                        document_id=doc.id,
                        owner_id=user_id,
                        chunk_index=i,
                        content=content,
                    )
                )
            doc.num_chunks = len(chunks)
            doc.status = "ready"
            db.commit()
            vector_store.rebuild_user_index(db, user_id)
        except Exception:
            doc.status = "failed"
            db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=DocumentOut)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    user_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(user_dir, safe_name)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = models.Document(
        owner_id=current_user.id,
        filename=file.filename,
        filepath=filepath,
        filetype=ext,
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(_process_document, doc.id, current_user.id)
    return doc


@router.get("", response_model=List[DocumentOut])
def list_documents(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.Document)
        .filter(models.Document.owner_id == current_user.id)
        .order_by(models.Document.created_at.desc())
        .all()
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = (
        db.query(models.Document)
        .filter(models.Document.id == document_id, models.Document.owner_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(doc.filepath):
        os.remove(doc.filepath)
    db.delete(doc)
    db.commit()
    vector_store.rebuild_user_index(db, current_user.id)
    return {"ok": True}
