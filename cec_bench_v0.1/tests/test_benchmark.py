import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmark.oracle import evaluate_file
from baselines.atomic_baseline import evaluate_case


def load_case(case_id):
    with open(
        ROOT / "cases" / f"{case_id}.json",
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def test_case_001_violation():
    result = evaluate_file(ROOT / "cases/CEC-BENCH-001.json")

    assert result["result"] == "VIOLATION"
    assert result["expected_violation"] is True
    assert result["oracle_consistent"] is True


def test_case_002_contained():
    result = evaluate_file(ROOT / "cases/CEC-BENCH-002.json")

    assert result["result"] == "CONTAINED"
    assert result["expected_violation"] is False
    assert result["oracle_consistent"] is True


def test_case_004_composition_violation():
    result = evaluate_file(ROOT / "cases/CEC-BENCH-004.json")

    assert result["result"] == "VIOLATION"
    assert "EXTERNAL_TRANSFER" in result["unauthorized_effects"]
    assert result["oracle_consistent"] is True


def test_atomic_baseline_misses_case_004():
    case = load_case("CEC-BENCH-004")
    baseline = evaluate_case(case)

    assert baseline["result"] == "CONTAINED"


def test_case_004_is_candidate_gap():
    oracle = evaluate_file(ROOT / "cases/CEC-BENCH-004.json")

    case = load_case("CEC-BENCH-004")
    baseline = evaluate_case(case)

    assert oracle["result"] == "VIOLATION"
    assert baseline["result"] == "CONTAINED"
    assert oracle["result"] != baseline["result"]


def test_case_005_order_variation_contained():
    result = evaluate_file(ROOT / "cases/CEC-BENCH-005.json")

    assert result["case_id"] == "CEC-BENCH-005"
    assert result["result"] == "CONTAINED"
    assert result["expected_violation"] is False
    assert result["unauthorized_effects"] == []
    assert result["oracle_consistent"] is True


if __name__ == "__main__":
    print("=== CEC-BENCH SELF-TEST ===")

    tests = [
        test_case_001_violation,
        test_case_002_contained,
        test_case_004_composition_violation,
        test_atomic_baseline_misses_case_004,
        test_case_004_is_candidate_gap,
        test_case_005_order_variation_contained
    ]

    for test in tests:
        test()
        print("PASS:", test.__name__)

    print("ALL TESTS PASSED")
