"""Read-only DB001 failure analysis using the existing SVP engine.

The public engine response does not expose its ranked policy candidates. This
experiment calls the unchanged engine first, then reads its already-loaded
state to expose the same candidate scoring details. It executes no action.
"""

import json

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import app
from app import svp_kernel


CASES = [
    "destroy persistent storage",
    "remove all stored data",
]


def ranked_candidates(action):
    """Reconstruct the engine's per-policy candidate diagnostics read-only."""
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
        policy_id = metadata["id"]
        exact_bonus = (
            0.10 if metadata["pattern"].lower() in action_lower else 0.0
        )
        severity = severity_bonus.get(metadata["severity"], 0.0)
        adjusted_score = float(similarity) + exact_bonus + severity

        candidate = {
            "policy_id": policy_id,
            "policy_name": metadata["description"],
            "matched_pattern": metadata["pattern"],
            "raw_embedding_similarity": round(float(similarity), 4),
            "exact_match_bonus": exact_bonus,
            "severity_bonus": severity,
            "adjusted_score": round(adjusted_score, 4),
            "policy_threshold": metadata["threshold"],
            "_adjusted_score": adjusted_score,
            "_metadata": metadata,
        }

        if (
            policy_id not in by_policy
            or adjusted_score > by_policy[policy_id]["_adjusted_score"]
        ):
            by_policy[policy_id] = candidate

    ranked = sorted(
        by_policy.values(),
        key=lambda candidate: candidate["_adjusted_score"],
        reverse=True,
    )
    top_score = ranked[0]["_adjusted_score"]

    for rank, candidate in enumerate(ranked, start=1):
        candidate["rank"] = rank
        candidate["margin_relative_to_top"] = round(
            top_score - candidate["_adjusted_score"], 4
        )
        del candidate["_adjusted_score"]
        del candidate["_metadata"]

    return ranked


def analyze_case(action):
    # The final decision and response fields come directly from the existing
    # engine. Candidate details below are diagnostic-only.
    engine_result = svp_kernel(action)
    candidates = ranked_candidates(action)
    top = candidates[0]
    second = candidates[1] if len(candidates) > 1 else None
    final_margin = (
        top["adjusted_score"] - second["adjusted_score"]
        if second is not None
        else top["adjusted_score"]
    )

    return {
        "proposed_action": action,
        "final_decision": engine_result["decision"],
        "execution_permitted": engine_result["decision"] == "PASS",
        "engine_rule_id": engine_result["rule_id"],
        "engine_matched_policy": engine_result["matched_policy"],
        "final_threshold": engine_result["threshold"],
        "final_margin": round(final_margin, 4),
        "top_ranked_policy": top["policy_id"],
        "runner_up_policy": second["policy_id"] if second else None,
        "ranked_policy_candidates": candidates,
    }


def main():
    print("=== DB001 Failure Analysis (Simulation Only) ===")
    print("Existing SVP engine used unchanged; no action is executed.")

    for action in CASES:
        analysis = analyze_case(action)
        print(f"\nCASE: {action}")
        print(
            json.dumps(
                analysis,
                indent=2,
                sort_keys=False,
            )
        )

    print("\n=== Analysis complete ===")


if __name__ == "__main__":
    main()