import { useEffect, useRef, useState, useCallback } from "react";
import { Upload, FileText, Trash2, RefreshCw } from "lucide-react";
import client from "../api/client";

const STATUS_STYLES = {
  ready: "text-lamp-dark bg-lamp/10 border-lamp/30",
  processing: "text-brass bg-brass/10 border-brass/30",
  failed: "text-danger bg-danger/10 border-danger/30",
};

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileInput = useRef();

  const fetchDocs = useCallback(async () => {
    const { data } = await client.get("/documents");
    setDocs(data);
  }, []);

  useEffect(() => {
    fetchDocs();
    const interval = setInterval(fetchDocs, 4000);
    return () => clearInterval(interval);
  }, [fetchDocs]);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      await client.post("/documents/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await fetchDocs();
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed.");
    } finally {
      setUploading(false);
      fileInput.current.value = "";
    }
  };

  const handleDelete = async (id) => {
    await client.delete(`/documents/${id}`);
    fetchDocs();
  };

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-1">
        <h2
          className="text-3xl text-ink"
          style={{ fontFamily: "var(--font-display)" }}
        >
          The Stacks
        </h2>
        <button
          onClick={fetchDocs}
          className="text-ink-soft hover:text-lamp-dark transition-colors"
          title="Refresh"
        >
          <RefreshCw size={16} />
        </button>
      </div>
      <p className="text-ink-soft text-sm mb-6">
        Upload PDFs, Word docs, or plain text. Each one is chunked and indexed for retrieval.
      </p>

      <label className="flex items-center justify-center gap-2 border-2 border-dashed border-rule rounded-sm py-8 cursor-pointer hover:border-lamp hover:bg-lamp/5 transition-colors mb-8">
        <Upload size={18} className="text-ink-soft" />
        <span className="text-sm text-ink-soft">
          {uploading ? "Uploading…" : "Click to add a document (.pdf, .docx, .txt, .md)"}
        </span>
        <input
          ref={fileInput}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          className="hidden"
          onChange={handleUpload}
          disabled={uploading}
        />
      </label>

      {error && (
        <div className="text-sm text-danger border border-danger/30 bg-danger/5 px-3 py-2 rounded-sm mb-6">
          {error}
        </div>
      )}

      <div className="space-y-2">
        {docs.length === 0 && (
          <p className="text-ink-soft text-sm italic">
            The stacks are empty. Add a document to get started.
          </p>
        )}
        {docs.map((doc) => (
          <div
            key={doc.id}
            className="flex items-center justify-between bg-card border border-rule rounded-sm px-4 py-3"
          >
            <div className="flex items-center gap-3 min-w-0">
              <FileText size={18} className="text-ink-soft shrink-0" />
              <div className="min-w-0">
                <p className="text-sm truncate">{doc.filename}</p>
                <p className="text-xs text-ink-soft font-mono">
                  {doc.num_chunks} chunk{doc.num_chunks === 1 ? "" : "s"} · {doc.filetype}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <span
                className={`text-xs px-2 py-0.5 border rounded-sm font-mono ${
                  STATUS_STYLES[doc.status] || ""
                }`}
              >
                {doc.status}
              </span>
              <button
                onClick={() => handleDelete(doc.id)}
                className="text-ink-soft hover:text-danger transition-colors"
                title="Remove"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
