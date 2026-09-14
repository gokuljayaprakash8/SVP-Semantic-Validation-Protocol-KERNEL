import hashlib
import hmac
import json
import time


SECRET = b"svp-v05-4-depth-stress-secret"


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
        "identity": "agent-0000",
        "purpose": "read dataset for research",
        "resource": "synthetic://dataset/record-001",
        "action": "read",
        "authority": "dataset-reader",
        "parent_commitment": None,
    }

    obj["commitment"] = attest(obj)
    return obj


def delegate(parent, index):
    child = {
        "type": "DELEGATION",
        "identity": f"agent-{index:04d}",
        "purpose": parent["purpose"],
        "resource": parent["resource"],
        "action": parent["action"],
        "authority": "delegated-reader",
        "parent_commitment": parent["commitment"],
    }

    child["commitment"] = attest(child)
    return child


def build_chain(depth):
    chain = [create_root()]

    for index in range(1, depth):
        chain.append(
            delegate(chain[-1], index)
        )

    return chain


def verify_chain(chain):
    if not chain:
        raise DelegationError("Empty chain")

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
                f"Cryptographic failure at hop {index}"
            )

        if index == 0:
            if node.get("parent_commitment") is not None:
                raise DelegationError(
                    "Root has unexpected parent"
                )
            continue

        parent = chain[index - 1]

        if node["parent_commitment"] != parent["commitment"]:
            raise DelegationError(
                f"Parent linkage failure at hop {index}"
            )

        for field in (
            "purpose",
            "resource",
            "action",
        ):
            if node[field] != parent[field]:
                raise DelegationError(
                    f"Intent violation at hop {index}: {field}"
                )

        if node["authority"] not in (
            "dataset-reader",
            "delegated-reader",
        ):
            raise DelegationError(
                f"Authority escalation at hop {index}"
            )

    return True


def measure_depth(depth):
    start = time.perf_counter()

    chain = build_chain(depth)

    build_ms = (
        time.perf_counter() - start
    ) * 1000

    start = time.perf_counter()

    try:
        verify_chain(chain)
        accepted = True
        failure = None
    except DelegationError as exc:
        accepted = False
        failure = str(exc)

    verify_ms = (
        time.perf_counter() - start
    ) * 1000

    return {
        "depth": depth,
        "accepted": accepted,
        "build_ms": build_ms,
        "verify_ms": verify_ms,
        "failure": failure,
    }


def mutation_test(depth, mutation_hop):
    chain = build_chain(depth)

    original = chain[mutation_hop]

    tampered = dict(original)

    # Change the semantic purpose without recomputing
    # the legitimate parent's authorization.
    tampered["purpose"] = "delete dataset"

    chain[mutation_hop] = tampered

    try:
        verify_chain(chain)
        return False
    except DelegationError:
        return True


def main():
    print("SVP v0.5.4 ARBITRARY-DEPTH DELEGATION STRESS")
    print("=" * 62)
    print()

    depths = [
        1,
        5,
        10,
        25,
        50,
        100,
        250,
        500,
        1000,
    ]

    results = []

    print(
        f"{'DEPTH':>8} "
        f"{'ACCEPTED':>10} "
        f"{'BUILD ms':>12} "
        f"{'VERIFY ms':>12}"
    )

    print("-" * 48)

    for depth in depths:
        result = measure_depth(depth)
        results.append(result)

        print(
            f"{depth:>8} "
            f"{str(result['accepted']):>10} "
            f"{result['build_ms']:>12.3f} "
            f"{result['verify_ms']:>12.3f}"
        )

    print()
    print("ADVERSARIAL DEPTH MUTATION TESTS")
    print("=" * 62)

    mutation_depth = 1000

    mutation_points = [
        0,
        1,
        10,
        100,
        500,
        999,
    ]

    mutation_results = []

    for hop in mutation_points:
        detected = mutation_test(
            mutation_depth,
            hop,
        )

        mutation_results.append(detected)

        print(
            f"HOP {hop:>4}: "
            f"MUTATION DETECTED = {detected}"
        )

    print()
    print("SVP v0.5.4 SUMMARY")
    print("=" * 62)

    depth_pass = all(
        result["accepted"]
        for result in results
    )

    mutation_pass = all(
        mutation_results
    )

    print(
        "DEPTH PRESERVATION:",
        "PASS" if depth_pass else "FAIL",
    )

    print(
        "ADVERSARIAL DETECTION:",
        "PASS" if mutation_pass else "FAIL",
    )

    print(
        "MAX DEPTH TESTED:",
        max(depths),
    )

    print(
        "MUTATION POINTS TESTED:",
        len(mutation_points),
    )

    if depth_pass and mutation_pass:
        print(
            "EXPERIMENT STATUS: PASS"
        )
    else:
        print(
            "EXPERIMENT STATUS: FINDING"
        )


if __name__ == "__main__":
    main()
