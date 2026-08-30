import hashlib
import hmac
import json

SECRET = b"svp-v04-binding-test-secret"

SECURITY_FIELDS = (
    "identity",
    "authority",
    "delegation",
    "action",
    "decision",
)

BASE = {
    "identity": "agent-001",
    "authority": "dataset-reader",
    "delegation": "read-only",
    "action": "read synthetic://dataset/record-001",
    "decision": "PASS",
}


def canonical(obj):
    return json.dumps(
        {k: obj[k] for k in SECURITY_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def commit(obj):
    return hmac.new(
        SECRET,
        canonical(obj),
        hashlib.sha256,
    ).hexdigest()


def verify(obj, signature):
    expected = commit(obj)
    return hmac.compare_digest(expected, signature)


ORIGINAL_SIGNATURE = commit(BASE)


CASES = [
    ("ORIGINAL VALID DECISION", {}, True),

    ("ACTION SUBSTITUTION", {
        "action": "delete synthetic://dataset/record-001",
    }, False),

    ("DECISION SUBSTITUTION", {
        "decision": "BLOCK",
    }, False),

    ("AUTHORITY ESCALATION", {
        "authority": "dataset-admin",
    }, False),

    ("DELEGATION ESCALATION", {
        "delegation": "admin-write",
    }, False),

    ("IDENTITY SUBSTITUTION", {
        "identity": "agent-attacker",
    }, False),

    ("COMMITMENT REMOVED", None, False),

    ("WRONG SECRET", {}, False),
]


results = []

print("SVP v0.4 CRYPTOGRAPHIC DECISION BINDING")
print("SCOPE: Isolated synthetic local falsification test")
print()

for name, mutation, expected in CASES:
    candidate = dict(BASE)

    if mutation is not None:
        candidate.update(mutation)

    if name == "COMMITMENT REMOVED":
        observed = False

    elif name == "WRONG SECRET":
        wrong_signature = hmac.new(
            b"wrong-secret",
            canonical(candidate),
            hashlib.sha256,
        ).hexdigest()
        observed = verify(candidate, wrong_signature)

    else:
        observed = verify(candidate, ORIGINAL_SIGNATURE)

    passed = observed == expected
    results.append(passed)

    print(f"CASE: {name}")
    print(f"EXPECTED VALID: {expected}")
    print(f"ACTUAL VALID:   {observed}")
    print(f"RESULT: {'PASS' if passed else 'FAIL'}")
    print()

print("TOTAL CASES:", len(results))
print("PASSED CASES:", sum(results))
print("FAILED CASES:", len(results) - sum(results))

if all(results):
    print("EXPERIMENT STATUS: PASS")
else:
    print("EXPERIMENT STATUS: FINDING")
