from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class LlmResult:
    text: str
    model: str


def generate_with_ollama(
    prompt: str,
    *,
    model: str = "llama3.1:8b",
    base_url: str = "http://127.0.0.1:11434",
    timeout_s: float = 30.0,
) -> LlmResult:
    """Generate using local Ollama (optional). Requires Ollama running locally."""

    url = f"{base_url}/api/generate"
    body = {"model": model, "prompt": prompt, "stream": False}

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    return LlmResult(text=str(payload.get("response", "")), model=model)
