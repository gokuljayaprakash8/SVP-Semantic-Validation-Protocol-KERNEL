import hmac
import hashlib
import json
from app import svp_kernel


SECRET = b"SVP-v0.6-INTEGRATION-TEST"


def canonicalize(obj):
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def mac(obj):
    return hmac.new(
        SECRET,
        canonicalize(obj),
        hashlib.sha256,
    ).hexdigest()


def evaluate(action):
    return svp_kernel(action)


def create_bound_decision(action):
    decision = evaluate(action)

    record = {
        "action": action,
        "decision": decision["decision"],
        "rule_id": decision.get("rule_id"),
        "threshold": decision.get("threshold"),
        "policy_version": "live",
    }

    record["request_commitment"] = mac(
        {"action": action}
    )

    record["decision_commitment"] = mac(
        {
            "request_commitment":
                record["request_commitment"],
            "decision":
                record["decision"],
            "rule_id":
                record["rule_id"],
            "threshold":
                record["threshold"],
            "policy_version":
                record["policy_version"],
        }
    )

    return record


def verify_bound_decision(action, record):
    expected_request = mac(
        {"action": action}
    )

    if not hmac.compare_digest(
        expected_request,
        record["request_commitment"],
    ):
        return False, "REQUEST BINDING INVALID"

    expected_decision = mac(
        {
            "request_commitment":
                record["request_commitment"],
            "decision":
                record["decision"],
            "rule_id":
                record["rule_id"],
            "threshold":
                record["threshold"],
            "policy_version":
                record["policy_version"],
        }
    )

    if not hmac.compare_digest(
        expected_decision,
        record["decision_commitment"],
    ):
        return False, "DECISION COMMITMENT INVALID"

    return True, "DECISION VALID"


def main():
    print("=" * 60)
    print("SVP v0.6 REAL-KERNEL INTEGRATION BRIDGE")
    print("=" * 60)

    action = "read synthetic://dataset/record-001"

    record = create_bound_decision(action)

    valid, reason = verify_bound_decision(
        action,
        record,
    )

    print("ACTION:", action)
    print("LIVE DECISION:", record["decision"])
    print("RULE:", record["rule_id"])
    print("VERIFICATION:", valid)
    print("OUTCOME:", reason)

    print("=" * 60)


if __name__ == "__main__":
    main()
