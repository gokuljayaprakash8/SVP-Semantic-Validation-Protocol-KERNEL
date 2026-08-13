from app import svp_kernel
from svp_v03_risk_aware_escalation import ranked_candidates, top_policy_metadata

TESTS = [
    "delete database logs",
    "archive database logs",
    "archive logs",
    "archive audit logs",
    "archive database records",
]

for action in TESTS:
    engine_result = svp_kernel(action)

    candidates = ranked_candidates(action)
    top = candidates[0]
    second = candidates[1]
    top_metadata = top_policy_metadata(top)

    score = engine_result["score"]
    threshold = engine_result["threshold"]
    margin = round(
        top["adjusted_score"] - second["adjusted_score"], 4
    )

    similarity_condition = score >= threshold
    margin_condition = margin >= 0.05
    high_risk = top_metadata["severity"] in {"CRITICAL", "HIGH"}

    if engine_result["decision"] == "BLOCK":
        v03_decision = "BLOCK"
    elif not similarity_condition:
        v03_decision = "PASS"
    elif not margin_condition and high_risk:
        v03_decision = "ESCALATE"
    else:
        v03_decision = "PASS"

    print("\n" + "=" * 70)
    print("INPUT:", repr(action))
    print("RAW DECISION:", engine_result["decision"])
    print("V0.3 DECISION:", v03_decision)
    print("RULE:", engine_result["rule_id"])
    print("SCORE:", score)
    print("THRESHOLD:", threshold)
    print("TOP POLICY:", top["policy_id"])
    print("TOP SEVERITY:", top_metadata["severity"])
    print("MARGIN:", margin)
    print("ESCALATION:", v03_decision == "ESCALATE")
