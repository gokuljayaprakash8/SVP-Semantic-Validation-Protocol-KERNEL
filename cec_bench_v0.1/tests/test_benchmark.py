import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmark.oracle import evaluate_file
from benchmark.composition_model import execute_composition
from baselines.atomic_baseline import evaluate_case


def load_case(case_id):
    path = ROOT / "cases" / f"{case_id}.json"

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_case_001_violation():
    result = evaluate_file(
        ROOT / "cases" / "CEC-BENCH-001.json"
    )

    assert result["result"] == "VIOLATION"
    assert result["oracle_consistent"] is True


def test_case_002_contained():
    result = evaluate_file(
        ROOT / "cases" / "CEC-BENCH-002.json"
    )

    assert result["result"] == "CONTAINED"
    assert result["oracle_consistent"] is True


def test_case_004_composition_violation():
    case = load_case("CEC-BENCH-004")

    execution = execute_composition(case)

    authorized = set(case["authorized_effects"])
    observed = set(execution["observed_effects"])

    assert "EXTERNAL_TRANSFER" in observed
    assert "EXTERNAL_TRANSFER" not in authorized


def test_atomic_baseline_misses_case_004():
    case = load_case("CEC-BENCH-004")

    baseline = evaluate_case(case)

    assert baseline["result"] == "CONTAINED"


def test_case_004_is_candidate_gap():
    case = load_case("CEC-BENCH-004")

    execution = execute_composition(case)

    authorized = set(case["authorized_effects"])
    observed = set(execution["observed_effects"])

    oracle_result = (
        "VIOLATION"
        if observed - authorized
        else "CONTAINED"
    )

    baseline_result = evaluate_case(case)["result"]

    assert oracle_result == "VIOLATION"
    assert baseline_result == "CONTAINED"
    assert oracle_result != baseline_result


if __name__ == "__main__":
    tests = [
        test_case_001_violation,
        test_case_002_contained,
        test_case_004_composition_violation,
        test_atomic_baseline_misses_case_004,
        test_case_004_is_candidate_gap
    ]

    print("=== CEC-BENCH SELF-TEST ===")

    for test in tests:
        test()
        print("PASS:", test.__name__)

    print("ALL TESTS PASSED")
