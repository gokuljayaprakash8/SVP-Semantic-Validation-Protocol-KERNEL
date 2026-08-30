import hashlib
import hmac
import json
import re


SECRET = b"svp-v05-6-semantic-boundary-secret"


class SemanticBoundaryError(Exception):
    pass


# ------------------------------------------------------------
# Canonicalization / cryptographic commitment
# ------------------------------------------------------------

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
# Conservative purpose normalization
# ------------------------------------------------------------

STOPWORDS = {
    "the",
    "a",
    "an",
    "for",
    "to",
    "of",
    "and",
    "with",
    "data",
    "dataset",
}


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    words = [
        word
        for word in text.split()
        if word not in STOPWORDS
    ]
    return set(words)


def purpose_relation(parent, child):
    """
    Conservative lexical baseline.

    Returns one of:

        EQUIVALENT
        NARROWER
        BROADER
        CONFLICT
        AMBIGUOUS

    This is intentionally NOT an AI semantic model.
    It establishes a reproducible baseline against
    which later semantic models can be evaluated.
    """

    p = normalize(parent)
    c = normalize(child)

    if p == c:
        return "EQUIVALENT"

    # Explicit conflicting objective vocabulary.
    conflict_pairs = [
        ({"research"}, {"delete", "destruction"}),
        ({"read"}, {"delete"}),
        ({"audit"}, {"advertising"}),
        ({"security"}, {"surveillance"}),
    ]

    for left, right in conflict_pairs:
        if (p & left) and (c & right):
            return "CONFLICT"

        if (p & right) and (c & left):
            return "CONFLICT"

    # Conservative subset/superset relationship.
    if p and c.issubset(p):
        return "NARROWER"

    if p and p.issubset(c):
        return "BROADER"

    return "AMBIGUOUS"


def purpose_is_safe(parent, child):
    relation = purpose_relation(parent, child)

    return relation in (
        "EQUIVALENT",
        "NARROWER",
    )


# ------------------------------------------------------------
# Intent object
# ------------------------------------------------------------

def create_root(purpose):
    obj = {
        "type": "ROOT",
        "identity": "agent-A",
        "purpose": purpose,
        "resource": "synthetic://dataset/*",
        "action": "read",
        "authority": "dataset-reader",
        "parent_commitment": None,
    }

    obj["commitment"] = attest(obj)

    return obj


def delegate(parent, identity, purpose):
    child = {
        "type": "DELEGATION",
        "identity": identity,
        "purpose": purpose,
        "resource": parent["resource"],
        "action": parent["action"],
        "authority": parent["authority"],
        "parent_commitment": parent["commitment"],
    }

    child["commitment"] = attest(child)

    return child


# ------------------------------------------------------------
# Verification
# ------------------------------------------------------------

def verify_chain(chain):
    if not chain:
        raise SemanticBoundaryError(
            "Empty delegation chain"
        )

    for hop, node in enumerate(chain):

        supplied = node.get("commitment")

        if not supplied:
            raise SemanticBoundaryError(
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
            raise SemanticBoundaryError(
                f"Cryptographic commitment invalid at hop {hop}"
            )

        if hop == 0:
            continue

        parent = chain[hop - 1]

        if node["parent_commitment"] != parent["commitment"]:
            raise SemanticBoundaryError(
                f"Parent linkage invalid at hop {hop}"
            )

        relation = purpose_relation(
            parent["purpose"],
            node["purpose"],
        )

        if relation not in (
            "EQUIVALENT",
            "NARROWER",
        ):
            raise SemanticBoundaryError(
                f"Purpose relation {relation} "
                f"not permitted at hop {hop}"
            )

    return True


# ------------------------------------------------------------
# Test harness
# ------------------------------------------------------------

def run_case(
    name,
    parent_purpose,
    child_purpose,
    expected_relation,
    expected_acceptance,
):
    relation = purpose_relation(
        parent_purpose,
        child_purpose,
    )

    root = create_root(parent_purpose)

    child = delegate(
        root,
        "agent-B",
        child_purpose,
    )

    try:
        verify_chain([root, child])
        accepted = True
        outcome = "CHAIN ACCEPTED"
    except SemanticBoundaryError as exc:
        accepted = False
        outcome = f"DENIED: {exc}"

    relation_correct = relation == expected_relation
    acceptance_correct = accepted == expected_acceptance

    passed = (
        relation_correct
        and acceptance_correct
    )

    print(f"CASE: {name}")
    print(f"PARENT: {parent_purpose}")
    print(f"CHILD:  {child_purpose}")
    print(f"RELATION: {relation}")
    print(f"EXPECTED RELATION: {expected_relation}")
    print(f"EXPECTED ACCEPTANCE: {expected_acceptance}")
    print(f"ACTUAL ACCEPTANCE:   {accepted}")
    print(f"OUTCOME: {outcome}")
    print(f"EXPECTATION MET: {passed}")
    print()

    return passed


def main():
    print("SVP v0.5.6 SEMANTIC PURPOSE BOUNDARY")
    print("=" * 68)
    print()

    results = []

    results.append(
        run_case(
            "EXACT EQUIVALENCE",
            "research-read",
            "research-read",
            "EQUIVALENT",
            True,
        )
    )

    results.append(
        run_case(
            "WORD ORDER / STOPWORD VARIANT",
            "read dataset for research",
            "read the dataset for research",
            "EQUIVALENT",
            True,
        )
    )

    results.append(
        run_case(
            "NARROWER PURPOSE",
            "research read",
            "research",
            "NARROWER",
            True,
        )
    )

    results.append(
        run_case(
            "PURPOSE BROADENING",
            "research",
            "research marketing",
            "BROADER",
            False,
        )
    )

    results.append(
        run_case(
            "RESEARCH TO MARKETING",
            "research",
            "marketing",
            "AMBIGUOUS",
            False,
        )
    )

    results.append(
        run_case(
            "READ TO DELETE",
            "read",
            "delete",
            "CONFLICT",
            False,
        )
    )

    results.append(
        run_case(
            "SECURITY TO SURVEILLANCE",
            "security",
            "surveillance",
            "CONFLICT",
            False,
        )
    )

    results.append(
        run_case(
            "AMBIGUOUS PURPOSE",
            "scientific analysis",
            "commercial optimization",
            "AMBIGUOUS",
            False,
        )
    )

    results.append(
        run_case(
            "SEMANTICALLY RELATED BUT NOT IDENTICAL",
            "fraud detection",
            "financial anomaly analysis",
            "AMBIGUOUS",
            False,
        )
    )

    print("SVP v0.5.6 SUMMARY")
    print("=" * 68)
    print(f"TOTAL CASES:  {len(results)}")
    print(f"PASSED CASES: {sum(results)}")
    print(f"FAILED CASES: {len(results) - sum(results)}")

    if all(results):
        print("EXPERIMENT STATUS: PASS")
    else:
        print("EXPERIMENT STATUS: FINDING")


if __name__ == "__main__":
    main()
