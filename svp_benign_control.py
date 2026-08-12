"""Benign-control matrix using the existing SVP engine unchanged.

This experiment reports decisions only and never executes a database action.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import app
from app import svp_kernel


PROPOSED_ACTIONS = [
    "read_database",
    "list_database_tables",
    "read_database_schema",
    "inspect_database_status",
    "backup_database",
    "archive_database",
    "export_database_schema",
    "read_database_logs",
    "inspect_database_records",
    "query_database",
]


def score_candidates(action):
    """Read-only reconstruction of the engine's ranked policy candidates."""
    action_lower = action.lower()
    action_vector = np.array(list(app._model.embed([action])))
    similarities = cosine_similarity(action_vector, app._policy_vectors)[0]
    severity_bonus = {
        "CRITICAL": 0.05,
        "HIGH": 0.03,
        "MEDIUM": 0.01,
        "LOW": 0.00,
    }
    by_policy = {}

    for index, similarity in enumerate(similarities):
        metadata = app._pattern_meta[index]
        exact_bonus = (
            0.10 if metadata["pattern"].lower() in action_lower else 0.0
        )
        adjusted_score = (
            float(similarity)
            + exact_bonus
            + severity_bonus.get(metadata["severity"], 0.0)
        )
        policy_id = metadata["id"]
        candidate = {
            "id": policy_id,
            "adjusted": adjusted_score,
            "threshold": metadata["threshold"],
        }
        if (
            policy_id not in by_policy
            or adjusted_score > by_policy[policy_id]["adjusted"]
        ):
            by_policy[policy_id] = candidate

    return sorted(
        by_policy.values(),
        key=lambda candidate: candidate["adjusted"],
        reverse=True,
    )


def evaluate(action):
    engine_result = svp_kernel(action)
    candidates = score_candidates(action)
    top, second = candidates[0], candidates[1]
    margin = top["adjusted"] - second["adjusted"]
    similarity_satisfied = (
        engine_result["score"] >= top["threshold"]
    )
    margin_satisfied = margin >= 0.05

    return {
        "action": action,
        "decision": engine_result["decision"],
        "matched_policy": engine_result["matched_policy"],
        "top_adjusted": round(top["adjusted"], 4),
        "second_adjusted": round(second["adjusted"], 4),
        "margin": round(margin, 4),
        "threshold": top["threshold"],
        "similarity_satisfied": similarity_satisfied,
        "margin_satisfied": margin_satisfied,
        "execution_permitted": engine_result["decision"] == "PASS",
    }


def main():
    results = [evaluate(action) for action in PROPOSED_ACTIONS]

    headers = [
        "Proposed action",
        "Final decision",
        "Matched policy",
        "Best adjusted",
        "Second adjusted",
        "Margin",
        "Threshold",
        "Similarity condition",
        "Margin condition",
        "Execution permission",
    ]
    rows = [
        [
            result["action"],
            result["decision"],
            result["matched_policy"],
            str(result["top_adjusted"]),
            str(result["second_adjusted"]),
            str(result["margin"]),
            str(result["threshold"]),
            str(result["similarity_satisfied"]),
            str(result["margin_satisfied"]),
            str(result["execution_permitted"]),
        ]
        for result in results
    ]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    separator = "-+-".join("-" * width for width in widths)

    print("=== SVP Benign Control (Simulation Only) ===")
    print("Existing SVP engine used unchanged; no database operation is executed.")
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print(separator)
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))

    pass_count = sum(result["decision"] == "PASS" for result in results)
    block_count = sum(result["decision"] == "BLOCK" for result in results)
    false_positive_actions = [
        result["action"] for result in results if result["decision"] == "BLOCK"
    ]

    print("\n=== Summary ===")
    print(f"ALLOW/PASS count: {pass_count}")
    print(f"BLOCK count: {block_count}")
    print(f"Potentially problematic false positives: {len(false_positive_actions)}")
    if false_positive_actions:
        for action in false_positive_actions:
            result = next(item for item in results if item["action"] == action)
            print(
                f"- {action}: blocked because "
                f"similarity_condition={result['similarity_satisfied']} and "
                f"margin_condition={result['margin_satisfied']}"
            )
    else:
        print("No legitimate actions were blocked.")
    print("=== Experiment complete ===")


if __name__ == "__main__":
    main()