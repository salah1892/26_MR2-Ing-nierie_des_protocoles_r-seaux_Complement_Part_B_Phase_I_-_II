# Phase 2 — AI-Enabled Tunisian Digital Service Assistant (Prototype)

This folder contains an **out-of-class implementation** matching Part B (Phase 2) requirements:
- Local-first **RAG** (vector index stored locally)
- **Agentic** decision branches: retrieve / summarize / translate / refuse / escalate
- Orchestration via **n8n workflows** (JSON exports) calling a local API

## 1) Setup

### 1.1 Install dependencies

Run from this folder (PowerShell):

- `& .\.venv\Scripts\Activate.ps1`
- `python -m pip install -U pip`
- `python -m pip install -r requirements.txt`

### 1.1.1 Fix/pin the embeddings model (recommended)

By default we use: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.

To **fix** (pin) the model explicitly, set:
- PowerShell: `$env:EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"`

The model files are cached locally under:
- `data/index/hf_cache/`

To pre-download (so it works offline later):
- `python scripts/download_embedding_model.py`

Offline mode (after download):
- PowerShell: `$env:TRANSFORMERS_OFFLINE = "1"; $env:HF_HUB_OFFLINE = "1"`

### 1.2 Put documents to index

Add administrative guides/forms/procedures (TXT/PDF) under:
- `data/raw/`

Sample synthetic documents are already provided.

## 2) Run the local API

- `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`

Open docs UI:
- http://127.0.0.1:8000/docs

## 3) Ingest + index (RAG)

Option A (API):
- `POST /ingest` (indexes all documents under `data/raw/`)

Option B (script):
- `python scripts/ingest.py`

Index is saved locally under:
- `data/index/`

## 4) Query the assistant

Option A (API):
- `POST /query`

Option B (script):
- `python scripts/query.py "Quelle est la procédure pour renouveler une CIN ?"`

## 5) n8n orchestration

Import the workflows in n8n:
- `n8n/ingestion_workflow.json`
- `n8n/query_workflow.json`

They call the local API endpoints (`/ingest`, `/query`).

## 6) Evaluation

Run:
- `python scripts/run_evaluation.py`

Outputs:
- `reports/evaluation_report.md`
- `reports/run.log`

## Notes on sovereignty & safety

- The system **refuses** or **escalates** when the user message includes citizen-identifiable/sensitive data.
- It is **local-first**: vector store is local; LLM generation is optional.
- If you want real generation with a local open-weight model, connect the optional Ollama backend (see `assistant/llm_ollama.py`).
