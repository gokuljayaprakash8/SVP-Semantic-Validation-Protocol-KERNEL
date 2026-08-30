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

    record["authorization_id"] = record["request_commitment"]

    return record


def execute(action, record):
    if record is None:
        return False, "EXECUTION DENIED: NO DECISION"

    # Integrity and request binding MUST be checked first.
    valid, reason = verify_bound_decision(action, record)

    if not valid:
        return False, f"EXECUTION DENIED: {reason}"

    # Replay check happens only after the authorization is proven valid.
    authorization_id = record["authorization_id"]

    if authorization_id in CONSUMED:
        return False, "EXECUTION DENIED: REPLAY"

    # Consume only after every verification succeeds.
    CONSUMED.add(authorization_id)
    EXECUTED.append(action)

    return True, "EXECUTION AUTHORIZED"


def check(name, actual, expected):
    passed = actual == expected
    print(f"CASE: {name}")
    print("RESULT:", actual)
    print("EXPECTED:", expected)
    print("EXPECTATION MET:", passed)
    print()
    return passed


def main():
    print("=" * 60)
    print("SVP v0.6.1 CLEAN EXECUTION-GATE REGRESSION")
    print("=" * 60)

    action = "read synthetic://dataset/record-001"

    results = []

    # 1. No authorization
    ok, reason = execute(action, None)
    results.append(check(
        "NO DECISION",
        (ok, reason),
        (False, "EXECUTION DENIED: NO DECISION"),
    ))

    # 2. Valid authorization
    record = authorize(action)
    ok, reason = execute(action, record)
    results.append(check(
        "FIRST EXECUTION",
        (ok, reason),
        (True, "EXECUTION AUTHORIZED"),
    ))

    # 3. Replay of the exact valid authorization
    ok, reason = execute(action, record)
    results.append(check(
        "REPLAY",
        (ok, reason),
        (False, "EXECUTION DENIED: REPLAY"),
    ))

    # 4. Fresh authorization, then forge the request/action.
    record = authorize(action)
    forged_action = "delete synthetic://dataset/secret"
    ok, reason = execute(forged_action, record)
    results.append(check(
        "FORGED ACTION",
        (ok, reason),
        (False, "EXECUTION DENIED: REQUEST BINDING INVALID"),
    ))

    # 5. Fresh authorization, then mutate the decision.
    record = authorize(action)
    record["decision"] = "BLOCK"
    ok, reason = execute(action, record)
    results.append(check(
        "DECISION MUTATION",
        (ok, reason),
        (False, "EXECUTION DENIED: DECISION COMMITMENT INVALID"),
    ))

    # 6. Fresh authorization, then mutate the rule.
    record = authorize(action)
    record["rule_id"] = "ADMIN-UNRESTRICTED"
    ok, reason = execute(action, record)
    results.append(check(
        "RULE MUTATION",
        (ok, reason),
        (False, "EXECUTION DENIED: DECISION COMMITMENT INVALID"),
    ))

    print("=" * 60)
    print("TOTAL CASES:", len(results))
    print("PASSED CASES:", sum(results))
    print("FAILED CASES:", len(results) - sum(results))
    print("EXECUTED ACTIONS:", EXECUTED)
    print("CONSUMED AUTHORIZATIONS:", len(CONSUMED))

    all_passed = all(results)

    print("=" * 60)
    print("EXPERIMENT STATUS:", "PASS" if all_passed else "FINDING")
    print("=" * 60)


if __name__ == "__main__":
    main()
