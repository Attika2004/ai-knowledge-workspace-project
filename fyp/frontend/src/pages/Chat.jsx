import { useEffect, useRef, useState } from "react";
import { Send, Sparkles, Wrench } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import client from "../api/client";

function CitationTab({ citation, index }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-block mr-1">
      <button className="catalog-tab" onClick={() => setOpen((o) => !o)}>
        {index}
      </button>
      {open && (
        <div className="absolute z-10 left-0 top-6 w-72 bg-card border border-brass rounded-sm shadow-lg p-3 text-left">
          <p className="text-xs font-mono text-lamp-dark mb-1">
            {citation.filename} · chunk {citation.chunk_index} · score {citation.score}
          </p>
          <p className="text-sm text-ink-soft leading-snug">{citation.snippet}…</p>
        </div>
      )}
    </span>
  );
}

function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-2xl px-4 py-3 rounded-sm text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-lamp text-paper"
            : "bg-card border border-rule text-ink"
        }`}
      >
        {msg.content}
        {msg.tool_calls?.length > 0 && (
          <div className="mt-2 pt-2 border-t border-rule/50 flex flex-wrap gap-1.5">
            {msg.tool_calls.map((t, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 text-xs font-mono text-brass bg-brass/10 border border-brass/30 px-1.5 py-0.5 rounded-sm"
              >
                <Wrench size={11} /> {t}
              </span>
            ))}
          </div>
        )}
        {msg.citations?.length > 0 && (
          <div className="mt-2 pt-2 border-t border-rule/50">
            {msg.citations.map((c, i) => (
              <CitationTab key={i} citation={c} index={i + 1} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chat() {
  const [params] = useSearchParams();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState(
    params.get("conversation_id") ? Number(params.get("conversation_id")) : null
  );
  const [useAgent, setUseAgent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef();

  useEffect(() => {
    const convoId = params.get("conversation_id");
    if (convoId) {
      client.get(`/history/${convoId}`).then(({ data }) => {
        setConversationId(data.id);
        setMessages(
          data.messages.map((m) => ({ role: m.role, content: m.content }))
        );
      });
    }
  }, [params]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const question = input;
    setInput("");
    setError("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);
    try {
      const { data } = await client.post("/chat", {
        message: question,
        conversation_id: conversationId,
        use_agent: useAgent,
      });
      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          citations: data.citations,
          tool_calls: data.tool_calls,
        },
      ]);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Something went wrong reaching the assistant. Is GROQ_API_KEY (or ANTHROPIC_API_KEY) set in backend/.env?"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <div className="px-8 py-5 border-b border-rule flex items-center justify-between">
        <div>
          <h2
            className="text-2xl text-ink"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Reading Room
          </h2>
          <p className="text-xs text-ink-soft font-mono">
            {useAgent ? "agent mode · tools enabled" : "grounded in your uploaded documents"}
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer select-none">
          <Sparkles size={15} className={useAgent ? "text-brass" : ""} />
          Agent mode
          <input
            type="checkbox"
            checked={useAgent}
            onChange={(e) => setUseAgent(e.target.checked)}
            className="accent-lamp"
          />
        </label>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        {messages.length === 0 && (
          <div className="text-ink-soft text-sm italic max-w-lg">
            Ask a question about what's in the stacks — or flip on agent mode
            to let the assistant use tools (document search, calculator) on
            its own to answer.
          </div>
        )}
        {messages.map((m, i) => (
          <Message key={i} msg={m} />
        ))}
        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="mx-8 mb-2 text-sm text-danger border border-danger/30 bg-danger/5 px-3 py-2 rounded-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSend} className="p-6 border-t border-rule flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your documents…"
          className="flex-1 px-4 py-3 border border-rule rounded-sm bg-card focus:outline-none focus:ring-2 focus:ring-lamp"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-lamp hover:bg-lamp-dark text-paper px-5 rounded-sm transition-colors disabled:opacity-60 flex items-center gap-2"
        >
          <Send size={16} />
          {loading ? "Thinking…" : "Send"}
        </button>
      </form>
    </div>
  );
}
