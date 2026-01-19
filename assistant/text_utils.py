from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from langdetect import detect


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    chunk_id: int


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "unknown"


def normalize_text(text: str) -> str:
    # Basic whitespace normalization; keep Arabic/French characters intact.
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, *, chunk_size: int, overlap: int) -> Iterable[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be < chunk_size")

    text = normalize_text(text)
    if not text:
        return []

    # Split on paragraph boundaries first.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks: list[str] = []
    current = ""
    for p in paragraphs:
        candidate = (current + "\n\n" + p).strip() if current else p
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        # Paragraph too large; hard-split.
        start = 0
        while start < len(p):
            end = min(len(p), start + chunk_size)
            chunks.append(p[start:end])
            start = end - overlap if end < len(p) else end

    if current:
        chunks.append(current)

    # Add overlap between chunks by character window.
    if overlap == 0 or len(chunks) <= 1:
        return chunks

    overlapped: list[str] = []
    for i, c in enumerate(chunks):
        if i == 0:
            overlapped.append(c)
            continue
        prev = overlapped[-1]
        tail = prev[-overlap:]
        overlapped.append((tail + c).strip())
    return overlapped
