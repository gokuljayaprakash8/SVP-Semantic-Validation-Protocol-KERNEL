import json
import sys

from delegation_model import execute_delegation


def evaluate_case(case):
    result = execute_delegation(case)

    child_authorities = {
        a["authority_id"]: a
        for a in case["authorities"]
    }

    unauthorized_effects = set()

    for action in result["authority_trace"]:
        authority = child_authorities[action["authority_id"]]

        effect = action["effect"]

        if effect not in authority["delegated_effects"]:
            unauthorized_effects.add(effect)

    aggregate_effect = case["unauthorized_aggregate_effect"]

    if aggregate_effect in result["observed_effects"]:
        unauthorized_effects.add(aggregate_effect)

    if unauthorized_effects:
        oracle_result = "VIOLATION"
    else:
        oracle_result = "CONTAINED"

    expected_violation = case["expected_violation"]

    return {
        "case_id": case["case_id"],
        "result": oracle_result,
        "unauthorized_effects": sorted(unauthorized_effects),
        "expected_violation": expected_violation,
        "oracle_consistent": (
            expected_violation
            == (oracle_result == "VIOLATION")
        )
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python benchmark/oracle.py <case.json>"
        )

    with open(sys.argv[1], encoding="utf-8") as f:
        case = json.load(f)

    result = evaluate_case(case)

    print("=== CEC DELEGATION v0.2 DETERMINISTIC ORACLE ===")
    print("CASE ID:", result["case_id"])
    print("RESULT:", result["result"])
    print("UNAUTHORIZED EFFECTS:",
          result["unauthorized_effects"])
    print("EXPECTED VIOLATION:",
          result["expected_violation"])
    print("ORACLE CONSISTENT:",
          result["oracle_consistent"])
