import sys
import json
from app import svp_kernel

TARGET = "svp_kernel"


def run_analysis(action_text):
    captured = {
        "exact_bonus": {},
        "scores": {},
        "sorted_scores": None,
        "second_score": None,
    }

    def local_trace(frame, event, arg):
        if event != "line":
            return local_trace

        loc = frame.f_locals

        # Capture loop-local values from the real implementation.
        if "meta" in loc and isinstance(loc["meta"], dict):
            pid = loc["meta"].get("id")

            if "exact_bonus" in loc:
                captured["exact_bonus"][pid] = loc["exact_bonus"]

            if "score" in loc and "similarity" in loc:
                captured["scores"][pid] = {
                    "score": loc["score"],
                    "similarity": loc["similarity"],
                    "policy": dict(loc["meta"]),
                }

        # Capture the actual completed ranking produced by svp_kernel().
        if "sorted_scores" in loc:
            captured["sorted_scores"] = list(loc["sorted_scores"])

        if "second_score" in loc:
            captured["second_score"] = loc["second_score"]

        return local_trace

    def global_trace(frame, event, arg):
        if event == "call" and frame.f_code.co_name == TARGET:
            return local_trace
        return None

    sys.settrace(global_trace)
    try:
        result = svp_kernel(action_text)
    finally:
        sys.settrace(None)

    return result, captured


if __name__ == "__main__":
    actions = [
        "read database",
        "list database tables",
        "backup database",
        "archive database",
        "read database logs",
    ]

    print("=" * 80)
    print("SVP ISOLATED POLICY RANKING ANALYSIS")
    print("Existing svp_kernel() only; no production modification")
    print("=" * 80)

    for action in actions:
        result, captured = run_analysis(action)

        print("\n" + "=" * 80)
        print("INPUT:", action)
        print("-" * 80)

        print("FINAL RESULT:")
        print(json.dumps(result, indent=2, default=str))

        print("\nSECOND SCORE:")
        print(captured["second_score"])

        print("\nTOP 5 CANDIDATES:")
        ranked = captured["sorted_scores"] or []

        for rank, candidate in enumerate(ranked[:5], start=1):
            policy = candidate.get("policy", {})
            pid = policy.get("id", "UNAVAILABLE")

            print(
                f"\n#{rank} {pid}"
                f"\n  policy name: {policy.get('description', 'UNAVAILABLE')}"
                f"\n  severity/risk: {policy.get('severity', 'UNAVAILABLE')}"
                f"\n  threshold: {policy.get('threshold', 'UNAVAILABLE')}"
                f"\n  raw similarity: {candidate.get('similarity', 'UNAVAILABLE')}"
                f"\n  adjusted score: {candidate.get('score', 'UNAVAILABLE')}"
                f"\n  exact-match bonus: "
                f"{captured['exact_bonus'].get(pid, 'UNAVAILABLE')}"
                f"\n  severity bonus: "
                f"{(
                    candidate.get('score', 0)
                    - candidate.get('similarity', 0)
                    - captured['exact_bonus'].get(pid, 0)
                ) if isinstance(candidate.get('score'), (int, float)) else 'UNAVAILABLE'}"
            )

        print("\nCAPTURE STATUS:")
        print("sorted_scores:", "CAPTURED" if captured["sorted_scores"] is not None else "UNAVAILABLE")
        print("second_score:", "CAPTURED" if captured["second_score"] is not None else "UNAVAILABLE")
        print("exact_bonus entries:", len(captured["exact_bonus"]))
        print("score entries:", len(captured["scores"]))
