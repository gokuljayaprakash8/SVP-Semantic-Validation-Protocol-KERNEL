import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass


SECRET = b"svp-v05-purpose-binding-secret"


class PurposeBindingError(Exception):
    pass


def canonicalize(obj):
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def commit(request):
    return hmac.new(
        SECRET,
        canonicalize(request),
        hashlib.sha256,
    ).hexdigest()


def verify_commitment(request, supplied_commitment):
    expected = commit(request)

    if not supplied_commitment:
        raise PurposeBindingError(
            "FATAL: Missing purpose-bound commitment; access denied."
        )

    if not hmac.compare_digest(expected, supplied_commitment):
        raise PurposeBindingError(
            "FATAL: Purpose-bound commitment invalid; access denied."
        )

    return True


@dataclass
class PurposeBoundAccessRequest:
    identity: str
    authority: str
    resource: str
    action: str
    purpose: str
    nonce: str


class PurposeBoundDataGate:

    def authorize(self, request):
        # v0.5 baseline policy.
        #
        # The purpose is part of the authorization decision,
        # not merely audit metadata.

        request = type("RequestView", (), request)()

        if request.action != "read":
            return False

        if request.resource != "synthetic://dataset/record-001":
            return False

        if request.authority != "dataset-reader":
            return False

        if request.purpose != "authorized dataset operation":
            return False

        return True

    def execute(self, request, commitment):
        # Verify the exact object immediately before access.
        verify_commitment(request, commitment)

        if not self.authorize(request):
            raise PurposeBindingError(
                "FATAL: Purpose/resource/action authorization failed; "
                "data access denied."
            )

        return "DATA_ACCESS_GRANTED"


def make_request(
    purpose="authorized dataset operation",
    action="read",
    resource="synthetic://dataset/record-001",
    authority="dataset-reader",
    identity="agent-001",
):
    return {
        "identity": identity,
        "authority": authority,
        "resource": resource,
        "action": action,
        "purpose": purpose,
        "nonce": secrets.token_hex(16),
    }


def run_case(name, request, mutate=None, expected=True):
    commitment = commit(request)

    if mutate:
        mutate(request)

    try:
        result = PurposeBoundDataGate().execute(
            request,
            commitment,
        )
        actual = True
        outcome = result
    except PurposeBindingError as exc:
        actual = False
        outcome = f"DENIED: {exc}"

    passed = actual == expected

    print(f"CASE: {name}")
    print(f"EXPECTED ACCESS: {expected}")
    print(f"ACTUAL ACCESS:   {actual}")
    print(f"OUTCOME:         {outcome}")
    print(f"EXPECTATION MET: {passed}")
    print()

    return passed


def mutate_purpose(request):
    request["purpose"] = "sell dataset externally"


def mutate_action(request):
    request["action"] = "delete"


def mutate_resource(request):
    request["resource"] = "synthetic://restricted/dataset"


def remove_purpose(request):
    del request["purpose"]


def mutate_authority(request):
    request["authority"] = "dataset-admin"


def main():
    print("SVP v0.5 PURPOSE-BOUND DATA ACCESS")
    print("=" * 42)
    print()

    results = []

    results.append(
        run_case(
            "LEGITIMATE PURPOSE-BOUND READ",
            make_request(),
            expected=True,
        )
    )

    results.append(
        run_case(
            "POST-COMMITMENT PURPOSE MUTATION",
            make_request(),
            mutate=mutate_purpose,
            expected=False,
        )
    )

    results.append(
        run_case(
            "POST-COMMITMENT ACTION MUTATION",
            make_request(),
            mutate=mutate_action,
            expected=False,
        )
    )

    results.append(
        run_case(
            "POST-COMMITMENT RESOURCE MUTATION",
            make_request(),
            mutate=mutate_resource,
            expected=False,
        )
    )

    results.append(
        run_case(
            "PURPOSE REMOVED",
            make_request(),
            mutate=remove_purpose,
            expected=False,
        )
    )

    results.append(
        run_case(
            "POST-COMMITMENT AUTHORITY MUTATION",
            make_request(),
            mutate=mutate_authority,
            expected=False,
        )
    )

    print("SVP v0.5 PURPOSE-BINDING SUMMARY")
    print("=" * 42)
    print(f"TOTAL CASES:  {len(results)}")
    print(f"PASSED CASES: {sum(results)}")
    print(f"FAILED CASES: {len(results) - sum(results)}")

    if all(results):
        print("EXPERIMENT STATUS: PASS")
    else:
        print("EXPERIMENT STATUS: FINDING")


if __name__ == "__main__":
    main()
