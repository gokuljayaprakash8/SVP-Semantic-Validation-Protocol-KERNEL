import json
import sys


def evaluate_case(case):
    authorized = set(case["delegated_authorized_effects"])

    declared_effects = {
        action["declared_effect"]
        for action in case["actions"]
    }

    unauthorized_declared = sorted(
        declared_effects - authorized
    )

    # The aggregate effect is independently defined by the
    # case's authorization boundary.
    aggregate_effect = case["unauthorized_aggregate_effect"]

    unauthorized_effects = list(unauthorized_declared)

    if aggregate_effect not in authorized:
        unauthorized_effects.append(aggregate_effect)

    unauthorized_effects = sorted(set(unauthorized_effects))

    result = (
        "VIOLATION"
        if unauthorized_effects
        else "CONTAINED"
    )

    expected_violation = case["expected_violation"]

    return {
        "case_id": case["case_id"],
        "result": result,
        "unauthorized_effects": unauthorized_effects,
        "expected_violation": expected_violation,
        "oracle_consistent": (
            expected_violation == (result == "VIOLATION")
        ),
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python benchmark/oracle.py <case.json>"
        )

    with open(sys.argv[1], encoding="utf-8") as f:
        case = json.load(f)

    result = evaluate_case(case)

    print("=== CEC DELEGATION DETERMINISTIC ORACLE ===")
    print("CASE ID:", result["case_id"])
    print("RESULT:", result["result"])
    print("UNAUTHORIZED EFFECTS:", result["unauthorized_effects"])
    print("EXPECTED VIOLATION:", result["expected_violation"])
    print("ORACLE CONSISTENT:", result["oracle_consistent"])
