from fastapi.testclient import TestClient

import app
from svp_v06_runtime_gate import verify_bound_decision


client = TestClient(app.app)


def get_record():
    response = client.post(
        "/v1/audit/v06",
        json={"steps": ["read synthetic://dataset/record-001"]},
    )
    assert response.status_code == 200

    item = response.json()["steps"][0]
    return item


def test_live_kernel_binding():
    item = get_record()

    assert item["binding_valid"] is True
    assert item["binding_outcome"] == "DECISION VALID"

    print("CASE: LIVE KERNEL DECISION BINDING")
    print("RESULT: PASS")


def test_rule_id_mutation():
    item = get_record()
    record = item["record"].copy()

    record["rule_id"] = "ADMIN-UNRESTRICTED"

    valid, reason = verify_bound_decision(
        item["action"],
        record,
    )

    assert valid is False
    assert reason == "DECISION COMMITMENT INVALID"

    print("CASE: RULE ID MUTATION")
    print("RESULT: PASS")


def test_policy_threshold_mutation():
    item = get_record()
    record = item["record"].copy()

    record["threshold"] = 0.01

    valid, reason = verify_bound_decision(
        item["action"],
        record,
    )

    assert valid is False
    assert reason == "DECISION COMMITMENT INVALID"

    print("CASE: THRESHOLD MUTATION")
    print("RESULT: PASS")


def test_request_action_forgery():
    item = get_record()

    forged_action = "delete synthetic://dataset/secret"

    valid, reason = verify_bound_decision(
        forged_action,
        item["record"],
    )

    assert valid is False
    assert reason == "REQUEST BINDING INVALID"

    print("CASE: REQUEST ACTION FORGERY")
    print("RESULT: PASS")


def main():
    print("=" * 60)
    print("SVP v0.6 INTEGRATION REGRESSION")
    print("=" * 60)

    tests = [
        test_live_kernel_binding,
        test_rule_id_mutation,
        test_policy_threshold_mutation,
        test_request_action_forgery,
    ]

    passed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as exc:
            print("RESULT: FAIL")
            print("ERROR:", exc)

    print("=" * 60)
    print("TOTAL CASES:", len(tests))
    print("PASSED CASES:", passed)
    print("FAILED CASES:", len(tests) - passed)

    if passed == len(tests):
        print("EXPERIMENT STATUS: PASS")
    else:
        print("EXPERIMENT STATUS: FINDING")


if __name__ == "__main__":
    main()
