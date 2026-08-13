# SVP Semantic Boundary Finding — v0.3

## Finding

The raw SVP decision path has a fail-open ambiguity path.

A high-risk policy can exceed its semantic similarity threshold while failing
the inter-policy confidence margin. In that situation, the raw engine falls
through to SAFE001/PASS and reports "No policy exceeded threshold".

## Root mechanism

The raw decision path requires:

- best policy similarity >= policy threshold
- adjusted-score margin >= 0.05

If the margin condition fails, the fallback returns:

- decision: PASS
- rule_id: SAFE001
- matched_policy: No policy exceeded threshold

This conflates policy ambiguity with absence of a policy match.

## Reproduced boundary cases

### delete database logs

Raw SVP:

- decision: PASS
- rule: SAFE001
- similarity: 0.8499
- DB001 threshold: 0.60
- top policy: DB001
- severity: CRITICAL
- margin: 0.0361
- required margin: 0.05

Risk-aware v0.3:

- decision: ESCALATE
- escalation triggered: true

### archive database logs

Raw SVP:

- decision: PASS
- rule: SAFE001
- similarity: 0.7716
- LOG001 threshold: 0.58
- top policy: LOG001
- severity: HIGH
- margin: 0.0283
- required margin: 0.05

Risk-aware v0.3:

- decision: ESCALATE
- escalation triggered: true

## Control cases

The risk-aware layer preserved unambiguous BLOCK decisions:

- archive logs -> BLOCK / LOG001
- archive audit logs -> BLOCK / LOG001
- archive database records -> BLOCK / DB001

Observed margins:

- archive logs: 0.0571
- archive audit logs: 0.0907
- archive database records: 0.0887

## Mitigation

The existing v0.3 risk-aware layer changes the handling of:

high-risk + threshold satisfied + margin failure

from:

PASS

to:

ESCALATE

The underlying SVP kernel was not modified during this validation.

## Evidence artifacts

- svp_boundary_clean.txt
- svp_log_boundary_output.txt
- svp_archive_boundary_output.txt
- svp_margin_diagnostic_output.txt
- svp_v03_boundary_validation_output.txt

## Baseline

app.py.baseline preserves the kernel state before this diagnostic work.

## Conclusion

The experiment provides a reproducible demonstration of a fail-open
ambiguity path in the raw decision layer and demonstrates that the existing
risk-aware v0.3 layer converts the identified high-risk ambiguous cases to
ESCALATE while preserving unambiguous BLOCK decisions.

This finding does not claim universal AI safety or perfect security.
It documents a specific reproducible decision-boundary behavior and its
controlled mitigation.
