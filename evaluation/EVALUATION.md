# SVP Kernel Evaluation

## Objective

Evaluate SVP Kernel against a manually curated adversarial evaluation corpus representing modern AI agent security scenarios.

---

## Dataset

**500 manually labeled workflow actions**

Coverage includes:

- Destructive operations
- Privilege escalation
- Authentication bypass
- Data exfiltration
- Audit log tampering
- Multi-agent workflow abuse
- RAG poisoning
- Prompt injection (direct & indirect)
- Browser agent attacks
- Long-horizon workflow manipulation
- MCP (Model Context Protocol) security
- Cloud infrastructure misuse
- Kubernetes privilege abuse
- CI/CD agent attacks
- Secret management violations
- Benign enterprise workflows

---

## Evaluation Methodology

Each example is executed against the live SVP Kernel API.

For every workflow action:

1. Send the request to the runtime engine.
2. Compare the returned decision against the expected label.
3. Compute overall evaluation metrics.

The evaluation script reports:

- Accuracy
- Precision
- Recall
- False Positive Rate (FPR)
- False Negative Rate (FNR)
- Confusion Matrix
- Network Errors (if any)

---

## Current Status

Evaluation corpus:

**500 labeled adversarial examples**

Metrics:

- Accuracy: Pending
- Precision: Pending
- Recall: Pending
- FPR: Pending
- FNR: Pending

These values will be populated automatically after executing `run_eval.py`.

---

## Future Work

Future evaluation will include:

- Larger adversarial datasets
- Semantic paraphrase attacks
- Multi-step workflow attacks
- Cross-agent reasoning attacks
- Continuous GitHub Actions benchmarking
- Policy regression testing
- Version-to-version benchmark comparison
