import { useState } from "react";
import { Search as SearchIcon } from "lucide-react";
import client from "../api/client";

const MODES = [
  { id: "hybrid", label: "Hybrid" },
  { id: "vector", label: "Vector" },
  { id: "keyword", label: "Keyword" },
];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("hybrid");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const { data } = await client.post("/search", { query, mode, top_k: 8 });
      setResults(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl">
      <h2
        className="text-3xl text-ink mb-1"
        style={{ fontFamily: "var(--font-display)" }}
      >
        Catalog Search
      </h2>
      <p className="text-ink-soft text-sm mb-6">
        Query the index directly to compare keyword, vector, and hybrid retrieval.
      </p>

      <form onSubmit={handleSearch} className="flex gap-3 mb-4">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search your documents…"
          className="flex-1 px-4 py-2.5 border border-rule rounded-sm bg-card focus:outline-none focus:ring-2 focus:ring-lamp"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-lamp hover:bg-lamp-dark text-paper px-5 rounded-sm transition-colors flex items-center gap-2"
        >
          <SearchIcon size={16} />
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      <div className="flex gap-2 mb-6">
        {MODES.map((m) => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            className={`text-xs font-mono px-3 py-1.5 rounded-sm border transition-colors ${
              mode === m.id
                ? "bg-ink text-paper border-ink"
                : "border-rule text-ink-soft hover:border-lamp"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {results && (
        <div className="space-y-3">
          {results.length === 0 && (
            <p className="text-ink-soft text-sm italic">No matches found.</p>
          )}
          {results.map((r, i) => (
            <div
              key={i}
              className="bg-card border border-rule rounded-sm p-4"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-mono text-lamp-dark">
                  {r.filename} · chunk {r.chunk_index}
                </span>
                <span className="text-xs font-mono text-brass">
                  score {r.score.toFixed(3)}
                </span>
              </div>
              <p className="text-sm text-ink-soft leading-relaxed">
                {r.content.length > 400 ? r.content.slice(0, 400) + "…" : r.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
