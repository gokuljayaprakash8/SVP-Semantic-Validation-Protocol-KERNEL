import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmark.composition_model import execute_composition


def deterministic_oracle(authorized_effects, observed_effects):
    authorized = set(authorized_effects)
    observed = set(observed_effects)

    unauthorized = sorted(observed - authorized)

    return {
        "result": (
            "VIOLATION"
            if unauthorized
            else "CONTAINED"
        ),
        "unauthorized_effects": unauthorized
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python benchmark/run_execution_case.py <case.json>"
        )

    path = Path(sys.argv[1])

    with path.open("r", encoding="utf-8") as f:
        case = json.load(f)

    execution = execute_composition(case)

    oracle = deterministic_oracle(
        case["authorized_effects"],
        execution["observed_effects"]
    )

    print("=== CEC-BENCH EXECUTION-DERIVED CASE ===")
    print("CASE ID:", case["case_id"])
    print("STATE:", execution["state"])
    print("OBSERVED EFFECTS:", execution["observed_effects"])
    print("UNAUTHORIZED EFFECTS:", oracle["unauthorized_effects"])
    print("ORACLE RESULT:", oracle["result"])
