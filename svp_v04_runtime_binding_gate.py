import hashlib
import hmac
import json

from fastapi.testclient import TestClient
from app import app
from svp_kernel.decorators import ZeroTrustRuntime
from svp_kernel.exceptions import SVPSemanticDriftError


SECRET = b"svp-v04-runtime-binding-gate"


FIELDS = (
    "identity",
    "authority",
    "delegation",
    "action",
    "decision",
)


def canonical(obj):
    return json.dumps(
        {k: obj[k] for k in FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def sign(obj):
    return hmac.new(
        SECRET,
        canonical(obj),
        hashlib.sha256,
    ).hexdigest()


def verify(obj, signature):
    if not signature:
        return False
    return hmac.compare_digest(sign(obj), signature)


class Telemetry:
    def __init__(self):
        self.threats = []

    def log_threat_intercept(self, action, score, intent):
        self.threats.append({
            "action": action,
            "score": score,
            "intent": intent,
        })


class BindingClient:
    def __init__(self, audit_result):
        self.audit_result = audit_result
        self.telemetry = Telemetry()

    def audit_sync(self, actions, custom_policies=None):
        return dict(self.audit_result)


def make_decision(
    identity="agent-001",
    authority="dataset-reader",
    delegation="read-only",
    action="read synthetic://dataset/record-001",
    decision="PASS",
):
    obj = {
        "identity": identity,
        "authority": authority,
        "delegation": delegation,
        "action": action,
        "decision": decision,
    }
    obj["commitment"] = sign(obj)
    return obj


def binding_gate(obj):
    signature = obj.get("commitment")
    security_obj = {
        k: obj[k]
        for k in FIELDS
        if k in obj
    }

    if set(security_obj.keys()) != set(FIELDS):
        return False

    return verify(security_obj, signature)


def run_case(name, obj, expected_execution):
    executed = False

    def action():
        nonlocal executed
        executed = True
        print("!!! PROTECTED FUNCTION EXECUTED !!!")
        return "EXECUTED"

    valid_binding = binding_gate(obj)

    # Runtime gate:
    # execution is allowed only when the exact committed
    # security decision is valid AND the decision is PASS.
    should_execute = (
        valid_binding
        and obj.get("decision") == "PASS"
    )

    try:
        if should_execute:
            result = action()
            outcome = "EXECUTED"
        else:
            raise SVPSemanticDriftError(
                "RUNTIME BINDING GATE DENIED EXECUTION",
                1.0,
                obj.get("action", "unknown"),
            )

    except SVPSemanticDriftError as e:
        outcome = f"DENIED: {type(e).__name__}"

    expectation_met = executed == expected_execution

    print(f"CASE: {name}")
    print("COMMITMENT VALID:", valid_binding)
    print("DECISION:", obj.get("decision"))
    print("EXPECTED EXECUTION:", expected_execution)
    print("ACTUAL EXECUTION:", executed)
    print("OUTCOME:", outcome)
    print("EXPECTATION MET:", expectation_met)
    print()

    return expectation_met


BASE = make_decision()

cases = []


# 1. Legitimate PASS
cases.append((
    "VALID PASS DECISION",
    dict(BASE),
    True,
))


# 2. BLOCK decision with valid commitment
blocked = make_decision(decision="BLOCK")
cases.append((
    "VALID BLOCK DECISION",
    blocked,
    False,
))


# 3. Decision changed after commitment
tampered_decision = dict(BASE)
tampered_decision["decision"] = "BLOCK"
cases.append((
    "DECISION MUTATED AFTER COMMITMENT",
    tampered_decision,
    False,
))


# 4. Authority changed
tampered_authority = dict(BASE)
tampered_authority["authority"] = "dataset-admin"
cases.append((
    "AUTHORITY MUTATED AFTER COMMITMENT",
    tampered_authority,
    False,
))


# 5. Delegation changed
tampered_delegation = dict(BASE)
tampered_delegation["delegation"] = "admin-write"
cases.append((
    "DELEGATION MUTATED AFTER COMMITMENT",
    tampered_delegation,
    False,
))


# 6. Action changed
tampered_action = dict(BASE)
tampered_action["action"] = "delete synthetic://dataset/record-001"
cases.append((
    "ACTION MUTATED AFTER COMMITMENT",
    tampered_action,
    False,
))


# 7. Identity changed
tampered_identity = dict(BASE)
tampered_identity["identity"] = "agent-attacker"
cases.append((
    "IDENTITY MUTATED AFTER COMMITMENT",
    tampered_identity,
    False,
))


# 8. Commitment removed
missing_commitment = dict(BASE)
del missing_commitment["commitment"]
cases.append((
    "COMMITMENT REMOVED",
    missing_commitment,
    False,
))


# 9. Signature replaced
invalid_signature = dict(BASE)
invalid_signature["commitment"] = "00" * 32
cases.append((
    "INVALID SIGNATURE",
    invalid_signature,
    False,
))


# 10. Wrong secret/signature
wrong_secret = dict(BASE)
wrong_secret["commitment"] = hmac.new(
    b"attacker-secret",
    canonical(wrong_secret),
    hashlib.sha256,
).hexdigest()
cases.append((
    "WRONG SIGNING SECRET",
    wrong_secret,
    False,
))


print("SVP v0.4 RUNTIME CRYPTOGRAPHIC BINDING GATE")
print("SCOPE: Isolated synthetic runtime-boundary falsification")
print()

results = []

for name, obj, expected in cases:
    results.append(run_case(name, obj, expected))

print("========================================")
print("SVP v0.4 BINDING GATE SUMMARY")
print("========================================")
print("TOTAL CASES:", len(results))
print("PASSED CASES:", sum(results))
print("FAILED CASES:", len(results) - sum(results))

if all(results):
    print("EXPERIMENT STATUS: PASS")
else:
    print("EXPERIMENT STATUS: FINDING")
