import uuid
from datetime import datetime


class AuditLogger:
    """
    Generates structured audit records for every SVP Kernel decision.
    """

    def create_event(
        self,
        action: str,
        decision: str,
        risk_score: float,
        policy_triggered: str,
        kernel_version: str,
    ):
        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "decision": decision,
            "risk_score": risk_score,
            "policy_triggered": policy_triggered,
            "kernel_version": kernel_version,
        }
