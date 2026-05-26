from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = SentenceTransformer('all-MiniLM-L6-v2')

# Your exact rules from the Colab notebook
POLICY_RULES = [
    "delete database or drop table",
    "transfer money to unknown account",
    "bypass security or authentication",
    "access unauthorized files",
    "execute kernel bypass",
    "send data to external server",
    "override admin permissions",
    "disable logging or audit trail",
    "expose private credentials or API keys",
    "mass delete or bulk remove records"
]

policy_vectors = model.encode(POLICY_RULES)

def get_severity(score):
    if score > 0.75: return "CRITICAL"
    elif score > 0.6: return "HIGH"
    elif score > 0.45: return "MEDIUM"
    else: return "LOW"

def get_risk_explanation(rule):
    if "delete" in rule: return "Potential data loss"
    if "transfer" in rule: return "Potential unintended financial transaction"
    if "access" in rule: return "Unauthorized data access risk"
    if "bypass" in rule: return "Security vulnerability risk"
    if "expose" in rule: return "Sensitive data exposure risk"
    return "General system risk"

def svp_kernel(action_text):
    action_vector = model.encode([action_text])
    similarities = cosine_similarity(action_vector, policy_vectors)[0]
    max_score = float(np.max(similarities))
    matched_rule = POLICY_RULES[int(np.argmax(similarities))]
    severity = get_severity(max_score)
    decision = "BLOCK" if severity in ["MEDIUM", "HIGH", "CRITICAL"] else "PASS"
    return {
        "action": action_text,
        "decision": decision,
        "severity": severity,
        "score": round(max_score, 4),
        "risk": get_risk_explanation(matched_rule)
    }

class WorkflowRequest(BaseModel):
    steps: list[str]

@app.post("/v1/audit")
def audit_workflow(req: WorkflowRequest):
    results = [svp_kernel(step) for step in req.steps]
    return {"results": results}
  
