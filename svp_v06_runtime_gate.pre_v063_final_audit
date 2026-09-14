import hmac
import hashlib
import json
import sqlite3

SECRET = b"SVP-v0.6-RUNTIME"


def canonicalize(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def mac(obj):
    return hmac.new(SECRET, canonicalize(obj), hashlib.sha256).hexdigest()


def create_bound_decision(action, decision):
    record = {
        "action": action,
        "decision": decision.get("decision"),
        "rule_id": decision.get("rule_id"),
        "threshold": decision.get("threshold"),
    }
    record["request_commitment"] = mac({"action": action})
    record["decision_commitment"] = mac({
        "request_commitment": record["request_commitment"],
        "decision": record["decision"],
        "rule_id": record["rule_id"],
        "threshold": record["threshold"],
    })
    return record


def verify_bound_decision(action, record):
    if action != record.get("action"):
        return False, "REQUEST BINDING INVALID"

    expected_request = mac({"action": record["action"]})
    if not hmac.compare_digest(expected_request, record["request_commitment"]):
        return False, "REQUEST COMMITMENT INVALID"

    expected_decision = mac({
        "request_commitment": record["request_commitment"],
        "decision": record["decision"],
        "rule_id": record["rule_id"],
        "threshold": record["threshold"],
    })

    if not hmac.compare_digest(expected_decision, record["decision_commitment"]):
        return False, "DECISION COMMITMENT INVALID"

    if record["decision"] != "PASS":
        return False, "SVP DECISION DENIED"

    return True, "DECISION VALID"


REPLAY_DB = "svp_v063_replay.sqlite3"


def _init_replay_db():
    conn = sqlite3.connect(REPLAY_DB)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consumed_authorizations (
                authorization_id TEXT PRIMARY KEY
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def consume_authorization(record):
    try:
        _init_replay_db()
    except sqlite3.Error:
        return False, "AUTHORIZATION STORE UNAVAILABLE"

    authorization_id = record.get("request_commitment")

    if not authorization_id:
        return False, "NO AUTHORIZATION ID"

    conn = sqlite3.connect(REPLAY_DB)

    try:
        try:
            conn.execute(
                "INSERT INTO consumed_authorizations "
                "(authorization_id) VALUES (?)",
                (authorization_id,),
            )
            conn.commit()
            return True, "AUTHORIZATION CONSUMED"
        except sqlite3.IntegrityError:
            return False, "REPLAY"
    finally:
        conn.close()
