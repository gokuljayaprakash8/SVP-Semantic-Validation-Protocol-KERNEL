import hashlib
import hmac
import json


SECRET = b"svp-v05-3-forged-child-secret"


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


def create_root():
    obj = {
        "type": "ROOT",
        "identity": "agent-A",
        "purpose": "read dataset for research",
        "resource": "synthetic://dataset/record-001",
        "action": "read",
        "authority": "dataset-reader",
        "parent_commitment": None,
    }
    obj["commitment"] = attest(obj)
    return obj


def delegate(parent, identity, authority):
    child = {
        "type": "DELEGATION",
        "identity": identity,
        "purpose": parent["purpose"],
        "resource": parent["resource"],
        "action": parent["action"],
        "authority": authority,
        "parent_commitment": parent["commitment"],
    }
    child["commitment"] = attest(child)
    return child


def verify_chain(chain):
    if not chain:
        raise DelegationError("Empty chain")

    for i, node in enumerate(chain):
        supplied = node.get("commitment")

        if not supplied:
            raise DelegationError(
                f"Missing commitment at hop {i}"
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
                f"Cryptographic commitment invalid at hop {i}"
            )

        if i == 0:
            if node.get("parent_commitment") is not None:
                raise DelegationError(
                    "Root cannot have a parent"
                )
            continue

        parent = chain[i - 1]

        if node.get("parent_commitment") != parent.get(
            "commitment"
        ):
            raise DelegationError(
                f"Parent linkage invalid at hop {i}"
            )

        for field in (
            "purpose",
            "resource",
            "action",
        ):
            if node.get(field) != parent.get(field):
                raise DelegationError(
                    f"Intent propagation violated: "
                    f"{field} changed at hop {i}"
                )

        # Authority cannot silently escalate.
        parent_authority = parent.get("authority")
        child_authority = node.get("authority")

        if parent_authority == "dataset-reader":
            if child_authority not in (
                "dataset-reader",
                "delegated-reader",
            ):
                raise DelegationError(
                    f"Authority escalation at hop {i}"
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
    print("SVP v0.5.3 FORGED-CHILD / AUTHORITY-AMPLIFICATION")
    print("=" * 62)
    print()

    root = create_root()

    child = delegate(
        root,
        "agent-B",
        "delegated-reader",
    )

    valid_chain = [root, child]

    results = []

    results.append(
        run_case(
            "VALID CHILD DELEGATION",
            valid_chain,
            True,
        )
    )

    # --------------------------------------------------
    # Attack 1: malicious child changes purpose AND
    # creates a fresh commitment.
    # --------------------------------------------------

    forged = {
        "type": "DELEGATION",
        "identity": "agent-B",
        "purpose": "delete dataset",
        "resource": root["resource"],
        "action": "read",
        "authority": "delegated-reader",
        "parent_commitment": root["commitment"],
    }

    forged["commitment"] = attest(forged)

    results.append(
        run_case(
            "FORGED CHILD PURPOSE",
            [root, forged],
            False,
        )
    )

    # --------------------------------------------------
    # Attack 2: authority amplification with a fresh
    # cryptographic commitment.
    # --------------------------------------------------

    forged = {
        "type": "DELEGATION",
        "identity": "agent-B",
        "purpose": root["purpose"],
        "resource": root["resource"],
        "action": root["action"],
        "authority": "system-admin",
        "parent_commitment": root["commitment"],
    }

    forged["commitment"] = attest(forged)

    results.append(
        run_case(
            "AUTHORITY AMPLIFICATION",
            [root, forged],
            False,
        )
    )

    # --------------------------------------------------
    # Attack 3: resource substitution with a fresh
    # commitment.
    # --------------------------------------------------

    forged = {
        "type": "DELEGATION",
        "identity": "agent-B",
        "purpose": root["purpose"],
        "resource": "synthetic://secret-dataset",
        "action": root["action"],
        "authority": "delegated-reader",
        "parent_commitment": root["commitment"],
    }

    forged["commitment"] = attest(forged)

    results.append(
        run_case(
            "FORGED CHILD RESOURCE",
            [root, forged],
            False,
        )
    )

    # --------------------------------------------------
    # Attack 4: action escalation with a fresh commitment.
    # --------------------------------------------------

    forged = {
        "type": "DELEGATION",
        "identity": "agent-B",
        "purpose": root["purpose"],
        "resource": root["resource"],
        "action": "delete",
        "authority": "delegated-reader",
        "parent_commitment": root["commitment"],
    }

    forged["commitment"] = attest(forged)

    results.append(
        run_case(
            "FORGED CHILD ACTION",
            [root, forged],
            False,
        )
    )

    # --------------------------------------------------
    # Attack 5: detached malicious root.
    # --------------------------------------------------

    detached = {
        "type": "ROOT",
        "identity": "attacker-agent",
        "purpose": "delete dataset",
        "resource": "synthetic://secret-dataset",
        "action": "delete",
        "authority": "system-admin",
        "parent_commitment": None,
    }

    detached["commitment"] = attest(detached)

    results.append(
        run_case(
            "DETACHED MALICIOUS ROOT",
            [root, child, detached],
            False,
        )
    )

    print("SVP v0.5.3 SUMMARY")
    print("=" * 62)
    print(f"TOTAL CASES:  {len(results)}")
    print(f"PASSED CASES: {sum(results)}")
    print(f"FAILED CASES: {len(results) - sum(results)}")

    if all(results):
        print("EXPERIMENT STATUS: PASS")
    else:
        print("EXPERIMENT STATUS: FINDING")


if __name__ == "__main__":
    main()
