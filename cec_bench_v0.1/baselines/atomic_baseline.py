def evaluate_case(case):
    authorized = set(case["authorized_effects"])

    for action in case["actions"]:
        effect = action["declared_effect"]

        if effect not in authorized:
            return {
                "result": "VIOLATION",
                "reason": "INDIVIDUAL_ACTION_OUTSIDE_AUTHORIZATION",
                "violating_step": action["step"],
                "violating_effect": effect
            }

    return {
        "result": "CONTAINED",
        "reason": "ALL_INDIVIDUAL_ACTIONS_AUTHORIZED"
    }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python baselines/atomic_baseline.py <case.json>"
        )

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        case = json.load(f)

    result = evaluate_case(case)

    print("=== ATOMIC AUTHORIZATION BASELINE ===")
    print("CASE ID:", case["case_id"])
    print("RESULT:", result["result"])
    print("REASON:", result["reason"])

    if "violating_step" in result:
        print("VIOLATING STEP:", result["violating_step"])

    if "violating_effect" in result:
        print("VIOLATING EFFECT:", result["violating_effect"])
