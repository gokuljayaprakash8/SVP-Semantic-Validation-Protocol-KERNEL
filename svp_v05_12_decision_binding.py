import hashlib
import hmac
import json


SECRET = b"svp-v05-12-decision-binding"

FIELDS = (
    "identity",
    "authority",
    "purpose",
    "resource",
    "action",
)


def canonicalize(obj):
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def mac(obj):
    return hmac.new(
        SECRET,
        canonicalize(obj),
        hashlib.sha256,
    ).hexdigest()


def make_request():
    return {
        "identity": "agent-001",
        "authority": "dataset-reader",
        "purpose": "authorized dataset research",
        "resource": "synthetic://dataset/record-001",
        "action": "read synthetic://dataset/record-001",
    }


def evaluate(request):
    # v0.5.12 intentionally uses a deterministic evaluator.
    # The research target here is cryptographic binding of
    # the decision to the evaluated request/context.
    return {
        "decision": "ALLOW",
        "policy_id": "SVP-RESEARCH-READ-001",
        "policy_version": "0.5.12",
    }


def create_decision_record(request):
    evaluation = evaluate(request)

    request_commitment = mac(request)

    record = {
        "request_commitment": request_commitment,
        "decision": evaluation["decision"],
        "policy_id": evaluation["policy_id"],
        "policy_version": evaluation["policy_version"],
    }

    record["decision_commitment"] = mac(record)

    return record


def verify_decision(request, record):
    expected_request_commitment = mac(request)

    if not hmac.compare_digest(
        expected_request_commitment,
        record["request_commitment"],
    ):
        return False, "REQUEST BINDING INVALID"

    unsigned_record = {
        "request_commitment": record["request_commitment"],
        "decision": record["decision"],
        "policy_id": record["policy_id"],
        "policy_version": record["policy_version"],
    }

    expected_decision_commitment = mac(unsigned_record)

    if not hmac.compare_digest(
        expected_decision_commitment,
        record["decision_commitment"],
    ):
        return False, "DECISION COMMITMENT INVALID"

    return True, "DECISION VALID"


def run_case(name, mutation, expected):
    request = make_request()

    original_record = create_decision_record(request)

    mutated_request = dict(request)
    mutated_record = dict(original_record)

    mutation(mutated_request, mutated_record)

    accepted, outcome = verify_decision(
        mutated_request,
        mutated_record,
    )

    passed = accepted == expected

    print()
    print("CASE:", name)
    print("EXPECTED ACCEPTANCE:", expected)
    print("ACTUAL ACCEPTANCE:", accepted)
    print("OUTCOME:", outcome)
    print("EXPECTATION MET:", passed)

    return passed


def main():
    print("SVP v0.5.12 CRYPTOGRAPHIC DECISION BINDING")
    print("=" * 60)

    results = []

    results.append(
        run_case(
            "VALID DECISION",
            lambda request, record: None,
            True,
        )
    )

    results.append(
        run_case(
            "POST-EVALUATION ACTION MUTATION",
            lambda request, record: request.update(
                action="delete synthetic://dataset/record-001"
            ),
            False,
        )
    )

    results.append(
        run_case(
            "POST-EVALUATION RESOURCE MUTATION",
            lambda request, record: request.update(
                resource="synthetic://dataset/secret"
            ),
            False,
        )
    )

    results.append(
        run_case(
            "DECISION MUTATION ALLOW TO DENY",
            lambda request, record: record.update(
                decision="DENY"
            ),
            False,
        )
    )

    results.append(
        run_case(
            "DECISION MUTATION ALLOW TO ALLOW_WITH_ESCALATED_POLICY",
            lambda request, record: record.update(
                policy_id="ADMIN-UNRESTRICTED"
            ),
            False,
        )
    )

    results.append(
        run_case(
            "POLICY VERSION MUTATION",
            lambda request, record: record.update(
                policy_version="999.0"
            ),
            False,
        )
    )

    results.append(
        run_case(
            "STALE DECISION ON DIFFERENT REQUEST",
            lambda request, record: request.update(
                action="read synthetic://dataset/record-999"
            ),
            False,
        )
    )

    print()
    print("SVP v0.5.12 SUMMARY")
    print("=" * 60)
    print("TOTAL CASES:", len(results))
    print("PASSED CASES:", sum(results))
    print("FAILED CASES:", len(results) - sum(results))

    if all(results):
        print("EXPERIMENT STATUS: PASS")
    else:
        print("EXPERIMENT STATUS: FINDING")


if __name__ == "__main__":
    main()
