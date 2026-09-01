import { useEffect, useState } from "react";
import { BookOpen, Layers, MessagesSquare, Timer } from "lucide-react";
import client from "../api/client";

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="bg-card border border-rule rounded-sm p-5 flex items-center gap-4">
      <div className="text-lamp-dark bg-lamp/10 p-2.5 rounded-sm">
        <Icon size={20} strokeWidth={1.75} />
      </div>
      <div>
        <p className="text-2xl" style={{ fontFamily: "var(--font-display)" }}>
          {value}
        </p>
        <p className="text-xs text-ink-soft font-mono uppercase tracking-wide">
          {label}
        </p>
      </div>
    </div>
  );
}

export default function Evaluation() {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    client.get("/evaluation/summary").then(({ data }) => setSummary(data));
  }, []);

  if (!summary) {
    return <div className="p-8 text-ink-soft text-sm">Loading ledger…</div>;
  }

  return (
    <div className="p-8 max-w-4xl">
      <h2
        className="text-3xl text-ink mb-1"
        style={{ fontFamily: "var(--font-display)" }}
      >
        The Ledger
      </h2>
      <p className="text-ink-soft text-sm mb-6">
        Basic usage and latency metrics — a starting point before wiring in
        RAGAS / LangSmith-style evaluation.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard icon={BookOpen} label="Documents" value={summary.documents} />
        <StatCard icon={Layers} label="Chunks" value={summary.chunks} />
        <StatCard
          icon={MessagesSquare}
          label="Conversations"
          value={summary.conversations}
        />
        <StatCard
          icon={Timer}
          label="Avg latency (ms)"
          value={summary.avg_latency_ms}
        />
      </div>

      <h3 className="text-sm font-mono uppercase tracking-wide text-ink-soft mb-3">
        Recent requests
      </h3>
      <div className="space-y-1.5">
        {summary.recent.length === 0 && (
          <p className="text-ink-soft text-sm italic">
            No requests logged yet — send a chat message to populate this.
          </p>
        )}
        {summary.recent
          .slice()
          .reverse()
          .map((r, i) => (
            <div
              key={i}
              className="flex items-center justify-between bg-card border border-rule rounded-sm px-4 py-2 text-sm font-mono"
            >
              <span className="text-lamp-dark">{r.kind}</span>
              <span className="text-ink-soft">{r.num_citations} citations</span>
              <span className="text-brass">{r.latency_ms} ms</span>
            </div>
          ))}
      </div>
    </div>
  );
}
