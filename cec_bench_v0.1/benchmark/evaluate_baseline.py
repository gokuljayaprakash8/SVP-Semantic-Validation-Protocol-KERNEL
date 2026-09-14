import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmark.oracle import evaluate_file
from baselines.atomic_baseline import evaluate_case


def load_case(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate(path):
    case = load_case(path)

    oracle = evaluate_file(path)
    baseline = evaluate_case(case)

    oracle_result = oracle["result"]
    baseline_result = baseline["result"]

    return {
        "case_id": case["case_id"],
        "oracle_result": oracle_result,
        "baseline_result": baseline_result,
        "agreement": oracle_result == baseline_result,
        "oracle_violation": oracle_result == "VIOLATION",
        "baseline_missed_violation": (
            oracle_result == "VIOLATION"
            and baseline_result == "CONTAINED"
        )
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python benchmark/evaluate_baseline.py <case.json>"
        )

    result = evaluate(sys.argv[1])

    print("=== BASELINE VS ORACLE ===")
    print("CASE ID:", result["case_id"])
    print("ORACLE:", result["oracle_result"])
    print("ATOMIC BASELINE:", result["baseline_result"])
    print("AGREEMENT:", result["agreement"])
    print(
        "BASELINE MISSED VIOLATION:",
        result["baseline_missed_violation"]
    )
