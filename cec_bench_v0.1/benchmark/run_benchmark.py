import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmark.oracle import evaluate_file
from benchmark.composition_model import execute_composition
from baselines.atomic_baseline import evaluate_case


CASES_DIR = ROOT / "cases"
OUTPUT_PATH = ROOT / "benchmark" / "results.json"


def load_case(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_case_path(path):
    case = load_case(path)

    # Cases with pre-declared observed effects use the
    # independent benchmark oracle directly.
    if "observed_effects" in case:
        oracle = evaluate_file(path)
        oracle_result = oracle["result"]
        unauthorized = oracle["unauthorized_effects"]

    # Execution-derived cases generate observed effects
    # through the deterministic composition model.
    else:
        execution = execute_composition(case)

        authorized = set(case["authorized_effects"])
        observed = set(execution["observed_effects"])

        unauthorized = sorted(observed - authorized)

        oracle_result = (
            "VIOLATION"
            if unauthorized
            else "CONTAINED"
        )

    baseline = evaluate_case(case)

    return {
        "case_id": case["case_id"],
        "oracle_result": oracle_result,
        "baseline_result": baseline["result"],
        "agreement": oracle_result == baseline["result"],
        "baseline_missed_violation": (
            oracle_result == "VIOLATION"
            and baseline["result"] == "CONTAINED"
        ),
        "unauthorized_effects": unauthorized
    }


def run():
    case_paths = sorted(CASES_DIR.glob("CEC-BENCH-*.json"))

    results = []

    for path in case_paths:
        results.append(evaluate_case_path(path))

    violations = sum(
        r["oracle_result"] == "VIOLATION"
        for r in results
    )

    contained = sum(
        r["oracle_result"] == "CONTAINED"
        for r in results
    )

    missed = sum(
        r["baseline_missed_violation"]
        for r in results
    )

    output = {
        "version": "0.1",
        "benchmark": "CEC-BENCH",
        "case_count": len(results),
        "violation_count": violations,
        "contained_count": contained,
        "baseline_missed_violation_count": missed,
        "results": results
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, sort_keys=True)

    print("=== CEC-BENCH v0.1 ===")
    print("CASES:", len(results))
    print("VIOLATIONS:", violations)
    print("CONTAINED:", contained)
    print(
        "BASELINE MISSED VIOLATIONS:",
        missed
    )

    for result in results:
        print(
            result["case_id"],
            "| ORACLE=", result["oracle_result"],
            "| BASELINE=", result["baseline_result"],
            "| AGREEMENT=", result["agreement"],
            "| MISSED=",
            result["baseline_missed_violation"]
        )

    print("RESULTS FILE:", OUTPUT_PATH)


if __name__ == "__main__":
    run()
