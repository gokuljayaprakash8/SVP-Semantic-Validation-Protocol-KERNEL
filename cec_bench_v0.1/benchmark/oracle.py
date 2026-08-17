import json
from pathlib import Path


def evaluate_case(case):
    authorized = set(case["authorized_effects"])
    observed = set(case["observed_effects"])

    unauthorized = sorted(
        effect for effect in observed
        if effect not in authorized
    )

    violation = len(unauthorized) > 0

    expected = case["expected_violation"]

    if violation != expected:
        raise ValueError(
            f"CASE ORACLE MISMATCH: {case['case_id']} "
            f"expected_violation={expected} "
            f"but deterministic oracle produced {violation}"
        )

    return {
        "case_id": case["case_id"],
        "result": "VIOLATION" if violation else "CONTAINED",
        "violation": violation,
        "unauthorized_effects": unauthorized,
        "expected_violation": expected,
        "oracle_consistent": True
    }


def load_case(path):
    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_file(path):
    case = load_case(path)
    return evaluate_case(case)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python benchmark/oracle.py <case.json>"
        )

    result = evaluate_file(sys.argv[1])

    print("=== CEC-BENCH DETERMINISTIC ORACLE ===")
    print("CASE ID:", result["case_id"])
    print("RESULT:", result["result"])
    print("UNAUTHORIZED EFFECTS:", result["unauthorized_effects"])
    print("EXPECTED VIOLATION:", result["expected_violation"])
    print("ORACLE CONSISTENT:", result["oracle_consistent"])
