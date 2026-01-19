from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    base_dir: Path

    @property
    def data_raw(self) -> Path:
        return self.base_dir / "data" / "raw"

    @property
    def data_index(self) -> Path:
        return self.base_dir / "data" / "index"

    @property
    def faiss_index_path(self) -> Path:
        return self.data_index / "docs.faiss"

    @property
    def meta_path(self) -> Path:
        return self.data_index / "docs_meta.json"

    @property
    def run_log_path(self) -> Path:
        return self.base_dir / "reports" / "run.log"

    @property
    def eval_report_path(self) -> Path:
        return self.base_dir / "reports" / "evaluation_report.md"

    @property
    def hf_cache_dir(self) -> Path:
        # Local cache to avoid re-downloading embedding models.
        return self.data_index / "hf_cache"


DEFAULT_EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
DEFAULT_TOP_K = 4
DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 120
