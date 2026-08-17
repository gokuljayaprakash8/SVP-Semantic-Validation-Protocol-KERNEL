import json
import sys


def evaluate_case(case):
    authorized = set(case["delegated_authorized_effects"])

    for action in case["actions"]:
        if action["declared_effect"] not in authorized:
            return {
                "case_id": case["case_id"],
                "result": "VIOLATION",
                "reason": "INDIVIDUAL_DELEGATED_ACTION_UNAUTHORIZED",
            }

    return {
        "case_id": case["case_id"],
        "result": "CONTAINED",
        "reason": "ALL_INDIVIDUAL_DELEGATED_ACTIONS_AUTHORIZED",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python benchmark/atomic_baseline.py <case.json>"
        )

    with open(sys.argv[1], encoding="utf-8") as f:
        case = json.load(f)

    result = evaluate_case(case)

    print("=== DELEGATED ATOMIC AUTHORIZATION BASELINE ===")
    print("CASE ID:", result["case_id"])
    print("RESULT:", result["result"])
    print("REASON:", result["reason"])
