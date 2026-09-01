"""
Per-user vector store built on FAISS + the embedding backend, plus a BM25
keyword index, combined for hybrid search. Index is rebuilt from the DB
whenever a user's document set changes -- fine at FYP/demo scale (hundreds
to low thousands of chunks). For production scale you'd move to incremental
upsert-capable stores (pgvector, Qdrant, etc.) -- noted in the README.
"""
import os
import pickle
from typing import List, Optional, Tuple

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models
from app.services.embeddings import get_embedding_backend


def _user_dir(user_id: int) -> str:
    path = os.path.join(settings.VECTOR_DIR, str(user_id))
    os.makedirs(path, exist_ok=True)
    return path


def rebuild_user_index(db: Session, user_id: int) -> int:
    """Refit embeddings + FAISS + BM25 over ALL of a user's chunks."""
    chunks = (
        db.query(models.Chunk)
        .filter(models.Chunk.owner_id == user_id)
        .order_by(models.Chunk.id.asc())
        .all()
    )
    user_dir = _user_dir(user_id)

    if not chunks:
        for fname in ("faiss.index", "backend.pkl", "bm25.pkl", "chunk_ids.pkl"):
            fp = os.path.join(user_dir, fname)
            if os.path.exists(fp):
                os.remove(fp)
        return 0

    texts = [c.content for c in chunks]
    chunk_ids = [c.id for c in chunks]

    backend = get_embedding_backend()
    dense_vectors = backend.fit(texts)

    index = faiss.IndexFlatIP(dense_vectors.shape[1])
    index.add(dense_vectors)

    tokenized = [t.lower().split() for t in texts]
    bm25 = BM25Okapi(tokenized)

    for row, chunk in enumerate(chunks):
        chunk.vector_row = row
    db.commit()

    faiss.write_index(index, os.path.join(user_dir, "faiss.index"))
    with open(os.path.join(user_dir, "backend.pkl"), "wb") as f:
        pickle.dump(backend, f)
    with open(os.path.join(user_dir, "bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)
    with open(os.path.join(user_dir, "chunk_ids.pkl"), "wb") as f:
        pickle.dump(chunk_ids, f)

    return len(chunks)


def _load_user_index(user_id: int):
    user_dir = _user_dir(user_id)
    paths = {
        "index": os.path.join(user_dir, "faiss.index"),
        "backend": os.path.join(user_dir, "backend.pkl"),
        "bm25": os.path.join(user_dir, "bm25.pkl"),
        "chunk_ids": os.path.join(user_dir, "chunk_ids.pkl"),
    }
    if not all(os.path.exists(p) for p in paths.values()):
        return None

    index = faiss.read_index(paths["index"])
    with open(paths["backend"], "rb") as f:
        backend = pickle.load(f)
    with open(paths["bm25"], "rb") as f:
        bm25 = pickle.load(f)
    with open(paths["chunk_ids"], "rb") as f:
        chunk_ids = pickle.load(f)
    return {"index": index, "backend": backend, "bm25": bm25, "chunk_ids": chunk_ids}


def _minmax(scores: np.ndarray) -> np.ndarray:
    if scores.size == 0:
        return scores
    lo, hi = scores.min(), scores.max()
    if hi - lo < 1e-9:
        return np.zeros_like(scores)
    return (scores - lo) / (hi - lo)


def search(
    db: Session,
    user_id: int,
    query: str,
    top_k: int = 5,
    mode: str = "hybrid",
    document_ids: Optional[List[int]] = None,
) -> List[Tuple[int, float]]:
    """Returns list of (chunk_id, score) sorted descending by score."""
    state = _load_user_index(user_id)
    if state is None:
        return []

    chunk_ids = state["chunk_ids"]
    n = len(chunk_ids)

    vector_scores = np.zeros(n, dtype="float32")
    keyword_scores = np.zeros(n, dtype="float32")

    if mode in ("vector", "hybrid"):
        q_vec = state["backend"].embed_query(query).reshape(1, -1)
        k = min(n, max(top_k * 4, top_k))
        scores, idxs = state["index"].search(q_vec, k)
        for score, idx in zip(scores[0], idxs[0]):
            if idx != -1:
                vector_scores[idx] = score

    if mode in ("keyword", "hybrid"):
        tokenized_query = query.lower().split()
        raw = np.array(state["bm25"].get_scores(tokenized_query), dtype="float32")
        keyword_scores = raw

    v = _minmax(vector_scores)
    k = _minmax(keyword_scores)

    if mode == "vector":
        combined = v
    elif mode == "keyword":
        combined = k
    else:  # hybrid: weighted blend, vector slightly favoured for semantic matches
        combined = 0.6 * v + 0.4 * k

    # optional filter to specific documents
    allowed_rows = None
    if document_ids:
        chunk_id_to_doc = {
            c.id: c.document_id
            for c in db.query(models.Chunk).filter(models.Chunk.id.in_(chunk_ids)).all()
        }
        allowed_rows = {
            row for row, cid in enumerate(chunk_ids) if chunk_id_to_doc.get(cid) in document_ids
        }

    ranked_rows = np.argsort(-combined)
    results = []
    for row in ranked_rows:
        if allowed_rows is not None and row not in allowed_rows:
            continue
        results.append((chunk_ids[row], float(combined[row])))
        if len(results) >= top_k:
            break
    return results
