"""
LangSmith tracing setup.

LangSmith works almost entirely through environment variables -- once these
are set, every LangChain/LangGraph call (langchain_rag.rag_answer,
langgraph_agent.run_agent) is automatically traced with no code changes
needed in those files. This module just validates the setup at import time
so you get a clear error instead of silent no-op tracing if you forget a
key.

Import this once at app startup (e.g. top of app/main.py):
    from app.services import tracing  # noqa: F401
"""
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