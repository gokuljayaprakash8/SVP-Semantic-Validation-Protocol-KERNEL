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
    def setUp(self):
        self.original_replay_db = legacy_gate.REPLAY_DB
        self.original_executed = list(app_module.V06_EXECUTED_ACTIONS)
        self.original_audit = app_module.governance_runtime.audit
        app_module.governance_runtime.audit = AuditTrail()

    def tearDown(self):
        legacy_gate.REPLAY_DB = self.original_replay_db
        app_module.V06_EXECUTED_ACTIONS[:] = self.original_executed
        app_module.governance_runtime.audit = self.original_audit

    def _legacy_pass_record(self, action):
        return create_bound_decision(
            action,
            {
                "decision": "PASS",
                "rule_id": "LEGACY-PASS",
                "threshold": 0.0,
            },
        )

    def _isolated_replay_db(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        legacy_gate.REPLAY_DB = str(
            Path(temp_dir.name) / "bypass-regression.sqlite3"
        )

    def test_current_semantic_block_prevents_legacy_endpoint_execution(self):
        """The active endpoint must use a fresh current governance decision."""

        action = "delete production data"
        current_policy_result = app_module.svp_kernel(action)
        self.assertEqual(current_policy_result["decision"], BLOCK)
        self.assertEqual(current_policy_result["rule_id"], "DB001")
        self._isolated_replay_db()

        with patch.object(
            app_module.governance_runtime.engine,
            "evaluate",
            wraps=app_module.governance_runtime.engine.evaluate,
        ) as evaluate:
            response = app_module.execute_v06_test(
                {
                    "action": action,
                    "record": self._legacy_pass_record(action),
                }
            )

        self.assertEqual(evaluate.call_count, 1)
        self.assertFalse(response["executed"])
        self.assertEqual(response["reason"], "POLICY_VIOLATION")
        self.assertEqual(app_module.V06_EXECUTED_ACTIONS, [])

    def test_legacy_pass_cannot_override_current_block(self):
        """A legacy PASS is evidence, not permission to execute."""

        action = "delete production data"
        self._isolated_replay_db()
        with patch.object(
            app_module,
            "svp_kernel",
            return_value={
                "action": action,
                "decision": BLOCK,
                "rule_id": "DB001",
                "severity": "CRITICAL",
                "score": 1.0,
            },
        ):
            response = app_module.execute_v06_test(
                {
                    "action": action,
                    "record": self._legacy_pass_record(action),
                }
            )

        self.assertFalse(response["executed"])
        self.assertEqual(app_module.V06_EXECUTED_ACTIONS, [])

    def test_unapproved_escalate_cannot_reach_active_sink(self):
        action = "rotate production signing keys"
        self._isolated_replay_db()
        with patch.object(
            app_module,
            "svp_kernel",
            return_value={
                "action": action,
                "decision": "PASS",
                "rule_id": "KEYS001",
                "severity": "HIGH",
                "score": 0.95,
            },
        ):
            response = app_module.execute_v06_test(
                {
                    "action": action,
                    "record": self._legacy_pass_record(action),
                }
            )

        self.assertFalse(response["executed"])
        self.assertEqual(response["reason"], "HIGH_RISK_REQUIRES_APPROVAL")
        self.assertEqual(app_module.V06_EXECUTED_ACTIONS, [])

    def test_allow_reaches_active_sink_exactly_once(self):
        action = "read synthetic record"
        self._isolated_replay_db()
        with patch.object(
            app_module,
            "svp_kernel",
            return_value={
                "action": action,
                "decision": "PASS",
                "rule_id": "SAFE001",
                "severity": "LOW",
                "score": 0.10,
            },
        ):
            response = app_module.execute_v06_test(
                {
                    "action": action,
                    "record": self._legacy_pass_record(action),
                }
            )

        self.assertTrue(response["executed"])
        self.assertEqual(response["reason"], "EXECUTION AUTHORIZED")
        self.assertEqual(app_module.V06_EXECUTED_ACTIONS, [action])

    def test_direct_legacy_gate_call_cannot_reach_sink_after_block(self):
        action = "delete production data"
        self._isolated_replay_db()
        with patch.object(
            app_module,
            "svp_kernel",
            return_value={
                "action": action,
                "decision": BLOCK,
                "rule_id": "DB001",
                "severity": "CRITICAL",
                "score": 1.0,
            },
        ):
            allowed, reason = app_module.v06_execution_gate(
                action,
                self._legacy_pass_record(action),
            )

        self.assertFalse(allowed)
        self.assertEqual(reason, "POLICY_VIOLATION")
        self.assertEqual(app_module.V06_EXECUTED_ACTIONS, [])

    def test_active_dispatcher_blocks_v06_adapter_on_block(self):
        action = "delete production data"
        request = GovernanceRequest(
            principal="agent-controlled",
            agent="untrusted-agent",
            delegation={},
            intent="prohibited operation",
            action=action,
            resource="db://production",
        )
        runtime = GovernanceRuntime(
            GovernanceEngine(
                lambda _: {
                    "decision": BLOCK,
                    "rule_id": "DB001",
                    "severity": "CRITICAL",
                    "score": 1.0,
                }
            ),
            AuditTrail(),
        )

        result = runtime.execute(request, app_module.v06_execution_adapter)

        self.assertEqual(result.decision.outcome, BLOCK)
        self.assertFalse(result.executed)
        self.assertEqual(app_module.V06_EXECUTED_ACTIONS, [])


    def test_direct_v06_adapter_requires_governance_capability(self):
        """Direct access to the active V06 sink cannot execute an action."""

        request = GovernanceRequest.from_mapping(
            {
                "principal": "test-principal",
                "agent": "test-agent",
                "delegation": {},
                "intent": "delete production data",
                "action": "delete production data",
                "resource": "production-database",
            }
        )

        with self.assertRaises(PermissionError):
            app_module.v06_execution_adapter.execute(request)

        self.assertEqual(app_module.V06_EXECUTED_ACTIONS, [])

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
