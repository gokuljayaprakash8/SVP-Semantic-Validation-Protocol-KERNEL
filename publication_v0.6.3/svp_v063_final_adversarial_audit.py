import json
import multiprocessing
import os
from pathlib import Path

from fastapi.testclient import TestClient

import app
import svp_v06_runtime_gate as gate


DB = "svp_v063_final_audit.sqlite3"


def fresh_record(action):
    decision = {
        "action": action,
        "decision": "PASS",
        "rule_id": "SAFE001",
        "threshold": 0.75,
    }
    return gate.create_bound_decision(action, decision)


def post(action, record):
    client = TestClient(app.app)
    return client.post(
        "/v1/execute/v06-test",
        json={"action": action, "record": record},
    )


def check(name, condition, detail):
    print(f"CASE: {name}")
    print(f"RESULT: {detail}")
    print(f"EXPECTATION MET: {condition}")
    print()
    return condition


def concurrent_worker(worker_id):
    import app
    import svp_v06_runtime_gate as gate
    gate.REPLAY_DB = os.environ["SVP_V063_REPLAY_DB"]
    from fastapi.testclient import TestClient

    action = f"read synthetic://dataset/v063-final-concurrent-{worker_id}"

    decision = {
        "action": action,
        "decision": "PASS",
        "rule_id": "SAFE001",
        "threshold": 0.75,
    }

    record = gate.create_bound_decision(action, decision)
    client = TestClient(app.app)

    r = client.post(
        "/v1/execute/v06-test",
        json={"action": action, "record": record},
    )

    return r.json()


def main():
    os.environ["SVP_V063_REPLAY_DB"] = DB
    gate.REPLAY_DB = DB

    try:
        Path(DB).unlink()
    except FileNotFoundError:
        pass

    passed = 0
    total = 0

    # 1. No authorization
    total += 1
    r = post(
        "read synthetic://dataset/v063-final-no-auth",
        None,
    )
    passed += check(
        "NO AUTHORIZATION",
        r.json().get("executed") is False
        and r.json().get("reason") == "NO DECISION",
        r.json(),
    )

    # 2. Valid authorization
    action = "read synthetic://dataset/v063-final-valid"
    record = fresh_record(action)

    total += 1
    r = post(action, record)
    passed += check(
        "VALID AUTHORIZATION",
        r.json().get("executed") is True,
        r.json(),
    )

    # 3. Same-process replay
    total += 1
    r = post(action, record)
    passed += check(
        "SAME-PROCESS REPLAY",
        r.json().get("executed") is False
        and r.json().get("reason") == "REPLAY",
        r.json(),
    )

    # 4. Forged action
    action = "read synthetic://dataset/v063-final-forged"
    record = fresh_record(action)

    total += 1
    r = post(
        "write synthetic://dataset/v063-final-forged",
        record,
    )
    passed += check(
        "FORGED ACTION",
        r.json().get("executed") is False
        and r.json().get("reason") == "REQUEST BINDING INVALID",
        r.json(),
    )

    # 5. Decision mutation
    action = "read synthetic://dataset/v063-final-decision"
    record = fresh_record(action)
    record["decision"] = "BLOCK"

    total += 1
    r = post(action, record)
    passed += check(
        "DECISION MUTATION",
        r.json().get("executed") is False
        and r.json().get("reason") == "DECISION COMMITMENT INVALID",
        r.json(),
    )

    # 6. Rule mutation
    action = "read synthetic://dataset/v063-final-rule"
    record = fresh_record(action)
    record["rule_id"] = "MUTATED"

    total += 1
    r = post(action, record)
    passed += check(
        "RULE MUTATION",
        r.json().get("executed") is False
        and r.json().get("reason") == "DECISION COMMITMENT INVALID",
        r.json(),
    )

    # 7. Threshold mutation
    action = "read synthetic://dataset/v063-final-threshold"
    record = fresh_record(action)
    record["threshold"] = 0.01

    total += 1
    r = post(action, record)
    passed += check(
        "THRESHOLD MUTATION",
        r.json().get("executed") is False
        and r.json().get("reason") == "DECISION COMMITMENT INVALID",
        r.json(),
    )

    # 8. Empty record
    total += 1
    r = post(
        "read synthetic://dataset/v063-final-empty",
        {},
    )
    passed += check(
        "EMPTY RECORD",
        r.json().get("executed") is False,
        r.json(),
    )

    # 9. Authorization substitution
    action_a = "read synthetic://dataset/v063-final-A"
    action_b = "read synthetic://dataset/v063-final-B"

    record_a = fresh_record(action_a)
    record_b = fresh_record(action_b)

    total += 1
    r1 = post(action_a, record_b)
    r2 = post(action_b, record_a)

    substitution_pass = (
        r1.json().get("executed") is False
        and r2.json().get("executed") is False
    )

    passed += check(
        "AUTHORIZATION SUBSTITUTION",
        substitution_pass,
        {"A_with_B": r1.json(), "B_with_A": r2.json()},
    )

    # 10. Concurrent consumption
    total += 1

    # The concurrent worker creates one fresh authorization per worker,
    # so this section is a smoke test of the persistent store rather than
    # a double-spend test.
    multiprocessing.set_start_method("spawn", force=True)

    with multiprocessing.Pool(2) as pool:
        results = pool.map(concurrent_worker, [0, 1])

    concurrent_ok = (
        sum(r.get("executed") is True for r in results) == 2
    )

    passed += check(
        "CONCURRENT DISTINCT AUTHORIZATIONS",
        concurrent_ok,
        results,
    )

    print("=" * 60)
    print("SVP v0.6.3 FINAL ADVERSARIAL AUDIT")
    print("=" * 60)
    print("TOTAL CASES:", total)
    print("PASSED CASES:", passed)
    print("FAILED CASES:", total - passed)
    print("EXPERIMENT STATUS:", "PASS" if passed == total else "FAIL")
    print("REPLAY DATABASE:", DB)
    print("=" * 60)


if __name__ == "__main__":
    main()
