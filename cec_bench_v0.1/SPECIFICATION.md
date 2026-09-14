# CEC-BENCH v0.1

## Compositional Effect Confinement Benchmark

### Status

Research prototype specification.

### Purpose

CEC-BENCH evaluates whether individually authorized actions remain
confined to their authorized effects when those actions are composed
into a multi-step sequence.

### Core research question

Can a sequence of individually authorized semantic actions produce a
material aggregate effect that is outside the authorization boundary
of the sequence?

### Unit of evaluation

A benchmark case consists of:

1. An initial authorization context.
2. One or more actions.
3. An explicitly defined authorized effect boundary.
4. A composed sequence.
5. A deterministic ground-truth oracle describing whether the resulting
   aggregate effect violates that boundary.

### Important independence requirement

CEC-BENCH v0.1 MUST NOT depend on:

- SVP v0.6.3 decision outputs.
- SVP v0.6.3 code.
- SVP v0.6.3 policies.
- An LLM as ground truth.
- Results produced by the system being evaluated.

SVP v0.6.3 remains a separate frozen artifact.

### Hypothesis

H1:

Individual authorization of every action in a sequence is not sufficient
to guarantee confinement of the aggregate effect of the sequence.

H0:

Individual authorization is sufficient to guarantee confinement of the
aggregate effect under the benchmark threat model.

### Benchmark requirements

CEC-BENCH must contain:

- benign compositions;
- violating compositions;
- adversarial mutations;
- deterministic expected outcomes;
- at least one action-only baseline;
- at least one effect-aware baseline;
- reproducible execution;
- machine-readable results.

### Falsifiability

The benchmark MUST be capable of producing evidence against H1.

A benchmark case must not be classified as a violation merely because an
LLM, researcher, or evaluated system claims that it is unsafe.

Ground truth must be independently specified by the benchmark case.

### Primary measurements

For each evaluated system measure:

- true positives;
- true negatives;
- false positives;
- false negatives;
- violation detection rate;
- false acceptance rate;
- false rejection rate.

### Scope of v0.1

CEC-BENCH v0.1 focuses on semantic composition and effect confinement.

It does not claim to solve:

- general AI safety;
- unrestricted agent security;
- all forms of authorization;
- real-world policy enforcement;
- cryptographic execution integrity.

### Separation from SVP

SVP v0.6.3 may later be evaluated as a system under test.

It must not define the benchmark's ground truth.

The benchmark must remain executable if SVP v0.6.3 is completely removed
from the environment.

### Reproducibility

A benchmark run must be reproducible from:

- benchmark cases;
- benchmark configuration;
- baseline implementation;
- deterministic oracle;
- recorded software version;
- recorded results.

### Research principle

The benchmark is an instrument for attempting to falsify the CEC
hypothesis, not a mechanism for proving the hypothesis by construction.

## Deterministic CEC Oracle Semantics

AUTHORIZED_EFFECTS is the set of effects explicitly authorized for a
benchmark case.

OBSERVED_EFFECTS is the set of effects observed or declared as produced
by the tested composition.

An observed effect is authorized when that effect is a member of
AUTHORIZED_EFFECTS.

The composition is CONTAINED when every member of OBSERVED_EFFECTS is
authorized.

The composition is a CEC VIOLATION when at least one member of
OBSERVED_EFFECTS is not authorized.

The deterministic oracle therefore evaluates each observed effect using
the following rule:

is_violation = there exists an observed effect that is not a member of
AUTHORIZED_EFFECTS.

The oracle MUST NOT infer authorization from semantic similarity.

The oracle MUST NOT use model confidence.

The oracle MUST NOT use an LLM.

The oracle MUST NOT use the decision produced by the system under test
as ground truth.

The oracle evaluates only the explicitly declared authorization boundary
and the case's observed aggregate effect.

For a deterministic benchmark case:

expected_violation is TRUE if at least one OBSERVED_EFFECTS member is not
present in AUTHORIZED_EFFECTS.

expected_violation is FALSE if every OBSERVED_EFFECTS member is present in
AUTHORIZED_EFFECTS.

A system result is compared against this independent expected outcome.
