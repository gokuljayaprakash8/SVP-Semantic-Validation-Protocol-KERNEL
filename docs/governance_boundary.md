# SVP Pre-Execution Governance Boundary

SVP now exposes a small, domain-agnostic governance boundary in
`svp_kernel/governance.py`.

```text
PROPOSE → NORMALIZE → GOVERN → ALLOW / BLOCK / ESCALATE
                                 ↓
                         EXECUTE ONLY IF ALLOWED
                                 ↓
                               AUDIT
```

## Request and decision model

`GovernanceRequest` contains:

- `principal`, `agent`, and `delegation`
- human-readable `intent`
- proposed `action` and `resource`
- `context` and `state`
- caller-supplied `request_id` and `trace_id`

`GovernanceDecision` contains `outcome` (`ALLOW`, `BLOCK`, or `ESCALATE`),
`reason`, `rule`, normalized `risk`, `policy_version`, and the request/trace
identifiers. `execution_allowed` is true only for `ALLOW`.

The engine adapts the existing semantic policy evaluator. `BLOCK` remains a
hard denial. High-risk results become `ESCALATE` until the request carries an
explicit approval state. Unknown evaluator results and evaluator failures
fail closed as `BLOCK`.

## Enforcement and integration

`GovernanceRuntime.execute(request, adapter)` is the enforcement boundary. It
evaluates the request before calling the adapter. The adapter is not called
for `BLOCK`, `ESCALATE`, malformed input, or unavailable governance.
Applications provide an adapter implementing:

```python
def execute(self, request: GovernanceRequest) -> object:
    ...
```

The FastAPI endpoint `POST /v1/govern` exposes proposal evaluation and a
structured audit trace without executing an action. Existing `/v1/audit` and
historical v0.3/v0.6 research paths remain available. In the active
application, `/v1/execute/v06-test` treats its legacy authorization record as
compatibility evidence, then creates a fresh `GovernanceRequest` and routes
the sink through `GovernanceRuntime.execute()`. A legacy `PASS` cannot
override a current `BLOCK` or unapproved `ESCALATE`.

`GovernanceExtension` is an extension point for future multi-step or CEC
composition. Extensions may tighten a result but cannot relax a `BLOCK` or
an unapproved `ESCALATE`.

## Audit and limitations

`AuditTrail` emits structured, hash-chained in-memory traces for governance,
enforcement, and execution outcomes. The application integration also forwards
the decision to the existing legacy `AuditLogger` for compatibility.

The prototype does not execute real tools, provide durable distributed audit
storage, model multi-step workflows yet, or prove that semantic evaluation
is complete. Policy coverage and semantic false positives/negatives remain
limitations of the existing evaluator. This experiment establishes a
mandatory boundary for the active application sink only; it does not prevent
arbitrary in-process code from calling a retained adapter reference, bypass
an older decorated function through `__wrapped__`, or execute preserved
historical standalone scripts.

Run the side-effect-free demonstration with:

```bash
python examples/governance_demo.py
```