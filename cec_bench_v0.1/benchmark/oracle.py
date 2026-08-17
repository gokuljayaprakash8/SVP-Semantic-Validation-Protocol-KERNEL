import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_case(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def derive_observed_effects(case):
    from benchmark.composition_model import execute_composition

    execution = execute_composition(case)
    return execution["observed_effects"]


def evaluate_case(case):
    authorized = set(case["authorized_effects"])

    if "observed_effects" in case:
        observed = set(case["observed_effects"])
    else:
        observed = set(derive_observed_effects(case))

    unauthorized = sorted(observed - authorized)

    expected_violation = len(unauthorized) > 0

    result = (
        "VIOLATION"
        if expected_violation
        else "CONTAINED"
    )

    return {
        "case_id": case["case_id"],
        "result": result,
        "unauthorized_effects": unauthorized,
        "expected_violation": expected_violation,
        "oracle_consistent": (
            expected_violation == (result == "VIOLATION")
        )
    }


def evaluate_file(path):
    case = load_case(path)
    return evaluate_case(case)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python benchmark/oracle.py <case.json>"
        )

    result = evaluate_file(sys.argv[1])

    print("=== CEC-BENCH DETERMINISTIC ORACLE ===")
    print("CASE ID:", result["case_id"])
    print("RESULT:", result["result"])
    print(
        "UNAUTHORIZED EFFECTS:",
        result["unauthorized_effects"]
    )
    print(
        "EXPECTED VIOLATION:",
        result["expected_violation"]
    )
    print(
        "ORACLE CONSISTENT:",
        result["oracle_consistent"]
    )
