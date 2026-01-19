from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from assistant.config import DEFAULT_EMBED_MODEL, DEFAULT_TOP_K, Paths


@dataclass(frozen=True)
class Retrieved:
    id: int
    source: str
    chunk_id: int
    text: str
    score: float


class RagStore:
    def __init__(self, paths: Paths, *, embed_model: str = DEFAULT_EMBED_MODEL) -> None:
        self.paths = paths
        self.embed_model_name = embed_model
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self.paths.hf_cache_dir.mkdir(parents=True, exist_ok=True)
            # cache_folder makes the environment reproducible and reduces repeated downloads.
            self._model = SentenceTransformer(
                self.embed_model_name,
                cache_folder=str(self.paths.hf_cache_dir),
            )
        return self._model

    def _load_meta(self) -> list[dict[str, Any]]:
        if not self.paths.meta_path.exists():
            raise FileNotFoundError(f"Missing metadata: {self.paths.meta_path}")
        return json.loads(self.paths.meta_path.read_text(encoding="utf-8"))

    def build_and_save(self, texts: list[str]) -> None:
        self.paths.data_index.mkdir(parents=True, exist_ok=True)
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        emb = np.asarray(embeddings, dtype="float32")
        index = faiss.IndexFlatIP(emb.shape[1])
        index.add(emb)
        faiss.write_index(index, str(self.paths.faiss_index_path))

    def retrieve(self, query: str, *, top_k: int = DEFAULT_TOP_K) -> list[Retrieved]:
        if not self.paths.faiss_index_path.exists():
            raise FileNotFoundError(f"Missing FAISS index: {self.paths.faiss_index_path}")

        index = faiss.read_index(str(self.paths.faiss_index_path))
        meta = self._load_meta()

        q = self.model.encode([query], normalize_embeddings=True)
        q = np.asarray(q, dtype="float32")

        scores, ids = index.search(q, top_k)
        results: list[Retrieved] = []
        for idx, score in zip(ids[0].tolist(), scores[0].tolist(), strict=True):
            if idx < 0:
                continue
            m = meta[idx]
            results.append(
                Retrieved(
                    id=int(m["id"]),
                    source=str(m["source"]),
                    chunk_id=int(m["chunk_id"]),
                    text=str(m["text"]),
                    score=float(score),
                )
            )
        return results
