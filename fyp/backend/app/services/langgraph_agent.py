
import ast
import operator
from typing import Annotated, List, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services import vector_store
from app.db import models

# --- Safe calculator (reused from agent.py, no eval()) ---
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


SYSTEM_PROMPT = (
    "You are an assistant with access to tools. Use `document_search` "
    "to look things up in the user's uploaded files and `calculator` "
    "for any arithmetic. Only call a tool when it's actually needed."
)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    tool_calls_made: List[str]


def _make_tools(db: Session, user_id: int):
    @tool
    def calculator(expression: str) -> str:
        """Evaluate a basic arithmetic expression, e.g. (12+8)*3/2"""
        try:
            tree = ast.parse(expression, mode="eval").body
            return str(_safe_eval(tree))
        except Exception as e:
            return f"Error evaluating expression: {e}"

    @tool
    def document_search(query: str) -> str:
        """Search the user's uploaded documents for relevant passages."""
        results = vector_store.search(db, user_id, query, top_k=3, mode="hybrid")
        if not results:
            return "No matching documents found."
        out = []
        for chunk_id, score in results:
            chunk = db.query(models.Chunk).get(chunk_id)
            if chunk:
                out.append(f"[score={score:.2f}] {chunk.content[:300]}")
        return "\n\n".join(out) if out else "No matching documents found."

    return [calculator, document_search]


def _get_chat_model():
    provider = settings.LLM_PROVIDER.lower()
    if provider == "groq":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            max_tokens=1024,
        )
    if provider == "ollama":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key="ollama",
            base_url="http://localhost:11434/v1",
            max_tokens=1024,
        )
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.LLM_MODEL, api_key=settings.ANTHROPIC_API_KEY, max_tokens=1024
        )
    raise RuntimeError(f"Unknown LLM_PROVIDER: {provider!r}")


def _build_graph(db: Session, user_id: int):
    tools = _make_tools(db, user_id)
    llm = _get_chat_model().bind_tools(tools)
    tools_by_name = {t.name: t for t in tools}

    def agent_node(state: AgentState):
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    def tools_node(state: AgentState):
        last = state["messages"][-1]
        outputs = []
        calls_made = []
        for call in last.tool_calls:
            result = tools_by_name[call["name"]].invoke(call["args"])
            outputs.append(
                ToolMessage(content=str(result), tool_call_id=call["id"], name=call["name"])
            )
            calls_made.append(f"{call['name']}({call['args']})")
        return {"messages": outputs, "tool_calls_made": calls_made}

    def should_continue(state: AgentState):
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


def _to_lc_messages(history: List[dict]):
    out = []
    for m in history:
        if m["role"] == "user":
            out.append(HumanMessage(content=m["content"]))
        else:
            out.append(AIMessage(content=m["content"]))
    return out


def run_agent(db: Session, user_id: int, question: str, history: List[dict]):
    """Same signature as agent.run_agent() -- swap the import in chat.py to use this."""
    app = _build_graph(db, user_id)

    initial_messages = (
        [SystemMessage(content=SYSTEM_PROMPT)]
        + _to_lc_messages(history)
        + [HumanMessage(content=question)]
    )

    tool_calls_made: List[str] = []
    final_state = None
    # Recursion limit doubles as the "4 iterations max" cap from the original agent.py
    for step in app.stream(
        {"messages": initial_messages, "tool_calls_made": []},
        {"recursion_limit": 10},
        stream_mode="values",
    ):
        final_state = step
        if "tool_calls_made" in step and step["tool_calls_made"]:
            tool_calls_made.extend(step["tool_calls_made"])

    if final_state is None:
        return "I wasn't able to process that -- please try again.", tool_calls_made

    last_message = final_state["messages"][-1]
    answer = last_message.content if isinstance(last_message, AIMessage) else str(last_message.content)
    return answer, tool_calls_made
