# SVP Kernel

**Pre-execution runtime risk scoring for AI agent workflows.**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Open Source](https://img.shields.io/badge/Open%20Source-Yes-brightgreen.svg)]()
[![Security](https://img.shields.io/badge/Security-Responsible%20Disclosure-orange.svg)](SECURITY.md)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-success.svg)](CONTRIBUTING.md)
[![Research](https://img.shields.io/badge/Research-AI%20Safety-purple.svg)]()

SVP Kernel evaluates a planned sequence of AI agent actions before execution. It scores each action against predefined risk policies and tracks workflow state across multiple steps, helping identify situations where individually safe actions become risky when combined.

The project was designed, built, tested, and deployed entirely from an Android phone using browser-based development tools, without a laptop.

---

# Live Demo

- **Interactive Demo:** https://gokuljayaprakash8.github.io/SVP-Semantic-Vector-Protocol-KERNEL/
- **Live API:** `POST https://svp-semantic-vector-protocol-kernel-api.onrender.com/v1/audit`

---

# Why SVP Kernel?

Many validation systems evaluate AI-agent actions independently.

SVP Kernel also considers workflow context by tracking sensitive data touched in earlier steps. This allows it to identify workflows that become risky only when multiple individually acceptable actions are combined.

---

# Architecture

```text
Workflow Request
        │
        ▼
FastAPI API (/v1/audit)
        │
        ▼
Sentence Embeddings
        │
        ▼
Cosine Similarity Policy Matching
        │
        ▼
Workflow State Tracking
        │
        ▼
Decision Engine
        │
        ▼
JSON Response
```

---

# Features

- Pre-execution runtime risk scoring
- REST API built with FastAPI
- Sentence embeddings for semantic similarity matching
- Cosine similarity scoring
- Multi-step workflow state tracking
- Interactive browser-based testing interface
- Designed, built, tested, and deployed entirely from an Android phone

---

# API

### Endpoint

```text
POST /v1/audit
```

### Example Request

```json
{
  "steps": [
    "delete all user records from database",
    "send invoice to client email"
  ]
}
```

### Example Response

```json
{
  "overall": "BLOCKED",
  "blocked_count": 2,
  "steps": [
    {
      "action": "delete all user records from database",
      "decision": "BLOCK",
      "severity": "CRITICAL",
      "score": 0.79
    },
    {
      "action": "send invoice to client email",
      "decision": "BLOCK",
      "severity": "HIGH",
      "score": 0.68
    }
  ]
}
```

---

# Engineering Decisions

- Python + FastAPI backend
- Sentence embeddings for semantic similarity matching
- Cosine similarity for lightweight policy matching
- GitHub Pages for frontend hosting
- Render for backend deployment
- Mobile-first development workflow (Android only)

---

# Repository Structure

```text
SVP-Semantic-Vector-Protocol-KERNEL/
├── app.py
├── myengine.py
├── index.html
├── README.md
├── LICENSE
```

---

# Roadmap

Planned future work:

- Configurable policy management
- Authentication
- Official SDKs
- LangGraph integration
- CrewAI integration
- Request history
- Developer documentation
- Automated testing

---

# Current Status

SVP Kernel is an actively developed prototype demonstrating pre-execution runtime risk scoring for AI agent workflows.

It is not yet an enterprise platform and continues to evolve through experimentation and iterative development.

---

# Current Limitations

- Risk policies are currently hardcoded
- No authentication on the API
- No persistent storage or request history
- Sequence tracking currently uses rule-based destination matching
- No formal benchmark evaluation yet

---

# Contributing

Feedback, issues, and suggestions are welcome.

---

# License

All Rights Reserved.

See the **LICENSE** file for complete licensing terms.

The source code is available for evaluation and portfolio purposes. Commercial use requires explicit permission from the author.
