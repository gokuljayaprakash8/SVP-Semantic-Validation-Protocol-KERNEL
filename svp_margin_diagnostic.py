import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import app

TESTS = [
    "delete database logs",
    "archive database logs",
]

app._ensure_model_loaded()

severity_bonus = {
    "CRITICAL": 0.05,
    "HIGH": 0.03,
    "MEDIUM": 0.01,
    "LOW": 0.00,
}

for action_text in TESTS:
    print("\n" + "=" * 80)
    print("INPUT:", repr(action_text))

    action_lower = action_text.lower()
    action_vector = np.array(list(app._model.embed([action_text])))
    similarities = cosine_similarity(
        action_vector, app._policy_vectors
    )[0]

    policy_scores = {}

    for i, similarity in enumerate(similarities):
        meta = app._pattern_meta[i]
        pid = meta["id"]

        exact_bonus = (
            0.10
            if meta["pattern"].lower() in action_lower
            else 0.0
        )

        score = (
            float(similarity)
            + exact_bonus
            + severity_bonus.get(meta["severity"], 0)
        )

        if pid not in policy_scores or score > policy_scores[pid]["score"]:
            policy_scores[pid] = {
                "score": score,
                "similarity": float(similarity),
                "policy": meta,
            }

    ranked = sorted(
        policy_scores.values(),
        key=lambda x: x["score"],
        reverse=True,
    )

    for rank, item in enumerate(ranked[:5], 1):
        p = item["policy"]
        print(
            f"{rank}. {p['id']} | "
            f"similarity={item['similarity']:.4f} | "
            f"score={item['score']:.4f} | "
            f"threshold={p['threshold']} | "
            f"severity={p['severity']} | "
            f"action={p['action']} | "
            f"pattern={p['pattern']}"
        )

    best = ranked[0]
    second_score = ranked[1]["score"] if len(ranked) > 1 else 0
    margin = best["score"] - second_score

    print("\nBEST POLICY:", best["policy"]["id"])
    print("BEST SIMILARITY:", round(best["similarity"], 4))
    print("BEST THRESHOLD:", best["policy"]["threshold"])
    print("SECOND SCORE:", round(second_score, 4))
    print("MARGIN:", round(margin, 4))
    print("MARGIN REQUIRED: 0.0500")
    print("MARGIN PASSES:", margin >= 0.05)
