# Tasks: <feature/project name>

> Implements: spec.md + plan.md · Last updated: <date>

Ordered units of work. An agent executes these top to bottom, respecting dependencies. Each task is locally complete: it names the requirements and files it needs, so the agent doesn't reconstruct context from the whole document.

Status legend: `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked

---

## T-001 — <one-line goal>
- **Status:** [ ]
- **Satisfies:** REQ-001
- **Depends on:** —
- **Files:** `<path/to/file>`
- **Do:** <the specific change, in 1–2 sentences>
- **Accept:** <the checkable end state — a test passes, an endpoint returns the specified shape, a function exists with the specified signature>

## T-002 — <one-line goal>
- **Status:** [ ]
- **Satisfies:** REQ-002, REQ-003
- **Depends on:** T-001
- **Files:** `<path/to/file>`
- **Do:** <the specific change>
- **Accept:** <checkable end state>

<!--
Granularity check for each task:
- One concern. If you wrote "and", consider splitting.
- Ends in a verifiable state.
- Touches few files (narrow blast radius = easy to review and roll back).
- Ordered by dependency, not by file.
-->

---

## Execution notes

- Work in order; before each task, read the REQs and plan sections it references.
- After each task, run its **Accept** check, then set status to `[x]`.
- If a task can't be done as written, set `[!]`, state why, and stop — don't improvise scope. Update spec/plan first, then resume.
