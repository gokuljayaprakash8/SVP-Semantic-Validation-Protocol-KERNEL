# SVP Kernel

A runtime governance kernel for AI agents. It evaluates agent actions against semantic policies using embeddings and returns deterministic PASS/BLOCK decisions with a tamper-evident audit trail.

## Stack

- **Language:** Python 3.12
- **Framework:** FastAPI + Uvicorn
- **Embeddings:** fastembed (`BAAI/bge-small-en-v1.5`, ~67MB, downloaded on first run)
- **Similarity:** scikit-learn cosine similarity
- **Policy config:** YAML (`policies/default.yaml`)

## How to run

The workflow `Start application` runs:

```
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Note:** First startup downloads the embedding model (~67MB) and takes ~15–20 seconds.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `POST` | `/v1/audit` | Evaluate a list of agent action steps |
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
