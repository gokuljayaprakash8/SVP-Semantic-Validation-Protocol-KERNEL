import json
import tempfile
import threading
import unittest
from pathlib import Path

from svp_kernel.audit.audit_logger import AuditLogger


class AuditLoggerTests(unittest.TestCase):
    def test_event_persists_and_chain_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "audit_log.json"

            logger = AuditLogger()
            logger.log_file = str(log_path)

            event = {
                "event_id": "test-1",
                "timestamp": "2026-01-01T00:00:00+00:00",
                "action": "test_action",
                "decision": "PASS",
                "previous_hash": None,
            }
            event["hash"] = logger._generate_hash(event)

            logger.save_event(event)

            self.assertTrue(log_path.exists())
            self.assertTrue(logger.verify_chain())

            with log_path.open() as f:
                logs = json.load(f)

            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]["event_id"], "test-1")

    def test_concurrent_writes_preserve_all_events(self):
        import threading

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "audit_log.json"
            errors = []

            def write_event(index):
                try:
                    logger = AuditLogger()
                    logger.log_file = str(log_path)

                    decision = {
                        "action": f"action-{index}",
                        "decision": "PASS",
                        "rule_id": f"rule-{index}",
                        "matched_policy": "test-policy",
                        "severity": "LOW",
                        "score": 0.1,
                        "threshold": 0.5,
                    }

                    event = logger.create_event(decision, "test")
                    logger.save_event(event)
                except Exception as exc:
                    errors.append(exc)

            threads = [
                threading.Thread(target=write_event, args=(i,))
                for i in range(10)
            ]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            self.assertEqual(errors, [])

            with log_path.open() as f:
                logs = json.load(f)

            self.assertEqual(len(logs), 10)

            verifier = AuditLogger()
            verifier.log_file = str(log_path)
            self.assertTrue(verifier.verify_chain())


if __name__ == "__main__":
    unittest.main()
