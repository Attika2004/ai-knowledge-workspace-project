import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, Layers, MessagesSquare, MessageSquare, FileStack, Search } from "lucide-react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

function QuickLink({ to, icon: Icon, label, desc }) {
  return (
    <Link
      to={to}
      className="flex items-start gap-3 bg-card border border-rule rounded-sm p-4 hover:border-lamp transition-colors"
    >
      <div className="text-lamp-dark bg-lamp/10 p-2 rounded-sm shrink-0">
        <Icon size={18} strokeWidth={1.75} />
      </div>
      <div>
        <p className="text-sm">{label}</p>
        <p className="text-xs text-ink-soft mt-0.5">{desc}</p>
      </div>
    </Link>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    client.get("/evaluation/summary").then(({ data }) => setSummary(data));
  }, []);

  return (
    <div className="p-8 max-w-4xl">
      <h2
        className="text-3xl text-ink mb-1"
        style={{ fontFamily: "var(--font-display)" }}
      >
        Welcome back{user?.full_name ? `, ${user.full_name}` : ""}
      </h2>
      <p className="text-ink-soft text-sm mb-8">
        Here's what's in your workspace right now.
      </p>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-card border border-rule rounded-sm p-5 flex items-center gap-3">
          <BookOpen size={20} className="text-lamp-dark" />
          <div>
            <p className="text-xl" style={{ fontFamily: "var(--font-display)" }}>
              {summary?.documents ?? "–"}
            </p>
            <p className="text-xs text-ink-soft font-mono">documents</p>
          </div>
        </div>
        <div className="bg-card border border-rule rounded-sm p-5 flex items-center gap-3">
          <Layers size={20} className="text-lamp-dark" />
          <div>
            <p className="text-xl" style={{ fontFamily: "var(--font-display)" }}>
              {summary?.chunks ?? "–"}
            </p>
            <p className="text-xs text-ink-soft font-mono">indexed chunks</p>
          </div>
        </div>
        <div className="bg-card border border-rule rounded-sm p-5 flex items-center gap-3">
          <MessagesSquare size={20} className="text-lamp-dark" />
          <div>
            <p className="text-xl" style={{ fontFamily: "var(--font-display)" }}>
              {summary?.conversations ?? "–"}
            </p>
            <p className="text-xs text-ink-soft font-mono">conversations</p>
          </div>
        </div>
      </div>

      <h3 className="text-sm font-mono uppercase tracking-wide text-ink-soft mb-3">
        Jump in
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <QuickLink
          to="/documents"
          icon={FileStack}
          label="Add a document"
          desc="Upload a PDF, DOCX, or text file"
        />
        <QuickLink
          to="/chat"
          icon={MessageSquare}
          label="Start a conversation"
          desc="Ask questions grounded in your files"
        />
        <QuickLink
          to="/search"
          icon={Search}
          label="Search the catalog"
          desc="Compare keyword vs. vector retrieval"
        />
      </div>
    </div>
  );
}
