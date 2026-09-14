import hashlib
import hmac
import json

from fastapi.testclient import TestClient
from app import app


SECRET = b"svp-v05-11-joint-intent"
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


def make_child(parent, **overrides):
    child = {
        "identity": "agent-002",
        "authority": parent["authority"],
        "purpose": parent["purpose"],
        "resource": parent["resource"],
        "action": parent["action"],
        "parent_commitment": parent["commitment"],
    }

    child.update(overrides)

    # Deliberately recompute the commitment.
    # Therefore cryptographic integrity alone cannot detect
    # an intentionally constructed alternate authorization.
    child["commitment"] = commitment(child)

    return child


def semantic_intent_allows(parent, child):
    if child["purpose"] != parent["purpose"]:
        return False, "PURPOSE DRIFT"

    if child["resource"] != parent["resource"]:
        return False, "RESOURCE DRIFT"

    if child["action"] != parent["action"]:
        return False, "ACTION DRIFT"

    if child["authority"] != parent["authority"]:
        return False, "AUTHORITY DRIFT"

    return True, "JOINT INTENT PRESERVED"


def verify(parent, child):
    parent_valid = hmac.compare_digest(
        parent["commitment"],
        commitment(parent),
    )

    child_valid = hmac.compare_digest(
        child["commitment"],
        commitment(child),
    )

    lineage_valid = (
        child["parent_commitment"] == parent["commitment"]
    )

    if not parent_valid:
        return False, "PARENT COMMITMENT INVALID"

    if not child_valid:
        return False, "CHILD COMMITMENT INVALID"

    if not lineage_valid:
        return False, "PARENT LINEAGE INVALID"

    parent_audit = real_svp_audit(parent["action"])
    child_audit = real_svp_audit(child["action"])

    if parent_audit["decision"] != "PASS":
        return False, "PARENT SVP DENIED"

    if child_audit["decision"] != "PASS":
        return False, "CHILD SVP DENIED"

    allowed, reason = semantic_intent_allows(
        parent,
        child,
    )

    if not allowed:
        return False, reason

    return True, "JOINT INTENT PRESERVED"


def run_case(name, child_overrides, expected):
    parent = make_root()
    child = make_child(
        parent,
        **child_overrides,
    )

    accepted, outcome = verify(
        parent,
        child,
    )

    passed = accepted == expected

    print()
    print("CASE:", name)
    print("PARENT PURPOSE:", parent["purpose"])
    print("CHILD PURPOSE:", child["purpose"])
    print("PARENT RESOURCE:", parent["resource"])
    print("CHILD RESOURCE:", child["resource"])
    print("PARENT ACTION:", parent["action"])
    print("CHILD ACTION:", child["action"])
    print("PARENT AUTHORITY:", parent["authority"])
    print("CHILD AUTHORITY:", child["authority"])

    print(
        "PARENT COMMITMENT VALID:",
        hmac.compare_digest(
            parent["commitment"],
            commitment(parent),
        ),
    )

    print(
        "CHILD COMMITMENT VALID:",
        hmac.compare_digest(
            child["commitment"],
            commitment(child),
        ),
    )

    print("EXPECTED ACCEPTANCE:", expected)
    print("ACTUAL ACCEPTANCE:", accepted)
    print("OUTCOME:", outcome)
    print("EXPECTATION MET:", passed)

    return passed


def main():
    print("SVP v0.5.11 JOINT-INTENT DELEGATION")
    print("=" * 60)

    cases = [
        (
            "EXACT JOINT INTENT",
            {},
            True,
        ),
        (
            "ACTION ESCALATION",
            {
                "action": "delete synthetic://dataset/record-001",
            },
            False,
        ),
        (
            "RESOURCE ESCALATION",
            {
                "resource": "synthetic://dataset/secret",
            },
            False,
        ),
        (
            "AUTHORITY ESCALATION",
            {
                "authority": "admin",
            },
            False,
        ),
        (
            "PURPOSE ESCALATION",
            {
                "purpose": "commercial optimization",
            },
            False,
        ),
        (
            "COMBINED ESCALATION",
            {
                "purpose": "commercial optimization",
                "resource": "synthetic://dataset/secret",
                "action": "delete synthetic://dataset/secret",
                "authority": "admin",
            },
            False,
        ),
    ]

    results = []

    for name, overrides, expected in cases:
        results.append(
            run_case(
                name,
                overrides,
                expected,
            )
        )

    print()
    print("SVP v0.5.11 SUMMARY")
    print("=" * 60)
    print("TOTAL CASES:", len(results))
    print("PASSED CASES:", sum(results))
    print("FAILED CASES:", len(results) - sum(results))

    if all(results):
        print("EXPERIMENT STATUS: PASS")
    else:
        print("EXPERIMENT STATUS: FINDING")


if __name__ == "__main__":
    main()
