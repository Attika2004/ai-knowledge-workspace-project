from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.api.routes import auth, documents, chat, search, history, evaluation

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Knowledge Workspace API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before deploying anywhere real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(history.router)
app.include_router(evaluation.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
