from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- Documents ---
class DocumentOut(BaseModel):
    id: int
    filename: str
    filetype: str
    num_chunks: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Chat ---
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    document_ids: Optional[List[int]] = None  # restrict RAG to specific docs
    use_agent: bool = False


class Citation(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    snippet: str
    score: float


class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    citations: List[Citation] = []
    tool_calls: List[str] = []


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationOut):
    messages: List[MessageOut] = []


# --- Search ---
class SearchRequest(BaseModel):
    query: str
    mode: str = "hybrid"  # keyword | vector | hybrid
    top_k: int = 5


class SearchResultItem(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    content: str
    score: float
