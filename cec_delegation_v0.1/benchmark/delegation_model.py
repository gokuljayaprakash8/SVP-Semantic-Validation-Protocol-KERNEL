import json
import sys


def execute_delegation(case):
    state = {
        "dataset_accessed": False,
        "analysis_created": False,
        "artifact_prepared": False,
        "externalized": False,
    }

    observed_effects = []

    for action in case["actions"]:
        effect = action["declared_effect"]
        observed_effects.append(effect)

        if effect == "INTERNAL_READ":
            state["dataset_accessed"] = True

        elif effect == "INTERNAL_DERIVE":
            if state["dataset_accessed"]:
                state["analysis_created"] = True

        elif effect == "INTERNAL_PREPARE":
            if state["analysis_created"]:
                state["artifact_prepared"] = True

    # Critical compositional transition:
    # individually authorized delegated effects produce
    # an aggregate effect outside the delegated boundary.
    if (
        state["dataset_accessed"]
        and state["analysis_created"]
        and state["artifact_prepared"]
    ):
        state["externalized"] = True
        observed_effects.append("EXTERNAL_TRANSFER")

    return {
        "state": state,
        "observed_effects": observed_effects,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python benchmark/delegation_model.py <case.json>"
        )

    with open(sys.argv[1], encoding="utf-8") as f:
        case = json.load(f)

    result = execute_delegation(case)

    print("=== CEC DELEGATION MODEL ===")
    print("CASE ID:", case["case_id"])
    print("STATE:", result["state"])
    print("OBSERVED EFFECTS:", result["observed_effects"])
    print(
        "EXTERNAL_TRANSFER:",
        "EXTERNAL_TRANSFER" in result["observed_effects"],
    )
