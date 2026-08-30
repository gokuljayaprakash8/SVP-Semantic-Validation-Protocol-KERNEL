import hashlib
import hmac
import json


SECRET = b"svp-v05-5-intent-invariants-secret"


class IntentViolation(Exception):
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


# ------------------------------------------------------------
# Intent model
# ------------------------------------------------------------

ACTION_ORDER = {
    "read": 1,
    "write": 2,
    "delete": 3,
}

AUTHORITY_ORDER = {
    "dataset-reader": 1,
    "delegated-reader": 1,
    "dataset-writer": 2,
    "dataset-admin": 3,
}


def resource_is_within(parent, child):
    """
    Conservative resource containment rule.

    Exact resource equality is always valid.

    A child may narrow a dataset resource from:

        dataset/*
            ->
        dataset/record-001

    but may not broaden it.
    """

    if child == parent:
        return True

    if parent.endswith("/*"):
        prefix = parent[:-1]
        return child.startswith(prefix)

    return False


def action_is_within(parent, child):
    """
    A child cannot acquire a more powerful action.
    """

    parent_rank = ACTION_ORDER.get(parent)
    child_rank = ACTION_ORDER.get(child)

    if parent_rank is None or child_rank is None:
        return parent == child

    return child_rank <= parent_rank


def authority_is_within(parent, child):
    """
    A child cannot escalate authority.
    """

    parent_rank = AUTHORITY_ORDER.get(parent)
    child_rank = AUTHORITY_ORDER.get(child)

    if parent_rank is None or child_rank is None:
        return parent == child

    return child_rank <= parent_rank


def purpose_is_preserved(parent, child):
    """
    v0.5.5 conservative rule:

    Purpose must remain exactly bound.

    We intentionally do NOT claim semantic equivalence yet.
    That requires a separately validated semantic model.
    """

    return parent == child


def intent_is_preserved(parent, child):
    return (
        purpose_is_preserved(
            parent["purpose"],
            child["purpose"],
        )
        and resource_is_within(
            parent["resource"],
            child["resource"],
        )
        and action_is_within(
            parent["action"],
            child["action"],
        )
        and authority_is_within(
            parent["authority"],
            child["authority"],
        )
    )


# ------------------------------------------------------------
# Cryptographic delegation
# ------------------------------------------------------------

def create_root():
    obj = {
        "type": "ROOT",
        "identity": "agent-A",
        "purpose": "research-read",
        "resource": "synthetic://dataset/*",
        "action": "read",
        "authority": "dataset-reader",
        "parent_commitment": None,
    }

    obj["commitment"] = attest(obj)

    return obj


def delegate(parent, identity, **changes):
    child = {
        "type": "DELEGATION",
        "identity": identity,
        "purpose": changes.get(
            "purpose",
            parent["purpose"],
        ),
        "resource": changes.get(
            "resource",
            parent["resource"],
        ),
        "action": changes.get(
            "action",
            parent["action"],
        ),
        "authority": changes.get(
            "authority",
            parent["authority"],
        ),
        "parent_commitment": parent["commitment"],
    }

    child["commitment"] = attest(child)

    return child


# ------------------------------------------------------------
# Verification
# ------------------------------------------------------------

def verify_chain(chain):
    if not chain:
        raise IntentViolation("Empty chain")

    for hop, node in enumerate(chain):

        supplied = node.get("commitment")

        if not supplied:
            raise IntentViolation(
                f"Missing commitment at hop {hop}"
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
            raise IntentViolation(
                f"Cryptographic commitment invalid at hop {hop}"
            )

        if hop == 0:
            if node.get("parent_commitment") is not None:
                raise IntentViolation(
                    "Root cannot have a parent"
                )

            continue

        parent = chain[hop - 1]

        if node.get("parent_commitment") != parent.get(
            "commitment"
        ):
            raise IntentViolation(
                f"Parent linkage invalid at hop {hop}"
            )

        if not intent_is_preserved(
            parent,
            node,
        ):
            raise IntentViolation(
                f"Intent preservation violated at hop {hop}"
            )

    return True


# ------------------------------------------------------------
# Test harness
# ------------------------------------------------------------

def run_case(name, chain, expected):
    try:
        verify_chain(chain)
        actual = True
        outcome = "CHAIN ACCEPTED"
    except IntentViolation as exc:
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
    print("SVP v0.5.5 INTENT PRESERVATION INVARIANTS")
    print("=" * 64)
    print()

    root = create_root()

    results = []

    # --------------------------------------------------------
    # 1. Exact inheritance
    # --------------------------------------------------------

    child = delegate(
        root,
        "agent-B",
    )

    results.append(
        run_case(
            "EXACT INTENT INHERITANCE",
            [root, child],
            True,
        )
    )

    # --------------------------------------------------------
    # 2. Legitimate resource narrowing
    # --------------------------------------------------------

    child = delegate(
        root,
        "agent-B",
        resource="synthetic://dataset/record-001",
    )

    results.append(
        run_case(
            "RESOURCE NARROWING",
            [root, child],
            True,
        )
    )

    # --------------------------------------------------------
    # 3. Resource broadening
    # --------------------------------------------------------

    child = delegate(
        root,
        "agent-B",
        resource="synthetic://*",
    )

    results.append(
        run_case(
            "RESOURCE BROADENING",
            [root, child],
            False,
        )
    )

    # --------------------------------------------------------
    # 4. Action escalation
    # --------------------------------------------------------

    child = delegate(
        root,
        "agent-B",
        action="delete",
    )

    results.append(
        run_case(
            "ACTION ESCALATION",
            [root, child],
            False,
        )
    )

    # --------------------------------------------------------
    # 5. Authority escalation
    # --------------------------------------------------------

    child = delegate(
        root,
        "agent-B",
        authority="dataset-admin",
    )

    results.append(
        run_case(
            "AUTHORITY ESCALATION",
            [root, child],
            False,
        )
    )

    # --------------------------------------------------------
    # 6. Purpose substitution
    # --------------------------------------------------------

    child = delegate(
        root,
        "agent-B",
        purpose="delete-for-profit",
    )

    results.append(
        run_case(
            "PURPOSE SUBSTITUTION",
            [root, child],
            False,
        )
    )

    # --------------------------------------------------------
    # 7. Combined malicious transformation
    # --------------------------------------------------------

    child = delegate(
        root,
        "agent-B",
        purpose="delete-for-profit",
        resource="synthetic://*",
        action="delete",
        authority="dataset-admin",
    )

    results.append(
        run_case(
            "COMBINED INTENT ESCALATION",
            [root, child],
            False,
        )
    )

    # --------------------------------------------------------
    # 8. Multi-hop narrowing
    # --------------------------------------------------------

    b = delegate(
        root,
        "agent-B",
        resource="synthetic://dataset/record-001",
    )

    c = delegate(
        b,
        "agent-C",
        resource="synthetic://dataset/record-001",
    )

    results.append(
        run_case(
            "MULTI-HOP NARROWING",
            [root, b, c],
            True,
        )
    )

    print("SVP v0.5.5 SUMMARY")
    print("=" * 64)
    print(f"TOTAL CASES:  {len(results)}")
    print(f"PASSED CASES: {sum(results)}")
    print(f"FAILED CASES: {len(results) - sum(results)}")

    if all(results):
        print("EXPERIMENT STATUS: PASS")
    else:
        print("EXPERIMENT STATUS: FINDING")


if __name__ == "__main__":
    main()
