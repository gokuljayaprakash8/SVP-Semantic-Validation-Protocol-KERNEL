import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as app_module
import svp_v06_runtime_gate as legacy_gate
from svp_kernel.decorators import ZeroTrustRuntime
from svp_kernel.exceptions import SVPSemanticDriftError
from svp_kernel.governance import (
    BLOCK,
    AuditTrail,
    GovernanceEngine,
    GovernanceRequest,
    GovernanceRuntime,
)
from svp_v06_runtime_gate import create_bound_decision


class _RecordingAdapter:
    def __init__(self):
        self.calls = []

    def execute(self, request):
        self.calls.append(request.action)
        return {"action": request.action}


class _BlockingTelemetry:
    def log_threat_intercept(self, *args):
        return None


class _BlockingClient:
    telemetry = _BlockingTelemetry()

    def audit_sync(self, actions):
        return {"overall": "BLOCKED"}


class GovernanceBypassFindingsTests(unittest.TestCase):
    def test_legacy_execution_endpoint_bypasses_current_block(self):
        """Document the active v06 endpoint's separate PASS authorization path."""

        action = "delete production data"
        original_replay_db = legacy_gate.REPLAY_DB
        original_executed = list(app_module.V06_EXECUTED_ACTIONS)

        try:
            current_policy_result = app_module.svp_kernel(action)
            self.assertEqual(current_policy_result["decision"], BLOCK)
            self.assertEqual(current_policy_result["rule_id"], "DB001")

            with tempfile.TemporaryDirectory() as temp_dir:
                legacy_gate.REPLAY_DB = str(
                    Path(temp_dir) / "bypass-regression.sqlite3"
                )

                legacy_pass_record = create_bound_decision(
                    action,
                    {
                        "decision": "PASS",
                        "rule_id": "LEGACY-PASS",
                        "threshold": 0.0,
                    },
                )

                fail_if_governance_is_called = patch.object(
                    app_module.governance_runtime.engine,
                    "evaluate",
                    side_effect=AssertionError(
                        "legacy execution path unexpectedly invoked GovernanceRuntime"
                    ),
                )
                with fail_if_governance_is_called:
                    response = app_module.execute_v06_test(
                        {"action": action, "record": legacy_pass_record}
                    )

            self.assertTrue(response["executed"])
            self.assertEqual(response["reason"], "EXECUTION AUTHORIZED")
            self.assertEqual(app_module.V06_EXECUTED_ACTIONS, [action])
        finally:
            legacy_gate.REPLAY_DB = original_replay_db
            app_module.V06_EXECUTED_ACTIONS[:] = original_executed

    def test_direct_adapter_remains_callable_after_governance_block(self):
        """Document that the adapter is supplied, not owned, by the runtime."""

        effects = []

        class DirectAdapter:
            def execute(self, request):
                effects.append(request.action)

        request = GovernanceRequest(
            principal="agent-controlled",
            agent="untrusted-agent",
            delegation={},
            intent="perform a prohibited operation",
            action="delete production data",
            resource="db://production",
        )
        runtime = GovernanceRuntime(
            GovernanceEngine(
                lambda _: {
                    "decision": BLOCK,
                    "rule_id": "POLICY-BLOCK",
                    "severity": "CRITICAL",
                    "score": 1.0,
                }
            ),
            AuditTrail(),
        )
        adapter = DirectAdapter()

        result = runtime.execute(request, adapter)
        self.assertEqual(result.decision.outcome, BLOCK)
        self.assertFalse(result.executed)
        self.assertEqual(effects, [])

        adapter.execute(request)
        self.assertEqual(effects, [request.action])

    def test_decorator_original_function_bypasses_guard_via_wrapped(self):
        """Document the older decorator path's exposed original callable."""

        effects = []
        runtime = ZeroTrustRuntime(_BlockingClient())

        @runtime.protect("delete production data")
        def governed_action(value):
            effects.append(value)

        with self.assertRaises(SVPSemanticDriftError):
            governed_action("blocked")
        self.assertEqual(effects, [])

        governed_action.__wrapped__("bypassed")
        self.assertEqual(effects, ["bypassed"])


if __name__ == "__main__":
    unittest.main()