# Evaluation Methodology

## Measuring Semantic Runtime Governance Performance

---

# 1. Introduction

Evaluation is an essential component of security engineering.

Without repeatable measurement, it is difficult to determine whether changes to a system improve detection capability or simply alter behavior in unpredictable ways.

SVP Kernel therefore includes a structured evaluation process designed to measure the effectiveness of its semantic governance decisions against a labeled dataset of representative instructions.

The objective of this evaluation is not to demonstrate perfect security, but to establish a transparent, reproducible baseline that can guide future improvements.

---

# 2. Evaluation Objectives

The evaluation methodology is designed to answer several engineering questions:

- How accurately does the Policy Engine identify representative high-risk instructions?
- How often are legitimate instructions incorrectly blocked?
- How frequently do unsafe instructions evade existing governance policies?
- Which threat categories require additional policy coverage?
- How do changes to the Policy Engine affect overall performance over time?

By measuring these questions consistently, the project can evolve through evidence rather than intuition.

---

# 3. Scope of Evaluation

The current evaluation measures the behavior of the runtime governance layer only.

Specifically, it evaluates:

- semantic policy matching,
- similarity threshold evaluation,
- policy selection,
- runtime governance decisions,
- and decision consistency.

The evaluation does **not** measure:

- embedding model training,
- language model reasoning,
- tool execution,
- downstream agent behavior,
- operating system security,
- network security,
- or infrastructure reliability.

These concerns are intentionally outside the scope of the current benchmark.

---

# 4. Evaluation Dataset

The benchmark uses a manually curated adversarial evaluation dataset containing representative natural-language instructions.

The dataset contains both:

- benign operational requests expected to be allowed, and
- high-risk instructions expected to be blocked.

Representative categories include:

- prompt injection,
- privilege escalation,
- destructive database operations,
- filesystem abuse,
- cloud resource destruction,
- authorization bypass,
- dangerous tool use,
- and data exfiltration.

The objective is to provide broad coverage across representative runtime governance scenarios rather than exhaustive coverage of every possible attack.

---

# 5. Dataset Philosophy

The evaluation dataset is intended to represent realistic operational requests rather than artificially simplified examples.

Both benign and malicious instructions include natural-language variation to better approximate real-world interactions with AI systems.

Examples include:

- direct requests,
- paraphrased instructions,
- operational workflows,
- and representative adversarial phrasing.

This approach encourages evaluation of semantic understanding rather than exact keyword matching.
---

# 6. Evaluation Procedure

The evaluation process follows the same sequence for every benchmark run.

```
Evaluation Dataset
        │
        ▼
Instruction Selection
        │
        ▼
POST /v1/audit
        │
        ▼
Semantic Validation
        │
        ▼
Policy Evaluation
        │
        ▼
Governance Decision
        │
        ▼
Prediction Collection
        │
        ▼
Metric Calculation
```

Every instruction is submitted to the deployed runtime through the same API interface used during normal operation.

This ensures that benchmark results reflect the behavior of the complete runtime pipeline rather than isolated internal functions.

---

# 7. Ground Truth Labels

Each instruction within the evaluation dataset has an expected outcome assigned before evaluation.

The current benchmark uses two labels:

**ALLOW**

Represents instructions that should be permitted because they do not exceed the configured governance thresholds.

Examples include:

- reading approved documentation,
- verifying application status,
- retrieving operational information,
- reviewing audit logs,
- and other representative low-risk requests.

---

**BLOCK**

Represents instructions that should be prevented because they request representative high-risk operations.

Examples include:

- destructive database actions,
- privilege escalation,
- authorization bypass,
- prompt injection,
- filesystem destruction,
- cloud resource deletion,
- and representative data exfiltration attempts.

These labels provide the reference against which runtime decisions are compared.

---

# 8. Runtime Decision Evaluation

For every evaluated instruction, the runtime returns a governance decision.

The current implementation produces one of two outcomes:

**PASS**

The instruction does not exceed any configured policy threshold and is considered safe to continue.

**BLOCK**

The instruction exceeds one or more governance thresholds and is classified as high risk.

The predicted runtime decision is compared directly against the expected dataset label to determine whether the prediction is correct.

---

# 9. Confusion Matrix

Benchmark performance is summarized using a confusion matrix.

```
                    Expected

               ALLOW      BLOCK

Predicted

ALLOW            TN          FN

BLOCK            FP          TP
```

Where:

- **True Positive (TP)** — a malicious instruction is correctly blocked.
- **True Negative (TN)** — a benign instruction is correctly allowed.
- **False Positive (FP)** — a benign instruction is incorrectly blocked.
- **False Negative (FN)** — a malicious instruction is incorrectly allowed.

These four outcomes provide the foundation for every reported evaluation metric.

---

# 10. Metric Definitions

The benchmark reports several standard classification metrics.

**Accuracy**

The proportion of all predictions that are correct.

**Precision**

The proportion of blocked instructions that were actually malicious.

Higher precision indicates fewer unnecessary blocks.

**Recall**

The proportion of malicious instructions successfully identified.

Higher recall indicates broader threat detection.

**False Positive Rate**

The proportion of benign requests incorrectly classified as malicious.

Reducing false positives improves usability.

**False Negative Rate**

The proportion of malicious requests that were incorrectly allowed.

Reducing false negatives improves security coverage.

Together these metrics provide a balanced view of current runtime behavior rather than relying on a single score.

---

# 11. Current Benchmark Results

The following results were obtained using the current implementation of SVP Kernel against the evaluation dataset.

## Dataset Summary

Total Examples: 510
Network Errors: 2

Accuracy: 68.6%
Precision: 85.9%
Recall: 59.4%
False Positive Rate: 16.1%
False Negative Rate: 40.6%

Confusion Matrix
[[161  31]
 [129 189]]

The benchmark values reported in this document are generated by executing python evaluation/run_eval.py against the current evaluation dataset.

These results establish the current performance baseline for the runtime governance layer.

Future engineering changes should be evaluated against this benchmark to measure improvements or regressions.

---

# 12. Confusion Matrix

The current evaluation produced the following confusion matrix:

```
                Expected

             ALLOW   BLOCK

Predicted

ALLOW          161      129

BLOCK           31      189
```

This corresponds to:

- True Negatives (TN): **161**
- False Positives (FP): **31**
- False Negatives (FN): **129**
- True Positives (TP): **189**

The confusion matrix provides the raw classification outcomes from which all reported metrics are derived.

---

# 13. Interpretation of Results

The current implementation demonstrates several important characteristics.

### High Precision

A precision of **85.9%** indicates that most instructions classified as high risk genuinely correspond to representative malicious requests within the evaluation dataset.

This reduces unnecessary blocking and increases confidence in generated BLOCK decisions.

---

### Moderate Recall

The current recall of **59.4%** indicates that many representative malicious instructions are successfully detected, while others remain undetected.

Improving recall is expected to remain a primary area of future engineering work.

---

### Measurable Baseline

Rather than claiming comprehensive protection, the project publishes measured performance using a repeatable benchmark.

This baseline enables future improvements to be evaluated objectively rather than relying on anecdotal demonstrations.

---

# 14. Benchmark Philosophy

The purpose of this benchmark is not to maximize a single metric.

Instead, the evaluation seeks to balance:

- detection capability,
- operational usability,
- explainability,
- and repeatability.

Security systems often involve trade-offs.

Aggressively lowering similarity thresholds may improve recall while simultaneously increasing false positives.

Conversely, raising thresholds may reduce false positives while allowing more malicious instructions to pass.

Documenting these trade-offs is an important aspect of responsible security engineering.

---

# 15. Analysis of False Positives

The current evaluation produced **31 false positives**.

A false positive occurs when a benign instruction is incorrectly classified as high risk.

Representative examples include:

- rotating API keys,
- reviewing audit logs,
- retrieving approved documentation,
- verifying backup status,
- reading application logs,
- and summarizing operational information.

These requests share vocabulary with higher-risk operations despite representing legitimate administrative activities.

This behavior reflects a known characteristic of semantic similarity models.

Instructions with related terminology may occupy nearby regions in embedding space even when their operational intent differs.

Reducing false positives will require improvements beyond simple threshold adjustment, including richer policy representations and more context-aware evaluation.

---

# 16. Analysis of False Negatives

The current evaluation produced **129 false negatives**.

A false negative occurs when a representative malicious instruction is incorrectly classified as safe.

Examples include:

- deleting the production database,
- wiping storage buckets,
- overriding user permissions,
- bypassing authorization checks,
- privilege escalation,
- and representative prompt injection attempts.

These cases indicate that some adversarial phrasing currently falls below configured policy thresholds or is insufficiently represented by the existing policy set.

Improving recall while preserving precision remains one of the primary engineering objectives for future development.

---

# 17. Known Limitations

The current benchmark intentionally measures the existing implementation rather than an idealized system.

Several important limitations remain.

Current limitations include:

- semantic similarity alone cannot perfectly infer intent,
- representative policies cannot capture every possible adversarial phrasing,
- requests are evaluated independently rather than as complete workflows,
- multilingual evaluation has not yet been performed,
- policy thresholds currently require manual tuning,
- and benchmark coverage continues to evolve.

These limitations are expected for an early-stage runtime governance system and are documented to encourage transparent evaluation.

---

# 18. Engineering Observations

The current benchmark highlights several practical observations.

Semantic policy matching provides a useful first-pass governance mechanism for many representative high-risk instructions.

However, measured performance also demonstrates that semantic similarity alone is not sufficient for comprehensive runtime protection.

Future improvements are therefore expected to focus on expanding policy coverage, improving contextual reasoning, and refining evaluation methodology rather than relying exclusively on threshold adjustments.

The benchmark should therefore be viewed as a continuously evolving engineering tool rather than a one-time measurement.

---

# 19. Future Evaluation Roadmap

Evaluation is intended to remain a continuous engineering process throughout the evolution of SVP Kernel.

Future work will focus on expanding both the quality and breadth of benchmark coverage.

Planned areas of improvement include:

- larger adversarial evaluation datasets,
- additional benign operational workflows,
- multi-step agent workflow evaluation,
- multilingual instruction coverage,
- policy regression testing,
- automated benchmark execution through continuous integration,
- comparison across multiple embedding models,
- threshold sensitivity analysis,
- and longitudinal performance tracking across releases.

Every significant modification to the Policy Engine should be accompanied by a new benchmark run to measure its impact on both security coverage and operational usability.

---

# 20. Reproducibility

The evaluation methodology is designed to be repeatable.

Each benchmark is executed against the deployed runtime using the same API endpoints available to external users.

Using the production API for evaluation helps ensure that published metrics represent the behavior of the complete system rather than isolated internal components.

Future benchmark updates should continue using a consistent methodology so that performance changes can be compared across versions.

---

# 21. Continuous Evaluation Philosophy

Security evaluation is never complete.

As AI capabilities evolve, new attack techniques and operational patterns will continue to emerge.

For this reason, benchmark results should be interpreted as a snapshot of the current implementation rather than a permanent measure of security.

The objective is not to achieve perfect scores, but to improve measurable protection while maintaining transparency, explainability, and reproducibility.

Continuous evaluation provides a structured mechanism for identifying regressions, validating improvements, and guiding future engineering decisions.

---

# 22. Relationship to the Project

The evaluation process supports every major component of SVP Kernel.

```
Threat Model
      │
      ▼
Policy Definitions
      │
      ▼
Semantic Validation
      │
      ▼
Decision Engine
      │
      ▼
Evaluation
      │
      ▼
Benchmark Results
      │
      ▼
Engineering Improvements
```

This feedback loop enables the project to evolve through measured iteration rather than assumptions.

Each benchmark provides evidence that can be used to refine policies, adjust thresholds, expand datasets, and improve future releases.

---

# 23. Conclusion

Evaluation is a foundational component of SVP Kernel.

Rather than relying on demonstrations or qualitative claims, the project measures runtime governance performance using a repeatable benchmark built around representative benign and adversarial instructions.

Publishing both strengths and limitations provides a realistic view of the current implementation and establishes a transparent baseline for future development.

As the Policy Engine, evaluation dataset, and governance capabilities evolve, this methodology will continue to guide engineering decisions through measurable evidence rather than intuition.

---

## Related Documentation

- `README.md` — Project overview, features, benchmarks, deployment, and usage.
- `architecture.md` — Overall runtime architecture and component interactions.
- `policy_engine.md` — YAML-based governance policy design and configuration.
- `decision_engine.md` — Semantic matching, policy selection, and runtime decision logic.
- `threat_model.md` — Protected assets, supported threat categories, and security boundaries.





