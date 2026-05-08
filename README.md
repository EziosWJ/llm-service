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

Upload `docx`, `pdf`, or `txt` material and replace its chunks in Qdrant.
If the same `material_id` and `user_id` already have vectors, old vectors are deleted before new chunks are written.

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

Response:

```json
{
  "deleted_count": 0,
  "chunk_count": 8
}
```

### `DELETE /materials/{material_id}/vectors`

Delete all vectors for one `user_id + material_id`.

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
- `user_id`: required
- `top_k`: default `5`

If `material_ids` is provided, it must be a non-empty list and retrieval is scoped by `user_id + material_ids`.
If `material_ids` is omitted, retrieval is scoped by `user_id`.

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

### `POST /ask`

Ask a question and get an LLM-summarized answer based on retrieved materials.

Request fields:

- `query`: required, the question
- `material_ids`: optional
- `user_id`: required
- `top_k`: default `3`

If `material_ids` is provided, it must be a non-empty list and retrieval is scoped by `user_id + material_ids`.
If `material_ids` is omitted, retrieval is scoped by `user_id`.

Example:

```bash
curl -s -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "射击游戏有哪些",
    "user_id": "user-001",
    "material_ids": ["mat-001"],
    "top_k": 3
  }' | jq
```

Returned `sources` include `text`, `material_id`, `chunk_index`, and `score`.

## Test

```bash
uv run pytest -q
```

Current baseline: `36 passed`.
