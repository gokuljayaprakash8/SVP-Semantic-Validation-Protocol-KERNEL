# SVP Kernel

**Pre-execution Runtime Decision Engine for AI Agent Workflows**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-green.svg)]()
[![AI Safety](https://img.shields.io/badge/AI-Agentic%20Security-purple.svg)]()
[![Research](https://img.shields.io/badge/Research-Active-orange.svg)]()
[![License](https://img.shields.io/badge/License-Source%20Available-lightgrey.svg)]()

---

## Overview

SVP Kernel is a deterministic pre-execution runtime safety layer for AI agent workflows.

Instead of allowing autonomous agents to execute actions immediately, SVP Kernel evaluates every planned action against configurable semantic security policies before execution.

The kernel combines semantic similarity matching, configurable policy rules, and deterministic decision logic to classify workflow actions as **PASS** or **BLOCK** while producing transparent decision evidence.

Unlike traditional rule-based filters that depend on exact keyword matching, SVP Kernel uses sentence embeddings to detect semantically similar unsafe actions, making the system more resilient to paraphrasing while remaining deterministic in its final decision process.

---

## Motivation

As AI agents gain the ability to access databases, APIs, cloud infrastructure, developer tools, and enterprise systems, runtime governance becomes increasingly important.

A single unsafe tool call can result in:

- Database destruction
- Privilege escalation
- Credential exposure
- Sensitive data exfiltration
- Audit trail tampering

SVP Kernel provides an explicit decision layer between an AI planner and execution, enabling organizations to inspect, evaluate, and govern planned actions before they occur.

---

# Live Demo

### Interactive Demo

https://gokuljayaprakash8.github.io/SVP-Semantic-Vector-Protocol-KERNEL/

### Live API

```text
POST https://svp-semantic-vector-protocol-kernel-api.onrender.com/v1/audit

---

Core Features

- Deterministic pre-execution decision engine
- Semantic policy matching using sentence embeddings
- YAML-based Policy DSL
- Runtime policy validation
- Configurable similarity thresholds
- Severity-aware decisions
- External policy loading
- Multi-policy evaluation
- FastAPI REST interface
- JSON audit evidence
- First-pass adversarial evaluation suite
- Modular architecture designed for future expansion

---

System Architecture

                AI Agent

                    │

                    ▼

          Planned Workflow Actions

                    │

                    ▼

             SVP Kernel Runtime

                    │

        ┌───────────┴───────────┐

        ▼                       ▼

Policy DSL Loader        Policy Validator

        │

        ▼

Sentence Embedding Engine

        │

        ▼

Semantic Similarity Engine

        │

        ▼

Deterministic Decision Engine

        │

        ▼

 PASS / BLOCK Decision

        │

        ▼

 Structured JSON Evidence

---

Repository Structure

SVP-Semantic-Vector-Protocol-KERNEL/

├── app.py
├── validator.py
├── policies/
│   └── default.yaml
│
├── evaluation/
│   ├── adversarial_examples.json
│   ├── run_eval.py
│   └── EVALUATION.md
│
├── docs/
│   └── architecture.md
│
├── index.html
├── README.md
├── LICENSE
└── requirements.txt

---

Installation

git clone https://github.com/gokuljayaprakash8/SVP-Semantic-Vector-Protocol-KERNEL.git

cd SVP-Semantic-Vector-Protocol-KERNEL

pip install -r requirements.txt

uvicorn app:app --reload

The API will be available at:

http://127.0.0.1:8000

Interactive documentation:

http://127.0.0.1:8000/docs

---

Policy DSL

SVP Kernel uses a YAML-based Policy DSL instead of hardcoded rules.

Example:

version: 1

policies:

- id: DB001
  description: Database deletion

  patterns:
    - delete database
    - drop table
    - remove database

  threshold: 0.62
  severity: CRITICAL
  action: BLOCK

Each policy defines:

- Rule ID
- Human-readable description
- Multiple semantic patterns
- Similarity threshold
- Severity level
- Runtime action
---

# REST API

## Endpoint

```http
POST /v1/audit
```

## Request

```json
{
  "steps": [
    "delete the production database",
    "send invoice to customer"
  ]
}
```

## Example Response

```json
{
  "overall": "BLOCKED",
  "blocked_count": 1,
  "steps": [
    {
      "action": "delete the production database",
      "decision": "BLOCK",
      "rule_id": "DB001",
      "matched_policy": "Database deletion",
      "severity": "CRITICAL",
      "score": 0.82,
      "threshold": 0.62
    },
    {
      "action": "send invoice to customer",
      "decision": "PASS",
      "rule_id": "DATA001",
      "matched_policy": "Data exfiltration",
      "severity": "LOW",
      "score": 0.18,
      "threshold": 0.60
    }
  ]
}
```

---

# Decision Flow

For every workflow step:

1. Receive the planned action.
2. Generate a sentence embedding.
3. Compare against every configured policy pattern.
4. Select the highest semantic similarity score.
5. Compare the score against the policy threshold.
6. Produce a deterministic PASS or BLOCK decision.
7. Return structured decision evidence.

The current implementation always returns the same decision for the same input, model, and policy configuration.

---

# First-Pass Adversarial Evaluation

SVP Kernel includes a manually curated adversarial evaluation suite designed to measure how well semantic policy matching detects unsafe requests beyond exact keyword matching.

Current evaluation includes **100 examples** covering:

- Database destruction
- Authentication bypass
- Privilege escalation
- Data exfiltration
- Audit trail tampering
- Safe administrative operations
- Benign business workflows
- Semantic paraphrases
- Obfuscated unsafe intent
- Near-miss examples

The evaluation methodology is documented in:

```text
evaluation/EVALUATION.md
```

The dataset is available in:

```text
evaluation/adversarial_examples.json
```

This evaluation is intended as a first-pass engineering benchmark rather than a comprehensive security certification.

---

# Engineering Decisions

SVP Kernel intentionally favors deterministic behavior over model-generated decisions.

Current design choices include:

- FastAPI for a lightweight REST interface.
- Sentence embeddings for semantic similarity.
- Cosine similarity for efficient policy matching.
- YAML Policy DSL for externalized configuration.
- Runtime policy validation before loading.
- Rule-specific similarity thresholds.
- Transparent JSON decision evidence.
- Simple architecture to enable future extensions.

The project emphasizes explainability and reproducibility over autonomous reasoning.

---

# Current Limitations

SVP Kernel is an actively evolving prototype.

Current limitations include:

- Workflow decisions are evaluated step-by-step rather than using deep cross-step semantic reasoning.
- Policy matching relies on embedding similarity and manually configured thresholds.
- Policies are loaded at startup rather than reloaded dynamically.
- Authentication and authorization are not yet implemented.
- No persistent audit storage.
- No policy version management.
- Evaluation dataset is manually curated and intended for engineering validation rather than production benchmarking.

These limitations are intentional trade-offs to keep the implementation understandable and extensible during early development.

---

# Roadmap

Planned areas of future work include:

- Runtime policy reloading
- Policy versioning
- Nested Policy DSL
- Rich policy conditions
- Cross-workflow state analysis
- Continuous adversarial benchmarking
- Evaluation dashboards
- Request history and persistent audit logs
- Authentication and API keys
- SDKs for Python and JavaScript
- LangGraph integration
- CrewAI integration
- Multi-agent workflow governance
- Policy explanation engine
- Enterprise deployment tooling

---

# Documentation

Additional documentation is available in:

```text
docs/architecture.md
evaluation/EVALUATION.md
```

---

# Contributing

Feedback, issues, discussions, and pull requests are welcome.

If you discover bugs, have ideas for improving policy evaluation, or would like to contribute adversarial test cases, please open an issue describing the proposed change.

Constructive feedback is appreciated as the project continues to evolve.

---

# Development Notes

SVP Kernel was initially designed and developed using browser-based tools from an Android device as an experiment in mobile-first software development.

The project demonstrates that meaningful infrastructure prototypes can be designed, implemented, documented, and published without relying on a traditional desktop development environment.

---

# License

Source Available.

The repository is intended for research, learning, evaluation, and portfolio purposes.

Commercial use requires explicit permission from the author.

See the `LICENSE` file for complete licensing terms.

---

# Disclaimer

SVP Kernel is an experimental research project exploring deterministic runtime governance for AI agent workflows.

It is not intended to replace comprehensive enterprise security controls and should not be treated as a production-ready security product without additional validation, testing, and operational safeguards.

