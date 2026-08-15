# SVP v0.6 Security Evidence

## Scope

SVP v0.6 adds cryptographic binding between an authorization request and
the resulting SVP decision before the authorization is accepted by the
runtime gate.

No real-world external action is executed by these experiments.

## Verified Properties

### 1. Semantic lineage protection

- Depth: 1000
- Mutation hop: 500
- Purpose escalation: blocked
- Resource escalation: blocked
- Action escalation: blocked
- Authority escalation: blocked
- Combined escalation: blocked
- False acceptance rate: 0.000
- Experiment status: PASS

### 2. Decision binding

Verified rejection of:

- Decision mutation
- Policy version mutation
- Policy ID mutation
- Request mutation

Post-evaluation false acceptance rate: 0.000.

### 3. Replay resistance

Verified:

- First valid authorization: accepted
- Exact authorization replay: rejected
- Fresh authorization: accepted

Replay resistance experiment: PASS.

### 4. Execution gate

Verified rejection of:

- Allow → escalated policy mutation
- Policy version forgery
- Policy ID forgery
- Request/action forgery

Unauthorized execution rate: 0.000.

### 5. Original action-binding finding

Initial test demonstrated that a valid authorization could be reused
with a different action.

Initial result:

- Original: read synthetic://dataset/record-001
- Forged: delete synthetic://dataset/secret
- Result: EXECUTION AUTHORIZED
- Finding: request/action binding bypass

A request-binding check was then added to the runtime gate.

Regression result:

- Original: read synthetic://dataset/record-001
- Forged: delete synthetic://dataset/secret
- Verification: False
- Outcome: REQUEST BINDING INVALID
- Expectation met: True

### 6. Real-kernel HTTP integration

Endpoint:

POST /v1/audit/v06

Verified that the endpoint:

1. Calls the real `svp_kernel()`.
2. Produces the live semantic decision.
3. Creates a cryptographically bound decision record.
4. Verifies the bound decision.
5. Rejects subsequent decision tampering.
6. Rejects a forged action against the authorization record.

Example legitimate result:

- HTTP status: 200
- Decision: PASS
- Rule: SAFE001
- Binding: valid
- Outcome: DECISION VALID

HTTP-level forged-action regression:

- Verification: False
- Outcome: REQUEST BINDING INVALID
- Expectation met: True

## Current Architecture

request
  ↓
real SVP semantic evaluation
  ↓
decision record
  ↓
request commitment
  ↓
decision commitment
  ↓
runtime verification
  ↓
execution authorization

## Important Limitations

This evidence does not establish:

- production cryptographic key management
- distributed replay prevention
- persistent nonce storage across processes
- concurrency/race-condition safety
- authorization revocation
- production deployment security
- protection against compromise of the signing/verification secret
- independent security audit

The v0.6 work demonstrates a tested prototype security boundary,
not a production security guarantee.

## Status

SVP v0.6 security integration evidence: PASS

The original action-binding bypass was reproduced, patched, and
regression-tested at the HTTP-integrated boundary.
