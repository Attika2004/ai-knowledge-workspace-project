venv\Scripts\activate# AI Knowledge Workspace

An end-to-end RAG + agents application: upload documents, chat with them
using Retrieval-Augmented Generation, search with hybrid keyword+vector
retrieval, and let an AI agent call tools on your behalf. Built as a working
FYP starting point — not a mockup, everything below actually runs.

```
fyp/
├── backend/     FastAPI + SQLite + FAISS/BM25 + Anthropic API
├── frontend/    React + Vite + Tailwind v4
└── docker-compose.yml
```

## What's implemented right now

| Feature (from the project plan)             | Status |
|----------------------------------------------|--------|
| User authentication (JWT)                     | ✅ done |
| Document upload & management (PDF/DOCX/TXT/MD)| ✅ done |
| Text extraction & chunking                    | ✅ done |
| Embedding generation & vector indexing        | ✅ done (TF‑IDF+SVD → FAISS, see note below) |
| RAG question answering with citations         | ✅ done (Claude via Anthropic API) |
| Hybrid search (keyword + vector)              | ✅ done (BM25 + FAISS, blended) |
| Conversation history                          | ✅ done |
| Tool calling (calculator, document search)    | ✅ done |
| Agent workflow (multi-step tool use loop)     | ✅ done |
| Evaluation dashboard (latency, counts)        | ✅ basic version done |
| Frontend: Login/Register/Dashboard/Upload/Chat/Search/History/Settings/Evaluation | ✅ all pages built |
| Docker deployment                             | ✅ Dockerfiles + docker-compose |
| CI/CD                                         | ✅ GitHub Actions (build + smoke test) |
| LangChain / LangGraph                         | ⬜ not used — current pipeline is hand-rolled so you can see exactly what's happening; swapping in LangChain/LangGraph is a good "week 2/3" exercise once the fundamentals feel solid |
| Local models (Ollama/vLLM), Hugging Face embeddings | ⬜ see "Swapping in real embeddings" below |
| LoRA/QLoRA fine-tuning demo                   | ⬜ not started — genuinely a separate mini-project, tackle last |
| Quantization                                  | ⬜ only relevant once you're running local models |
| LangSmith / W&B tracing                       | ⬜ the `/api/evaluation` endpoint is the hook point — swap in real tracing there |

## Why TF‑IDF instead of a real embedding model?

The retrieval pipeline (`backend/app/services/embeddings.py`) currently uses
TF‑IDF + SVD to turn text into dense vectors, combined with BM25 for keyword
scoring, blended in `vector_store.py`. This is a **real, working hybrid
search implementation** — I tested it live with multiple documents and it
correctly retrieves the right document for both semantic and keyword-style
queries.

It's not a proper "embedding model" in the Hugging Face sense (like
`all-MiniLM-L6-v2`) because that requires downloading model weights, which
wasn't possible in the sandbox I built this in. The code is structured so
swapping it in is a small, contained change:

1. `pip install sentence-transformers`
2. In `backend/app/services/embeddings.py`, uncomment the
   `SentenceTransformerBackend` class at the bottom.
3. Change `get_embedding_backend()` to return `SentenceTransformerBackend()`
   instead of `TfidfEmbeddingBackend()`.

Nothing else in the app needs to change — `vector_store.py` only calls
`.fit()` and `.embed_query()` on whichever backend is active.

## Running it locally (no Docker)

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs (FastAPI's
auto-generated Swagger UI) — useful for testing endpoints directly.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The Vite dev server proxies `/api/*` to the
backend on port 8000 (see `frontend/vite.config.js`), so you don't need to
configure CORS or a separate API base URL for local dev.

### First run

1. Register an account at `/register`.
2. Go to **Stacks** and upload a `.txt`, `.pdf`, `.docx`, or `.md` file.
3. Wait a couple of seconds for its status to flip to `ready` (it's chunked
   and indexed in the background).
4. Go to **Reading Room** and ask a question about it.
5. Try **Catalog Search** to compare hybrid vs. keyword vs. vector retrieval
   directly.
6. Flip on **Agent mode** in the chat header to watch the assistant decide
   whether to call the calculator or document-search tool on its own.

## Running it with Docker

```bash
cp backend/.env.example backend/.env   # then add your ANTHROPIC_API_KEY
docker compose up --build
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

## Getting an API key (free by default)

This project defaults to **Groq**, which has a genuinely free tier — no
credit card required:

1. Go to [console.groq.com](https://console.groq.com) and sign up.
2. Go to **API Keys** → **Create Key**, copy it (starts with `gsk_`).
3. In `backend/.env`, set `GROQ_API_KEY=gsk_...` (leave `LLM_PROVIDER=groq`).

Everything else (upload, hybrid search, evaluation counts) works without
any key at all. If you'd rather use Claude instead (paid), set
`LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=sk-ant-...` in `.env` — the
code path for both providers lives side by side in
`backend/app/services/llm.py` and `agent.py`, so switching is just an env
var change, no code edits needed.

Free tiers are rate-limited (Groq: roughly 30 requests/minute, ~1,000/day
at the time of writing) — plenty for FYP development and demos, just don't
expect to hammer it with load tests.

## Architecture notes for your report

- **Auth**: JWT bearer tokens, bcrypt password hashing, stored in
  `localStorage` on the frontend (fine for a demo; for production you'd move
  to httpOnly cookies).
- **Chunking**: sliding-window over words (800 words, 150 overlap) —
  simple and dependency-free; a text-aware splitter (e.g. by sentence
  boundary) is a natural improvement to mention as future work.
- **Indexing strategy**: the whole per-user index is rebuilt on every
  document add/delete rather than incrementally updated. Fine at FYP scale
  (hundreds–low thousands of chunks); for production you'd want an
  upsert-capable vector store (pgvector, Qdrant, Weaviate) instead of
  rebuilding from scratch.
- **Agent loop**: capped at 4 tool-use iterations to avoid runaway loops —
  a real deployment would add per-user rate limiting and cost tracking too.
- **Evaluation**: currently an in-memory ring buffer of the last 200
  requests per process (resets on restart). Good enough to demo the concept;
  swap for persistent storage + RAGAS/LangSmith once you get to that part of
  the plan.

## Suggested order for extending this

Given your 1-month plan, a reasonable path from here:
1. Get comfortable with what's here — read through `backend/app/services/`,
   it's the core of the RAG pipeline.
2. Swap in real embeddings (sentence-transformers) once you have internet
   access to Hugging Face — see the section above.
3. Add a second tool to the agent (e.g. a mock "database" lookup) to
   practice the tool-calling pattern before moving to LangGraph.
4. Try re-implementing the RAG pipeline in LangChain as a comparison
   exercise — you'll have a working reference to check your understanding
   against.
5. Persist evaluation metrics to a real store and try RAGAS for
   answer-quality scoring.
6. Local models: install Ollama, and duplicate `llm.py`'s interface with an
   Ollama-backed implementation behind the same function signature.
7. LoRA/QLoRA fine-tuning is a genuinely separate mini-project — treat it as
   its own milestone at the end.
