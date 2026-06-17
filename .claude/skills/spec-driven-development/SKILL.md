---
name: spec-driven-development
description: Write specifications for Spec-Driven Development (SDD) projects — specs precise enough that an AI agent can implement them with little ambiguity, and structured enough that a human can review them fast. Use whenever the user wants to specify a feature or project, write requirements or a PRD, plan a build before coding, break work into agent-executable tasks, or set up the spec → plan → tasks artifacts that drive AI-assisted implementation. Trigger on "write a spec", "spec this out", "SDD", "requirements doc", "plan this feature for an agent to build", "break this into tasks", or any request to define WHAT to build before building it — even if the user doesn't say "spec".
---

# Spec-Driven Development

A spec is a contract between human intent and machine execution. Its only job is to delete ambiguity before code exists.

This matters more for AI agents than for humans. An agent fills every gap with an assumption, pattern-matches to the most common shape, and loses the thread over long context. A vague spec doesn't slow an agent down — it sends it confidently in the wrong direction. So a good spec replaces assumption with instruction, and makes every requirement something you can check pass/fail.

Three properties make a spec agent-ready:

- **Unambiguous** — one reading, not several. Quantified, not adjectival.
- **Verifiable** — every requirement maps to a check. If you can't test it, it's a wish, not a requirement.
- **Decomposable** — it breaks into bounded, ordered units an agent finishes one at a time and you review one at a time.

The skill itself follows the rules it teaches: legible, objective, no filler. Write specs the same way.

## The workflow

Move through phases in order. Each has a gate — don't cross it until the gate is met. The whole point of SDD is to resolve ambiguity *before* the expensive phase (implementation), so don't rush toward code.

```
0. Clarify   — intent + unknowns surfaced, scope agreed
1. Specify   — spec.md written (WHAT / WHY)
2. Plan      — plan.md written (HOW)
3. Tasks     — tasks.md written (ordered, executable units)
4. Execute   — agent builds task-by-task against the spec
```

For small features, phases 1–3 may collapse into a single document — that's fine. Don't manufacture ceremony. Keep the gates regardless of how many files you produce.

### Phase 0 — Clarify (before writing anything)

Do not write a spec on top of ambiguity; you'll just encode the ambiguity. First extract intent and surface what isn't known yet.

- Restate the goal in 1–2 sentences and confirm it.
- List what's genuinely undecided. Ask only the questions whose answers would change the spec. Don't interrogate — batch the few that matter.
- Agree on scope boundaries: what's in, what's explicitly out.

If the user wants you to proceed without answering, mark each unknown inline as `[NEEDS CLARIFICATION: question]` in the spec rather than silently guessing. Unresolved markers in must-have scope block Phase 4.

**Gate:** the goal is confirmed and scope is bounded.

### Phase 1 — Specify (spec.md, the WHAT and WHY)

Describe behavior and outcomes, never implementation. No tech stack, no class names, no algorithms here — those belong in the plan. Mixing them is the most common way specs rot: the reader can't tell a decision from a requirement.

Use `assets/spec-template.md`. It contains: purpose, scope (in / out / non-goals), users & stories, functional requirements, non-functional requirements, domain entities, assumptions & open questions, success criteria.

Write functional requirements in EARS notation — see "Requirements" below. Give every requirement a stable ID (`REQ-001`) so the plan and tasks can point back to it.

**Gate:** every requirement has an ID and at least one acceptance criterion; no unresolved clarifications in must-have scope.

### Phase 2 — Plan (plan.md, the HOW)

Now decide implementation. Record decisions *and their rationale* briefly — the rationale is what stops an agent from "improving" a deliberate choice later.

Use `assets/plan-template.md`: tech stack & key decisions, architecture, data model, interfaces/contracts, dependencies, risks & mitigations, and a traceability note (which component satisfies which `REQ`).

Don't restate requirements here. The plan answers "how do we satisfy REQ-007", not "what is REQ-007".

**Gate:** every must-have requirement is covered by some component in the plan.

### Phase 3 — Tasks (tasks.md, the execution units)

Break the plan into an ordered list an agent executes one at a time. This is the layer that makes AI-assisted creation *manageable* — small, verifiable, reviewable steps instead of one heroic generation.

Use `assets/tasks-template.md`. Each task carries: ID, one-line goal, files it touches, the `REQ`s it satisfies, an acceptance check, and dependencies. See "Task decomposition" below for granularity.

**Gate:** tasks are ordered, dependencies are explicit, and each task is independently verifiable.

### Phase 4 — Execute (drive the build)

When implementing against the spec — yourself or by directing another agent — hold this discipline:

- Work tasks in order; respect dependencies. Before a task, read the `REQ`s and plan sections it references. Each task should be locally complete — the agent shouldn't need to reconstruct context from the whole document.
- After a task, verify against its acceptance check, then mark it done.
- **Never invent scope.** If a task can't be done as specified, stop and flag it. Don't improvise a fix that drifts from the spec — that silent drift is exactly what SDD exists to prevent.
- Keep spec and code in sync. If reality forces a change, update the spec *first*, then implement. The spec stays the source of truth; stale specs are worse than none.
- Maintain traceability: every change traces to a task, every task to a `REQ`.

## Requirements: write them in EARS

EARS (Easy Approach to Requirements Syntax) constrains requirements to a few sentence shapes. The constraint is the feature — it forces a trigger and a response, which is exactly what an agent needs and a tester can check. Full guide in `references/ears.md`; the core patterns:

- **Ubiquitous:** The system SHALL `<response>`.
- **Event:** WHEN `<trigger>`, the system SHALL `<response>`.
- **State:** WHILE `<state>`, the system SHALL `<response>`.
- **Optional:** WHERE `<feature is present>`, the system SHALL `<response>`.
- **Unwanted:** IF `<condition>`, THEN the system SHALL `<response>`.

One requirement per statement. If you wrote "and" joining two behaviors, split it into two requirements with two IDs. Where EARS reads awkwardly (e.g. a pure data constraint), a plain testable SHALL statement is fine — keep the testability, drop the ceremony.

## Task decomposition

Right-size a task to *one focused change that one agent can complete and you can review in one sitting*. Too big and the agent wanders and you can't review it; too small and you drown in coordination.

- One concern per task. "Build the auth system" is a milestone, not a task. "Add password-hashing on user creation (REQ-012)" is a task.
- Order by dependency, not by file. A task that needs another's output comes after it, and says so.
- Every task ends in a checkable state — a test passes, an endpoint returns the specified shape, a function exists with the specified signature.
- Prefer tasks that touch few files. Wide blast radius is hard to verify and hard to roll back.

## Quality gates — definition of ready

A spec is ready to implement only when all hold:

- Every requirement has an ID and at least one acceptance criterion.
- No unresolved `[NEEDS CLARIFICATION]` in must-have scope.
- Scope is explicit: in, out, and non-goals are stated.
- Terms are used consistently — define each once, never two ways.
- Tasks are ordered and each is independently verifiable.

If any fail, the spec isn't done. Say so plainly rather than shipping something that looks complete but isn't.

## Anti-patterns — reject these on sight

- **Adjectival requirements.** "Fast", "secure", "user-friendly", "robust" are unfalsifiable. Quantify ("p95 < 200ms") or name the control ("passwords hashed with Argon2id") or cut it.
- **What/how bleed.** Implementation in the spec, or requirements restated in the plan. Keep the layers clean so a reader can tell a decision from a constraint.
- **Smuggled requirements.** "and"/"or" hiding two requirements in one line. Split them.
- **Mega-tasks.** "Implement the backend." Decompose until each unit is verifiable.
- **Silent assumptions.** Anything the agent would have to guess. Make it a stated assumption or a clarification marker.
- **Verbosity.** Restating the obvious, hedging, narration. Every sentence either constrains the build or gets cut. A reviewer should grasp each requirement in one pass.

## References & assets

- `references/ears.md` — full EARS patterns with examples and conversion recipes. Read before writing requirements if unsure.
- `references/example.md` — a compact feature spec'd end to end (spec → plan → tasks). Read to anchor on the target shape.
- `assets/spec-template.md`, `assets/plan-template.md`, `assets/tasks-template.md` — copy these and fill them in. They are the canonical structure; don't reinvent it per project.
