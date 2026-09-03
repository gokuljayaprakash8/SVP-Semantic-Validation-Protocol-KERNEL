# SVP Kernel v0.6.3 — Reproducibility Artifact

This archive accompanies the preprint:

From Semantic Decisions to Single-Use Execution Authorization: A Vulnerability-Driven Runtime Security Study of the SVP Kernel

Zenodo DOI: https://doi.org/10.5281/zenodo.21954019

## Contents

- app.py — HTTP execution-gate integration used in the experiment.
- svp_v06_runtime_gate.py — cryptographic decision-binding and replay-consumption logic.
- svp_v063_final_adversarial_audit.py — final adversarial audit.
- svp_v06_integration_regression.py — v0.6 integration regression tests.
- svp_v06_decisive_benchmark.py — decisive benchmark experiment.
- SVP_V06_SECURITY_EVIDENCE.md — consolidated security evidence and limitations.
- SVP_V06_2_RESTART_REPLAY_FINDING.md — restart/persistence replay finding.
- SHA256SUMS.txt — SHA-256 hashes for the artifact files.

## Reproduction

Run from the project environment:

    python -m py_compile app.py svp_v06_runtime_gate.py
    python svp_v06_integration_regression.py
    python svp_v063_final_adversarial_audit.py

The experiments use synthetic actions and do not execute real external actions.

## Scope and limitations

This artifact documents an experimental prototype and its measured behavior.

It does not establish production security, distributed deployment security, production key management, authorization revocation, or resistance to compromise of the prototype signing secret.

The SQLite replay store used during experiments is intentionally not included in this public archive.

## Reproducibility

Results reported in the paper should be interpreted together with the source files, experimental output, and limitations described in the manuscript.
