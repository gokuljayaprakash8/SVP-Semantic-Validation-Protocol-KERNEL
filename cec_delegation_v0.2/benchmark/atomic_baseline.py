import json
import sys


def evaluate_case(case):
    authorities = {
        a["authority_id"]: a
        for a in case["authorities"]
    }

    for action in case["actions"]:
        authority_id = action["authority_id"]

        if authority_id not in authorities:
            return {
                "case_id": case["case_id"],
                "result": "VIOLATION",
                "reason": "UNKNOWN_AUTHORITY"
            }

        authority = authorities[authority_id]

        if action["declared_effect"] not in authority["delegated_effects"]:
            return {
                "case_id": case["case_id"],
                "result": "VIOLATION",
                "reason": "INDIVIDUAL_DELEGATED_ACTION_UNAUTHORIZED"
            }

    return {
        "case_id": case["case_id"],
        "result": "CONTAINED",
        "reason": "ALL_INDIVIDUAL_DELEGATED_ACTIONS_AUTHORIZED"
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python benchmark/atomic_baseline.py <case.json>"
        )

    with open(sys.argv[1], encoding="utf-8") as f:
        case = json.load(f)

    result = evaluate_case(case)

    print("=== CEC DELEGATION v0.2 ATOMIC BASELINE ===")
    print("CASE ID:", result["case_id"])
    print("RESULT:", result["result"])
    print("REASON:", result["reason"])
