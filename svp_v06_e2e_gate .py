import hmac
import hashlib
import json
import secrets
from app import svp_kernel

SECRET = b"SVP-v0.6-E2E-TEST"
CONSUMED = set()

def canonicalize(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

def mac(obj):
    return hmac.new(SECRET, canonicalize(obj), hashlib.sha256).hexdigest()

def authorize(step):
    decision = svp_kernel(step)
    record = {
        "identity": "agent-001",
        "authority": "runtime-agent",
        "action": step,
        "purpose": "authorized runtime operation",
        "resource": step,
        "nonce": secrets.token_hex(16),
        "decision": decision["decision"],
        "rule_id": decision.get("rule_id"),
        "threshold": decision.get("threshold"),
    }
    record["request_commitment"] = mac({
        "identity": record["identity"],
        "authority": record["authority"],
        "action": record["action"],
        "purpose": record["purpose"],
        "resource": record["resource"],
        "nonce": record["nonce"],
    })
    record["decision_commitment"] = mac({
        "request_commitment": record["request_commitment"],
        "decision": record["decision"],
        "rule_id": record["rule_id"],
        "threshold": record["threshold"],
    })
    return record

def execute(step, record):
    if step != record["action"]:
        return False, "REQUEST BINDING INVALID"
    expected_request = mac({
        "identity": record["identity"],
        "authority": record["authority"],
        "action": record["action"],
        "purpose": record["purpose"],
        "resource": record["resource"],
        "nonce": record["nonce"],
    })
    if not hmac.compare_digest(expected_request, record["request_commitment"]):
        return False, "REQUEST BINDING INVALID"
    expected_decision = mac({
        "request_commitment": record["request_commitment"],
        "decision": record["decision"],
        "rule_id": record["rule_id"],
        "threshold": record["threshold"],
    })
    if not hmac.compare_digest(expected_decision, record["decision_commitment"]):
        return False, "DECISION COMMITMENT INVALID"
    if record["decision"] != "PASS":
        return False, "SVP DECISION DENIED"
    authorization_id = record["request_commitment"]
    if authorization_id in CONSUMED:
        return False, "REPLAY DENIED"
    CONSUMED.add(authorization_id)
    return True, "EXECUTION AUTHORIZED"

def main():
    print("=" * 60)
    print("SVP v0.6 END-TO-END GATE")
    print("=" * 60)
    step = "read synthetic://dataset/record-001"
    record = authorize(step)
    first, first_reason = execute(step, record)
    second, second_reason = execute(step, record)
    print("STEP:", step)
    print("LIVE DECISION:", record["decision"])
    print("RULE:", record["rule_id"])
    print("FIRST EXECUTION:", first)
    print("FIRST OUTCOME:", first_reason)
    print("REPLAY EXECUTION:", second)
    print("REPLAY OUTCOME:", second_reason)
    passed = first is True and second is False
    print("EXPECTATION MET:", passed)
    print("EXPERIMENT STATUS:", "PASS" if passed else "FINDING")

if __name__ == "__main__":
    main()
