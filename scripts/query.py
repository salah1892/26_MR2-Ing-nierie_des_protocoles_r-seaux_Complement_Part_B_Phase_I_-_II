from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assistant.agent import handle_query
from assistant.config import Paths
from assistant.logging_utils import JsonlLogger
from assistant.rag_store import RagStore


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python scripts/query.py "your question"')
        raise SystemExit(2)

    text = sys.argv[1]
    base = Path(__file__).resolve().parents[1]
    paths = Paths(base_dir=base)

    logger = JsonlLogger(paths.run_log_path)
    rag = RagStore(paths)

    res = handle_query(user_text=text, rag=rag, logger=logger, top_k=4, allow_generation=False)
    print(res.answer)


if __name__ == "__main__":
    main()
