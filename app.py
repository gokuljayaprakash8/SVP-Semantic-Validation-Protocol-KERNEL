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
            "pattern": pattern,
        })

policy_vectors = np.array(list(model.embed(PATTERNS))) 
audit_logger = AuditLogger()

def get_severity(score):
    if score > 0.75: return "CRITICAL"
    elif score > 0.6: return "HIGH"
    elif score > 0.45: return "MEDIUM"
    else: return "LOW"
        
def svp_kernel(action_text):
    action_lower = action_text.lower()

    action_vector = np.array(list(model.embed([action_text])))
    similarities = cosine_similarity(action_vector, policy_vectors)[0]

    policy_scores = {}

    severity_bonus = {
        "CRITICAL": 0.05,
        "HIGH": 0.03,
        "MEDIUM": 0.01,
        "LOW": 0.00,
    }

    for i, similarity in enumerate(similarities):
        meta = PATTERN_META[i]
        pid = meta["id"]

        exact_bonus = 0.0
        if meta["pattern"].lower() in action_lower:
            exact_bonus = 0.10

        score = float(similarity) + exact_bonus + severity_bonus.get(meta["severity"], 0)

        if pid not in policy_scores or score > policy_scores[pid]["score"]:
            policy_scores[pid] = {
                "score": score,
                "similarity": float(similarity),
                "policy": meta,
            }

    best = max(policy_scores.values(), key=lambda x: x["score"])
policy = best["policy"]

margin = 0.05

sorted_scores = sorted(
    policy_scores.values(),
    key=lambda x: x["score"],
    reverse=True
)

second_score = sorted_scores[1]["score"] if len(sorted_scores) > 1 else 0

if (
    best["similarity"] >= policy["threshold"]
    and (best["score"] - second_score) >= margin
):
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

class WorkflowRequest(BaseModel):
    steps: list[str]

@app.post("/v1/audit")
def audit(req: WorkflowRequest):
    results = []

    for step in req.steps:
      try:
         decision = svp_kernel(step)
       except Exception as e:
         return {"error": str(e)}

        audit_event = audit_logger.create_event(decision, "1.0.0")
        audit_logger.save_event(audit_event)
        results.append(decision)

    blocked = [r for r in results if r["decision"] == "BLOCK"]

    return {
        "overall": "BLOCKED" if blocked else "CLEAR",
        "blocked_count": len(blocked),
        "steps": results,
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/audit/verify")
def verify_audit():
    return {"valid": audit_logger.verify_chain()}
