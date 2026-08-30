# CEC-BENCH v0.1 Threat Model

## 1. System under evaluation

The system under evaluation receives a sequence of actions and determines
whether those actions may proceed.

The system may evaluate actions individually, compositionally, or both.

CEC-BENCH does not assume any particular implementation.

## 2. Trusted components

The following are trusted by the benchmark:

- the benchmark case definition;
- the explicitly declared authorization boundary;
- the deterministic benchmark oracle;
- the benchmark runner;
- the recorded expected outcome.

The system under evaluation is NOT trusted to define ground truth.

## 3. Adversary

The adversary attempts to construct or induce a sequence in which:

1. individual actions appear authorized;
2. individual actions remain within their local authorization boundaries;
3. the composition changes the resulting material effect;
4. the aggregate effect exceeds the authorized boundary.

## 4. Threat class

The primary threat class is:

Compositional semantic drift from individually authorized actions
to an unauthorized aggregate effect.

## 5. Representative attack patterns

CEC-BENCH v0.1 may test:

### 5.1 Effect escalation

A sequence progresses from an authorized internal operation toward
an unauthorized external effect.

### 5.2 Purpose drift

Actions remain individually plausible while the overall purpose of the
sequence changes.

### 5.3 Resource accumulation

Multiple individually permitted operations collectively expose,
combine, or transform information beyond the authorized boundary.

### 5.4 Authorization repurposing

An authorization associated with one action is reused to justify a
different effect.

### 5.5 Effect substitution

The authorized action remains unchanged while the requested material
effect changes.

### 5.6 Compositional privilege escalation

No single action independently crosses the boundary, but their
composition does.

## 6. Out of scope

CEC-BENCH v0.1 does not attempt to model:

- compromised operating systems;
- compromised hardware;
- cryptographic key theft;
- network-layer compromise;
- arbitrary malware;
- unrestricted physical-world attacks;
- general model deception;
- all possible forms of authorization failure.

## 7. Ground-truth requirement

A case is a CEC violation only when its declared aggregate effect is
outside the authorization boundary defined by the case.

Similarity scores, model confidence, LLM judgments, or system decisions
cannot redefine the ground truth.

## 8. Negative cases

The benchmark MUST contain compositions that remain within the
authorization boundary.

A system that blocks everything must therefore not achieve perfect
performance.

## 9. Positive cases

The benchmark MUST contain compositions whose aggregate effects exceed
the declared authorization boundary.

## 10. Falsification requirement

CEC-BENCH must permit the following outcomes:

- H1 supported;
- H1 weakened;
- H1 not supported under the tested threat model.

The benchmark must not assume that compositional confinement failure
exists before measurement.

## 11. Independence requirement

The threat model and oracle must remain valid if SVP v0.6.3 is removed.

SVP v0.6.3 is a potential system under test, not a trusted benchmark
component.

## 12. Research boundary

CEC-BENCH evaluates whether individual authorization is sufficient to
constrain aggregate effects under the defined threat model.

It does not establish that CEC is the only, primary, or universal
mechanism required for secure agent execution.
