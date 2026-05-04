# llm-service

Material-aware LLM service based on FastAPI.

## Setup

Create `.env` from `.env.example` and set these values:

```env
LLM_BASE_URL=http://127.0.0.1:1234/v1
LLM_MODEL=qwen3.5-4b
LLM_API_KEY=
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_PREFIX=materials
```

Install deps and start service:

```bash
uv sync
uv run uvicorn src.main:app --reload
```

## Health Check

`GET /health` is lightweight by default:

- checks Qdrant collection reachability
- skips LLM inference
- returns `llm.status = "skipped"`

Use `deep=true` only for manual upstream probing:

```bash
curl -s "http://127.0.0.1:8000/health?deep=true" | jq
```

Default probe:

```bash
curl -s "http://127.0.0.1:8000/health" | jq
```

## APIs

### `POST /materials/process`

Upload `docx`, `pdf`, or `txt` material and write chunks into Qdrant.

Form fields:

- `file`
- `material_id`
- `user_id`

Example:

```bash
curl -s -X POST "http://127.0.0.1:8000/materials/process" \
  -F "file=@/absolute/path/sample.txt" \
  -F "material_id=mat-001" \
  -F "user_id=user-001" | jq
```

### `DELETE /materials/{material_id}/vectors`

Delete all vectors for one `material_id`.

Example:

```bash
curl -s -X DELETE "http://127.0.0.1:8000/materials/mat-001/vectors?user_id=user-001" | jq
```

### `POST /generate`

Generate content from retrieved sources.

Request fields:

- `type`: `outline` | `draft` | `polished` | `title`
- `topic`
- `content`: required when `type=polished`
- `material_ids`: optional
- `user_id`: optional
- `top_k`: default `5`

Example:

```bash
curl -s -X POST "http://127.0.0.1:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "outline",
    "topic": "大模型应用架构",
    "material_ids": ["mat-001"],
    "user_id": "user-001",
    "top_k": 5
  }' | jq
```

## Test

```bash
uv run pytest -q
```

Current baseline: `26 passed`.
