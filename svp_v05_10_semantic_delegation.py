import hashlib
import hmac
import json

from fastapi.testclient import TestClient
from app import app


SECRET = b"svp-v05-10-semantic-delegation"
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
        "rule_id": step.get("rule_id"),
    }


def semantic_relation(parent, child):
    p = parent.lower().strip()
    c = child.lower().strip()

    if p == c:
        return "EQUIVALENT"

    # Explicit semantic substitutions/broadening.
    dangerous_pairs = [
        ("research", "commercial"),
        ("research", "marketing"),
        ("security", "surveillance"),
        ("audit", "advertising"),
        ("read", "delete"),
        ("analysis", "destruction"),
    ]

    for left, right in dangerous_pairs:
        if left in p and right in c:
            return "BROADER"

    # Conservative narrowing examples.
    if p in c:
        return "BROADER"

    if c in p:
        return "NARROWER"

    return "AMBIGUOUS"


def semantic_allows(parent, child):
    relation = semantic_relation(parent, child)

    # For this experiment:
    # exact equivalence and conservative narrowing are allowed.
    return relation in {"EQUIVALENT", "NARROWER"}, relation


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


def make_child(parent, purpose):
    child = {
        "identity": "agent-002",
        "authority": parent["authority"],
        "purpose": purpose,
        "resource": parent["resource"],
        "action": parent["action"],
        "parent_commitment": parent["commitment"],
    }

    # IMPORTANT:
    # Recompute the commitment.
    # This means cryptographic integrity alone cannot detect
    # the semantic alteration.
    child["commitment"] = commitment(child)

    return child


def verify(parent, child):
    parent_mac_valid = hmac.compare_digest(
        parent["commitment"],
        commitment(parent),
    )

    child_mac_valid = hmac.compare_digest(
        child["commitment"],
        commitment(child),
    )

    parent_link_valid = (
        child["parent_commitment"] == parent["commitment"]
    )

    semantic_ok, relation = semantic_allows(
        parent["purpose"],
        child["purpose"],
    )

    if not parent_mac_valid:
        return False, "PARENT COMMITMENT INVALID", relation

    if not child_mac_valid:
        return False, "CHILD COMMITMENT INVALID", relation

    if not parent_link_valid:
        return False, "PARENT LINK INVALID", relation

    if not semantic_ok:
        return False, f"SEMANTIC INTENT VIOLATION: {relation}", relation

    return True, "CHAIN ACCEPTED", relation


def run_case(name, child_purpose, expected):
    parent = make_root()
    child = make_child(parent, child_purpose)

    accepted, outcome, relation = verify(parent, child)

    passed = accepted == expected

    print()
    print("CASE:", name)
    print("PARENT PURPOSE:", parent["purpose"])
    print("CHILD PURPOSE:", child["purpose"])
    print("SEMANTIC RELATION:", relation)

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
    print("SVP v0.5.10 SEMANTICALLY ATTACKED DELEGATION")
    print("=" * 60)

    cases = [
        (
            "EXACT PURPOSE",
            "authorized dataset research",
            True,
        ),
        (
            "SAFE NARROWING",
            "authorized dataset research",
            True,
        ),
        (
            "PURPOSE BROADENING",
            "authorized dataset research marketing",
            False,
        ),
        (
            "PURPOSE SUBSTITUTION",
            "commercial optimization",
            False,
        ),
        (
            "SECURITY TO SURVEILLANCE",
            "security surveillance",
            False,
        ),
        (
            "RESEARCH TO COMMERCIAL",
            "commercial research",
            False,
        ),
    ]

    results = []

    for name, purpose, expected in cases:
        results.append(
            run_case(
                name,
                purpose,
                expected,
            )
        )

    print()
    print("SVP v0.5.10 SUMMARY")
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
