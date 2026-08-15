# SVP v0.6.2 Adversarial Finding: Process-Restart Replay

## Finding

A previously consumed authorization can be replayed after the Python process is restarted.

## Test

### Process A

A valid authorization was created for:

`read synthetic://dataset/restart-replay-001`

The authorization was submitted to the actual `app.py` HTTP execution gate.

Result:

- `executed: True`
- `reason: EXECUTION AUTHORIZED`

The authorization was therefore consumed in Process A.

### Process B

A fresh Python process was started.

The exact same action and authorization record from Process A were submitted again.

Result:

- `executed: True`
- `reason: EXECUTION AUTHORIZED`

Expected result:

- `executed: False`
- `reason: REPLAY`

## Result

**FAIL / SECURITY FINDING**

The replay was accepted across a process boundary.

## Root Cause

Replay state is maintained in process-local memory:

`V06_CONSUMED = set()`

When the process terminates, the consumed-authorization state is lost. A new process initializes an empty set.

## Security Impact

An authorization consumed before process termination can be presented again to a fresh process and accepted as unused.

This means the current implementation provides same-process replay protection but does not provide persistent or distributed replay prevention.

## Scope

This finding concerns the prototype execution-gate implementation.

It does not invalidate the previously demonstrated cryptographic request binding or decision commitment integrity.

## Current Status

FINDING — remediation not yet implemented.

## Required Future Property

A production implementation would require durable, concurrency-safe authorization consumption state with appropriate replay semantics across process restarts and, where applicable, across multiple workers or hosts.
