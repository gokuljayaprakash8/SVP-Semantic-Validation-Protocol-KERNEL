import json
import sys


def execute_delegation(case):
    authorities = {
        a["authority_id"]: a
        for a in case["authorities"]
    }

    # CEC delegation-integrity invariants:
    # - root authorities have no parent and depth 0
    # - delegated authorities must reference an existing parent
    # - child depth must equal parent depth + 1
    # - child delegated scope cannot exceed parent scope
    for authority_id, authority in authorities.items():
        parent_id = authority.get("parent_authority")
        depth = authority.get("delegation_depth")
        effects = set(authority.get("delegated_effects", []))

        if parent_id is None:
            if depth != 0:
                raise ValueError(
                    f"Invalid root delegation depth: {authority_id}"
                )
            continue

        # PARENT-001 is the implicit trusted root used by the CEC fixtures.
        # It is not represented in the authorities list.
        if parent_id == "PARENT-001":
            if depth != 1:
                raise ValueError(
                    f"Invalid root-child delegation depth: "
                    f"{authority_id} depth={depth}, expected=1"
                )
            continue

        if parent_id not in authorities:
            raise ValueError(
                f"Broken delegation lineage: "
                f"{authority_id} -> {parent_id}"
            )

        parent = authorities[parent_id]
        parent_depth = parent.get("delegation_depth")
        parent_effects = set(parent.get("delegated_effects", []))

        if depth != parent_depth + 1:
            raise ValueError(
                f"Invalid delegation depth: "
                f"{authority_id} depth={depth}, "
                f"expected={parent_depth + 1}"
            )

        if not effects.issubset(parent_effects):
            escalated = sorted(effects - parent_effects)
            raise ValueError(
                f"Delegation scope escalation: "
                f"{authority_id} exceeds {parent_id}: {escalated}"
            )

    state = {
        "dataset_accessed": False,
        "analysis_created": False,
        "artifact_prepared": False,
        "externalized": False
    }

    observed_effects = []
    authority_trace = []

    for action in case["actions"]:
        authority_id = action["authority_id"]

        if authority_id not in authorities:
            raise ValueError(
                f"Unknown authority: {authority_id}"
            )

        authority = authorities[authority_id]

        if action["declared_effect"] not in authority["delegated_effects"]:
            raise ValueError(
                f"Action effect outside delegated scope: "
                f"{action['declared_effect']}"
            )

        authority_trace.append({
            "authority_id": authority_id,
            "parent_authority": authority["parent_authority"],
            "delegation_depth": authority["delegation_depth"],
            "effect": action["declared_effect"]
        })

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

        if (
            state["dataset_accessed"]
            and state["analysis_created"]
            and state["artifact_prepared"]
        ):
            state["externalized"] = True

            if "EXTERNAL_TRANSFER" not in observed_effects:
                observed_effects.append("EXTERNAL_TRANSFER")

    return {
        "state": state,
        "observed_effects": observed_effects,
        "authority_trace": authority_trace
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python benchmark/delegation_model.py <case.json>"
        )

    with open(sys.argv[1], encoding="utf-8") as f:
        case = json.load(f)

    result = execute_delegation(case)

    print("=== CEC DELEGATION v0.2 MODEL ===")
    print("CASE ID:", case["case_id"])
    print("STATE:", result["state"])
    print("AUTHORITY TRACE:", result["authority_trace"])
    print("OBSERVED EFFECTS:", result["observed_effects"])
    print(
        "EXTERNAL_TRANSFER:",
        "EXTERNAL_TRANSFER" in result["observed_effects"]
    )
