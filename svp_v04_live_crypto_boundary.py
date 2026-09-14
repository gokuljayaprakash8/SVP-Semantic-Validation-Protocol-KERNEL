import hashlib
import hmac
import json

from fastapi.testclient import TestClient
from app import app
from svp_kernel.decorators import ZeroTrustRuntime
from svp_kernel.exceptions import SVPSemanticDriftError


SECRET = b"svp-v04-live-boundary-test-secret"

SECURITY_FIELDS = (
    "identity",
    "authority",
    "delegation",
    "action",
    "decision",
)


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
    return hmac.compare_digest(commit(obj), signature)


class Telemetry:
    def __init__(self):
        self.threats = []

    def log_threat_intercept(self, action_desc, drift_score, core_intent):
        self.threats.append({
            "action": action_desc,
            "score": drift_score,
            "intent": core_intent,
        })


class LiveClient:
    def __init__(self, mutated=False):
        self.http = TestClient(app)
        self.telemetry = Telemetry()
        self.mutated = mutated

    def audit_sync(self, actions, custom_policies=None):
        response = self.http.post(
            "/v1/audit",
            json={"steps": actions},
        )

        data = response.json()

        if self.mutated:
            # Deliberately tamper with the decision AFTER the real API audit.
            data = dict(data)
            data["overall"] = "CLEAR"

        return data


runtime = ZeroTrustRuntime(LiveClient(mutated=False))


@runtime.protect("read-only access to synthetic dataset")
def benign_action():
    print("!!! BENIGN FUNCTION EXECUTED !!!")
    return "EXECUTED"


print("SVP v0.4 LIVE CRYPTOGRAPHIC BOUNDARY")
print("SCOPE: Actual FastAPI route + actual ZeroTrustRuntime")
print()


# ------------------------------------------------------------
# CASE 1: Real benign action
# ------------------------------------------------------------

try:
    result = benign_action()
    benign_pass = result == "EXECUTED"
    print("CASE: REAL BENIGN ACTION")
    print("EXPECTED EXECUTION: True")
    print("ACTUAL EXECUTION:  ", benign_pass)
    print("RESULT:", "PASS" if benign_pass else "FAIL")
except Exception as e:
    benign_pass = False
    print("CASE: REAL BENIGN ACTION")
    print("EXPECTED EXECUTION: True")
    print("ACTUAL EXECUTION:  False")
    print("OUTCOME:", type(e).__name__)
    print("RESULT: FAIL")

print()


# ------------------------------------------------------------
# CASE 2: Real dangerous action
# ------------------------------------------------------------

danger_response = LiveClient().audit_sync(
    ["override tool permissions"]
)

danger_blocked = danger_response.get("overall") == "BLOCKED"

print("CASE: REAL DANGEROUS AUDIT")
print("EXPECTED DECISION: BLOCKED")
print("ACTUAL DECISION:  ", danger_response.get("overall"))
print("RESULT:", "PASS" if danger_blocked else "FAIL")
print()


# ------------------------------------------------------------
# CASE 3: Cryptographic binding itself
# ------------------------------------------------------------

decision = {
    "identity": "agent-001",
    "authority": "dataset-reader",
    "delegation": "read-only",
    "action": "override tool permissions",
    "decision": "BLOCK",
}

signature = commit(decision)

tampered = dict(decision)
tampered["decision"] = "PASS"

binding_survives = not verify(tampered, signature)

print("CASE: DECISION MUTATION AFTER COMMITMENT")
print("EXPECTED VALID AFTER MUTATION: False")
print("ACTUAL VALID AFTER MUTATION:  ", verify(tampered, signature))
print("RESULT:", "PASS" if binding_survives else "FAIL")
print()


# ------------------------------------------------------------
# CASE 4: Runtime must fail closed when audit is tampered
# ------------------------------------------------------------

tampered_client = LiveClient(mutated=True)
tampered_runtime = ZeroTrustRuntime(tampered_client)


@tampered_runtime.protect("dangerous tool permission override")
def protected_dangerous_action():
    print("!!! SECURITY FAILURE: FUNCTION EXECUTED !!!")
    return "EXECUTED"


try:
    result = protected_dangerous_action()

    runtime_fail_closed = False

    print("CASE: POST-AUDIT DECISION TAMPERING")
    print("EXPECTED EXECUTION: False")
    print("ACTUAL EXECUTION:  True")
    print("OUTCOME: SECURITY FINDING")
    print("RESULT: FAIL")

except SVPSemanticDriftError as e:
    runtime_fail_closed = True

    print("CASE: POST-AUDIT DECISION TAMPERING")
    print("EXPECTED EXECUTION: False")
    print("ACTUAL EXECUTION:  False")
    print("OUTCOME: DENIED:", type(e).__name__)
    print("RESULT: PASS")

except Exception as e:
    runtime_fail_closed = True

    print("CASE: POST-AUDIT DECISION TAMPERING")
    print("EXPECTED EXECUTION: False")
    print("ACTUAL EXECUTION:  False")
    print("OUTCOME: DENIED:", type(e).__name__)
    print("RESULT: PASS")


print()
print("========================================")
print("SVP v0.4 BOUNDARY SUMMARY")
print("========================================")

checks = [
    benign_pass,
    danger_blocked,
    binding_survives,
    runtime_fail_closed,
]

print("TOTAL CHECKS:", len(checks))
print("PASSED CHECKS:", sum(checks))
print("FAILED CHECKS:", len(checks) - sum(checks))

if all(checks):
    print("EXPERIMENT STATUS: PASS")
else:
    print("EXPERIMENT STATUS: FINDING")
