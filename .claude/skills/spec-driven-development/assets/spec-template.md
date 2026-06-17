# Spec: <feature/project name>

> Status: Draft | Ready | Implementing | Done
> Owner: <name> · Last updated: <date>

## Purpose

<1–3 sentences: the problem and why it's worth solving. No solution detail.>

## Scope

**In scope**
- <what this delivers>

**Out of scope**
- <adjacent things explicitly not included>

**Non-goals**
- <things one might assume are goals but aren't — kills the assumption up front>

## Users & stories

- As a `<role>`, I want `<capability>` so that `<outcome>`.
- As a `<role>`, I want `<capability>` so that `<outcome>`.

## Functional requirements

Write each in EARS. One requirement per ID. Each has ≥1 acceptance criterion.

### REQ-001 — <short title>
WHEN `<trigger>`, the system SHALL `<response>`.

Acceptance:
- GIVEN `<context>` WHEN `<action>` THEN `<observable result>`

### REQ-002 — <short title>
IF `<condition>`, THEN the system SHALL `<response>`.

Acceptance:
- GIVEN `<context>` WHEN `<action>` THEN `<observable result>`

<!-- add as many REQ-NNN as needed; keep IDs stable once assigned -->

## Non-functional requirements

Quantify or name the control — no adjectives.

- **Performance:** <e.g. p95 latency < 200 ms at 100 rps>
- **Security:** <e.g. personal data encrypted at rest with AES-256>
- **Reliability:** <e.g. 99.9% monthly availability>
- **Accessibility / other:** <as applicable>

## Domain entities

The shape of the data, not the storage tech. Names, fields, relationships.

- **<Entity>**: `<field: type>`, `<field: type>` — `<relationship to other entity>`

## Assumptions & open questions

- **Assumption:** <something taken as given — state it so it can be challenged>
- `[NEEDS CLARIFICATION: <question that must be answered before implementation>]`

## Success criteria

How we know the whole thing worked — measurable, at the feature level.

- <e.g. a new user can sign up and verify in under 2 minutes with no support>
