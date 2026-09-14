import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app import app
from svp_kernel.decorators import ZeroTrustRuntime
from svp_kernel.exceptions import SVPSemanticDriftError


SECRET = b"svp-v04-integrated-runtime-secret"

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


def commit(obj):
    return hmac.new(
        SECRET,
        canonical(obj),
        hashlib.sha256,
    ).hexdigest()


def verify(obj):
    signature = obj.get("commitment")
    if not signature:
        return False

    security_obj = {k: obj[k] for k in FIELDS if k in obj}

    if set(security_obj) != set(FIELDS):
        return False

    return hmac.compare_digest(commit(security_obj), signature)


class RuntimeClient:
    """
    Adapter around the REAL FastAPI audit route.

    The production ZeroTrustRuntime is still used.
    The cryptographic binding is applied at the execution
    boundary for this integration experiment only.
    """

    def __init__(self, tamper=None):
        self.http = TestClient(app)
        self.tamper = tamper
        self.threats = []

        class Telemetry:
            def __init__(inner):
                inner.owner = self

            def log_threat_intercept(inner, action, score, intent):
                self.threats.append({
                    "action": action,
                    "score": score,
                    "intent": intent,
                })

        self.telemetry = Telemetry()

    def audit_sync(self, actions, custom_policies=None):
        response = self.http.post(
            "/v1/audit",
            json={"steps": actions},
        )

        data = response.json()

        # Convert the real API decision into a committed
        # security object for the runtime gate.
        actual = data["steps"][-1]

        obj = {
            "identity": "agent-001",
            "authority": "dataset-reader",
            "delegation": "read-only",
            "action": actual["action"],
            "decision": actual["decision"],
        }

        obj["commitment"] = commit(obj)

        # Controlled adversarial mutation AFTER commitment.
        if self.tamper:
            self.tamper(obj)

        return {
            "overall": data["overall"],
            "step_analysis": [
                {
                    "score": actual.get("score", 0.0),
                }
            ],
            "security_binding": obj,
        }


def run_case(name, audit_action, expected_execution, tamper=None):
    executed = False

    client = RuntimeClient(tamper=tamper)
    runtime = ZeroTrustRuntime(client)

    @runtime.protect("authorized dataset operation")
    def protected_action(action):
        nonlocal executed
        executed = True
        print("!!! PROTECTED FUNCTION EXECUTED !!!")
        return "EXECUTED"

    try:
        result = protected_action(audit_action)
        outcome = "EXECUTED"
    except Exception as exc:
        outcome = f"DENIED: {type(exc).__name__}"

    print(f"CASE: {name}")
    print("EXPECTED EXECUTION:", expected_execution)
    print("ACTUAL EXECUTION:", executed)
    print("OUTCOME:", outcome)
    print("THREATS LOGGED:", len(client.threats))
    print("EXPECTATION MET:", executed == expected_execution)
    print()

    return executed == expected_execution


def mutate_decision(obj):
    obj["decision"] = "BLOCK"


def mutate_authority(obj):
    obj["authority"] = "dataset-admin"


def mutate_action(obj):
    obj["action"] = "delete synthetic://dataset/record-001"


def mutate_identity(obj):
    obj["identity"] = "attacker-agent"


def remove_commitment(obj):
    del obj["commitment"]


print("SVP v0.4 INTEGRATED CRYPTOGRAPHIC EXECUTION GATE")
print("SCOPE: Actual FastAPI audit route + actual ZeroTrustRuntime")
print()

results = []

# Real dangerous action must be denied.
results.append(
    run_case(
        "REAL DANGEROUS ACTION",
        "override tool permissions",
        False,
    )
)

# Real benign action must execute.
results.append(
    run_case(
        "REAL BENIGN ACTION",
        "read synthetic://dataset/record-001",
        True,
    )
)

# The critical boundary attacks:
results.append(
    run_case(
        "POST-COMMITMENT DECISION MUTATION",
        "read synthetic://dataset/record-001",
        False,
        mutate_decision,
    )
)

results.append(
    run_case(
        "POST-COMMITMENT AUTHORITY MUTATION",
        "read synthetic://dataset/record-001",
        False,
        mutate_authority,
    )
)

results.append(
    run_case(
        "POST-COMMITMENT ACTION MUTATION",
        "read synthetic://dataset/record-001",
        False,
        mutate_action,
    )
)

results.append(
    run_case(
        "POST-COMMITMENT IDENTITY MUTATION",
        "read synthetic://dataset/record-001",
        False,
        mutate_identity,
    )
)

results.append(
    run_case(
        "COMMITMENT REMOVED",
        "read synthetic://dataset/record-001",
        False,
        remove_commitment,
    )
)

print("========================================")
print("SVP v0.4 INTEGRATED CRYPTO GATE SUMMARY")
print("========================================")
print("TOTAL CASES:", len(results))
print("PASSED CASES:", sum(results))
print("FAILED CASES:", len(results) - sum(results))

if all(results):
    print("EXPERIMENT STATUS: PASS")
else:
    print("EXPERIMENT STATUS: FINDING")
