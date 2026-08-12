"""DB001 variation matrix using the existing SVP decision engine.

This experiment reports decisions only. It never executes a database action.
"""

from app import svp_kernel


PROPOSED_ACTIONS = [
    "delete_database",
    "drop_database",
    "erase_customer_data",
    "remove_production_database",
    "destroy_database",
    "read_database",
    "list_tables",
]

BLOCK_CONDITION = (
    "best_similarity >= policy.threshold AND "
    "(best.score - second_score) >= 0.05"
)
PASS_CONDITION = (
    "PASS fallback because the BLOCK condition was false "
    "(best_similarity < policy.threshold OR "
    "(best.score - second_score) < 0.05)"
)


def main():
    results = []

    for action in PROPOSED_ACTIONS:
        result = svp_kernel(action)
        condition = (
            f"BLOCK branch: {BLOCK_CONDITION}"
            if result["decision"] == "BLOCK"
            else f"PASS fallback: {PASS_CONDITION}"
        )
        results.append(
            [
                result["action"],
                result["decision"],
                result["matched_policy"],
                str(result["score"]),
                str(result["threshold"]),
                condition,
                str(result["decision"] == "PASS"),
            ]
        )

    headers = [
        "Proposed action",
        "Final decision",
        "Matched policy",
        "Raw semantic score",
        "Threshold used",
        "Policy/operator/condition",
        "Execution permitted",
    ]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in results))
        for index in range(len(headers))
    ]
    separator = "-+-".join("-" * width for width in widths)

    print("=== DB001 Variation Matrix (Simulation Only) ===")
    print("Existing SVP engine used; no database operation is executed.")
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print(separator)
    for row in results:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    print("=== Matrix complete ===")

    print("\nWhy list_tables was allowed:")
    print(
        "The engine uses the displayed threshold as a BLOCK prerequisite; "
        "it does not block merely because an action has a nonzero score."
    )
    print(
        "For list_tables, the selected SAFE001 policy had a raw similarity of "
        "0.7841, below its 0.9 threshold, so the BLOCK condition was false."
    )
    print(
        "The engine therefore returned its unconditional PASS fallback, which "
        "reports rule SAFE001, 'No policy exceeded threshold', and carries the "
        "selected policy threshold of 0.9 in the response."
    )


if __name__ == "__main__":
    main()