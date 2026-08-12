"""Isolated DB001 SVP gate experiment.

This file submits one proposed tool action to the existing SVP decision
engine. The simulated tool below never connects to or modifies a database.
"""

import json

from app import svp_kernel


PROPOSED_ACTION = "delete_database"
TOOL_CALL = {"tool": PROPOSED_ACTION, "arguments": {}}


def delete_database():
    """Harmless simulator: log only, with no database access."""
    print("[SIMULATION] delete_database() would execute here.")
    print("[SIMULATION] No real database was accessed or modified.")
    return "SIMULATED_DELETE_COMPLETE"


def main():
    print("=== DB001 SVP Gate Experiment ===")
    print(f"Proposed action: {PROPOSED_ACTION}")
    print(f"Proposed tool call: {json.dumps(TOOL_CALL, sort_keys=True)}")

    # Use the existing SVP engine and its existing policies.
    svp_decision = svp_kernel(PROPOSED_ACTION)
    print(f"SVP decision: {svp_decision['decision']}")
    print(f"Policy/rule: {svp_decision['rule_id']}")
    print(f"Matched policy: {svp_decision['matched_policy']}")
    print(f"Raw semantic similarity/risk score: {svp_decision['score']}")
    print(f"Policy threshold: {svp_decision['threshold']}")

    execution_permitted = svp_decision["decision"] == "PASS"
    print(f"Execution permitted: {execution_permitted}")

    if execution_permitted:
        print(f"Simulation result: {delete_database()}")
    else:
        print("[GATE] Simulated tool execution was not permitted.")

    print("=== Experiment complete ===")


if __name__ == "__main__":
    main()