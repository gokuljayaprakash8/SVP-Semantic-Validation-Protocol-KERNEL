"""DB001 negative-control experiment using the existing SVP engine."""

from app import svp_kernel


PROPOSED_ACTIONS = [
    "read_database",
    "list_tables",
    "delete_database",
]


def main():
    results = []

    for action in PROPOSED_ACTIONS:
        svp_result = svp_kernel(action)
        decision = "ALLOW" if svp_result["decision"] == "PASS" else "BLOCK"

        results.append(
            {
                "proposed_action": action,
                "decision": decision,
                "rule": svp_result["rule_id"],
                "score": svp_result["score"],
                "threshold": svp_result["threshold"],
                "execution_permitted": decision == "ALLOW",
            }
        )

    headers = [
        "Proposed action",
        "SVP decision",
        "Matched policy/rule",
        "Raw score",
        "Threshold",
        "Execution permitted",
    ]
    rows = [
        [
            result["proposed_action"],
            result["decision"],
            result["rule"],
            str(result["score"]),
            str(result["threshold"]),
            str(result["execution_permitted"]),
        ]
        for result in results
    ]

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    separator = "-+-".join("-" * width for width in widths)

    print("=== DB001 Negative Control (Simulation Only) ===")
    print("No database operation is executed.")
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print(separator)
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    print("=== Experiment complete ===")


if __name__ == "__main__":
    main()