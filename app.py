from svp_kernel.audit.audit_logger import AuditLogger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastembed import TextEmbedding
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

import yaml

from validator import load_policy_file

config = load_policy_file("policies/default.yaml")

POLICIES = config["policies"]

PATTERNS = []
PATTERN_META = []

for policy in POLICIES:
    for pattern in policy["patterns"]:
        PATTERNS.append(pattern)
        PATTERN_META.append({
            "id": policy["id"],
            "description": policy["description"],
            "threshold": policy["threshold"],
            "severity": policy["severity"],
            "action": policy["action"],
        })

policy_vectors = np.array(list(model.embed(PATTERNS))) 
audit_logger = AuditLogger()

def get_severity(score):
    if score > 0.75: return "CRITICAL"
    elif score > 0.6: return "HIGH"
    elif score > 0.45: return "MEDIUM"
    else: return "LOW"

def svp_kernel(action_text):
    action_vector = np.array(list(model.embed([action_text])))

    similarities = cosine_similarity(action_vector, policy_vectors)[0]

    matches = []

    for i, score in enumerate(similarities):
        policy = PATTERN_META[i]

        if score >= policy["threshold"]:
            matches.append({
                "score": float(score),
                "policy": policy,
            })

    if not matches:
        best_index = int(np.argmax(similarities))
        best_score = float(similarities[best_index])
        best_policy = PATTERN_META[best_index]

        return {
            "action": action_text,
            "decision": "PASS",
            "rule_id": best_policy["id"],
            "matched_policy": best_policy["description"],
            "severity": "LOW",
            "score": round(best_score, 4),
            "threshold": best_policy["threshold"],
        }

    best_match = max(matches, key=lambda x: x["score"])
    policy = best_match["policy"]

    return {
        "action": action_text,
        "decision": policy["action"],
        "rule_id": policy["id"],
        "matched_policy": policy["description"],
        "severity": policy["severity"],
        "score": round(best_match["score"], 4),
        "threshold": policy["threshold"],
    }

class WorkflowRequest(BaseModel):
    steps: list[str]

@app.post("/v1/audit")
def audit(req: WorkflowRequest):
    results = []

    for step in req.steps:
     decision = svp_kernel(step)
     audit_event = audit_logger.create_event(decision, "1.0.0")
     audit_logger.save_event(audit_event)
     results.append(decision)
    blocked = [r for r in results if r["decision"] == "BLOCK"]
    return {"overall": "BLOCKED" if blocked else "CLEAR", "blocked_count": len(blocked), "steps": results}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/audit/verify")
def verify_audit():
    return {"valid": audit_logger.verify_chain()}
