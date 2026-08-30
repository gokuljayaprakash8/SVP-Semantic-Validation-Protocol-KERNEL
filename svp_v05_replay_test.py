from svp_v05_purpose_binding import (
    PurposeBoundDataGate,
    PurposeBindingError,
    make_request,
    commit,
)


def main():
    print("SVP v0.5 REPLAY RESISTANCE TEST")
    print("=" * 42)
    print()

    request = make_request()
    commitment = commit(request)

    gate = PurposeBoundDataGate()

    # First use of the valid authorization.
    try:
        first = gate.execute(request, commitment)
        first_access = True
        first_outcome = first
    except PurposeBindingError as exc:
        first_access = False
        first_outcome = f"DENIED: {exc}"

    # Replay the exact same request + commitment.
    try:
        second = gate.execute(request, commitment)
        second_access = True
        second_outcome = second
    except PurposeBindingError as exc:
        second_access = False
        second_outcome = f"DENIED: {exc}"

    print("FIRST USE")
    print("ACCESS:", first_access)
    print("OUTCOME:", first_outcome)
    print()

    print("REPLAY")
    print("ACCESS:", second_access)
    print("OUTCOME:", second_outcome)
    print()

    print("REPLAY RESISTANCE EXPECTATION: False")
    print("REPLAY ACTUAL ACCESS:", second_access)

    if second_access:
        print("FINDING: VALID AUTHORIZATION CAN CURRENTLY BE REPLAYED")
    else:
        print("PASS: REPLAY WAS DENIED")


if __name__ == "__main__":
    main()
