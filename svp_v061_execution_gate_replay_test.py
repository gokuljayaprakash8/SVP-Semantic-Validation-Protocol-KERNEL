from svp_v06_runtime_gate import (
    create_bound_decision,
    verify_bound_decision,
)

CONSUMED = set()
EXECUTED = []


def authorize(action):
    decision = {
        "decision": "PASS",
        "rule_id": "SAFE001",
        "threshold": 0.75,
    }

    record = create_bound_decision(action, decision)

    # Give this authorization a stable identity for this harness.
    record["authorization_id"] = record["request_commitment"]

    return record


def execute(action, record):
    if record is None:
        return False, "EXECUTION DENIED: NO DECISION"

    authorization_id = record["authorization_id"]

    if authorization_id in CONSUMED:
        return False, "EXECUTION DENIED: REPLAY"

    valid, reason = verify_bound_decision(action, record)

    if not valid:
        return False, f"EXECUTION DENIED: {reason}"

    # Consume only after verification succeeds.
    CONSUMED.add(authorization_id)
    EXECUTED.append(action)

    return True, "EXECUTION AUTHORIZED"


def main():
    print("=" * 60)
    print("SVP v0.6.1 COMPLETE EXECUTION-GATE TEST")
    print("=" * 60)

    action = "read synthetic://dataset/record-001"

    # 1. No authorization
    ok, reason = execute(action, None)
    print("CASE: NO DECISION")
    print("RESULT:", ok, reason)
    print("EXPECTED:", False)
    print()

    # 2. Fresh authorization
    record = authorize(action)
    ok, reason = execute(action, record)
    print("CASE: FIRST EXECUTION")
    print("RESULT:", ok, reason)
    print("EXPECTED:", True)
    print()

    # 3. Replay
    ok, reason = execute(action, record)
    print("CASE: REPLAY")
    print("RESULT:", ok, reason)
    print("EXPECTED:", False)
    print()

    # 4. Forged action
    forged = "delete synthetic://dataset/secret"
    fresh_record = authorize(action)
    ok, reason = execute(forged, fresh_record)
    print("CASE: FORGED ACTION")
    print("RESULT:", ok, reason)
    print("EXPECTED:", False)
    print()

    # 5. Decision mutation
    fresh_record = authorize(action)
    fresh_record["decision"] = "BLOCK"
    ok, reason = execute(action, fresh_record)
    print("CASE: DECISION MUTATION")
    print("RESULT:", ok, reason)
    print("EXPECTED:", False)
    print()

    # 6. Rule mutation
    fresh_record = authorize(action)
    fresh_record["rule_id"] = "ADMIN-UNRESTRICTED"
    ok, reason = execute(action, fresh_record)
    print("CASE: RULE MUTATION")
    print("RESULT:", ok, reason)
    print("EXPECTED:", False)
    print()

    print("=" * 60)
    print("EXECUTED ACTIONS:", EXECUTED)
    print("CONSUMED AUTHORIZATIONS:", len(CONSUMED))
    print("=" * 60)


if __name__ == "__main__":
    main()
