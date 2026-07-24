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

with open("policies/default.yaml", "r") as f:
    config = yaml.safe_load(f)

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

def get_severity(score):
    if score > 0.75: return "CRITICAL"
    elif score > 0.6: return "HIGH"
    elif score > 0.45: return "MEDIUM"
    else: return "LOW"

def svp_kernel(action_text):
    action_vector = np.array(list(model.embed([action_text])))

    similarities = cosine_similarity(action_vector, policy_vectors)[0]

    best_index = int(np.argmax(similarities))
    best_score = float(similarities[best_index])

    policy = PATTERN_META[best_index]

    decision = policy["action"] if best_score >= policy["threshold"] else "PASS"

    return {
        "action": action_text,
        "decision": decision,
        "rule_id": policy["id"],
        "matched_policy": policy["description"],
        "severity": policy["severity"] if decision != "PASS" else "LOW",
        "score": round(best_score, 4),
        "threshold": policy["threshold"],
    }

class WorkflowRequest(BaseModel):
    steps: list[str]

@app.post("/v1/audit")
def audit(req: WorkflowRequest):
    results = [svp_kernel(step) for step in req.steps]
    blocked = [r for r in results if r["decision"] == "BLOCK"]
    return {"overall": "BLOCKED" if blocked else "CLEAR", "blocked_count": len(blocked), "steps": results}

@app.get("/health")
def health():
    return {"status": "ok"}
