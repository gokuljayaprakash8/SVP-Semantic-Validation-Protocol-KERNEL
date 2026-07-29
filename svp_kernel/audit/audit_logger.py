import hashlib
import json
import uuid
from datetime import datetime


class AuditLogger:
    """
    Generates tamper-evident audit records for every SVP Kernel decision.
    """

    def __init__(self):
        self.log_file = "audit_log.json"
        self._previous_hash = self._load_last_hash()

    def _load_last_hash(self):
        try:
            with open(self.log_file, "r") as f:
                logs = json.load(f)
            if logs:
                return logs[-1]["hash"]
        except Exception:
            pass
        return None

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

    def save_event(self, event: dict):
        try:
            with open(self.log_file, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []

        logs.append(event)

        with open(self.log_file, "w") as f:
            json.dump(logs, f, indent=2)

    def verify_chain(self):
        try:
            with open(self.log_file, "r") as f:
                logs = json.load(f)
        except Exception:
            return False

        previous_hash = None

        for event in logs:
            stored_hash = event.get("hash")

            event_copy = event.copy()
            event_copy.pop("hash", None)

            calculated_hash = self._generate_hash(event_copy)

            if stored_hash != calculated_hash:
                return False

            if event.get("previous_hash") != previous_hash:
                return False

            previous_hash = stored_hash

        return True
