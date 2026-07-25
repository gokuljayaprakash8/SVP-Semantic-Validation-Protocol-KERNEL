import json
import requests
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
)

API = "https://svp-semantic-vector-protocol-kernel-api.onrender.com/v1/audit"

# Load evaluation dataset
with open("evaluation/evaluation/adversarial_examples.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)

y_true = []
y_pred = []

network_errors = 0

false_positives = []
false_negatives = []

for sample in dataset:
    try:
        response = requests.post(
            API,
            json={"steps": [sample["input"]]},
            timeout=60,
        )

        response.raise_for_status()

        result = response.json()["steps"][0]["decision"]

    except (
        requests.exceptions.RequestException,
        KeyError,
        IndexError,
        ValueError,
    ):
        network_errors += 1

        if sample["expected"] == "BLOCK":
            result = "PASS"
        else:
            result = "BLOCK"

    y_true.append(sample["expected"])
    y_pred.append(result)

    if sample["expected"] == "PASS" and result == "BLOCK":
        false_positives.append(sample)

    if sample["expected"] == "BLOCK" and result == "PASS":
        false_negatives.append(sample)

accuracy = accuracy_score(y_true, y_pred)

precision = precision_score(
    y_true,
    y_pred,
    pos_label="BLOCK",
    zero_division=0,
)

recall = recall_score(
    y_true,
    y_pred,
    pos_label="BLOCK",
    zero_division=0,
)

tn, fp, fn, tp = confusion_matrix(
    y_true,
    y_pred,
    labels=["PASS", "BLOCK"],
).ravel()

fpr = fp / (fp + tn) if (fp + tn) else 0
fnr = fn / (fn + tp) if (fn + tp) else 0

print("\n========== SVP KERNEL EVALUATION ==========\n")

print(f"Examples       : {len(dataset)}")
print(f"Accuracy       : {accuracy:.3f}")
print(f"Precision      : {precision:.3f}")
print(f"Recall         : {recall:.3f}")
print(f"False Pos Rate : {fpr:.3f}")
print(f"False Neg Rate : {fnr:.3f}")
print(f"Network Errors : {network_errors}")

print("\nConfusion Matrix")
print(
    confusion_matrix(
        y_true,
        y_pred,
        labels=["PASS", "BLOCK"],
    )
)

print("\n========== FALSE POSITIVES ==========")
print(f"Count: {len(false_positives)}")

for sample in false_positives[:10]:
    print(f"{sample['id']} : {sample['input']}")

print("\n========== FALSE NEGATIVES ==========")
print(f"Count: {len(false_negatives)}")

for sample in false_negatives[:10]:
    print(f"{sample['id']} : {sample['input']}")
