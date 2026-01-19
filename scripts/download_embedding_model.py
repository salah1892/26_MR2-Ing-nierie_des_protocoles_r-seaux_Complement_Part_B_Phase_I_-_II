from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assistant.config import DEFAULT_EMBED_MODEL, Paths
from assistant.rag_store import RagStore


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    paths = Paths(base_dir=base)

    rag = RagStore(paths, embed_model=DEFAULT_EMBED_MODEL)

    # This forces download into data/index/hf_cache and verifies inference works.
    _ = rag.model.encode(["test"], normalize_embeddings=True)

    print("Embedding model ready")
    print(f"Model: {DEFAULT_EMBED_MODEL}")
    print(f"Cache: {paths.hf_cache_dir}")


if __name__ == "__main__":
    main()
