# SVP Kernel

## Semantic Validation Protocol Kernel

### A Runtime Decision Kernel for Safer AI Agents

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![AI Security](https://img.shields.io/badge/AI-Security-red)
![Semantic Validation](https://img.shields.io/badge/Semantic-Validation-purple)
![Policy Engine](https://img.shields.io/badge/Policy-YAML-orange)
![Docker](https://img.shields.io/badge/Docker-Container-blue)
![GitHub Actions](https://img.shields.io/badge/CI-GitHub_Actions-black)
![License](https://img.shields.io/badge/License-Proprietary-red)


SVP Kernel is a runtime decision layer that evaluates AI agent actions before execution using semantic validation, configurable policy enforcement, deterministic decision logic, and tamper-evident audit logging.

The goal is to explore how AI agents can be given stronger runtime governance through a combination of semantic understanding and explicit safety controls.



---

## 🚀 Live Demo

Interact with the deployed SVP Kernel runtime:

**Frontend Demo**

https://gokuljayaprakash8.github.io/SVP-Semantic-Validation-Protocol-KERNEL/


**API Documentation**

https://svp-semantic-vector-protocol-kernel-api.onrender.com/docs


**Health Check**

https://svp-semantic-vector-protocol-kernel-api.onrender.com/health


**Source Code**

https://github.com/gokuljayaprakash8/SVP-Semantic-Validation-Protocol-KERNEL



---

# Overview

Modern AI agents are moving beyond simple text generation.

They can:

- Execute tools
- Access external APIs
- Read and process documents
- Trigger automated workflows
- Interact with software systems
- Perform multi-step operations


As agent capabilities increase, a critical engineering question emerges:

> Before an AI agent performs an action, how can we evaluate whether that action should be allowed?

SVP Kernel explores a runtime governance approach where agent actions are evaluated before execution through:

- Semantic policy matching
- Configurable YAML-based rules
- Deterministic decision logic
- Transparent risk scoring
- Tamper-evident audit records


Instead of relying only on keyword matching, SVP Kernel evaluates the meaning of an instruction against defined security policies.



---

# Why SVP Kernel?

Large language models are highly capable at understanding context, but their flexibility creates challenges when used for autonomous actions.

A runtime system requires additional properties:

- Predictable decisions
- Explainable outcomes
- Configurable policies
- Auditable execution history


SVP Kernel separates two responsibilities:



The semantic layer helps identify contextual similarity between actions and known policies.

The policy and decision layers provide explicit rules for generating consistent outcomes.


Every evaluated action produces a structured response containing:

- Decision outcome
- Matched policy
- Risk score
- Severity level
- Threshold information


When enabled, decisions are recorded through a tamper-evident audit chain for later verification.

---

# How SVP Kernel Works

SVP Kernel evaluates an AI agent action through a multi-stage runtime validation pipeline.

The current implementation follows this flow:

Agent Action
↓
Semantic Validation
↓
Policy Evaluation
↓
Decision Engine
↓
Kernel Decision
↓
Audit Logging



The objective is to create a transparent decision path where every outcome can be inspected and evaluated.



---

# Architecture

SVP Kernel is built as a modular runtime decision system consisting of five primary components.



## 1. API Layer

The API layer provides the interface between external applications and the runtime engine.

Responsibilities:

- Receives agent actions through FastAPI endpoints.
- Validates incoming requests.
- Returns structured decision responses.



Technology:

- FastAPI
- REST API



---


## 2. Semantic Validation Layer

The semantic validation layer evaluates the meaning of incoming actions rather than relying only on exact keyword matching.

Responsibilities:

- Converts actions into semantic embeddings.
- Compares incoming instructions against policy representations.
- Calculates similarity scores using vector comparison.


Current approach:

- Sentence embedding models
- Cosine similarity evaluation



Purpose:

Allow the system to recognize related meanings even when wording changes.



---


## 3. Policy Engine

The policy engine provides configurable governance rules.

Policies are defined externally using YAML configuration files.


Each policy can contain:

- Policy identifier
- Description
- Severity
- Similarity threshold
- Expected action
- Risk classification


Example policy structure:

```yaml
id: DB001

description: 
  Delete production database

severity:
  critical

threshold:
  0.65

action:
  block

External policy configuration allows rules to evolve without modifying core runtime logic.

4. Decision Engine
The decision engine combines semantic results with policy requirements to produce the final runtime decision.
Responsibilities:
Evaluates matched policies.
Applies configured thresholds.
Determines the highest-confidence policy match.
Produces deterministic PASS or BLOCK decisions.
Decision output includes:
Decision status
Rule identifier
Matched policy
Risk score
Severity
Threshold value
5. Audit Layer
The audit layer records runtime decisions using tamper-evident logging.
Responsibilities:
Creates structured audit events.
Stores decision history.
Generates SHA-256 chained hashes.
Verifies audit integrity.
Verification example:

{
  "valid": true
}

This provides a mechanism to detect unauthorized modification of recorded decisions.

Decision Pipeline
Every request follows the same deterministic execution sequence:

Incoming Request

        ↓

Input Validation

        ↓

Embedding Generation

        ↓

Semantic Similarity Calculation

        ↓

Policy Threshold Evaluation

        ↓

Policy Selection

        ↓

Decision Generation

        ↓

Audit Event Creation

        ↓

API Response

The separation between semantic interpretation and deterministic enforcement is the core design principle of SVP Kernel.

Design Principle
AI systems are effective at interpreting complex instructions, but safety-critical runtime decisions require predictability and transparency.
SVP Kernel explores the combination of:

Semantic Understanding

+
Explicit Policy Controls

+
Deterministic Runtime Decisions

+
Auditable History

to create a foundation for safer AI agent execution.


---

## Part 2 alignment:

✅ Matches new index.html architecture section  
✅ Five components instead of old six  
✅ Uses "runtime decision kernel" terminology  
✅ Explains actual implementation  
✅ Does not claim enterprise production readiness  

---

# Current Capabilities

SVP Kernel currently implements the following runtime governance capabilities:


## Semantic Policy Evaluation

- Evaluates agent actions using semantic embeddings.
- Compares incoming instructions against configured policy patterns.
- Uses similarity scoring rather than only exact keyword matching.



## Configurable Policy Engine

- Policies are externalized using YAML configuration.
- Rules can define:
  - Severity levels
  - Similarity thresholds
  - Risk categories
  - Expected decision actions



## Deterministic Runtime Decisions

The kernel produces structured decisions based on evaluated policies.

Each response includes:

- Decision outcome
- Matched rule
- Matched policy
- Risk score
- Severity
- Threshold value



## AI Security Policy Coverage

Current policy coverage includes scenarios such as:

- Prompt injection attempts
- Privilege escalation requests
- Authorization bypass attempts
- Destructive database operations
- Filesystem abuse
- Unsafe tool execution
- Data access risks
- Cloud resource deletion scenarios



## Tamper-Evident Audit Logging

SVP Kernel includes an audit logging mechanism that:

- Records decision events.
- Creates SHA-256 chained hashes.
- Maintains decision history integrity.
- Supports verification through an API endpoint.



## Evaluation Framework

The project includes an adversarial evaluation framework to measure:

- Accuracy
- Precision
- Recall
- False Positive Rate
- False Negative Rate
- Confusion Matrix performance



---

# Engineering Highlights

The project focuses on engineering principles required for AI infrastructure and security systems.



## Modular Architecture

SVP Kernel separates:

- API handling
- Semantic evaluation
- Policy management
- Decision generation
- Audit recording


This allows individual components to evolve independently.



---


## Externalized Governance Policies

Security rules are not hardcoded into application logic.

Instead, policies are defined separately through YAML configuration files.

Benefits:

- Easier policy updates.
- Better maintainability.
- Clear separation between code and governance rules.



---


## Deterministic Decision Layer

The system does not depend on an LLM making the final safety decision.

Instead:

Semantic Similarity
+
Policy Rules
+
Threshold Evaluation
↓
Deterministic Decision




This design improves transparency and reproducibility.



---


## Security-Focused Evaluation

The project includes adversarial testing rather than only functional demonstrations.

Evaluation focuses on understanding:

- What is detected.
- What is missed.
- Where semantic ambiguity occurs.
- How policies can improve over time.



---


# Technology Stack

## Core Runtime

| Technology | Purpose |
|---|---|
| Python | Core implementation |
| FastAPI | Runtime API framework |
| Sentence Transformers | Semantic embedding generation |
| ONNX Runtime | Model execution support |
| NumPy | Vector operations |
| YAML | Policy configuration |
| Docker | Containerization |
| GitHub Actions | CI workflows |
| Render | API deployment |
| GitHub Pages | Frontend deployment |



---

# Repository Structure

Current repository organization:

SVP-Semantic-Validation-Protocol-KERNEL/
│ ├── app.py │   FastAPI application entry point │ ├── myengine.py │   Semantic decision engine │ ├── audit_logger.py │   Tamper-evident audit logging system │ ├── policies/ │   YAML policy definitions │ ├── evaluation/ │   Benchmark and evaluation framework │ ├── benchmarks/ │   Evaluation datasets and metrics │ ├── docs/ │   Technical documentation │ ├── index.html │   Interactive frontend demonstration │ ├── requirements.txt │   Python dependencies │ └── Dockerfile Container deployment configuration

The above repository structure reflects the separation between runtime logic, policies, evaluation, and documentation.

---

# Evaluation Methodology

SVP Kernel is evaluated using an adversarial evaluation dataset designed to measure semantic policy enforcement behavior.

The objective is not only to measure successful detections, but also to understand:

- What the system detects.
- What it misses.
- Where semantic ambiguity affects decisions.
- How policy improvements change performance over time.



---

# Evaluation Dataset

Current evaluation size:
510 adversarial examples



The dataset contains both risky and benign scenarios.



Evaluation categories include:


## Destructive Operations

Examples:

- Delete production database.
- Remove cloud storage resources.
- Destroy critical infrastructure.



## Authorization Attacks

Examples:

- Privilege escalation attempts.
- Permission bypass requests.
- Unauthorized administrative actions.



## Prompt Injection Scenarios

Examples:

- Attempts to override system instructions.
- Requests to ignore safety restrictions.
- Attempts to manipulate agent behavior.



## Unsafe Tool Usage

Examples:

- Dangerous external tool execution.
- Unauthorized system operations.
- High-risk automation requests.



## Benign Operational Requests

Examples:

- Reading approved documents.
- Reviewing logs.
- Performing safe administrative tasks.



---

# Evaluation Metrics

SVP Kernel measures:


| Metric | Purpose |
|---|---|
| Accuracy | Overall classification correctness |
| Precision | Percentage of detected risks that were actually risky |
| Recall | Percentage of risky actions successfully detected |
| False Positive Rate | Rate of safe actions incorrectly flagged |
| False Negative Rate | Rate of risky actions missed |



---

# Current Benchmark Results

Current evaluation:
Examples: 510



| Metric | Result |
|---|---:|
| Accuracy | 68.6% |
| Precision | 85.9% |
| Recall | 59.4% |
| False Positive Rate | 16.1% |
| False Negative Rate | 40.6% |



---

# Confusion Matrix

Current confusion matrix:
Predicted

          Safe      Risk
Actual Safe    161        31
Actual Risk    129       189




Interpretation:


- True Negatives: 161
- False Positives: 31
- False Negatives: 129
- True Positives: 189



---

# Benchmark Interpretation

The current implementation demonstrates strong precision:
85.9%



This means when SVP Kernel identifies a risky action, it is frequently correct.



The primary improvement area is recall:
59.4%



Some semantically complex or adversarially modified instructions can still bypass current policy coverage.



This behavior highlights a known challenge in embedding-based security systems:

Similar language does not always represent identical intent.


For example:
"Review application logs"
and
"Erase application logs"


may contain related concepts while representing completely different security outcomes.



---

# Current Failure Analysis

The current evaluation reveals two primary improvement areas:


## Semantic Ambiguity

Embedding-based similarity can sometimes associate actions with similar vocabulary despite different intent.


Example:

Safe:

Review audit logs

Risky:

Delete audit logs


Both contain related concepts but require opposite decisions.



---


## Policy Coverage Expansion

Some adversarial variations require additional policies or stronger contextual reasoning.


Future improvements include:

- Better action understanding.
- Multi-step workflow evaluation.
- Expanded adversarial datasets.
- Improved policy reasoning.



---

# Evaluation Philosophy

The goal of evaluation is not to present perfect security detection.

The goal is to build measurable understanding of system behavior and improve the runtime decision layer through evidence-driven iteration.

---

# Current Limitations

SVP Kernel is an active engineering research project exploring runtime governance for AI agents.

The current implementation has several known limitations.



## Semantic Understanding Limitations

The system relies on embedding-based semantic similarity.

While this allows contextual matching beyond keywords, embeddings alone cannot perfectly understand every possible intent difference.


Examples:
"Review production logs"
vs
"Delete production logs"

may share similar language patterns while representing completely different actions.



---


## Recall Improvement

The current benchmark shows that recall remains the main improvement area.

Some adversarial variations can bypass existing policy coverage.

Future improvements require:

- Expanded policy datasets.
- Better contextual reasoning.
- More complex workflow analysis.
- Improved action decomposition.



---


## Single-Request Evaluation

The current runtime primarily evaluates individual actions.

Complex autonomous agents often execute multi-step workflows where risk may emerge from the sequence of actions rather than one isolated instruction.

Future versions can explore:

- Workflow-level analysis.
- State tracking.
- Sequential risk evaluation.



---


## Policy Management

Current policies are manually authored YAML configurations.

Future improvements may include:

- Policy generation assistance.
- Policy version management.
- Automated policy testing.
- Larger governance libraries.



---


## Production Infrastructure

The current deployment demonstrates runtime functionality but does not yet represent a complete enterprise production system.

Additional engineering would be required for:

- Distributed scaling.
- Durable storage.
- Advanced observability.
- Authentication and authorization layers.
- Enterprise integrations.



---

# Roadmap

The roadmap focuses on improving runtime governance capabilities while maintaining transparency and measurable evaluation.



## Completed

✅ Semantic validation engine

✅ YAML-based policy configuration

✅ Deterministic decision engine

✅ FastAPI runtime deployment

✅ Interactive frontend demonstration

✅ Tamper-evident audit logging

✅ Audit verification endpoint

✅ Adversarial evaluation framework



---


## In Progress

🚧 Policy coverage improvement

🚧 Recall improvement research

🚧 Expanded adversarial testing

🚧 Better semantic attack detection

🚧 Documentation refinement



---


## Future

Future engineering directions include:


### Agent Framework Integration

Explore integrations with AI agent frameworks and orchestration systems.



### Advanced Workflow Analysis

Move beyond single actions toward multi-step agent workflow evaluation.



### Policy Management Layer

Develop stronger policy lifecycle management capabilities.



### Runtime Observability

Improve monitoring, analytics, and operational visibility.



### Distributed Deployment

Explore scalable runtime deployment patterns for larger systems.



---

# Project Philosophy

SVP Kernel is built around a simple principle:
AI agents need capability.
AI systems also need control.
Runtime decisions require both understanding and enforcement.


The project focuses on building measurable, transparent, and explainable foundations for safer AI agent execution.


---

# API Reference

SVP Kernel exposes a REST API for evaluating AI agent actions and verifying audit history.

Base URL:https://svp-semantic-vector-protocol-kernel-api.onrender.com



---

# Health Check

## GET `/health`

Checks whether the runtime service is available.


Example response:

```json
{
  "status": "ok"
}

Runtime Decision Evaluation
POST /v1/audit
Evaluates an AI agent action against configured semantic policies.
Request
Example:
{
  "steps": [
    "delete the production database"
  ]
}
Response
Example:
{
  "overall": "BLOCKED",
  "blocked_count": 1,
  "steps": [
    {
      "action": "delete the production database",
      "decision": "BLOCK",
      "rule_id": "DB001",
      "matched_policy": "Production database deletion",
      "severity": "CRITICAL",
      "score": 0.91,
      "threshold": 0.65
    }
  ]
}
The response provides:
Overall decision
Blocked action count
Matched policy
Rule identifier
Risk score
Severity level
Threshold comparison

Audit Verification
GET /v1/audit/verify
Verifies the integrity of the tamper-evident audit chain.
Example response:
{
  "valid": true
}
A true response indicates that recorded audit events have passed hash-chain verification.

Running Locally
Clone Repository
git clone https://github.com/gokuljayaprakash8/SVP-Semantic-Validation-Protocol-KERNEL.git

Navigate to Project
cd SVP-Semantic-Validation-Protocol-KERNEL

Install Dependencies
pip install -r requirements.txt

Start API Server
uvicorn app:app --reload

The API will run locally:
http://127.0.0.1:8000

Interactive API documentation:
http://127.0.0.1:8000/docs

Deployment
Current deployment architecture:

GitHub Repository

        ↓

GitHub Actions

        ↓

Render Deployment

        ↓

FastAPI Runtime API

        ↓

GitHub Pages Frontend

Current hosted components:
Backend
FastAPI runtime deployed through Render.
Frontend
Interactive demonstration hosted through GitHub Pages.
The frontend communicates directly with the deployed API to evaluate agent actions in real time.

Example Workflow
User enters an AI agent action:
Delete the production database

Frontend sends request:
POST /v1/audit

Backend processes:
Input Validation

        ↓

Embedding Generation

        ↓

Semantic Matching

        ↓

Policy Evaluation

        ↓

Decision Generation

        ↓

Audit Logging

Backend processes:

Input Validation

        ↓

Embedding Generation

        ↓

Semantic Matching

        ↓

Policy Evaluation

        ↓

Decision Generation

        ↓

Audit Logging

Frontend displays:

PASS / BLOCK Decision

+

Policy Information

+

Risk Metadata

---

# License

Copyright (c) 2026 Gokul Jayaprakash

All Rights Reserved.

SVP Kernel and all associated materials, including but not limited to source code, architecture, frontend implementation, API design, documentation, evaluation framework, policy definitions, and related intellectual property are the exclusive property of Gokul Jayaprakash.

Permission is granted to view and inspect this repository solely for:

- Personal learning
- Educational review
- Research discussion
- Portfolio evaluation purposes


Without prior written permission from the owner, you may not:

- Copy, reproduce, or redistribute this software or any part of it.
- Modify, create derivative works, or publish altered versions.
- Use this project or any component of it for commercial purposes.
- Integrate this software into internal business systems.
- Deploy this software in production environments.
- Use the architecture, design, implementation, or concepts as the basis for competing products or services.


Any commercial usage, enterprise deployment, licensing arrangement, partnership, or technology evaluation beyond portfolio review requires explicit written authorization from the owner.


For licensing inquiries, enterprise usage, or partnership discussions:

Email:

gokuljayaprakashnair@gmail.com



---

# Contact


## GitHub

https://github.com/gokuljayaprakash8


## LinkedIn

https://www.linkedin.com/in/gokul-jayaprakash-5a9677423/



## Email

gokuljayaprakashnair@gmail.com



---

# Final Note

SVP Kernel is an ongoing exploration into runtime governance for AI agents.

The project focuses on a practical engineering question:

> As AI systems become more autonomous, how can we build transparent mechanisms that evaluate actions before execution?


Through semantic validation, policy-driven decisions, deterministic enforcement, and auditable execution history, SVP Kernel explores one possible foundation for safer AI agent infrastructure.


---

Built and engineered by Gokul Jayaprakash



