from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from assistant.agent import handle_query
from assistant.config import Paths
from assistant.ingestion import build_chunks, load_documents, save_metadata
from assistant.logging_utils import JsonlLogger
from assistant.rag_store import RagStore


BASE_DIR = Path(__file__).resolve().parents[1]
paths = Paths(base_dir=BASE_DIR)
logger = JsonlLogger(paths.run_log_path)
rag = RagStore(paths)

app = FastAPI(title="Tunisian Digital Service Assistant (Prototype)")


class IngestResponse(BaseModel):
    documents: int
    chunks: int
    index_path: str


@app.post("/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    docs = load_documents(paths.data_raw)
    chunks = build_chunks(docs)
    save_metadata(paths, chunks)
    rag.build_and_save([c.text for c in chunks])
    logger.log("Ingest", documents=len(docs), chunks=len(chunks), index=str(paths.faiss_index_path))
    return IngestResponse(documents=len(docs), chunks=len(chunks), index_path=str(paths.faiss_index_path))


class QueryRequest(BaseModel):
    text: str = Field(..., description="Citizen/civil-servant request in Arabic/French")
    top_k: int = 4
    allow_generation: bool = False


class QueryResponse(BaseModel):
    action: str
    answer: str
    language: str
    retrieved_sources: list[str]
    eval_hooks: dict


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    res = handle_query(
        user_text=req.text,
        rag=rag,
        logger=logger,
        top_k=req.top_k,
        allow_generation=req.allow_generation,
    )
    return QueryResponse(
        action=res.action,
        answer=res.answer,
        language=res.language,
        retrieved_sources=[r.source for r in res.retrieved],
        eval_hooks=res.eval_hooks,
    )
