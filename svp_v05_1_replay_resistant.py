import hashlib
import hmac
import json
import secrets


SECRET = b"svp-v05-1-purpose-binding-secret"


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


class ReplayResistantDataGate:
    def __init__(self):
        # Verifier-side freshness state.
        self.consumed = set()

    def authorize(self, request):
        return (
            request.get("action") == "read"
            and request.get("resource")
            == "synthetic://dataset/record-001"
            and request.get("authority")
            == "dataset-reader"
            and request.get("purpose")
            == "authorized dataset operation"
        )

    def execute(self, request, supplied_commitment):
        expected = commit(request)

        if not supplied_commitment:
            raise PurposeBindingError(
                "Missing commitment; access denied."
            )

        if not hmac.compare_digest(
            expected,
            supplied_commitment,
        ):
            raise PurposeBindingError(
                "Cryptographic commitment invalid; access denied."
            )

        # The commitment itself is the authorization instance.
        authorization_id = supplied_commitment

        # Freshness / single-use enforcement.
        if authorization_id in self.consumed:
            raise PurposeBindingError(
                "Authorization already consumed; replay denied."
            )

        if not self.authorize(request):
            raise PurposeBindingError(
                "Purpose/resource/action authorization failed; "
                "access denied."
            )

        # Consume only after all verification succeeds.
        self.consumed.add(authorization_id)

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


def run_case(name, gate, request, commitment, expected):
    try:
        result = gate.execute(request, commitment)
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


def main():
    print("SVP v0.5.1 REPLAY-RESISTANT PURPOSE BINDING")
    print("=" * 48)
    print()

    gate = ReplayResistantDataGate()
    results = []

    request = make_request()
    commitment = commit(request)

    # First use must succeed.
    results.append(
        run_case(
            "FIRST VALID USE",
            gate,
            request,
            commitment,
            True,
        )
    )

    # Exact replay must fail.
    results.append(
        run_case(
            "EXACT AUTHORIZATION REPLAY",
            gate,
            request,
            commitment,
            False,
        )
    )

    # New authorization instance should be usable.
    fresh_request = make_request()
    fresh_commitment = commit(fresh_request)

    results.append(
        run_case(
            "FRESH AUTHORIZATION",
            gate,
            fresh_request,
            fresh_commitment,
            True,
        )
    )

    print("SVP v0.5.1 SUMMARY")
    print("=" * 48)
    print(f"TOTAL CASES:  {len(results)}")
    print(f"PASSED CASES: {sum(results)}")
    print(f"FAILED CASES: {len(results) - sum(results)}")

    if all(results):
        print("EXPERIMENT STATUS: PASS")
    else:
        print("EXPERIMENT STATUS: FINDING")


if __name__ == "__main__":
    main()
