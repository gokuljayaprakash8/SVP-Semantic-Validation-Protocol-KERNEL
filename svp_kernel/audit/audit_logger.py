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
        import fcntl
        import os
        import tempfile

        lock_file = f"{self.log_file}.lock"
        with open(lock_file, "a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                try:
                    with open(self.log_file, "r") as f:
                        logs = json.load(f)
                except FileNotFoundError:
                    logs = []

                previous_hash = logs[-1]["hash"] if logs else None
                persisted_event = dict(event)
                persisted_event["previous_hash"] = previous_hash
                persisted_event.pop("hash", None)
                persisted_event["hash"] = self._generate_hash(persisted_event)

                directory = os.path.dirname(os.path.abspath(self.log_file))
                fd, temp_path = tempfile.mkstemp(dir=directory, prefix=".audit_log.", suffix=".tmp")
                try:
                    with os.fdopen(fd, "w") as f:
                        json.dump(logs + [persisted_event], f, indent=2)
                        f.flush()
                        os.fsync(f.fileno())
                    os.replace(temp_path, self.log_file)
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)

                self._previous_hash = persisted_event["hash"]
                return persisted_event
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

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
