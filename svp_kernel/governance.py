"""Framework-agnostic pre-execution governance primitives.

The module deliberately keeps policy evaluation separate from execution.  A
caller may propose an action, but only GovernanceRuntime can invoke an
ExecutionAdapter, and it does so only after an independent ALLOW decision.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol, Sequence


ALLOW = "ALLOW"
BLOCK = "BLOCK"
ESCALATE = "ESCALATE"
OUTCOMES = frozenset({ALLOW, BLOCK, ESCALATE})
DEFAULT_POLICY_VERSION = "1.0.0"
HIGH_RISK_SEVERITIES = frozenset({"HIGH", "CRITICAL"})


class GovernanceValidationError(ValueError):
    """Raised when a proposed governance request is malformed."""


class GovernanceUnavailableError(RuntimeError):
    """Raised by an evaluator when governance cannot make a decision."""


@dataclass(frozen=True)
class GovernanceRequest:
    """Normalized, domain-agnostic proposal presented to governance."""

    principal: str
    agent: str
    delegation: Mapping[str, Any]
    intent: str
    action: str
    resource: str
    context: Mapping[str, Any] = field(default_factory=dict)
    state: Mapping[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def __post_init__(self) -> None:
        for name in ("principal", "agent", "intent", "action", "resource"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise GovernanceValidationError(
                    f"{name} must be a non-empty string"
                )
        for name in ("delegation", "context", "state"):
            if not isinstance(getattr(self, name), Mapping):
                raise GovernanceValidationError(f"{name} must be an object")
        for name in ("request_id", "trace_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise GovernanceValidationError(
                    f"{name} must be a non-empty string"
                )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "GovernanceRequest":
        if not isinstance(payload, Mapping):
            raise GovernanceValidationError("request must be an object")

        required = ("principal", "agent", "intent", "action", "resource")
        missing = [name for name in required if name not in payload]
        if missing:
            raise GovernanceValidationError(
                f"missing required fields: {', '.join(missing)}"
            )

        values = dict(payload)
        values.setdefault("delegation", {})
        values.setdefault("context", {})
        values.setdefault("state", {})
        return cls(**values)

    def normalized(self) -> "GovernanceRequest":
        """Apply deterministic whitespace normalization before evaluation."""

        def clean(value: str) -> str:
            return re.sub(r"\s+", " ", value.strip())

        return GovernanceRequest(
            principal=clean(self.principal),
            agent=clean(self.agent),
            delegation=dict(self.delegation),
            intent=clean(self.intent),
            action=clean(self.action),
            resource=clean(self.resource),
            context=dict(self.context),
            state=dict(self.state),
            request_id=self.request_id,
            trace_id=self.trace_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "principal": self.principal,
            "agent": self.agent,
            "delegation": dict(self.delegation),
            "intent": self.intent,
            "action": self.action,
            "resource": self.resource,
            "context": dict(self.context),
            "state": dict(self.state),
            "request_id": self.request_id,
            "trace_id": self.trace_id,
        }


@dataclass(frozen=True)
class GovernanceDecision:
    """Enforceable governance result returned before any adapter call."""

    outcome: str
    reason: str
    rule: str
    risk: float | None
    policy_version: str
    request_id: str
    trace_id: str
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise GovernanceValidationError(
                f"unsupported governance outcome: {self.outcome}"
            )
        if not self.reason.strip() or not self.rule.strip():
            raise GovernanceValidationError("decision reason and rule are required")
        if self.risk is not None and not 0.0 <= self.risk <= 1.0:
            raise GovernanceValidationError("risk must be between 0 and 1")

    @property
    def execution_allowed(self) -> bool:
        return self.outcome == ALLOW

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "reason": self.reason,
            "rule": self.rule,
            "risk": self.risk,
            "policy_version": self.policy_version,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "execution_allowed": self.execution_allowed,
            "evidence": dict(self.evidence),
        }


class GovernanceEvaluator(Protocol):
    """Policy evaluator interface; semantic or deterministic implementations fit."""

    def __call__(self, request: GovernanceRequest) -> Mapping[str, Any]:
        ...


class GovernanceExtension(Protocol):
    """Future multi-step/CEC review hook.

    Extensions may tighten a decision to BLOCK or ESCALATE.  The runtime
    refuses an extension that would relax a BLOCK or an unapproved ESCALATE.
    """

    def review(
        self,
        request: GovernanceRequest,
        decision: GovernanceDecision,
    ) -> GovernanceDecision | None:
        ...


class ExecutionAdapter(Protocol):
    """The only interface through which a governed side effect may occur."""

    def execute(self, request: GovernanceRequest) -> Any:
        ...


def _risk_value(raw: Mapping[str, Any]) -> float | None:
    value = raw.get("score", raw.get("risk"))
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, numeric))


class GovernanceEngine:
    """Deterministic policy-to-decision adapter with fail-safe invariants."""

    def __init__(
        self,
        evaluator: GovernanceEvaluator,
        *,
        policy_version: str = DEFAULT_POLICY_VERSION,
        high_risk_threshold: float = 0.85,
        extensions: Sequence[GovernanceExtension] = (),
    ) -> None:
        self.evaluator = evaluator
        self.policy_version = policy_version
        self.high_risk_threshold = high_risk_threshold
        self.extensions = tuple(extensions)

    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        normalized = request.normalized()

        try:
            raw = self.evaluator(normalized)
            if not isinstance(raw, Mapping):
                raise GovernanceUnavailableError(
                    "evaluator returned a non-object result"
                )
            decision = self._decision_from_evaluation(normalized, raw)
        except Exception as exc:
            # Unavailable or malformed governance never becomes an ALLOW.
            decision = GovernanceDecision(
                outcome=BLOCK,
                reason="GOVERNANCE_UNAVAILABLE",
                rule="GOVERNANCE_FAIL_SAFE",
                risk=None,
                policy_version=self.policy_version,
                request_id=normalized.request_id,
                trace_id=normalized.trace_id,
                evidence={"error_type": type(exc).__name__},
            )

        return self._apply_extensions(normalized, decision)

    def _decision_from_evaluation(
        self,
        request: GovernanceRequest,
        raw: Mapping[str, Any],
    ) -> GovernanceDecision:
        raw_outcome = str(raw.get("decision", raw.get("outcome", ""))).upper()
        risk = _risk_value(raw)
        severity = str(raw.get("severity", "")).upper()
        risk_hint = str(request.context.get("risk_level", "")).upper()
        high_risk = (
            severity in HIGH_RISK_SEVERITIES
            or risk_hint in HIGH_RISK_SEVERITIES
            or (risk is not None and risk >= self.high_risk_threshold)
        )
        approved = request.state.get("approval_status") == "approved"
        rule = str(raw.get("rule_id", raw.get("rule", "GOVERNANCE_DEFAULT")))

        if raw_outcome == BLOCK:
            outcome = BLOCK
            reason = str(raw.get("reason", "POLICY_VIOLATION"))
        elif raw_outcome in {ESCALATE, "REVIEW"} or high_risk:
            if approved:
                outcome = ALLOW
                reason = "ESCALATION_APPROVED"
                rule = "GOVERNANCE_APPROVAL"
            else:
                outcome = ESCALATE
                reason = "HIGH_RISK_REQUIRES_APPROVAL"
        elif raw_outcome in {"PASS", ALLOW}:
            outcome = ALLOW
            reason = str(raw.get("reason", "POLICY_ALLOWED"))
        else:
            outcome = BLOCK
            reason = "UNKNOWN_GOVERNANCE_RESULT"
            rule = "GOVERNANCE_FAIL_SAFE"

        return GovernanceDecision(
            outcome=outcome,
            reason=reason,
            rule=rule,
            risk=risk,
            policy_version=self.policy_version,
            request_id=request.request_id,
            trace_id=request.trace_id,
            evidence={
                "normalized_action": request.action,
                "severity": severity or "UNKNOWN",
                "matched_policy": raw.get("matched_policy"),
                "threshold": raw.get("threshold"),
                "raw_decision": raw_outcome,
                "approval_status": request.state.get("approval_status"),
            },
        )

    def _apply_extensions(
        self,
        request: GovernanceRequest,
        decision: GovernanceDecision,
    ) -> GovernanceDecision:
        current = decision
        for extension in self.extensions:
            override = extension.review(request, current)
            if override is None:
                continue
            if current.outcome == BLOCK and override.outcome == ALLOW:
                current = GovernanceDecision(
                    outcome=BLOCK,
                    reason="EXTENSION_CANNOT_RELAX_BLOCK",
                    rule="GOVERNANCE_INVARIANT",
                    risk=current.risk,
                    policy_version=current.policy_version,
                    request_id=current.request_id,
                    trace_id=current.trace_id,
                    evidence={"rejected_extension_outcome": ALLOW},
                )
            elif current.outcome == ESCALATE and override.outcome == ALLOW:
                current = GovernanceDecision(
                    outcome=ESCALATE,
                    reason="ESCALATION_REQUIRES_APPROVAL",
                    rule="GOVERNANCE_INVARIANT",
                    risk=current.risk,
                    policy_version=current.policy_version,
                    request_id=current.request_id,
                    trace_id=current.trace_id,
                    evidence={"rejected_extension_outcome": ALLOW},
                )
            else:
                current = override
        return current


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


@dataclass(frozen=True)
class AuditTrace:
    """Structured, hash-chained trace for a governance attempt."""

    event_id: str
    timestamp: str
    stage: str
    request_id: str
    trace_id: str
    action: str
    outcome: str
    reason: str
    rule: str
    risk: float | None
    policy_version: str
    execution_status: str
    adapter_called: bool
    adapter_result: Any = None
    previous_hash: str | None = None
    event_hash: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "stage": self.stage,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "action": self.action,
            "outcome": self.outcome,
            "reason": self.reason,
            "rule": self.rule,
            "risk": self.risk,
            "policy_version": self.policy_version,
            "execution_status": self.execution_status,
            "adapter_called": self.adapter_called,
            "adapter_result": self.adapter_result,
            "previous_hash": self.previous_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "event_hash": self.event_hash}


class AuditTrail:
    """In-memory structured audit trail with optional legacy logger forwarding."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        legacy_logger: Any = None,
    ) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._legacy_logger = legacy_logger
        self._events: list[AuditTrace] = []

    @property
    def events(self) -> tuple[AuditTrace, ...]:
        return tuple(self._events)

    def record(
        self,
        request: GovernanceRequest,
        decision: GovernanceDecision,
        *,
        stage: str,
        execution_status: str,
        adapter_called: bool,
        adapter_result: Any = None,
    ) -> AuditTrace:
        timestamp = self._clock().astimezone(timezone.utc).isoformat()
        previous_hash = self._events[-1].event_hash if self._events else None
        trace = AuditTrace(
            event_id=uuid.uuid4().hex,
            timestamp=timestamp,
            stage=stage,
            request_id=request.request_id,
            trace_id=request.trace_id,
            action=request.action,
            outcome=decision.outcome,
            reason=decision.reason,
            rule=decision.rule,
            risk=decision.risk,
            policy_version=decision.policy_version,
            execution_status=execution_status,
            adapter_called=adapter_called,
            adapter_result=adapter_result,
            previous_hash=previous_hash,
        )
        event_hash = hashlib.sha256(_canonical_bytes(trace.payload())).hexdigest()
        trace = AuditTrace(**{**trace.__dict__, "event_hash": event_hash})
        self._events.append(trace)
        self._forward_legacy(request, decision)
        return trace

    def _forward_legacy(
        self,
        request: GovernanceRequest,
        decision: GovernanceDecision,
    ) -> None:
        if self._legacy_logger is None:
            return
        legacy_decision = {
            "action": request.action,
            "decision": "PASS" if decision.outcome == ALLOW else decision.outcome,
            "rule_id": decision.rule,
            "matched_policy": decision.reason,
            "severity": str(decision.evidence.get("severity", "UNKNOWN")),
            "score": decision.risk or 0.0,
            "threshold": decision.evidence.get("threshold") or 0.0,
        }
        event = self._legacy_logger.create_event(
            legacy_decision,
            decision.policy_version,
        )
        self._legacy_logger.save_event(event)

    def verify(self) -> bool:
        previous_hash = None
        for event in self._events:
            if event.previous_hash != previous_hash:
                return False
            expected = hashlib.sha256(
                _canonical_bytes(event.payload())
            ).hexdigest()
            if event.event_hash != expected:
                return False
            previous_hash = event.event_hash
        return True


@dataclass(frozen=True)
class ExecutionResult:
    decision: GovernanceDecision
    executed: bool
    adapter_called: bool
    output: Any
    audit: AuditTrace

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "executed": self.executed,
            "adapter_called": self.adapter_called,
            "output": self.output,
            "audit": self.audit.to_dict(),
        }


class GovernanceRuntime:
    """Pre-execution boundary: evaluate first, invoke adapter only on ALLOW."""

    def __init__(
        self,
        engine: GovernanceEngine,
        audit: AuditTrail | None = None,
        execution_capability: object | None = None,
    ):
        self.engine = engine
        self.audit = audit or AuditTrail()
        self._execution_capability = execution_capability

    def govern(self, request: GovernanceRequest) -> tuple[GovernanceDecision, AuditTrace]:
        decision = self.engine.evaluate(request)
        trace = self.audit.record(
            request.normalized(),
            decision,
            stage="GOVERN",
            execution_status="not_requested",
            adapter_called=False,
        )
        return decision, trace

    def execute(
        self,
        request: GovernanceRequest,
        adapter: ExecutionAdapter,
    ) -> ExecutionResult:
        normalized = request.normalized()
        decision = self.engine.evaluate(normalized)
        if not decision.execution_allowed:
            trace = self.audit.record(
                normalized,
                decision,
                stage="ENFORCE",
                execution_status="not_executed",
                adapter_called=False,
            )
            return ExecutionResult(decision, False, False, None, trace)

        try:
            governed_execute = getattr(adapter, "_execute_with_capability", None)
            if governed_execute is not None:
                output = governed_execute(
                    normalized,
                    self._execution_capability,
                )
            else:
                output = adapter.execute(normalized)
        except Exception as exc:
            trace = self.audit.record(
                normalized,
                decision,
                stage="EXECUTE",
                execution_status="execution_failed",
                adapter_called=True,
                adapter_result={"error_type": type(exc).__name__},
            )
            return ExecutionResult(decision, False, True, None, trace)

        trace = self.audit.record(
            normalized,
            decision,
            stage="EXECUTE",
            execution_status="executed",
            adapter_called=True,
            adapter_result=output,
        )
        return ExecutionResult(decision, True, True, output, trace)
