"""Extract text from uploaded files and split into overlapping chunks."""
import os
from typing import List

from pypdf import PdfReader
from docx import Document as DocxDocument

from app.core.config import settings


def extract_text(filepath: str, filetype: str) -> str:
    filetype = filetype.lower()
    if filetype == "pdf":
        reader = PdfReader(filepath)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if filetype in ("docx",):
        doc = DocxDocument(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    if filetype in ("txt", "md"):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    raise ValueError(f"Unsupported file type: {filetype}")


def chunk_text(
    text: str,
    chunk_size: int = None,
    overlap: int = None,
) -> List[str]:
    """Simple sliding-window chunker over words (keeps things dependency-free)."""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    step = max(chunk_size - overlap, 1)
    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunk = " ".join(chunk_words).strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks
