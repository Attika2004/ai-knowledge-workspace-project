import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    LLM_PROVIDER: str = "groq"  # "groq" (free), "ollama" (free, local), or "anthropic" (paid)
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    DATABASE_URL: str = "sqlite:///./app.db"
    UPLOAD_DIR: str = "uploads"
    VECTOR_DIR: str = "vector_data"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K: int = 5

    # LangSmith tracing (optional -- leave LANGCHAIN_TRACING_V2=false to skip)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "ai-knowledge-workspace"

    # Embeddings: "sentence-transformers" (default, HF/PyTorch, local) or "tfidf" (fallback)
    EMBEDDING_BACKEND: str = "sentence-transformers"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_DIR, exist_ok=True)
