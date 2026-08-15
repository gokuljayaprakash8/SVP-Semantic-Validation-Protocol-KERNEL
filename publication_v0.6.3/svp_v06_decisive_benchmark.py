import hashlib
import hmac
import json
import time

SECRET = b"svp-v06-test-secret"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def commit(obj):
    fields = {
        "purpose": obj["purpose"],
        "resource": obj["resource"],
        "action": obj["action"],
        "authority": obj["authority"],
        "parent_commitment": obj["parent_commitment"],
    }
    return hmac.new(
        SECRET,
        canonical(fields),
        hashlib.sha256,
    ).hexdigest()


def make_root():
    root = {
        "purpose": "authorized dataset research",
        "resource": "synthetic://dataset-A",
        "action": "read",
        "authority": "researcher",
        "parent_commitment": None,
    }
    root["commitment"] = commit(root)
    return root


def child(parent, mutation=None):
    mutation = mutation or {}

    obj = {
        "purpose": mutation.get("purpose", parent["purpose"]),
        "resource": mutation.get("resource", parent["resource"]),
        "action": mutation.get("action", parent["action"]),
        "authority": mutation.get("authority", parent["authority"]),
        "parent_commitment": parent["commitment"],
    }

    obj["commitment"] = commit(obj)
    return obj


def semantic_contained(parent, child_obj):
    return (
        child_obj["purpose"] == parent["purpose"]
        and child_obj["resource"] == parent["resource"]
        and child_obj["action"] == parent["action"]
        and child_obj["authority"] == parent["authority"]
    )


def verify_chain(chain):
    for i in range(1, len(chain)):
        parent = chain[i - 1]
        current = chain[i]

        if current["parent_commitment"] != parent["commitment"]:
            return False, f"parent linkage invalid at hop {i}"

        if not hmac.compare_digest(
            current["commitment"],
            commit(current),
        ):
            return False, f"commitment invalid at hop {i}"

        if not semantic_contained(parent, current):
            return False, f"semantic escalation at hop {i}"

    return True, "CHAIN ACCEPTED"


def build_chain(depth, mutation_hop=None, mutation=None):
    chain = [make_root()]

    for hop in range(1, depth + 1):
        current_mutation = mutation if hop == mutation_hop else {}
        chain.append(child(chain[-1], current_mutation))

    return chain


def run_case(name, depth, mutation_hop, mutation, expected):
    start = time.perf_counter_ns()

    chain = build_chain(
        depth,
        mutation_hop,
        mutation,
    )

    accepted, outcome = verify_chain(chain)

    elapsed_ms = (
        time.perf_counter_ns() - start
    ) / 1_000_000

    passed = accepted == expected

    print()
    print(f"CASE: {name}")
    print(f"DEPTH: {depth}")

    if mutation_hop is not None:
        print(f"MUTATION HOP: {mutation_hop}")

    print(f"EXPECTED ACCEPTANCE: {expected}")
    print(f"ACTUAL ACCEPTANCE: {accepted}")
    print(f"OUTCOME: {outcome}")
    print(f"VERIFICATION MS: {elapsed_ms:.3f}")
    print(f"EXPECTATION MET: {passed}")

    return passed


def main():
    print("=" * 60)
    print("SVP v0.6 DECISIVE ADVERSARIAL BENCHMARK")
    print("=" * 60)

    results = []

    depths = [1, 10, 100, 1000]

    # Benign controls
    for depth in depths:
        results.append(
            run_case(
                "BENIGN VALID DELEGATION",
                depth,
                None,
                {},
                True,
            )
        )

    attacks = [
        (
            "PURPOSE ESCALATION",
            {"purpose": "commercial optimization"},
        ),
        (
            "RESOURCE ESCALATION",
            {"resource": "synthetic://dataset-secret"},
        ),
        (
            "ACTION ESCALATION",
            {"action": "delete"},
        ),
        (
            "AUTHORITY ESCALATION",
            {"authority": "admin"},
        ),
        (
            "COMBINED ESCALATION",
            {
                "purpose": "commercial optimization",
                "resource": "synthetic://dataset-secret",
                "action": "delete",
                "authority": "admin",
            },
        ),
    ]

    for depth in depths:
        for name, mutation in attacks:
            mutation_hop = min(depth, max(1, depth // 2))

            results.append(
                run_case(
                    name,
                    depth,
                    mutation_hop,
                    mutation,
                    False,
                )
            )

    print()
    print("=" * 60)
    print("SVP v0.6 SUMMARY")
    print("=" * 60)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print("TOTAL CASES:", total)
    print("PASSED CASES:", passed)
    print("FAILED CASES:", failed)

    if failed == 0:
        print(
            "SEMANTIC ESCALATION FALSE ACCEPTANCE RATE: 0.000"
        )
        print("EXPERIMENT STATUS: PASS")
    else:
        print(
            "SEMANTIC ESCALATION FALSE ACCEPTANCE RATE: FINDING"
        )
        print("EXPERIMENT STATUS: FINDING")

    print("MAX DEPTH: 1000")


if __name__ == "__main__":
    main()
