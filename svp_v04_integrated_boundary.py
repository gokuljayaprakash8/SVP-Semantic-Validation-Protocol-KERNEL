import hashlib
import hmac

SECRET = b"svp-v04-integrated-test-secret"


def canonical_security(obj):
    fields = (
        "identity",
        "action",
        "resource",
        "authority",
        "delegation_depth",
        "max_delegation_depth",
        "expiry",
    )
    return "|".join(f"{k}={obj[k]}" for k in fields).encode()


def commit(obj):
    return hmac.new(
        SECRET,
        canonical_security(obj),
        hashlib.sha256,
    ).hexdigest()


def verify_commitment(obj, commitment):
    return hmac.compare_digest(commit(obj), commitment)


def security_projection(obj):
    # Independent projection of the committed security state.
    return {
        "identity": obj["identity"],
        "action": obj["action"],
        "resource": obj["resource"],
        "authority": obj["authority"],
        "delegation_depth": obj["delegation_depth"],
        "max_delegation_depth": obj["max_delegation_depth"],
        "expiry": obj["expiry"],
    }


def execution_gate(decision):
    # Same fail-closed invariant established by the runtime regression.
    if decision != "CLEAR":
        raise RuntimeError("EXECUTION DENIED")
    return "EXECUTED"


BASE = {
    "identity": "agent-001",
    "action": "read_record",
    "resource": "synthetic://dataset/record-001",
    "authority": "read",
    "delegation_depth": 0,
    "max_delegation_depth": 1,
    "expiry": 4102444800,
}


CASES = [
    {
        "name": "authorized read",
        "expected": "PASS",
        "mutation": {},
    },
    {
        "name": "authority escalation",
        "expected": "BLOCK",
        "mutation": {"authority": "read_write"},
    },
    {
        "name": "action escalation",
        "expected": "BLOCK",
        "mutation": {"action": "delete_record"},
    },
    {
        "name": "delegation escalation",
        "expected": "BLOCK",
        "mutation": {"delegation_depth": 2},
    },
    {
        "name": "identity substitution",
        "expected": "BLOCK",
        "mutation": {"identity": "agent-evil"},
    },
]


results = []

for case in CASES:
    mutated = dict(BASE)
    mutated.update(case["mutation"])

    original_commitment = commit(BASE)

    commitment_valid = verify_commitment(
        mutated,
        original_commitment,
    )

    projected = security_projection(mutated)

    security_ok = (
        projected == security_projection(BASE)
    )

    expected = case["expected"]

    # Authorization decision derived from commitment integrity
    # and projected security state.
    if commitment_valid and security_ok:
        decision = "CLEAR"
    else:
        decision = "BLOCKED"

    try:
        outcome = execution_gate(
            "CLEAR" if decision == "CLEAR" else "BLOCKED"
        )
        executed = outcome == "EXECUTED"
    except RuntimeError:
        outcome = "DENIED"
        executed = False

    expected_execution = expected == "PASS"
    passed = executed == expected_execution

    results.append(passed)

    print(f"CASE: {case['name']}")
    print(f"  EXPECTED: {expected}")
    print(f"  COMMITMENT_VALID: {commitment_valid}")
    print(f"  SECURITY_PROJECTION_MATCH: {security_ok}")
    print(f"  DECISION: {decision}")
    print(f"  OUTCOME: {outcome}")
    print(f"  EXECUTION_EXPECTATION_MET: {passed}")
    print()


passed = sum(results)
total = len(results)

print("SVP v0.4 INTEGRATED BOUNDARY FALSIFICATION")
print("SCOPE: Synthetic local test only")
print(f"TOTAL CASES: {total}")
print(f"PASSED CASES: {passed}")
print(f"FAILED CASES: {total - passed}")

if passed == total:
    print("EXPERIMENT STATUS: PASS")
else:
    print("EXPERIMENT STATUS: FINDING")
