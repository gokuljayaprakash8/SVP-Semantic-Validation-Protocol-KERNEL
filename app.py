import threading
import numpy as np
import yaml

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from svp_kernel.audit.audit_logger import AuditLogger
from validator import load_policy_file

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Policy config is cheap to load — do it at startup, no heavy deps needed.
# ---------------------------------------------------------------------------
config = load_policy_file("policies/default.yaml")
POLICIES = config["policies"]

audit_logger = AuditLogger()

# ---------------------------------------------------------------------------
# Embedding model — loaded LAZILY on first call to /v1/audit so that /
# and /health respond immediately and the health probe passes during startup.
# ---------------------------------------------------------------------------
_model = None
_policy_vectors = None
_pattern_meta = None
_init_lock = threading.Lock()


def _ensure_model_loaded() -> None:
    """Initialize the embedding model and policy vectors on first use."""
    global _model, _policy_vectors, _pattern_meta

    # Fast path — already initialised.
    if _model is not None:
        return

    with _init_lock:
        # Re-check inside the lock to avoid double-init.
        if _model is not None:
            return

        # Import here so the heavy fastembed / sklearn deps are not loaded
        # at module import time (which would block the gunicorn worker).
        from fastembed import TextEmbedding  # noqa: PLC0415
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: PLC0415 (imported for side-effect; used below)

        patterns: list[str] = []
        meta: list[dict] = []

        for policy in POLICIES:
            for pattern in policy["patterns"]:
                patterns.append(pattern)
                meta.append(
                    {
                        "id": policy["id"],
                        "description": policy["description"],
                        "threshold": policy["threshold"],
                        "severity": policy["severity"],
                        "action": policy["action"],
                        "pattern": pattern,
                    }
                )

        model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        policy_vectors = np.array(list(model.embed(patterns)))

        # Commit atomically — readers check `_model is not None`.
        _pattern_meta = meta
        _policy_vectors = policy_vectors
        _model = model


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------

def svp_kernel(action_text: str) -> dict:
    _ensure_model_loaded()

    from sklearn.metrics.pairwise import cosine_similarity  # noqa: PLC0415

    action_lower = action_text.lower()
    action_vector = np.array(list(_model.embed([action_text])))
    similarities = cosine_similarity(action_vector, _policy_vectors)[0]

    severity_bonus = {"CRITICAL": 0.05, "HIGH": 0.03, "MEDIUM": 0.01, "LOW": 0.00}
    policy_scores: dict = {}

    for i, similarity in enumerate(similarities):
        meta = _pattern_meta[i]
        pid = meta["id"]

        exact_bonus = 0.10 if meta["pattern"].lower() in action_lower else 0.0
        score = float(similarity) + exact_bonus + severity_bonus.get(meta["severity"], 0)

        if pid not in policy_scores or score > policy_scores[pid]["score"]:
            policy_scores[pid] = {"score": score, "similarity": float(similarity), "policy": meta}

    best = max(policy_scores.values(), key=lambda x: x["score"])
    policy = best["policy"]
    margin = 0.05

    sorted_scores = sorted(policy_scores.values(), key=lambda x: x["score"], reverse=True)
    second_score = sorted_scores[1]["score"] if len(sorted_scores) > 1 else 0

    if best["similarity"] >= policy["threshold"] and (best["score"] - second_score) >= margin:
        return {
            "action": action_text,
            "decision": policy["action"],
            "rule_id": policy["id"],
            "matched_policy": policy["description"],
            "severity": policy["severity"],
            "score": round(best["similarity"], 4),
            "threshold": policy["threshold"],
        }

    return {
        "action": action_text,
        "decision": "PASS",
        "rule_id": "SAFE001",
        "matched_policy": "No policy exceeded threshold",
        "severity": "LOW",
        "score": round(best["similarity"], 4),
        "threshold": policy["threshold"],
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

class WorkflowRequest(BaseModel):
    steps: list[str]


@app.get("/")
def root():
    return {"status": "ok", "service": "SVP Kernel"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/audit")
def audit(req: WorkflowRequest):
    results = []
    for step in req.steps:
        decision = svp_kernel(step)
        audit_event = audit_logger.create_event(decision, "1.0.0")
        audit_logger.save_event(audit_event)
        results.append(decision)

    blocked = [r for r in results if r["decision"] == "BLOCK"]
    return {
        "overall": "BLOCKED" if blocked else "CLEAR",
        "blocked_count": len(blocked),
        "steps": results,
    }


@app.get("/v1/audit/verify")
def verify_audit():
    return {"valid": audit_logger.verify_chain()}
