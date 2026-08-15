# SVP Kernel v0.6.3 — Reproducibility Snapshot

This directory contains the source files and security evidence associated with the SVP Kernel v0.6.3 experimental runtime-authorization study.

## Included

- app.py — experimental HTTP execution-gate integration
- svp_v06_runtime_gate.py — request/decision binding and replay-resistant runtime gate
- svp_v063_final_adversarial_audit.py — final adversarial audit
- svp_v06_integration_regression.py — integration regression checks
- svp_v06_decisive_benchmark.py — benchmark/evaluation script
- svp_v06_integration_bridge.py — integration bridge
- SVP_V06_SECURITY_EVIDENCE.md — security evidence and experimental findings
- SVP_V06_2_RESTART_REPLAY_FINDING.md — restart/replay persistence finding

## Reproduction

Run from the project environment:

    python -m py_compile app.py svp_v06_runtime_gate.py
    python svp_v06_integration_regression.py
    python svp_v063_final_adversarial_audit.py

The experiments use synthetic actions and do not execute real external actions.

## Scope and limitations

This is an experimental prototype and measured security study.

It does not establish production security, distributed deployment security, production key management, authorization revocation, or resistance to compromise of the prototype signing secret.

The SQLite replay stores used during experiments are not included in this public source snapshot.

## Publication

Zenodo DOI: https://doi.org/10.5281/zenodo.21954019

The Zenodo record is the archival publication record for the associated paper and experimental materials.
