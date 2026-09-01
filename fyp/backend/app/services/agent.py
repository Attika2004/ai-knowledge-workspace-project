
import ast
import operator
import json
from typing import Callable, List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services import vector_store
from app.services.llm import get_client

# --- Safe calculator (no eval()) ---
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator_tool(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval").body
        return str(_safe_eval(tree))
    except Exception as e:
        return f"Error evaluating expression: {e}"


def make_document_search_tool(db: Session, user_id: int) -> Callable[[str], str]:
    def _search(query: str) -> str:
        results = vector_store.search(db, user_id, query, top_k=3, mode="hybrid")
        if not results:
            return "No matching documents found."
        from app.db import models

        out = []
        for chunk_id, score in results:
            chunk = db.query(models.Chunk).get(chunk_id)
            if chunk:
                out.append(f"[score={score:.2f}] {chunk.content[:300]}")
        return "\n\n".join(out) if out else "No matching documents found."

    return _search


SYSTEM_PROMPT = (
    "You are an assistant with access to tools. Use `document_search` "
    "to look things up in the user's uploaded files and `calculator` "
    "for any arithmetic. Only call a tool when it's actually needed."
)

# Anthropic-style tool schema
ANTHROPIC_TOOLS = [
    {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression, e.g. (12+8)*3/2",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
    {
        "name": "document_search",
        "description": "Search the user's uploaded documents for relevant passages.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]

# OpenAI/Groq-style function-calling schema
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["input_schema"],
        },
    }
    for t in ANTHROPIC_TOOLS
]


def run_agent(db: Session, user_id: int, question: str, history: List[dict]):
    """Runs a short tool-use loop and returns (final_answer, tool_calls_made)."""
    client, provider = get_client()
    tool_impls = {
        "calculator": lambda inp: calculator_tool(inp["expression"]),
        "document_search": lambda inp: make_document_search_tool(db, user_id)(inp["query"]),
    }
    tool_calls_made: List[str] = []

    if provider == "groq":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
            {"role": "user", "content": question}
        ]
        for _ in range(4):
            resp = client.chat.completions.create(
                model=settings.LLM_MODEL,
                max_tokens=1024,
                messages=messages,
                tools=OPENAI_TOOLS,
            )
            msg = resp.choices[0].message
            if not msg.tool_calls:
                return msg.content or "", tool_calls_made

            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
                }
            )
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                tool_calls_made.append(f"{tc.function.name}({tc.function.arguments})")
                result = tool_impls[tc.function.name](args)
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": str(result)}
                )
        return (
            "I wasn't able to finish using my tools in time -- please rephrase your question.",
            tool_calls_made,
        )

    # anthropic
    messages = history + [{"role": "user", "content": question}]
    for _ in range(4):
        resp = client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=ANTHROPIC_TOOLS,
            messages=messages,
        )
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text"), tool_calls_made

        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                tool_calls_made.append(f"{block.name}({json.dumps(block.input)})")
                result = tool_impls[block.name](block.input)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": str(result)}
                )
        messages.append({"role": "user", "content": tool_results})

    return (
        "I wasn't able to finish using my tools in time -- please rephrase your question.",
        tool_calls_made,
    )
