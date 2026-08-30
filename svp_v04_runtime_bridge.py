from svp_kernel.decorators import ZeroTrustRuntime
from svp_kernel.exceptions import SVPSemanticDriftError


class FakeTelemetry:
    def __init__(self):
        self.threats = []

    def log_threat_intercept(self, action_desc, drift_score, core_intent):
        self.threats.append({
            "action": action_desc,
            "score": drift_score,
            "intent": core_intent,
        })


class FakeClient:
    def __init__(self, audit_result=None, audit_error=None):
        self.audit_result = audit_result
        self.audit_error = audit_error
        self.telemetry = FakeTelemetry()

    def audit_sync(self, actions):
        if self.audit_error is not None:
            raise self.audit_error
        return self.audit_result


CASES = [
    {
        "name": "VALID CLEAR",
        "audit": {
            "overall": "CLEAR",
            "step_analysis": [{"score": 0.02}],
        },
        "should_execute": True,
    },
    {
        "name": "COMMITMENT INVALID -> BLOCKED",
        "audit": {
            "overall": "BLOCKED",
            "step_analysis": [{"score": 0.91}],
        },
        "should_execute": False,
    },
    {
        "name": "PROJECTION INVALID -> BLOCKED",
        "audit": {
            "overall": "BLOCKED",
            "step_analysis": [{"score": 0.87}],
        },
        "should_execute": False,
    },
    {
        "name": "MISSING DECISION",
        "audit": {
            "step_analysis": [{"score": 0.50}],
        },
        "should_execute": False,
    },
    {
        "name": "UNKNOWN DECISION",
        "audit": {
            "overall": "UNKNOWN",
        },
        "should_execute": False,
    },
    {
        "name": "AUDIT FAILURE",
        "audit": None,
        "audit_error": RuntimeError("synthetic audit failure"),
        "should_execute": False,
    },
]


results = []

for case in CASES:
    telemetry = FakeTelemetry()

    if "audit_error" in case:
        client = FakeClient(
            audit_error=case["audit_error"]
        )
    else:
        client = FakeClient(
            audit_result=case["audit"]
        )

    runtime = ZeroTrustRuntime(client)
    executed = False

    @runtime.protect("read authorized dataset")
    def protected_action():
        nonlocal_marker[0] = True
        print("FUNCTION EXECUTED")

    nonlocal_marker = [False]

    try:
        protected_action()
        executed = True
        outcome = "EXECUTED"
    except SVPSemanticDriftError as e:
        outcome = "DENIED: SVPSemanticDriftError"
    except Exception as e:
        outcome = f"DENIED: {type(e).__name__}"

    expected = case["should_execute"]
    passed = executed == expected

    results.append(passed)

    print(f"CASE: {case['name']}")
    print(f"EXPECTED EXECUTION: {expected}")
    print(f"ACTUAL EXECUTION: {executed}")
    print(f"OUTCOME: {outcome}")
    print(f"THREATS LOGGED: {len(client.telemetry.threats)}")
    print(f"EXPECTATION MET: {passed}")
    print()


print("SVP v0.4 RUNTIME BRIDGE REGRESSION")
print("SCOPE: Synthetic test using actual ZeroTrustRuntime")
print(f"TOTAL CASES: {len(results)}")
print(f"PASSED CASES: {sum(results)}")
print(f"FAILED CASES: {len(results) - sum(results)}")

if all(results):
    print("EXPERIMENT STATUS: PASS")
else:
    print("EXPERIMENT STATUS: FINDING")
