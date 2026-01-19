from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

from assistant.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, Paths
from assistant.text_utils import Chunk, chunk_text, normalize_text


@dataclass(frozen=True)
class Doc:
    source: str
    text: str


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages_text: list[str] = []
    for p in reader.pages:
        pages_text.append(p.extract_text() or "")
    return "\n\n".join(pages_text)


def load_documents(raw_dir: Path) -> list[Doc]:
    docs: list[Doc] = []
    for path in sorted(raw_dir.rglob("*")):
        if path.is_dir():
            continue
        ext = path.suffix.lower()
        if ext not in {".txt", ".pdf"}:
            continue
        if ext == ".txt":
            text = _read_txt(path)
        else:
            text = _read_pdf(path)
        text = normalize_text(text)
        if text:
            docs.append(Doc(source=str(path), text=text))
    return docs


def build_chunks(
    docs: Iterable[Doc],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for d in docs:
        parts = list(chunk_text(d.text, chunk_size=chunk_size, overlap=overlap))
        for idx, part in enumerate(parts):
            all_chunks.append(Chunk(text=part, source=d.source, chunk_id=idx))
    return all_chunks


def save_metadata(paths: Paths, chunks: list[Chunk]) -> None:
    payload = [
        {"id": i, "source": c.source, "chunk_id": c.chunk_id, "text": c.text}
        for i, c in enumerate(chunks)
    ]
    paths.data_index.mkdir(parents=True, exist_ok=True)
    paths.meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
