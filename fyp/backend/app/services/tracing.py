
import os

from app.core.config import settings

if settings.LANGCHAIN_TRACING_V2:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT or "ai-knowledge-workspace"
    if not settings.LANGCHAIN_API_KEY:
        raise RuntimeError(
            "LANGCHAIN_TRACING_V2=true but LANGCHAIN_API_KEY is not set. "
            "Get a free key at https://smith.langchain.com and add it to backend/.env"
        )
