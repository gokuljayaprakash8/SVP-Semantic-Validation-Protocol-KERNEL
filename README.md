# SVP Kernel

Semantic Validation Protocol Kernel

A semantic runtime decision engine for AI agents that evaluates high-risk actions before execution using embedding-based policy matching, configurable governance rules, and tamper-evident audit logging.

What is it?

SVP Kernel is a runtime governance layer for AI agents. Instead of relying on exact keyword matching, it evaluates user instructions semantically against configurable security policies before execution.The system produces consistent policy decisions based on configurable semantic policies and similarity thresholds and records tamper-evident audit logs, and provides an extensible policy engine that can be adapted to different enterprise environments.

Why I Built This?

As AI agents become capable of executing real-world actions, a growing challenge is determining whether an instruction should actually be executed. Existing demonstrations often focus on what an agent can do, while spending less attention on how decisions should be governed before execution.
I built SVP Kernel as an exploration of semantic policy validation: a lightweight runtime decision layer that evaluates the intent of an instruction against configurable governance policies before execution. The project also became a practical way for me to study AI infrastructure, runtime systems, API engineering, deployment, and software security through implementation rather than theory.

Modern AI agents can:

• Execute tools

• Access APIs

• Read documents

• Trigger workflows

• Make autonomous decisions

Without a governance layer, unsafe instructions such as prompt injection, privilege escalation, destructive actions, and data exfiltration may be executed unintentionally.

SVP Kernel explores whether semantic similarity combined with configurable policy rules can provide an interpretable first-pass runtime decision layer before execution.

SVP Kernel receives an instruction.

↓

The instruction is converted into semantic embeddings.

↓

Configured policy rules are embedded.

↓

Cosine similarity is calculated.

↓

Matching policies are evaluated.

↓

Risk scores are computed.

↓

A governance decision is returned.

↓

Every decision is recorded using tamper-evident audit logs.

## Architecture

SVP Kernel consists of six primary components:

1. API Layer
   - Receives requests through FastAPI endpoints.
   - Validates incoming inputs.

2. Semantic Engine
   - Converts user instructions into vector embeddings.
   - Compares them against embedded policy patterns using cosine similarity.

3. Policy Engine
   - Loads configurable YAML policies.
   - Evaluates similarity thresholds.
   - Assigns severity and recommended actions.

4. Decision Engine
   - Selects the highest-confidence policy match.
   - Produces the final governance decision.

5. Audit Logger
   - Records every decision.
   - Creates tamper-evident hash chains for audit verification.

6. API Response Layer
   - Returns the governance decision.
   - Includes matched policy, confidence score, severity, and audit metadata.
  
## Decision Pipeline

Every request follows the same processing sequence:

Request

↓

Embedding Generation

↓

Policy Embedding Comparison

↓

Similarity Scoring

↓

Threshold Evaluation

↓

Policy Selection

↓

Decision Generation

↓

Audit Log Creation

↓

API Response

## Current Features

- Semantic policy matching using sentence embeddings
- Configurable YAML policy engine
- Runtime governance decisions
- Prompt injection detection
- Privilege escalation detection
- Dangerous tool execution detection
- Authorization bypass detection
- Filesystem protection rules
- Database protection rules
- Network exfiltration detection
- Tamper-evident audit logging
- Audit chain verification endpoint
- REST API built with FastAPI
- Live deployment
- Public evaluation framework

## Engineering Highlights

- Built as a modular FastAPI application.
- Policies are externalized into YAML rather than hardcoded.
- Evaluation performed using a labeled adversarial dataset.
- Audit logs use chained SHA-256 hashes for tamper evidence.
- Public API and live demonstration available.

## Evaluation Methodology

SVP Kernel is evaluated using a manually curated adversarial evaluation dataset containing both benign and malicious instructions.

The evaluation includes scenarios such as:

- Prompt injection
- Privilege escalation
- Destructive database operations
- Filesystem attacks
- Cloud resource deletion
- Authorization bypass
- Data exfiltration
- Safe operational requests

Each example is labeled with its expected outcome (ALLOW or BLOCK).

The evaluation reports:

- Accuracy
- Precision
- Recall
- False Positive Rate
- False Negative Rate
- Confusion Matrix

This methodology provides a repeatable baseline for measuring changes to the policy engine over time.


## Current Benchmark

Current Evaluation Results

Examples: 510

Accuracy: 68.6%

Precision: 85.9%

Recall: 59.4%

False Positive Rate: 16.1%

False Negative Rate: 40.6%

The current implementation prioritizes precision over recall, reducing unnecessary blocking of legitimate requests while still identifying many high-risk instructions.

These benchmarks serve as a baseline and will continue improving as policy coverage and semantic matching evolve.


## Current Limitations

SVP Kernel is an ongoing engineering project and currently has several known limitations.

- Semantic similarity alone cannot perfectly distinguish every malicious instruction.

- Some adversarial paraphrases still evade existing policy coverage.

- Policy effectiveness depends on carefully tuned similarity thresholds.

- Current evaluation focuses on English-language instructions.

- The system currently evaluates individual requests rather than long multi-step agent workflows.

- Policy rules are manually authored and require continuous refinement.

These limitations are intentionally documented because measuring and understanding failure cases is an important part of building trustworthy security systems.

## Roadmap

Completed

- Semantic policy engine
- YAML policy configuration
- Runtime governance decisions
- FastAPI deployment
- Public API
- Tamper-evident audit logging
- Audit verification endpoint
- Adversarial evaluation framework

In Progress

- Policy coverage improvements
- Multi-step workflow reasoning
- Better semantic attack detection
- Evaluation expansion

Future

- Production-grade observability
- SDK support
- Enterprise policy management
- Design partner integrations
- Runtime governance for autonomous AI agents

## Repository Structure

app.py                # FastAPI application

myengine.py           # Semantic decision engine

audit_logger.py       # Tamper-evident audit logging

policies/             # YAML governance policies

evaluation/           # Evaluation framework

docs/                 # Technical documentation

benchmarks/           # Benchmark data

index.html            # Live demonstration

## API Endpoints

The current REST API exposes the following endpoints:

### Health Check

GET /health

Returns the current health status of the deployed service.

---

### Semantic Decision

POST /v1/audit

Evaluates an incoming instruction against configured semantic security policies and returns:

- Governance decision
- Matched policy
- Confidence score
- Severity
- Risk score

---

### Audit Chain Verification

GET /v1/audit/verify

Verifies the integrity of the tamper-evident audit log by validating the SHA-256 hash chain.

Returns:

{
  "valid": true
}

if the audit history has not been modified.


## Technologies Used

- Python
- FastAPI
- Sentence Transformers
- ONNX Runtime
- YAML
- NumPy
- Docker
- GitHub Actions
- Render
- GitHub Pages

## Running Locally

### Clone the repository

```bash
git clone https://github.com/gokuljayaprakash8/SVP-Semantic-Validation-Protocol-KERNEL.git
```

### Move into the project

```bash
cd SVP-Semantic-Validation-Protocol-KERNEL
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Start the FastAPI server

```bash
uvicorn app:app --reload
```

The API will be available at:

```
http://127.0.0.1:8000
```

Interactive API documentation:

```
http://127.0.0.1:8000/docs
```


## Live Demo

Live Application

https://gokuljayaprakash8.github.io/SVP-Semantic-Validation-Protocol-KERNEL/


GitHub Repository

https://github.com/gokuljayaprakash8/SVP-Semantic-Validation-Protocol-KERNEL

## License

This project is released under the MIT License.


## Contact

GitHub

https://github.com/gokuljayaprakash8

LinkedIn:

https://www.linkedin.com/in/gokul-jayaprakash-5a9677423?utm_source=share_via&utm_content=profile&utm_medium=member_android



Email

gokuljayaprakashnair@gmail.com
