import hashlib
import json
import uuid
from datetime import datetime


class AuditLogger:
    """
    Generates tamper-evident audit records for every SVP Kernel decision.
    """

    def __init__(self):
        self._previous_hash = None

    def _generate_hash(self, event: dict) -> str:
        """
        Generate a deterministic SHA-256 hash for an audit event.
        """
        payload = json.dumps(event, sort_keys=True)

        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def create_event(self, decision_data: dict, kernel_version: str):
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": decision_data["action"],
        "decision": decision_data["decision"],
        "rule_id": decision_data["rule_id"],
        "matched_policy": decision_data["matched_policy"],
        "severity": decision_data["severity"],
        "risk_score": decision_data["score"],
        "threshold": decision_data["threshold"],
        "kernel_version": kernel_version,
        "previous_hash": self._previous_hash,
    }

    event["hash"] = self._generate_hash(event)

    self._previous_hash = event["hash"]

    return event
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "decision": decision,
            "risk_score": risk_score,
            "policy_triggered": policy_triggered,
            "kernel_version": kernel_version,
            "previous_hash": self._previous_hash,
        }

        event["hash"] = self._generate_hash(event)

        self._previous_hash = event["hash"]

        return event
