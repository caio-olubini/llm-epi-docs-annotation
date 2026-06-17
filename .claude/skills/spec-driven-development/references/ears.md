# EARS — requirements syntax reference

EARS (Easy Approach to Requirements Syntax) restricts every requirement to one of a few sentence templates. Each template forces a trigger and a response. That structure is what makes a requirement implementable by an agent and checkable by a tester: you always know *when* the behavior applies and *what* must happen.

Use the keyword **SHALL** for binding behavior. Reserve SHOULD/MAY for genuine recommendations (rare in a spec — usually a sign the requirement is underspecified).

## The five patterns

### 1. Ubiquitous — always true, no trigger
> The system SHALL `<response>`.

For invariants that hold at all times.
- The system SHALL store all timestamps in UTC.
- The API SHALL return responses in JSON.

### 2. Event-driven — a discrete trigger occurs
> WHEN `<trigger>`, the system SHALL `<response>`.

For behavior fired by an event or input.
- WHEN a user submits the signup form, the system SHALL send a verification email within 60 seconds.
- WHEN a payment succeeds, the system SHALL mark the order as `paid`.

### 3. State-driven — true throughout a state
> WHILE `<state>`, the system SHALL `<response>`.

For behavior that persists for the duration of a condition.
- WHILE an upload is in progress, the system SHALL display a progress bar.
- WHILE the account is suspended, the system SHALL reject all write operations.

### 4. Optional feature — conditional on a feature being present
> WHERE `<feature is included>`, the system SHALL `<response>`.

For behavior tied to a configurable or optional capability.
- WHERE two-factor authentication is enabled, the system SHALL prompt for a code after password entry.
- WHERE the export module is installed, the system SHALL offer CSV download.

### 5. Unwanted behavior — handling errors, edge cases, misuse
> IF `<unwanted condition>`, THEN the system SHALL `<response>`.

For error handling and edge cases. These are the requirements people forget; writing them explicitly is where EARS earns its keep.
- IF the password is shorter than 12 characters, THEN the system SHALL reject it and display the length requirement.
- IF an external payment call times out, THEN the system SHALL retry twice before marking the order `failed`.

### Complex — combine when truly needed
You can nest a state or condition into an event:
> WHILE `<state>`, WHEN `<trigger>`, the system SHALL `<response>`.

Use sparingly. If a requirement needs three clauses to express, it's usually two requirements.

## Rules

- **One requirement per statement.** If "and" joins two behaviors, split into two IDs. A reviewer must be able to pass/fail each independently.
- **Name the actor.** "the system", "the API", "the scheduler" — not a vague "it".
- **Quantify the response.** "within 60 seconds", "exactly once", "at most 3 retries". Numbers are testable; "quickly" is not.
- **Make the trigger observable.** The condition should be something code can actually detect.

## Converting prose to EARS

| Vague prose | EARS requirement |
|---|---|
| "Login should be fast." | WHEN a user submits valid credentials, the system SHALL return a session token within 500 ms (p95). |
| "Handle bad input gracefully." | IF a required field is missing, THEN the system SHALL return HTTP 400 with the field name. |
| "Users can reset passwords." | WHEN a user requests a reset, the system SHALL email a single-use link valid for 30 minutes. |
| "Keep data secure." | The system SHALL encrypt personal data at rest using AES-256. |
| "Show status while loading." | WHILE a query is running, the system SHALL display a loading indicator. |

Each conversion does the same thing: pin down the trigger, name the actor, and make the response measurable. If you can't, you've found a real gap — surface it as a `[NEEDS CLARIFICATION]`, don't paper over it.

## Acceptance criteria

Every requirement gets at least one acceptance criterion: a concrete pass/fail check, ideally in given/when/then form.

```
REQ-012 — WHEN a user submits the signup form with a valid email,
          the system SHALL send a verification email within 60 seconds.

Acceptance:
- GIVEN a valid, unregistered email
  WHEN the form is submitted
  THEN a verification email arrives within 60 seconds
  AND the email contains a single-use link valid for 24 hours
- GIVEN an email already registered
  WHEN the form is submitted
  THEN no email is sent AND the system returns "email already in use"
```

The acceptance criteria are what the agent builds against and what the task's verification step checks. A requirement with no acceptance criterion is not ready.
