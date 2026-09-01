import { useState } from "react";
import { useAuth } from "../context/AuthContext";

const SEARCH_MODE_KEY = "pref:defaultSearchMode";
const AGENT_MODE_KEY = "pref:defaultAgentMode";

export default function Settings() {
  const { user } = useAuth();
  const [searchMode, setSearchMode] = useState(
    localStorage.getItem(SEARCH_MODE_KEY) || "hybrid"
  );
  const [agentDefault, setAgentDefault] = useState(
    localStorage.getItem(AGENT_MODE_KEY) === "true"
  );
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    localStorage.setItem(SEARCH_MODE_KEY, searchMode);
    localStorage.setItem(AGENT_MODE_KEY, String(agentDefault));
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  return (
    <div className="p-8 max-w-2xl">
      <h2
        className="text-3xl text-ink mb-1"
        style={{ fontFamily: "var(--font-display)" }}
      >
        Settings
      </h2>
      <p className="text-ink-soft text-sm mb-8">
        Your account and workspace preferences.
      </p>

      <div className="bg-card border border-rule rounded-sm p-6 mb-6">
        <h3 className="text-sm font-mono uppercase tracking-wide text-ink-soft mb-4">
          Account
        </h3>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-ink-soft">Name</dt>
            <dd>{user?.full_name || "—"}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-ink-soft">Email</dt>
            <dd>{user?.email}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-ink-soft">User ID</dt>
            <dd className="font-mono">{user?.id}</dd>
          </div>
        </dl>
      </div>

      <div className="bg-card border border-rule rounded-sm p-6 mb-6">
        <h3 className="text-sm font-mono uppercase tracking-wide text-ink-soft mb-4">
          Retrieval preferences
        </h3>
        <div className="mb-4">
          <label className="block text-xs uppercase tracking-wide text-ink-soft mb-1.5 font-mono">
            Default search mode
          </label>
          <select
            value={searchMode}
            onChange={(e) => setSearchMode(e.target.value)}
            className="w-full px-3 py-2 border border-rule rounded-sm bg-paper focus:outline-none focus:ring-2 focus:ring-lamp"
          >
            <option value="hybrid">Hybrid (keyword + vector)</option>
            <option value="vector">Vector only</option>
            <option value="keyword">Keyword only</option>
          </select>
        </div>
        <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
          <input
            type="checkbox"
            checked={agentDefault}
            onChange={(e) => setAgentDefault(e.target.checked)}
            className="accent-lamp"
          />
          Start new chats in agent mode by default
        </label>
      </div>

      <div className="bg-card border border-rule rounded-sm p-6 mb-6">
        <h3 className="text-sm font-mono uppercase tracking-wide text-ink-soft mb-2">
          Model configuration
        </h3>
        <p className="text-sm text-ink-soft leading-relaxed">
          The LLM provider and API key are configured server-side in{" "}
          <code className="font-mono text-brass">backend/.env</code> (
          <code className="font-mono text-brass">LLM_PROVIDER</code>,{" "}
          <code className="font-mono text-brass">LLM_MODEL</code>,{" "}
          <code className="font-mono text-brass">GROQ_API_KEY</code> or{" "}
          <code className="font-mono text-brass">ANTHROPIC_API_KEY</code>) —
          not exposed to the browser for security. Groq is free; Anthropic
          is paid.
        </p>
      </div>

      <button
        onClick={handleSave}
        className="bg-lamp hover:bg-lamp-dark text-paper px-5 py-2.5 rounded-sm transition-colors"
      >
        {saved ? "Saved ✓" : "Save preferences"}
      </button>
    </div>
  );
}
