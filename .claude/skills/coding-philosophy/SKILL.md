---
name: coding-philosophy
description: The binding coding and testing standard for this project. Use whenever writing, reviewing, or refactoring any code or test in this repo — it defines how every line must be written (simplicity, self-explaining names, why-not-what comments, elegance over cleverness) and how tests must be written (failure modes over happy paths, load-bearing not exhaustive, guarding silent failures). Apply before and during implementation of any task in docs/tasks.md.
---

# Coding Philosophy

> Code is a communication tool. Its primary audience is humans — the next developer, your future
> self, your teammates. A solution is only elegant if it can be understood at a glance.

This document is **binding** for every contribution to this project, human or AI-generated. It is the
standard the spec's legibility requirement points to. When it conflicts with brevity, cleverness, or
convenience, this document wins.

---

## Core Principles

### 1. Simplicity Is the Goal, Not the Constraint
Choose the simplest solution that correctly solves the problem. If a simpler approach exists,
the complex one is wrong — not just worse. Avoid clever tricks, obscure language features, or
patterns that require deep expertise to parse. Complexity is noise.

**Ask before writing any solution:** *Could a junior developer understand this in 30 seconds?*

### 2. Code Should Explain Itself
Names carry meaning. Structure carries intent. If the code needs a comment to explain *what*
it does, the code should be rewritten — not commented.

- Variables, functions, and classes must be named for what they *mean*, not what they *are*
- A function named `calculateTax` is better than `calc` or `fn1`
- Prefer longer, honest names over short, ambiguous ones

### 3. Comments Give Context, Not Description
Comments exist to answer *why*, never *what*.

**Wrong use of comments:**
```python
# Loop through users
for user in users: ...
```

**Right use of comments:**
```python
# Inactive users are included so billing can audit discrepancies
for user in users: ...
```

Good comment subjects: business rules, non-obvious tradeoffs, known limitations, external
constraints (legal, API quirks, legacy compatibility), and intentional workarounds.

### 4. Elegance Over Cleverness
An elegant solution is one where removing anything would break it and adding anything would
bloat it. Clever code that impresses at first read but requires a second read to understand
is not elegant — it's a liability.

Avoid: deeply nested ternaries, one-liners that pack 4 operations, overuse of metaprogramming,
premature abstractions, and "magic" that hides behavior.

### 5. Structure Is Documentation
How code is organized communicates intent. Group related things together. Keep functions small
and single-purpose. Name files and modules so their role is clear before opening them. The
architecture should tell a story.

---

## Code Review Checklist

When reviewing or writing code, apply these in order:

1. **Naming** — Do names reveal intent without needing a comment?
2. **Complexity** — Is there a simpler path to the same result?
3. **Comments** — Do they explain *why*, not *what*? Are any redundant?
4. **Size** — Are functions doing one thing? Could anything be split?
5. **Readability** — Can this be read top-to-bottom like a narrative?

---

## Refactoring Heuristics

| Smell | Fix |
|---|---|
| Comment explains what code does | Rename or restructure until it's obvious |
| Function does two things | Split into two functions |
| Variable name is `data`, `temp`, `val`, `res` | Rename to reflect meaning |
| Logic requires re-reading to understand | Flatten or break into named steps |
| Abstraction exists before it's reused | Delete it; add it when the second use appears |

---

## What to Avoid

- **Over-engineering**: Don't design for hypothetical future requirements
- **Abstraction for abstraction's sake**: Every layer of indirection is a cost — pay it only when the benefit is clear
- **Terse syntax as style**: Brevity is only a virtue when it doesn't cost clarity
- **Comments as apologies**: `# this is a bit hacky` means the code should be fixed, not annotated

---

## Testing Philosophy

> Tests are not proof of correctness — they are a defense against regression and silent failure.
> A test suite should make wrong states unrepresentable, not tick a coverage box.

### 6. Test Code Is Code Too

Tests must meet the same standards as production code: clear names, single purpose, no magic
values without explanation. A test that is hard to read is a test that will be misread and
eventually ignored.

**Ask before writing any test:** *If this test fails, will the reader immediately know what broke and why?*

### 7. Test Failure Modes, Not Happy Paths Alone

Every function has an obvious success case. Tests that only cover the happy path are not tests
— they are demonstrations. The real value is in covering the ways things go wrong:

- **Boundary conditions**: empty inputs, zero, nulls, maximum values, single-item collections
- **Contract violations**: what happens when a caller passes the wrong type or an out-of-range value
- **State corruption**: does a failed operation leave the system in a broken intermediate state
- **Silent failures**: functions that swallow errors and return a default instead of surfacing the problem

### 8. One Smart Test Beats Five Trivial Ones

Don't spam test cases. A test suite bloated with redundant cases becomes noise — it slows
the suite, dilutes signal when something breaks, and creates maintenance burden.

Instead, write tests that are *load-bearing*: if removed, the project could silently break.

A good test:
- Covers a failure mode that would not be caught by any other test
- Documents a known edge case or constraint (acts as executable documentation)
- Guards a bug that was once fixed and must never regress
- Validates behavior at a boundary where the logic could plausibly go wrong

**Rule of thumb**: if you can delete a test and the suite still feels complete, the test should not exist.

### 9. Tests Document Intent and Constraints

Tests are the most reliable form of documentation because they are always up to date — they
either pass or they don't. Use test names and structure to communicate what the system is
*supposed* to do, including the constraints and edge cases that are not obvious from the code.

```python
# Bad: what is "works correctly"?
def test_process_payment_works_correctly(): ...

# Good: documents the constraint
def test_process_payment_rejects_amounts_above_daily_limit(): ...
def test_process_payment_is_idempotent_for_same_transaction_id(): ...
```

### 10. Prevent Silent Unintended Behavior

The most dangerous failures are the ones that produce no error — they return a wrong value,
corrupt state quietly, or skip a step without anyone noticing. Tests must actively guard
against this class of failure.

Patterns to watch for and test explicitly:
- Functions that return `None` / `""` instead of raising on bad input
- Optional chaining or fallback defaults that swallow missing data
- Async operations that fail silently when not awaited or caught
- State mutations that happen even when the operation logically should not proceed

---

## Testing Checklist

When writing or reviewing tests, apply these in order:

1. **Coverage of failure modes** — Are invalid inputs, nulls, and boundaries tested?
2. **Necessity** — Could each test be deleted without the suite losing meaningful coverage?
3. **Naming** — Does the test name state the exact behavior being verified?
4. **Silent failure guards** — Do tests assert on side effects and state, not just return values?
5. **Regression value** — Would this test have caught a real bug that occurred (or could occur)?

---

## Testing Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Testing only the happy path | Misses the real failure modes | Add a test for each way the function can receive bad input or produce wrong output |
| Dozens of near-identical cases | Noise, slows suite, dilutes signal | Collapse into one parameterized test or keep only the boundary case |
| Test named `"works"` or `"is correct"` | Tells you nothing when it fails | Name the exact behavior: `"returns None when document is not found"` |
| Asserting only the return value | Misses state corruption and side effects | Assert on system state, written files, and calls to dependencies |
| Tests coupled to implementation detail | Breaks on refactor even when behavior is correct | Test behavior (inputs → outputs/effects), not internals |

---

## How this applies to this project

The places where these rules bite hardest here:

- **The trust-critical paths** (`ledger.py`, resume logic) are exactly where "silent unintended
  behavior" (§10) must be tested: a corrupt output file must make `is_done` return `False`, not pass
  silently; resume must redo only pending tasks and never touch finished ones.
- **Provider differences** stay in `models.py` only — no abstraction layer "for future providers"
  beyond what `instructor` already gives us (§4, over-engineering).
- **Schema field descriptions** are the one place verbose, explicit prose is correct — they are sent
  to the model and are business intent, not redundant comments.
- **Tests are load-bearing, not exhaustive** (§8): cover schema validation, atomic-write/`is_done`
  including the corrupt-file case, resume identity, and an extraction smoke test — and stop there.
