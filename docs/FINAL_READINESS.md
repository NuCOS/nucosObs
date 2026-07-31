# nucosObs Final Readiness Screen

**Assessment date**: July 31, 2026
**Runtime support**: Python 3.11 through 3.13
**Verification**: 30 pytest tests pass; the package builds as both a wheel and
source distribution.

## Current Signal

| Area | Status | Evidence |
| --- | --- | --- |
| Core observable routing | Ready | 100% coverage for `observable.py` |
| Observer and runtime lifecycle | Ready with follow-up opportunities | 76-85% coverage, including thread, ordering, and isolation regressions |
| Websocket interfaces | Ready for covered flows | 75-77% coverage with loopback auth and cleanup tests |
| Stdin and two-way interfaces | Needs focused coverage | 45% and 33% coverage respectively |
| Developer workflow | Ready | Python 3.11-3.13 CI, JUnit output, wheel builds, templates, and policy files |

The project is suitable for public GitHub use. The highest-value next work is
not a public API rewrite; it is making behavior easier to observe, test, and
trust.

## Non-Breaking Proposals

### P1 - Cover directive interfaces end to end

Add pytest cases for `TwoWayInterface` routing, `send_all`, `waitTime`,
`leave_in`, and stop-interface behavior. Add `StdinInterface` tests for each
documented command and shutdown path.

**What users see**: documented commands behave consistently across releases.

**Compatibility**: test-only at first. If needed, add an optional
`input_stream` constructor argument to `StdinInterface`; keep `sys.stdin` as
the default.

**Done when**: each branch in both interfaces has a deterministic test and
module coverage reaches at least 80%.

### P1 - Make delivery failures observable

Replace broad silent exception handling in network send/broadcast and parser
boundaries with optional logging or an optional error callback. Preserve the
current default behavior when no callback is configured.

**What users see**: a failed send, rejected message, or failed callback can be
diagnosed without changing normal delivery semantics.

**Compatibility**: add keyword-only optional hooks; do not change existing
return values or default error handling.

**Done when**: tests prove an error hook receives context for failed send,
authentication callback, and handler errors while legacy callers still run.

### P1 - Make runtime shutdown explicit and inspectable

Add optional `Runtime.shutdown()` state reporting for open observers, pending
tasks, and interface connections. Keep `Runtime.close()` as the existing simple
terminal cleanup operation.

**What users see**: shutdown behavior matches the visible state of their
application instead of leaving them to infer what is still active.

**Compatibility**: additive API only; no change to `main_loop()` or
`Runtime.close()` behavior.

**Done when**: tests cover clean shutdown, cancelled work, repeated shutdown,
and the returned state report.

### P2 - Add a developer diagnostics command

Provide a small `python -m nucosObs` command that prints the package version,
supported Python range, installed websocket/aiohttp versions, and a concise
runtime health summary.

**What users see**: copy-pasteable diagnostics that tell them what is actually
installed and configured.

**Compatibility**: additive module entry point; existing imports and scripts
remain unchanged.

**Done when**: subprocess tests validate stable human-readable and JSON output.

### P2 - Test the public examples in CI

Extract the smallest safe examples into executable tests or doctests. Keep
network examples local-only and never depend on checked-in certificates or
external services.

**What users see**: README and example behavior is what they get after install.

**Compatibility**: test and documentation changes only.

**Done when**: CI executes the README event example and at least one example for
each interface family.

### P2 - Add gradual typing and runtime validation

Introduce typed event aliases and a validation helper for the documented
`{"name": ..., "args": [...]}` message shape. Keep accepting untyped dict and
string events exactly as today.

**What users see**: editor assistance and early, clear validation for users who
opt in, without rejecting existing event producers.

**Compatibility**: additive types and opt-in validation only.

**Done when**: type-checking runs in CI for public modules and tests prove both
valid and legacy event forms remain accepted.

### P3 - Establish coverage guardrails

Keep the current 72% baseline visible, then add per-module goals instead of an
immediate global failure threshold. Raise the overall threshold only after the
directive interfaces are covered.

**What users see**: regressions in important logic are caught without blocking
valid contributions because of legacy, untested paths.

**Compatibility**: CI-only change.

**Done when**: CI publishes coverage XML and rejects a coverage decrease in a
touched core module.

## Recommended Order

1. Directive-interface tests.
2. Optional error visibility hooks.
3. Runtime shutdown reporting.
4. Executable examples and diagnostics command.
5. Typing, validation, and coverage guardrails.

This order raises confidence in existing behavior before adding developer-facing
features. Every item is additive or preserves the existing default behavior.