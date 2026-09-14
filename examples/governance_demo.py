"""End-to-end, side-effect-free demonstration of the SVP boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from svp_kernel.governance import (
    AuditTrail,
    GovernanceEngine,
    GovernanceRequest,
    GovernanceRuntime,
)


class DemoExecutionAdapter:
    """A simulated adapter that records calls instead of causing side effects."""

    def __init__(self):
        self.calls = []

    def execute(self, request):
        self.calls.append(request.action)
        return {"simulated": True, "action": request.action}


def evaluator(request):
    if request.action == "prohibited_action":
        return {
            "decision": "BLOCK",
            "rule_id": "DEMO-BLOCK",
            "severity": "CRITICAL",
            "score": 0.99,
            "reason": "Synthetic prohibited action",
        }
    if request.action == "high_risk_action":
        return {
            "decision": "PASS",
            "rule_id": "DEMO-RISK",
            "severity": "HIGH",
            "score": 0.95,
            "reason": "Synthetic high-risk action requires approval",
        }
    return {
        "decision": "PASS",
        "rule_id": "DEMO-ALLOW",
        "severity": "LOW",
        "score": 0.10,
        "reason": "Synthetic benign action",
    }


def request(action, *, state=None, request_id=None):
    return GovernanceRequest(
        principal="demo-user",
        agent="demo-agent",
        delegation={"depth": 0},
        intent=f"demo intent for {action}",
        action=action,
        resource="synthetic://demo/resource",
        context={},
        state=state or {},
        request_id=request_id or f"demo-{action}",
        trace_id=f"trace-{request_id or action}",
    )


def main():
    audit = AuditTrail()
    runtime = GovernanceRuntime(GovernanceEngine(evaluator), audit)
    adapter = DemoExecutionAdapter()

    benign = runtime.execute(
        request("benign_action", request_id="allow-001"),
        adapter,
    )
    prohibited = runtime.execute(
        request("prohibited_action", request_id="block-001"),
        adapter,
    )
    escalated = runtime.execute(
        request("high_risk_action", request_id="escalate-001"),
        adapter,
    )
    approved = runtime.execute(
        request(
            "high_risk_action",
            state={"approval_status": "approved", "approval_reason": "demo review"},
            request_id="escalate-002",
        ),
        adapter,
    )

    print("SVP GOVERNANCE END-TO-END DEMO")
    print("All adapter effects are simulated; no real action is executed.")
    for label, result in (
        ("BENIGN", benign),
        ("PROHIBITED", prohibited),
        ("HIGH_RISK_PENDING", escalated),
        ("HIGH_RISK_APPROVED", approved),
    ):
        print(label)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    print("ADAPTER_CALLS", json.dumps(adapter.calls))
    print("AUDIT_EVENTS", len(audit.events))
    print("AUDIT_CHAIN_VALID", audit.verify())


if __name__ == "__main__":
    main()