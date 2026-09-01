"""
LangChain-based RAG pipeline. Drop-in replacement for llm.rag_answer():
same signature, same return type, so chat.py needs only a one-line import
swap to use this instead.

Wraps the existing Groq/Anthropic clients (via LangChain's ChatOpenAI /
ChatAnthropic wrappers) and builds the prompt with an LCEL chain instead of
hand-formatting a string, which is what "using LangChain for the RAG
pipeline" means in practice for a chat-completions-style backend (no
vectorstore retriever plugged in here since you already have a hybrid
FAISS+BM25 retriever in vector_store.py -- that stays as-is and just feeds
context_chunks into this chain, same as it fed llm.rag_answer() before).
"""
from typing import List

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from app.core.config import settings

_chain = None
_provider = None


def _build_chain():
    global _chain, _provider
    if _chain is not None:
        return _chain, _provider

    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            max_tokens=1024,
        )
        _provider = "groq"
    elif provider == "ollama":
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key="ollama",
            base_url="http://localhost:11434/v1",
            max_tokens=1024,
        )
        _provider = "ollama"
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(
            model=settings.LLM_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=1024,
        )
        _provider = "anthropic"
    else:
        raise RuntimeError(f"Unknown LLM_PROVIDER: {provider!r}")

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant embedded in a document-QA app. "
                "Answer the user's question using ONLY the provided context "
                "when it is relevant. If the context doesn't contain the "
                "answer, say so plainly instead of guessing. Keep answers "
                "concise and cite which excerpt you used when helpful.\n\n"
                "Context:\n{context}",
            ),
            MessagesPlaceholder("history"),
            ("human", "{question}"),
        ]
    )

    _chain = prompt | llm | StrOutputParser()
    return _chain, _provider


def _to_lc_messages(history: List[dict]):
    out = []
    for m in history:
        if m["role"] == "user":
            out.append(HumanMessage(content=m["content"]))
        else:
            out.append(AIMessage(content=m["content"]))
    return out


def rag_answer(question: str, context_chunks: List[str], history: List[dict]) -> str:
    """Same signature as llm.rag_answer() -- swap the import in chat.py to use this."""
    chain, _ = _build_chain()
    context = "\n\n---\n\n".join(context_chunks) if context_chunks else "(no relevant context found)"
    return chain.invoke(
        {
            "context": context,
            "history": _to_lc_messages(history),
            "question": question,
        }
    )
