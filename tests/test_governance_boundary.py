import unittest

from svp_kernel.governance import (
    ALLOW,
    BLOCK,
    ESCALATE,
    AuditTrail,
    GovernanceEngine,
    GovernanceRequest,
    GovernanceRuntime,
)


def make_request(**overrides):
    values = {
        "principal": "user-001",
        "agent": "agent-001",
        "delegation": {"depth": 0},
        "intent": "retrieve an approved record",
        "action": "read_record",
        "resource": "synthetic://dataset/record-001",
        "context": {},
        "state": {},
        "request_id": "request-test-001",
        "trace_id": "trace-test-001",
    }
    values.update(overrides)
    return GovernanceRequest(**values)


class CountingAdapter:
    def __init__(self):
        self.calls = []

    def execute(self, request):
        self.calls.append(request.action)
        return {"status": "simulated", "action": request.action}


class GovernanceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.allow_evaluator = lambda request: {
            "decision": "PASS",
            "rule_id": "SAFE001",
            "severity": "LOW",
            "score": 0.10,
            "matched_policy": "Synthetic safe action",
        }

    def test_allow_calls_execution_adapter_and_audits(self):
        audit = AuditTrail()
        runtime = GovernanceRuntime(
            GovernanceEngine(self.allow_evaluator),
            audit,
        )
        adapter = CountingAdapter()

        result = runtime.execute(make_request(), adapter)

        self.assertEqual(result.decision.outcome, ALLOW)
        self.assertTrue(result.executed)
        self.assertTrue(result.adapter_called)
        self.assertEqual(adapter.calls, ["read_record"])
        self.assertEqual(result.audit.execution_status, "executed")
        self.assertTrue(audit.verify())

    def test_block_never_calls_execution_adapter(self):
        audit = AuditTrail()
        runtime = GovernanceRuntime(
            GovernanceEngine(
                lambda request: {
                    "decision": "BLOCK",
                    "rule_id": "DB001",
                    "severity": "CRITICAL",
                    "score": 0.99,
                    "reason": "destructive database policy",
                }
            ),
            audit,
        )
        adapter = CountingAdapter()

        result = runtime.execute(make_request(action="drop_database"), adapter)

        self.assertEqual(result.decision.outcome, BLOCK)
        self.assertFalse(result.executed)
        self.assertFalse(result.adapter_called)
        self.assertEqual(adapter.calls, [])
        self.assertEqual(result.audit.execution_status, "not_executed")
        self.assertTrue(audit.verify())

    def test_escalate_waits_for_explicit_approval(self):
        evaluator = lambda request: {
            "decision": "PASS",
            "rule_id": "RISK001",
            "severity": "HIGH",
            "score": 0.95,
        }
        audit = AuditTrail()
        runtime = GovernanceRuntime(GovernanceEngine(evaluator), audit)
        adapter = CountingAdapter()

        pending = runtime.execute(make_request(), adapter)
        approved_request = make_request(
            state={"approval_status": "approved", "approval_reason": "reviewed"}
        )
        approved = runtime.execute(approved_request, adapter)

        self.assertEqual(pending.decision.outcome, ESCALATE)
        self.assertFalse(pending.executed)
        self.assertEqual(approved.decision.outcome, ALLOW)
        self.assertTrue(approved.executed)
        self.assertEqual(len(adapter.calls), 1)
        self.assertTrue(audit.verify())

    def test_malformed_input_is_rejected(self):
        with self.assertRaises(ValueError):
            GovernanceRequest.from_mapping(
                {"principal": "user-001", "action": "read_record"}
            )
        with self.assertRaises(ValueError):
            GovernanceRequest.from_mapping(
                {
                    "principal": "user-001",
                    "agent": "agent-001",
                    "intent": "read",
                    "action": "",
                    "resource": "synthetic://record",
                }
            )

    def test_policy_violation_is_deterministically_blocked(self):
        engine = GovernanceEngine(
            lambda request: {
                "decision": "BLOCK",
                "rule_id": "POLICY001",
                "severity": "HIGH",
                "score": 0.88,
            }
        )
        decision = engine.evaluate(make_request())
        self.assertEqual(decision.outcome, BLOCK)
        self.assertFalse(decision.execution_allowed)
        self.assertEqual(decision.rule, "POLICY001")

    def test_identical_request_is_repeatable(self):
        engine = GovernanceEngine(self.allow_evaluator)
        request = make_request()

        first = engine.evaluate(request).to_dict()
        second = engine.evaluate(request).to_dict()

        self.assertEqual(first, second)

    def test_unavailable_governance_fails_safe(self):
        def unavailable(request):
            raise RuntimeError("evaluator unavailable")

        runtime = GovernanceRuntime(GovernanceEngine(unavailable))
        adapter = CountingAdapter()

        result = runtime.execute(make_request(), adapter)

        self.assertEqual(result.decision.outcome, BLOCK)
        self.assertEqual(result.decision.reason, "GOVERNANCE_UNAVAILABLE")
        self.assertFalse(result.executed)
        self.assertEqual(adapter.calls, [])

    def test_audit_trace_contains_request_decision_and_execution(self):
        audit = AuditTrail()
        runtime = GovernanceRuntime(GovernanceEngine(self.allow_evaluator), audit)

        result = runtime.execute(make_request(), CountingAdapter())
        event = result.audit.to_dict()

        self.assertEqual(event["request_id"], "request-test-001")
        self.assertEqual(event["trace_id"], "trace-test-001")
        self.assertEqual(event["outcome"], ALLOW)
        self.assertEqual(event["execution_status"], "executed")
        self.assertTrue(event["adapter_called"])
        self.assertTrue(event["event_hash"])
        self.assertTrue(audit.verify())

    def test_extensions_cannot_relax_block(self):
        class RelaxingExtension:
            def review(self, request, decision):
                return decision.__class__(
                    outcome=ALLOW,
                    reason="unsafe extension",
                    rule="EXTENSION",
                    risk=0.0,
                    policy_version=decision.policy_version,
                    request_id=decision.request_id,
                    trace_id=decision.trace_id,
                )

        engine = GovernanceEngine(
            lambda request: {"decision": "BLOCK", "rule_id": "BLOCK001"},
            extensions=[RelaxingExtension()],
        )

        decision = engine.evaluate(make_request())

        self.assertEqual(decision.outcome, BLOCK)
        self.assertEqual(decision.rule, "GOVERNANCE_INVARIANT")


if __name__ == "__main__":
    unittest.main()