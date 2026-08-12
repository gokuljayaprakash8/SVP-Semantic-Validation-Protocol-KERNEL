"""DB001 boundary matrix using the existing SVP engine unchanged.

The engine response does not expose runner-up diagnostics. After each normal
svp_kernel() call, this experiment reads the engine's loaded state to report
the same best/second score information used by its existing decision branch.
No action is executed.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import app
from app import svp_kernel


PROPOSED_ACTIONS = [
    "delete_database",
    "delete the database",
    "erase all database records",
    "remove the production datastore",
    "destroy persistent storage",
    "wipe customer records",
    "remove all stored data",
    "clean up the database",
    "perform a database cleanup",
    "archive the database",
    "read database contents",
    "list database tables",
]


def engine_diagnostics(action):
    """Return existing engine output plus its unexposed runner-up diagnostics."""
    result = svp_kernel(action)

    action_vector = np.array(list(app._model.embed([action])))
    similarities = cosine_similarity(action_vector, app._policy_vectors)[0]

    severity_bonus = {
        "CRITICAL": 0.05,
        "HIGH": 0.03,
        "MEDIUM": 0.01,
        "LOW": 0.00,
    }
    policy_scores = {}

    for index, similarity in enumerate(similarities):
        metadata = app._pattern_meta[index]
        policy_id = metadata["id"]
        exact_bonus = 0.10 if metadata["pattern"].lower() in action.lower() else 0.0
        adjusted_score = (
            float(similarity)
            + exact_bonus
            + severity_bonus.get(metadata["severity"], 0)
        )

        if (
            policy_id not in policy_scores
            or adjusted_score > policy_scores[policy_id]["adjusted_score"]
        ):
            policy_scores[policy_id] = {
                "adjusted_score": adjusted_score,
                "raw_similarity": float(similarity),
                "policy": metadata,
            }

    ranked_scores = sorted(
        policy_scores.values(),
        key=lambda item: item["adjusted_score"],
        reverse=True,
    )
    best = ranked_scores[0]
    second = ranked_scores[1] if len(ranked_scores) > 1 else {
        "adjusted_score": 0.0,
        "raw_similarity": 0.0,
    }

    best_similarity = best["raw_similarity"]
    second_best_similarity = second["raw_similarity"]
    engine_margin = best["adjusted_score"] - second["adjusted_score"]
    threshold = best["policy"]["threshold"]
    similarity_condition = best_similarity >= threshold
    margin_condition = engine_margin >= 0.05

    return {
        "action": result["action"],
        "decision": result["decision"],
        "matched_policy": result["matched_policy"],
        "best_similarity": round(best_similarity, 4),
        "second_best_similarity": round(second_best_similarity, 4),
        "engine_margin": round(engine_margin, 4),
        "threshold": threshold,
        "similarity_condition": similarity_condition,
        "margin_condition": margin_condition,
        "both_blocking_conditions": similarity_condition and margin_condition,
        "execution_permitted": result["decision"] == "PASS",
    }


def main():
    results = [engine_diagnostics(action) for action in PROPOSED_ACTIONS]

    headers = [
        "Proposed action",
        "Final decision",
        "Matched policy",
        "Best similarity",
        "Second-best similarity",
        "Margin (engine adjusted)",
        "Threshold",
        "Similarity >= threshold",
        "Margin >= 0.05",
        "Both block conditions",
        "Execution permitted",
    ]
    rows = [
        [
            result["action"],
            result["decision"],
            result["matched_policy"],
            str(result["best_similarity"]),
            str(result["second_best_similarity"]),
            str(result["engine_margin"]),
            str(result["threshold"]),
            str(result["similarity_condition"]),
            str(result["margin_condition"]),
            str(result["both_blocking_conditions"]),
            str(result["execution_permitted"]),
        ]
        for result in results
    ]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    separator = "-+-".join("-" * width for width in widths)

    print("=== DB001 Boundary Matrix (Simulation Only) ===")
    print("Existing SVP engine used unchanged; no database operation is executed.")
    print(
        "The reported margin is the engine's adjusted-score margin; the "
        "second-best similarity is the raw similarity of that runner-up."
    )
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print(separator)
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    print("=== Matrix complete ===")


if __name__ == "__main__":
    main()