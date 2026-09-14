import hashlib
import hmac
import json
import re


SECRET = b"svp-v05-7-semantic-evaluator-secret"


class SemanticEvaluatorError(Exception):
    pass


# ------------------------------------------------------------
# Cryptographic commitment
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
# Semantic purpose evaluator
# ------------------------------------------------------------

PURPOSE_FAMILIES = {
    "research": {
        "research",
        "scientific",
        "science",
        "study",
        "analysis",
    },
    "security": {
        "security",
        "secure",
        "defense",
        "defence",
        "protection",
        "audit",
    },
    "fraud": {
        "fraud",
        "fraud-detection",
        "anomaly",
        "anomalies",
        "financial",
        "investigation",
    },
    "marketing": {
        "marketing",
        "advertising",
        "promotion",
        "sales",
        "commercial",
    },
    "destructive": {
        "delete",
        "deletion",
        "destroy",
        "destruction",
        "erase",
    },
}


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    return set(text.split())


def families(tokens):
    matched = set()

    for family, vocabulary in PURPOSE_FAMILIES.items():
        if tokens & vocabulary:
            matched.add(family)

    return matched


def semantic_relation(parent, child):
    """
    Conservative semantic baseline.

    This is NOT yet an embedding model.

    The evaluator deliberately distinguishes:

        EQUIVALENT
        NARROWER
        BROADER
        CONFLICT
        AMBIGUOUS
    """

    p_tokens = normalize(parent)
    c_tokens = normalize(child)

    p_families = families(p_tokens)
    c_families = families(c_tokens)

    # Exact normalized equality.
    if p_tokens == c_tokens:
        return "EQUIVALENT"

    # Explicit destructive contradiction.
    if "destructive" in c_families:
        if "destructive" not in p_families:
            return "CONFLICT"

    # Same semantic family with additional purpose terms.
    if p_families == c_families:
        if p_tokens.issubset(c_tokens):
            return "BROADER"

        if c_tokens.issubset(p_tokens):
            return "NARROWER"

        return "EQUIVALENT"

    # Parent has one purpose family and child retains it
    # while adding another family.
    if p_families and p_families.issubset(c_families):
        return "BROADER"

    # Child stays within the parent's family set.
    if c_families and c_families.issubset(p_families):
        return "NARROWER"

    return "AMBIGUOUS"


def semantic_allows(parent, child):
    relation = semantic_relation(
        parent,
        child,
    )

    return relation in {
        "EQUIVALENT",
        "NARROWER",
    }


# ------------------------------------------------------------
# Intent / delegation
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
    obj = {
        "type": "DELEGATION",
        "identity": identity,
        "purpose": purpose,
        "resource": parent["resource"],
        "action": parent["action"],
        "authority": parent["authority"],
        "parent_commitment": parent["commitment"],
    }

    obj["commitment"] = attest(obj)

    return obj


def verify(chain):
    if not chain:
        raise SemanticEvaluatorError(
            "Empty delegation chain"
        )

    for hop, node in enumerate(chain):

        supplied = node.get("commitment")

        if not supplied:
            raise SemanticEvaluatorError(
                f"Missing commitment at hop {hop}"
            )

        unsigned = {
            key: value
            for key, value in node.items()
            if key != "commitment"
        }

        expected = attest(unsigned)

        if not hmac.compare_digest(
            expected,
            supplied,
        ):
            raise SemanticEvaluatorError(
                f"Cryptographic commitment invalid at hop {hop}"
            )

        if hop == 0:
            continue

        parent = chain[hop - 1]

        if node["parent_commitment"] != parent["commitment"]:
            raise SemanticEvaluatorError(
                f"Parent linkage invalid at hop {hop}"
            )

        relation = semantic_relation(
            parent["purpose"],
            node["purpose"],
        )

        if relation not in {
            "EQUIVALENT",
            "NARROWER",
        }:
            raise SemanticEvaluatorError(
                f"Semantic intent violation: "
                f"{relation} at hop {hop}"
            )

    return True


# ------------------------------------------------------------
# Evaluation
# ------------------------------------------------------------

CASES = [
    (
        "EXACT PURPOSE",
        "research-read",
        "research-read",
        "EQUIVALENT",
        True,
    ),
    (
        "RESEARCH PARAPHRASE",
        "research",
        "scientific study",
        "EQUIVALENT",
        True,
    ),
    (
        "SECURITY PARAPHRASE",
        "security",
        "protection",
        "EQUIVALENT",
        True,
    ),
    (
        "FRAUD RELATED PURPOSE",
        "fraud detection",
        "financial anomaly analysis",
        "BROADER",
        False,
    ),
    (
        "RESEARCH BROADENING",
        "research",
        "research marketing",
        "BROADER",
        False,
    ),
    (
        "PURPOSE SUBSTITUTION",
        "research",
        "marketing",
        "AMBIGUOUS",
        False,
    ),
    (
        "DESTRUCTIVE DRIFT",
        "research",
        "delete",
        "CONFLICT",
        False,
    ),
    (
        "SECURITY TO ADVERTISING",
        "security",
        "advertising",
        "AMBIGUOUS",
        False,
    ),
    (
        "AMBIGUOUS PURPOSE",
        "scientific research",
        "commercial optimization",
        "AMBIGUOUS",
        False,
    ),
]


def run_case(
    name,
    parent,
    child,
    expected_relation,
    expected_acceptance,
):
    relation = semantic_relation(
        parent,
        child,
    )

    root = create_root(parent)

    delegated = delegate(
        root,
        "agent-B",
        child,
    )

    try:
        verify([root, delegated])
        accepted = True
        outcome = "CHAIN ACCEPTED"
    except SemanticEvaluatorError as exc:
        accepted = False
        outcome = f"DENIED: {exc}"

    relation_ok = relation == expected_relation
    acceptance_ok = accepted == expected_acceptance

    passed = relation_ok and acceptance_ok

    print(f"CASE: {name}")
    print(f"PARENT: {parent}")
    print(f"CHILD:  {child}")
    print(f"RELATION: {relation}")
    print(f"EXPECTED RELATION: {expected_relation}")
    print(f"EXPECTED ACCEPTANCE: {expected_acceptance}")
    print(f"ACTUAL ACCEPTANCE:   {accepted}")
    print(f"OUTCOME: {outcome}")
    print(f"EXPECTATION MET: {passed}")
    print()

    return passed


def main():
    print("SVP v0.5.7 SEMANTIC PURPOSE EVALUATOR")
    print("=" * 72)
    print()

    results = []

    for case in CASES:
        results.append(
            run_case(*case)
        )

    print("SVP v0.5.7 SUMMARY")
    print("=" * 72)
    print(f"TOTAL CASES:  {len(results)}")
    print(f"PASSED CASES: {sum(results)}")
    print(
        f"FAILED CASES: "
        f"{len(results) - sum(results)}"
    )

    if all(results):
        print("EXPERIMENT STATUS: PASS")
    else:
        print("EXPERIMENT STATUS: FINDING")


if __name__ == "__main__":
    main()
