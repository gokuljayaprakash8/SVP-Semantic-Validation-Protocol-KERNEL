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

    def create_event(
        self,
        action: str,
        decision: str,
        risk_score: float,
        policy_triggered: str,
        kernel_version: str,
    ):
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
