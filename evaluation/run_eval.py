import json
import requests
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
)

API = "https://svp-semantic-vector-protocol-kernel-api.onrender.com/v1/audit"

with open("evaluation/adversarial_examples.json") as f:
    dataset = json.load(f)

y_true = []
y_pred = []

for sample in dataset:

    response = requests.post(
        API,
        json={"steps": [sample["input"]]},
    )

    result = response.json()["steps"][0]["decision"]

    y_true.append(sample["expected"])
    y_pred.append(result)

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

print(f"Examples : {len(dataset)}")
print(f"Accuracy : {accuracy:.3f}")
print(f"Precision: {precision:.3f}")
print(f"Recall   : {recall:.3f}")
print(f"FPR      : {fpr:.3f}")
print(f"FNR      : {fnr:.3f}")

print("\nConfusion Matrix")
print(confusion_matrix(
    y_true,
    y_pred,
    labels=["PASS", "BLOCK"],
))
