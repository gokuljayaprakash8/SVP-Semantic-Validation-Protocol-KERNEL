import hashlib
import hmac
import json


SECRET = b"svp-v05-2-recursive-delegation-secret"


class DelegationError(Exception):
    pass


def canonicalize(obj):
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def attest(obj):
    return hmac.new(
        SECRET,
        canonicalize(obj),
        hashlib.sha256,
    ).hexdigest()


def create_root(
    identity,
    purpose,
    resource,
    action,
    authority,
):
    obj = {
        "type": "ROOT",
        "identity": identity,
        "purpose": purpose,
        "resource": resource,
        "action": action,
        "authority": authority,
        "parent_commitment": None,
    }

    obj["commitment"] = attest(obj)
    return obj


def delegate(parent, child_identity, child_authority):
    child = {
        "type": "DELEGATION",
        "identity": child_identity,

        # Critical invariant:
        # purpose/resource/action are inherited
        # from the parent rather than independently supplied.
        "purpose": parent["purpose"],
        "resource": parent["resource"],
        "action": parent["action"],

        "authority": child_authority,
        "parent_commitment": parent["commitment"],
    }

    child["commitment"] = attest(child)
    return child


def verify_chain(chain):
    if not chain:
        raise DelegationError("Empty delegation chain")

    for index, node in enumerate(chain):
        supplied = node.get("commitment")

        if not supplied:
            raise DelegationError(
                f"Missing commitment at hop {index}"
            )

        unsigned = {
            k: v
            for k, v in node.items()
            if k != "commitment"
        }

        expected = attest(unsigned)

        if not hmac.compare_digest(
            expected,
            supplied,
        ):
            raise DelegationError(
                f"Cryptographic commitment invalid at hop {index}"
            )

        if index == 0:
            if node.get("parent_commitment") is not None:
                raise DelegationError(
                    "Root cannot have a parent commitment"
                )
            continue

        parent = chain[index - 1]

        if node.get("parent_commitment") != parent.get(
            "commitment"
        ):
            raise DelegationError(
                f"Parent commitment mismatch at hop {index}"
            )

        # Recursive intent-preservation invariant.
        for field in (
            "purpose",
            "resource",
            "action",
        ):
            if node.get(field) != parent.get(field):
                raise DelegationError(
                    f"Intent violation at hop {index}: "
                    f"{field} changed"
                )

    return True


def run_case(name, chain, expected):
    try:
        verify_chain(chain)
        actual = True
        outcome = "CHAIN ACCEPTED"
    except DelegationError as exc:
        actual = False
        outcome = f"DENIED: {exc}"

    passed = actual == expected

    print(f"CASE: {name}")
    print(f"EXPECTED ACCEPTANCE: {expected}")
    print(f"ACTUAL ACCEPTANCE:   {actual}")
    print(f"OUTCOME: {outcome}")
    print(f"EXPECTATION MET: {passed}")
    print()

    return passed


def main():
    print("SVP v0.5.2 RECURSIVE INTENT-PRESERVING DELEGATION")
    print("=" * 58)
    print()

    root = create_root(
        identity="agent-A",
        purpose="read dataset for research",
        resource="synthetic://dataset/record-001",
        action="read",
        authority="dataset-reader",
    )

    agent_b = delegate(
        root,
        child_identity="agent-B",
        child_authority="delegated-reader",
    )

    agent_c = delegate(
        agent_b,
        child_identity="agent-C",
        child_authority="delegated-reader",
    )

    chain = [
        root,
        agent_b,
        agent_c,
    ]

    results = []

    results.append(
        run_case(
            "VALID A -> B -> C CHAIN",
            chain,
            True,
        )
    )

    # Attack 1: B attempts to change purpose.
    tampered = [dict(x) for x in chain]
    tampered[1]["purpose"] = "exfiltrate dataset"

    results.append(
        run_case(
            "B PURPOSE MUTATION",
            tampered,
            False,
        )
    )

    # Attack 2: C attempts to change resource.
    tampered = [dict(x) for x in chain]
    tampered[2]["resource"] = (
        "synthetic://secret-record"
    )

    results.append(
        run_case(
            "C RESOURCE MUTATION",
            tampered,
            False,
        )
    )

    # Attack 3: C attempts to change action.
    tampered = [dict(x) for x in chain]
    tampered[2]["action"] = "delete"

    results.append(
        run_case(
            "C ACTION MUTATION",
            tampered,
            False,
        )
    )

    # Attack 4: C attempts to detach from B.
    tampered = [dict(x) for x in chain]
    tampered[2]["parent_commitment"] = "forged-parent"

    results.append(
        run_case(
            "C PARENT DETACHMENT",
            tampered,
            False,
        )
    )

    print("SVP v0.5.2 SUMMARY")
    print("=" * 58)
    print(f"TOTAL CASES:  {len(results)}")
    print(f"PASSED CASES: {sum(results)}")
    print(f"FAILED CASES: {len(results) - sum(results)}")

    if all(results):
        print("EXPERIMENT STATUS: PASS")
    else:
        print("EXPERIMENT STATUS: FINDING")


if __name__ == "__main__":
    main()
