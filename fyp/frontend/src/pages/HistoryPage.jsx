import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MessageCircle, Trash2 } from "lucide-react";
import client from "../api/client";

export default function HistoryPage() {
  const [conversations, setConversations] = useState([]);
  const navigate = useNavigate();

  const fetchAll = async () => {
    const { data } = await client.get("/history");
    setConversations(data);
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    await client.delete(`/history/${id}`);
    fetchAll();
  };

  return (
    <div className="p-8 max-w-3xl">
      <h2
        className="text-3xl text-ink mb-1"
        style={{ fontFamily: "var(--font-display)" }}
      >
        The Archives
      </h2>
      <p className="text-ink-soft text-sm mb-6">Past conversations, filed for later.</p>

      <div className="space-y-2">
        {conversations.length === 0 && (
          <p className="text-ink-soft text-sm italic">No conversations yet.</p>
        )}
        {conversations.map((c) => (
          <div
            key={c.id}
            onClick={() => navigate(`/chat?conversation_id=${c.id}`)}
            className="flex items-center justify-between bg-card border border-rule rounded-sm px-4 py-3 cursor-pointer hover:border-lamp transition-colors"
          >
            <div className="flex items-center gap-3 min-w-0">
              <MessageCircle size={16} className="text-ink-soft shrink-0" />
              <div className="min-w-0">
                <p className="text-sm truncate">{c.title}</p>
                <p className="text-xs text-ink-soft font-mono">
                  {new Date(c.created_at).toLocaleString()}
                </p>
              </div>
            </div>
            <button
              onClick={(e) => handleDelete(c.id, e)}
              className="text-ink-soft hover:text-danger transition-colors shrink-0"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
