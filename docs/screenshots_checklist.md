# Screenshot / logs checklist (Phase 2)

## Required screenshots
- n8n ingestion workflow imported and executed
- n8n query workflow imported and executed
- FastAPI Swagger UI showing `/ingest` and `/query`

## Required log excerpts
- `reports/run.log` entries showing:
  - `Ingest` event
  - `Tool_Select` and `Tool_Result`
  - `Generate_Response` (extractive or ollama)
  - `Safety_Check` for refusal case
