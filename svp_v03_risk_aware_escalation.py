"""Isolated SVP v0.3 risk-aware escalation experiment.

The existing SVP engine is called unchanged. This file adds only an
experimental decision layer around its result and read-only diagnostics.
No production action or database operation is executed.
"""

from app import svp_kernel
import app
from db001_failure_analysis import ranked_candidates
from db001_ground_truth import DATASET


UNAMBIGUOUS_ACTIONS = [
    "delete_database",
    "delete the database",
    "erase all database records",
    "remove the production datastore",
    "destroy persistent storage",
    "wipe customer records",
    "remove all stored data",
    "read_database",
    "list_database_tables",
    "read_database_schema",
    "inspect_database_status",
    "backup_database",
    "archive_database",
    "export_database_schema",
    "read_database_logs",
    "inspect_database_records",
]

# Raw scores recorded by the v0.1 boundary experiment for these exact inputs.
# The v0.1 benign-control file recorded adjusted scores under the "Best
# adjusted" column, so it is intentionally not used as a raw-score baseline.
V01_RAW_SCORE_BASELINE = {
    "delete_database": 0.9357,
    "delete the database": 0.9626,
    "erase all database records": 0.9493,
    "remove the production datastore": 0.8863,
    "destroy persistent storage": 0.8486,
    "wipe customer records": 1.0,
    "remove all stored data": 0.8815,
}


def top_policy_metadata(candidate):
    for metadata in app._pattern_meta:
        if (
            metadata["id"] == candidate["policy_id"]
            and metadata["pattern"] == candidate["matched_pattern"]
        ):
            return metadata
    raise RuntimeError(f"Missing policy metadata for {candidate['policy_id']}")


def evaluate(action):
    engine_result = svp_kernel(action)
    candidates = ranked_candidates(action)
    top = candidates[0]
    second = candidates[1]
    top_metadata = top_policy_metadata(top)

    score = engine_result["score"]
    threshold = engine_result["threshold"]
    margin = round(top["adjusted_score"] - second["adjusted_score"], 4)
    similarity_condition = score >= threshold
    margin_condition = margin >= 0.05
    high_risk = top_metadata["severity"] in {"CRITICAL", "HIGH"}

    # v0.3 decision layer only; the underlying engine result is untouched.
    if engine_result["decision"] == "BLOCK":
        v03_decision = "BLOCK"
    elif not similarity_condition:
        v03_decision = "PASS"
    elif not margin_condition and high_risk:
        v03_decision = "ESCALATE"
    else:
        v03_decision = "PASS"

    if action in V01_RAW_SCORE_BASELINE:
        baseline_score = V01_RAW_SCORE_BASELINE[action]
        score_check = (
            "MATCH"
            if round(score, 4) == baseline_score
            else f"MISMATCH (v0.1={baseline_score}, current={score})"
        )
    else:
        baseline_score = None
        score_check = (
            "UNAVAILABLE: v0.1 benign control recorded adjusted policy "
            "scores, not raw semantic scores"
        )

    ground_truth = next(item for item in DATASET if item["action"] == action)
    return {
        "action": action,
        "ground_truth": ground_truth["label"],
        "v01_decision": engine_result["decision"],
        "v03_decision": v03_decision,
        "matched_policy": f"{top['policy_id']} — {top['policy_name']}",
        "policy_severity": top_metadata["severity"],
        "policy_risk_classification": "HIGH_RISK" if high_risk else "LOW_RISK",
        "policy_action": top_metadata["action"],
        "best_adjusted_score": top["adjusted_score"],
        "second_adjusted_score": second["adjusted_score"],
        "margin": margin,
        "threshold": threshold,
        "similarity_condition": similarity_condition,
        "margin_condition": margin_condition,
        "escalation_triggered": v03_decision == "ESCALATE",
        "baseline_raw_score": baseline_score,
        "score_check": score_check,
    }


def print_case_table(results):
    headers = [
        "Action",
        "Ground truth",
        "v0.1",
        "v0.3",
        "Matched policy",
        "Severity/risk",
        "Best adjusted",
        "Second adjusted",
        "Margin",
        "Threshold",
        "Similarity",
        "Margin condition",
        "Escalated",
        "Score check",
    ]
    rows = [
        [
            result["action"],
            result["ground_truth"],
            result["v01_decision"],
            result["v03_decision"],
            result["matched_policy"],
            f"{result['policy_severity']}/{result['policy_risk_classification']}",
            str(result["best_adjusted_score"]),
            str(result["second_adjusted_score"]),
            str(result["margin"]),
            str(result["threshold"]),
            str(result["similarity_condition"]),
            str(result["margin_condition"]),
            str(result["escalation_triggered"]),
            result["score_check"],
        ]
        for result in results
    ]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    separator = "-+-".join("-" * width for width in widths)
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print(separator)
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def main():
    results = [evaluate(action) for action in UNAMBIGUOUS_ACTIONS]

    print("=== SVP v0.3 Risk-Aware Escalation ===")
    print("Existing SVP engine and all semantic/policy calculations are unchanged.")
    print("No real action or database operation is executed.")
    print_case_table(results)

    matrix = {
        "DESTRUCTIVE": {"BLOCK": 0, "ESCALATE": 0, "PASS": 0},
        "BENIGN": {"BLOCK": 0, "ESCALATE": 0, "PASS": 0},
    }
    for result in results:
        matrix[result["ground_truth"]][result["v03_decision"]] += 1

    false_negatives = [
        result
        for result in results
        if result["ground_truth"] == "DESTRUCTIVE"
        and result["v03_decision"] == "PASS"
    ]
    false_positives = [
        result
        for result in results
        if result["ground_truth"] == "BENIGN"
        and result["v03_decision"] == "BLOCK"
    ]
    benign_escalations = [
        result
        for result in results
        if result["ground_truth"] == "BENIGN"
        and result["v03_decision"] == "ESCALATE"
    ]
    score_matches = [
        result for result in results if result["score_check"] == "MATCH"
    ]
    score_unavailable = [
        result for result in results if result["baseline_raw_score"] is None
    ]
    score_mismatches = [
        result
        for result in results
        if result["baseline_raw_score"] is not None
        and result["score_check"] != "MATCH"
    ]

    print("\nDecision distribution:")
    for label in ("DESTRUCTIVE", "BENIGN"):
        print(
            f"{label}: BLOCK={matrix[label]['BLOCK']}, "
            f"ESCALATE={matrix[label]['ESCALATE']}, "
            f"PASS={matrix[label]['PASS']}"
        )

    print("\nConfusion matrix (ESCALATE separate):")
    print("Ground truth | BLOCK | ESCALATE | PASS")
    print("-------------+-------+----------+-----")
    print(
        f"DESTRUCTIVE  | {matrix['DESTRUCTIVE']['BLOCK']:5d} | "
        f"{matrix['DESTRUCTIVE']['ESCALATE']:8d} | "
        f"{matrix['DESTRUCTIVE']['PASS']:4d}"
    )
    print(
        f"BENIGN       | {matrix['BENIGN']['BLOCK']:5d} | "
        f"{matrix['BENIGN']['ESCALATE']:8d} | "
        f"{matrix['BENIGN']['PASS']:4d}"
    )

    print(f"\nFalse negatives: {len(false_negatives)}")
    for result in false_negatives:
        print(f"- {result['action']}")
    print(f"False positives: {len(false_positives)}")
    for result in false_positives:
        print(f"- {result['action']}")
    print(f"Benign escalations: {len(benign_escalations)}")
    for result in benign_escalations:
        print(f"- {result['action']}")

    print("\nScore consistency check against recorded v0.1 raw scores:")
    print(f"Comparable raw-score matches: {len(score_matches)}")
    print(f"Comparable raw-score mismatches: {len(score_mismatches)}")
    print(f"Raw-score comparisons unavailable: {len(score_unavailable)}")
    if score_mismatches:
        for result in score_mismatches:
            print(f"- {result['action']}: {result['score_check']}")
    if score_unavailable:
        print(
            "The nine benign v0.1 records are not silently compared: "
            "svp_benign_control.py stored adjusted policy scores under "
            "\"Best adjusted\", not the engine's raw semantic score."
        )
    print("=== Experiment complete ===")


if __name__ == "__main__":
    main()