from svp_v06_runtime_gate import (
    create_bound_decision,
    verify_bound_decision,
)

EXECUTED = []


def execute_tool(action, record=None):
    if record is None:
        return False, "EXECUTION DENIED: NO DECISION"

    valid, reason = verify_bound_decision(action, record)

    if not valid:
        return False, f"EXECUTION DENIED: {reason}"

    EXECUTED.append(action)
    return True, "EXECUTION AUTHORIZED"


def make_decision(action):
    decision = {
        "decision": "PASS",
        "rule_id": "SAFE001",
        "threshold": 0.75,
    }
    return create_bound_decision(action, decision)


def main():
    print("=" * 60)
    print("SVP v0.6.1 EXECUTION-GATE BYPASS TEST")
    print("=" * 60)

    action = "read synthetic://dataset/record-001"

    # 1. No authorization
    ok, reason = execute_tool(action)
    print("CASE: NO DECISION")
    print("RESULT:", ok, reason)
    print("EXPECTED:", False)
    print()

    # 2. Valid authorization
    record = make_decision(action)
    ok, reason = execute_tool(action, record)
    print("CASE: VALID AUTHORIZATION")
    print("RESULT:", ok, reason)
    print("EXPECTED:", True)
    print()

    # 3. Forged action
    forged_action = "delete synthetic://dataset/secret"
    ok, reason = execute_tool(forged_action, record)
    print("CASE: FORGED ACTION")
    print("RESULT:", ok, reason)
    print("EXPECTED:", False)
    print()

    # 4. Decision mutation
    mutated = dict(record)
    mutated["decision"] = "BLOCK"
    ok, reason = execute_tool(action, mutated)
    print("CASE: DECISION MUTATION")
    print("RESULT:", ok, reason)
    print("EXPECTED:", False)
    print()

    # 5. Rule mutation
    mutated = dict(record)
    mutated["rule_id"] = "ADMIN-UNRESTRICTED"
    ok, reason = execute_tool(action, mutated)
    print("CASE: RULE MUTATION")
    print("RESULT:", ok, reason)
    print("EXPECTED:", False)
    print()

    # 6. Replay
    ok, reason = execute_tool(action, record)
    print("CASE: SECOND EXECUTION")
    print("RESULT:", ok, reason)
    print("EXPECTED:", True)
    print()

    print("=" * 60)
    print("EXECUTIONS RECORDED:", EXECUTED)
    print("=" * 60)


if __name__ == "__main__":
    main()
