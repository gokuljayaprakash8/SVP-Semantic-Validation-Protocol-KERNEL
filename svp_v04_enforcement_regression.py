from svp_kernel.decorators import ZeroTrustRuntime
from svp_kernel.exceptions import SVPSemanticDriftError


class FakeTelemetry:
    def __init__(self):
        self.events = []

    def log_threat_intercept(self, action_desc, drift_score, core_intent):
        self.events.append(
            ("THREAT", action_desc, drift_score, core_intent)
        )


class FakeClient:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.telemetry = FakeTelemetry()

    def audit_sync(self, actions):
        if self.error:
            raise self.error
        print("AUDIT_RESULT:", self.result)
        return self.result


def run_case(name, audit_result, expected_execution, audit_error=None):
    client = FakeClient(audit_result, audit_error)
    runtime = ZeroTrustRuntime(client)
    executed = []

    @runtime.protect("read synthetic record")
    def protected_action():
        executed.append(True)
        print("FUNCTION EXECUTED")
        return "EXECUTED"

    try:
        result = protected_action()
        outcome = "EXECUTED"
    except Exception as exc:
        outcome = type(exc).__name__
        result = None

    execution_ok = bool(executed) == expected_execution

    print(
        f"CASE: {name} | "
        f"OUTCOME: {outcome} | "
        f"EXECUTION_EXPECTATION_MET: {execution_ok} | "
        f"THREATS_LOGGED: {len(client.telemetry.events)}"
    )

    return execution_ok


CASES = [
    (
        "BLOCKED decision",
        {
            "overall": "BLOCKED",
            "step_analysis": [{"score": 0.91}],
        },
        False,
        None,
    ),
    (
        "CLEAR decision",
        {
            "overall": "CLEAR",
            "step_analysis": [{"score": 0.02}],
        },
        True,
        None,
    ),
    (
        "Missing decision field",
        {
            "step_analysis": [{"score": 0.50}],
        },
        False,
        None,
    ),
    (
        "Unknown decision",
        {
            "overall": "UNKNOWN",
        },
        False,
        None,
    ),
    (
        "Audit exception",
        None,
        False,
        RuntimeError("simulated audit failure"),
    ),
]


results = []

print("SVP v0.4 ENFORCEMENT REGRESSION")
print("SCOPE: Synthetic local test only")
print()

for case in CASES:
    results.append(run_case(*case))

passed = sum(results)
total = len(results)

print()
print("TOTAL CASES:", total)
print("PASSED CASES:", passed)
print("FAILED CASES:", total - passed)
print(
    "EXPERIMENT STATUS:",
    "PASS" if passed == total else "FINDING"
)
