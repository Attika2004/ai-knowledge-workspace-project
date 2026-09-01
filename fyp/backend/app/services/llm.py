
from typing import List, Optional

from app.core.config import settings

_client = None
_provider = None


def get_client():
    """Returns (client, provider) -- provider is 'groq' or 'anthropic'."""
    global _client, _provider
    if _client is not None:
        return _client, _provider

    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        if not settings.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
                "and add it to backend/.env"
            )
        from openai import OpenAI

        _client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        _provider = "groq"
    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to backend/.env to enable chat."
            )
        import anthropic

        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        _provider = "anthropic"
    else:
        raise RuntimeError(f"Unknown LLM_PROVIDER: {provider!r} (use 'groq' or 'anthropic')")

    return _client, _provider


def rag_answer(question: str, context_chunks: List[str], history: List[dict]) -> str:
    context = "\n\n---\n\n".join(context_chunks) if context_chunks else "(no relevant context found)"
    system = (
        "You are a helpful assistant embedded in a document-QA app. Answer the "
        "user's question using ONLY the provided context when it is relevant. "
        "If the context doesn't contain the answer, say so plainly instead of "
        "guessing. Keep answers concise and cite which excerpt you used when helpful."
    )
    user_content = f"Context:\n{context}\n\nQuestion: {question}"
    client, provider = get_client()

    if provider == "groq":
        messages = [{"role": "system", "content": system}] + history + [
            {"role": "user", "content": user_content}
        ]
        resp = client.chat.completions.create(
            model=settings.LLM_MODEL,
            max_tokens=1024,
            messages=messages,
        )
        return resp.choices[0].message.content

    # anthropic
    messages = history + [{"role": "user", "content": user_content}]
    resp = client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    return "".join(block.text for block in resp.content if block.type == "text")
