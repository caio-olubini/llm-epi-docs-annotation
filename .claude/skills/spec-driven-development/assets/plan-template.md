# Plan: <feature/project name>

> Implements: spec.md · Last updated: <date>

The plan answers *how* we satisfy the spec. Record decisions and their rationale; the rationale is what stops a later change from undoing a deliberate choice. Don't restate requirements here — reference them by ID.

## Tech stack & key decisions

| Decision | Choice | Rationale |
|---|---|---|
| <e.g. language> | <e.g. TypeScript> | <why — 1 line> |
| <e.g. datastore> | <e.g. Postgres> | <why> |

## Architecture

<A short paragraph or a simple component list. What the major pieces are and how data flows between them. A diagram description is fine; keep it skimmable.>

- **<Component A>** — `<responsibility>`
- **<Component B>** — `<responsibility>`

## Data model

Concrete schema: tables/collections, fields, types, keys, indexes.

```
<Entity>
  id          <type>  PK
  <field>     <type>  <constraints>
  <fk_field>  <type>  FK -> <Entity>.id
```

## Interfaces & contracts

The exact shapes an agent must implement against — endpoints, signatures, payloads. Precision here removes guesswork at execution time.

```
<METHOD> <path>
  request:  { <field>: <type> }
  response: { <field>: <type> }
  errors:   <code> -> <when>
```

## Dependencies

- **External:** <libraries, services, APIs — and version constraints if they matter>
- **Internal:** <existing modules this builds on>

## Risks & mitigations

- **Risk:** <what could go wrong> — **Mitigation:** <how we reduce it>

## Traceability

Every must-have requirement maps to a component. Gaps here mean the plan is incomplete.

| Requirement | Satisfied by |
|---|---|
| REQ-001 | <component / endpoint> |
| REQ-002 | <component / endpoint> |
