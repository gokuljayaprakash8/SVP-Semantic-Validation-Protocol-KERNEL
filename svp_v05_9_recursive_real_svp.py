import hashlib
import hmac
import json

from fastapi.testclient import TestClient
from app import app


SECRET = b"svp-v05-9-recursive-secret"
client = TestClient(app)


FIELDS = (
    "identity",
    "authority",
    "purpose",
    "resource",
    "action",
    "parent_commitment",
)


def canonicalize(binding):
    return json.dumps(
        {k: binding.get(k) for k in FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def commitment(binding):
    return hmac.new(
        SECRET,
        canonicalize(binding),
        hashlib.sha256,
    ).hexdigest()


def real_svp_audit(action):
    response = client.post(
        "/v1/audit",
        json={"steps": [action]},
    )
    response.raise_for_status()

    data = response.json()
    step = data["steps"][0]

    return {
        "overall": data["overall"],
        "decision": step["decision"],
        "score": step.get("score", 0.0),
        "threshold": step.get("threshold", 0.0),
        "rule_id": step.get("rule_id"),
    }


def make_root():
    binding = {
        "identity": "agent-001",
        "authority": "dataset-reader",
        "purpose": "authorized dataset research",
        "resource": "synthetic://dataset/record-001",
        "action": "read synthetic://dataset/record-001",
        "parent_commitment": None,
    }

    binding["commitment"] = commitment(binding)
    return binding


def delegate(parent, child_identity):
    child = {
        "identity": child_identity,
        "authority": parent["authority"],
        "purpose": parent["purpose"],
        "resource": parent["resource"],
        "action": parent["action"],
        "parent_commitment": parent["commitment"],
    }

    child["commitment"] = commitment(child)
    return child


def verify_hop(parent, child):
    parent_audit = real_svp_audit(parent["action"])
    child_audit = real_svp_audit(child["action"])

    if parent_audit["decision"] != "PASS":
        return False, "PARENT SEMANTIC DENIAL"

    if child_audit["decision"] != "PASS":
        return False, "CHILD SEMANTIC DENIAL"

    if not hmac.compare_digest(
        parent["commitment"],
        commitment(parent),
    ):
        return False, "PARENT COMMITMENT INVALID"

    if not hmac.compare_digest(
        child["commitment"],
        commitment(child),
    ):
        return False, "CHILD COMMITMENT INVALID"

    if child["parent_commitment"] != parent["commitment"]:
        return False, "PARENT LINK INVALID"

    if child["purpose"] != parent["purpose"]:
        return False, "PURPOSE DRIFT"

    if child["resource"] != parent["resource"]:
        return False, "RESOURCE DRIFT"

    if child["authority"] != parent["authority"]:
        return False, "AUTHORITY DRIFT"

    if child["action"] != parent["action"]:
        return False, "ACTION DRIFT"

    return True, "HOP ACCEPTED"


def run_chain(depth, mutate_at=None, mutation=None):
    root = make_root()
    current = root

    for hop in range(1, depth + 1):
        child = delegate(
            current,
            f"agent-{hop + 1:03d}",
        )

        if mutate_at == hop:
            child[mutation["field"]] = mutation["value"]

            # Deliberately DO NOT recompute the commitment.
            # This models an attacker modifying a committed delegation.
        accepted, reason = verify_hop(
            current,
            child,
        )

        if not accepted:
            return False, hop, reason

        current = child

    return True, depth, "CHAIN ACCEPTED"


def main():
    print("SVP v0.5.9 RECURSIVE REAL-SVP")
    print("=" * 60)

    passed = 0
    total = 0

    tests = [
        ("DEPTH 1", 1, None),
        ("DEPTH 5", 5, None),
        ("DEPTH 10", 10, None),
        ("DEPTH 25", 25, None),
        ("DEPTH 100", 100, None),

        (
            "PURPOSE MUTATION HOP 5",
            10,
            {
                "hop": 5,
                "field": "purpose",
                "value": "commercial advertising",
            },
        ),

        (
            "RESOURCE MUTATION HOP 7",
            10,
            {
                "hop": 7,
                "field": "resource",
                "value": "synthetic://dataset/secret",
            },
        ),

        (
            "AUTHORITY MUTATION HOP 3",
            10,
            {
                "hop": 3,
                "field": "authority",
                "value": "admin",
            },
        ),
    ]

    for name, depth, mutation in tests:
        total += 1

        if mutation is None:
            result = run_chain(depth)
        else:
            result = run_chain(
                depth,
                mutate_at=mutation["hop"],
                mutation=mutation,
            )

        accepted, hop, reason = result

        expected = mutation is None

        passed_case = accepted == expected
        passed += int(passed_case)

        print()
        print(f"CASE: {name}")
        print("DEPTH:", depth)
        print("EXPECTED ACCEPTANCE:", expected)
        print("ACTUAL ACCEPTANCE:", accepted)
        print("STOP/FINAL HOP:", hop)
        print("OUTCOME:", reason)
        print("EXPECTATION MET:", passed_case)

    print()
    print("SVP v0.5.9 SUMMARY")
    print("=" * 60)
    print("TOTAL CASES:", total)
    print("PASSED CASES:", passed)
    print("FAILED CASES:", total - passed)

    if passed == total:
        print("EXPERIMENT STATUS: PASS")
    else:
        print("EXPERIMENT STATUS: FINDING")


if __name__ == "__main__":
    main()
