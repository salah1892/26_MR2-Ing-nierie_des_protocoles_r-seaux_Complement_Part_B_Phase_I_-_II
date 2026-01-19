from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assistant.config import Paths
from assistant.ingestion import build_chunks, load_documents, save_metadata
from assistant.logging_utils import JsonlLogger
from assistant.rag_store import RagStore


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    paths = Paths(base_dir=base)
    logger = JsonlLogger(paths.run_log_path)
    rag = RagStore(paths)

    docs = load_documents(paths.data_raw)
    chunks = build_chunks(docs)
    save_metadata(paths, chunks)
    rag.build_and_save([c.text for c in chunks])

    logger.log("Ingest", documents=len(docs), chunks=len(chunks), index=str(paths.faiss_index_path))
    print(f"Ingested {len(docs)} docs / {len(chunks)} chunks")
    print(f"Index: {paths.faiss_index_path}")


if __name__ == "__main__":
    main()
