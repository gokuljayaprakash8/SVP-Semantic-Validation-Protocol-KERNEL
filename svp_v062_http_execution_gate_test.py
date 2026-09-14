from fastapi import FastAPI
from fastapi.testclient import TestClient

from svp_v06_runtime_gate import (
    create_bound_decision,
    verify_bound_decision,
)

app = FastAPI()

CONSUMED = set()
EXECUTED = []


def authorize(action):
    decision = {
        "decision": "PASS",
        "rule_id": "SAFE001",
        "threshold": 0.75,
    }

    record = create_bound_decision(action, decision)
    record["authorization_id"] = record["request_commitment"]

    return record


def execution_gate(action, record):
    if record is None:
        return False, "NO DECISION"

    valid, reason = verify_bound_decision(action, record)

    if not valid:
        return False, reason

    authorization_id = record["authorization_id"]

    if authorization_id in CONSUMED:
        return False, "REPLAY"

    CONSUMED.add(authorization_id)
    EXECUTED.append(action)

    return True, "EXECUTION AUTHORIZED"


@app.post("/v1/execute-test")
def execute_test(payload: dict):
    action = payload.get("action")
    record = payload.get("record")

    allowed, reason = execution_gate(action, record)

    if not allowed:
        return {
            "executed": False,
            "reason": reason,
        }

    return {
        "executed": True,
        "reason": reason,
    }


def main():
    client = TestClient(app)

    action = "read synthetic://dataset/record-001"

    print("=" * 60)
    print("SVP v0.6.2 HTTP EXECUTION-GATE TEST")
    print("=" * 60)

    # 1. No authorization
    r = client.post(
        "/v1/execute-test",
        json={"action": action, "record": None},
    )
    result = r.json()

    print("CASE: NO AUTHORIZATION")
    print("HTTP:", r.status_code)
    print("RESULT:", result)
    print("EXPECTED EXECUTED:", False)
    print()

    # 2. Valid authorization
    record = authorize(action)

    r = client.post(
        "/v1/execute-test",
        json={"action": action, "record": record},
    )
    result = r.json()

    print("CASE: VALID AUTHORIZATION")
    print("HTTP:", r.status_code)
    print("RESULT:", result)
    print("EXPECTED EXECUTED:", True)
    print()

    # 3. Replay
    r = client.post(
        "/v1/execute-test",
        json={"action": action, "record": record},
    )
    result = r.json()

    print("CASE: REPLAY")
    print("HTTP:", r.status_code)
    print("RESULT:", result)
    print("EXPECTED EXECUTED:", False)
    print()

    # 4. Forged action with fresh authorization
    record = authorize(action)
    forged = "delete synthetic://dataset/secret"

    r = client.post(
        "/v1/execute-test",
        json={"action": forged, "record": record},
    )
    result = r.json()

    print("CASE: FORGED ACTION")
    print("HTTP:", r.status_code)
    print("RESULT:", result)
    print("EXPECTED EXECUTED:", False)
    print()

    # 5. Mutated decision with fresh authorization
    record = authorize(action)
    record["decision"] = "BLOCK"

    r = client.post(
        "/v1/execute-test",
        json={"action": action, "record": record},
    )
    result = r.json()

    print("CASE: DECISION MUTATION")
    print("HTTP:", r.status_code)
    print("RESULT:", result)
    print("EXPECTED EXECUTED:", False)
    print()

    print("=" * 60)
    print("EXECUTED SINK:", EXECUTED)
    print("TOTAL EXECUTIONS:", len(EXECUTED))
    print("=" * 60)


if __name__ == "__main__":
    main()
