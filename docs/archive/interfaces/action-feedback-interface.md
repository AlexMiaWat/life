# 12.3 — Action → Feedback Interface

> Layer junction: **12 Action / Execution → 13 Feedback**
> Purpose: architectural integrity check

---

## Why this document exists

This document fixes the **only allowed interface** between Action and Feedback.

Without this fixation:

* actions may leak intent
* feedback may leak evaluation
* future adaptation becomes corrupted

This is a **hard boundary document**.

---

## Direction of Dependency

```
Action (12) ───▶ Feedback (13)
```

Rules:

* Action does not know Feedback exists
* Feedback depends on Action output
* No reverse calls, signals, or queries

---

## What Action is allowed to emit

Action emits a **fact record**, not a result.

Allowed fields:

* action_id
* action_type
* start_timestamp
* end_timestamp
* execution_status
* raw_effects

Explicitly forbidden:

* success / failure semantics
* confidence
* expectation
* comparison to goal
* internal decision rationale

If Action emits meaning — Action layer is broken.

---

## What Feedback is allowed to consume

Feedback consumes:

* exactly what Action emitted
* plus post-action environment signals

Feedback may:

* timestamp
* persist
* correlate by action_id

Feedback may NOT:

* reinterpret execution_status
* normalise effects
* classify outcomes

---

## State & Memory Interaction

Feedback writes:

### State (08)

* last_action_id
* last_action_execution_status
* last_action_effects

### Memory (09)

* immutable feedback record
* append-only
* never re-written

State is volatile.
Memory is historical.

---

## Failure Scenarios

### Action fails before Feedback

* Feedback receives failure status
* No retry logic here

### Feedback fails

* Action still completes
* No compensation
* Blindness is acceptable

---

## Baseline Safety

This document:

* does not change meaning of Action
* does not extend Feedback semantics
* only constrains interaction

---

## Placement in docs/

```
docs/
└── archive/
    └── 12.3_ACTION_FEEDBACK_INTERFACE.md
```
