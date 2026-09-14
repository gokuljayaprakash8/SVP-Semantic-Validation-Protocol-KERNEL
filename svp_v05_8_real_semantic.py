import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app import app


SECRET = b"svp-v05-8-real-semantic-secret"

client = TestClient(app)


def canonicalize(binding):
    fields = (
        "identity",
        "authority",
        "purpose",
        "resource",
        "action",
    )

    return json.dumps(
        {k: binding[k] for k in fields},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def commit(binding):
    return hmac.new(
        SECRET,
        canonicalize(binding),
        hashlib.sha256,
    ).hexdigest()


def audit(action):
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
        "severity": step.get("severity"),
    }


def verify(binding):
    supplied = binding.get("commitment")

    if not supplied:
        return False

    expected = commit(binding)

    return hmac.compare_digest(
        supplied,
        expected,
    )


def authorize_child(parent, child):
    parent_audit = audit(parent["action"])
    child_audit = audit(child["action"])

    if parent_audit["decision"] != "PASS":
        return False, "PARENT DENIED"

    if child_audit["decision"] != "PASS":
        return False, "CHILD DENIED"

    if child["purpose"] != parent["purpose"]:
        return False, "PURPOSE DRIFT"

    if child["resource"] != parent["resource"]:
        return False, "RESOURCE DRIFT"

    if child["authority"] != parent["authority"]:
        return False, "AUTHORITY DRIFT"

    if child["parent_commitment"] != parent["commitment"]:
        return False, "PARENT COMMITMENT INVALID"

    if not verify(parent):
        return False, "PARENT COMMITMENT INVALID"

    if not verify(child):
        return False, "CHILD COMMITMENT INVALID"

    return True, "CHAIN ACCEPTED"


def make_binding(
    identity,
    authority,
    purpose,
    resource,
    action,
    parent_commitment=None,
):
    binding = {
        "identity": identity,
        "authority": authority,
        "purpose": purpose,
        "resource": resource,
        "action": action,
    }

    if parent_commitment is not None:
        binding["parent_commitment"] = parent_commitment

    binding["commitment"] = commit(binding)

    return binding


def main():
    print("SVP v0.5.8 REAL SEMANTIC DELEGATION")
    print("=" * 60)

    parent = make_binding(
        identity="agent-001",
        authority="dataset-reader",
        purpose="authorized dataset research",
        resource="synthetic://dataset/record-001",
        action="read synthetic://dataset/record-001",
    )

    child = make_binding(
        identity="agent-002",
        authority="dataset-reader",
        purpose=parent["purpose"],
        resource=parent["resource"],
        action=parent["action"],
        parent_commitment=parent["commitment"],
    )

    accepted, outcome = authorize_child(parent, child)

    print("CASE: VALID REAL-SVP DELEGATION")
    print("PARENT DECISION:", audit(parent["action"])["decision"])
    print("CHILD DECISION:", audit(child["action"])["decision"])
    print("ACCEPTED:", accepted)
    print("OUTCOME:", outcome)
    print()

    mutated = dict(child)
    mutated["purpose"] = "commercial advertising"

    accepted, outcome = authorize_child(parent, mutated)

    print("CASE: PURPOSE MUTATION")
    print("ACCEPTED:", accepted)
    print("OUTCOME:", outcome)
    print()

    print("SVP v0.5.8 STATUS")


if __name__ == "__main__":
    main()
