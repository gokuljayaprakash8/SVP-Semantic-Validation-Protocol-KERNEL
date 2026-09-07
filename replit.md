# SVP Kernel

A runtime governance kernel for AI agents. It evaluates agent actions against semantic policies using embeddings and returns deterministic PASS/BLOCK decisions with a tamper-evident audit trail.

## Stack

- **Language:** Python 3.12.12
- **Framework:** FastAPI + Uvicorn
- **Embeddings:** FastEmbed 0.8.0 (`BAAI/bge-small-en-v1.5`, ~67MB)
- **Similarity:** scikit-learn cosine similarity
- **Policy config:** YAML (`policies/default.yaml`)

## How to run

The workflow `Start application` runs:

```
uvicorn app:app --host 0.0.0.0 --port 8000
```

The model is initialized on the first readiness or governance request. The
application downloads the pinned Qdrant ONNX snapshot revision
`52398278842ec682c6f32300af41344b1c0b0bb2` into `SVP_MODEL_CACHE_DIR`
(default `/tmp/svp-fastembed`) and passes that local snapshot to FastEmbed.
There is no semantic fallback if the model cannot load.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `GET` | `/ready` | Readiness check — verifies policy and model inference |
| `POST` | `/v1/govern` | Evaluate a structured proposal without execution |
| `POST` | `/v1/audit` | Evaluate a list of agent action steps |
| `POST` | `/v1/audit/v06` | Produce legacy v0.6 bound decision evidence |
| `POST` | `/v1/execute/v06-test` | Synthetic compatibility path through current governance |
| `GET` | `/v1/audit/verify` | Verify audit log chain integrity |

### Example: evaluate actions

```bash
curl -X POST http://localhost:8000/v1/audit \
  -H "Content-Type: application/json" \
  -d '{"steps": ["read user profile", "drop all tables in the database"]}'
```

## Project structure

```
app.py               # FastAPI app + SVP kernel logic
validator.py         # Policy file loader
policies/
  default.yaml       # Policy rules (severity, thresholds, patterns)
svp_kernel/
  audit/             # Tamper-evident audit logger (SHA-256 chained)
  decorators.py      # @svp_guard decorator
  client.py          # Programmatic client
docs/                # Architecture and design docs
evaluation/          # Adversarial evaluation suite
examples/            # Sample blocked/safe workflow JSON
```

## User preferences

_None recorded yet._
