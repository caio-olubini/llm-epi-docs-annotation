# Worked example — a feature spec'd end to end

A deliberately small feature (a URL shortener) shown across all three artifacts. The point isn't the feature; it's the *shape* — note how the spec stays free of implementation, the plan adds the how with rationale, and the tasks are small and checkable. Yours can be longer, but should read this tightly.

---

## spec.md (excerpt)

### Purpose
Let users turn long URLs into short links they can share, and redirect visitors to the original.

### Scope
**In scope:** create a short link, redirect via it, basic click count.
**Out of scope:** custom aliases, link expiry, user accounts.
**Non-goals:** analytics dashboards, branded domains.

### Functional requirements

**REQ-001 — create a short link**
WHEN a user submits a valid URL, the system SHALL return a short code of 7 characters.
Acceptance:
- GIVEN a valid `https` URL WHEN submitted THEN a 7-char code is returned AND resolving it redirects to the original.

**REQ-002 — reject invalid input**
IF the submitted string is not a valid `http`/`https` URL, THEN the system SHALL return HTTP 400 with the reason.
Acceptance:
- GIVEN `"not a url"` WHEN submitted THEN response is 400 AND body names the validation failure.

**REQ-003 — redirect**
WHEN a request hits an existing short code, the system SHALL respond 302 to the original URL.
Acceptance:
- GIVEN a known code WHEN fetched THEN status is 302 AND `Location` is the original URL.

**REQ-004 — count clicks**
WHEN a short code is resolved, the system SHALL increment that link's click count by exactly 1.
Acceptance:
- GIVEN a code with count N WHEN resolved THEN count is N+1.

### Non-functional
- **Performance:** redirect p95 < 50 ms.
- **Collision:** code generation SHALL be unique; IF a generated code already exists, THEN the system SHALL regenerate.

### Domain entities
- **Link**: `code: string(7)`, `original_url: string`, `clicks: int`, `created_at: timestamp`.

### Assumptions & open questions
- Assumption: links never expire (per scope).
- `[NEEDS CLARIFICATION: rate limit on creation? assuming none for v1]`

### Success criteria
- A user can shorten a URL and have it redirect, with an accurate click count, with no manual steps.

---

## plan.md (excerpt)

### Tech stack & key decisions
| Decision | Choice | Rationale |
|---|---|---|
| Runtime | Node + Fastify | Low-overhead redirects; meets p95 budget |
| Store | Postgres | Need durable counts + unique constraint on code |
| Code gen | base62 of random 42 bits | 7 chars, huge space → collisions rare |

### Architecture
- **API** — two routes: `POST /links` (create), `GET /:code` (redirect).
- **Store** — single `links` table; unique index on `code` enforces REQ collision rule.

### Data model
```
links
  code         char(7)      PK
  original_url text         not null
  clicks       integer      not null default 0
  created_at   timestamptz  not null default now()
```

### Interfaces & contracts
```
POST /links
  request:  { url: string }
  response: { code: string, short_url: string }
  errors:   400 -> url fails validation

GET /:code
  response: 302 with Location: <original_url>
  errors:   404 -> code not found
```

### Traceability
| Requirement | Satisfied by |
|---|---|
| REQ-001 | POST /links + base62 gen |
| REQ-002 | POST /links validation |
| REQ-003 | GET /:code |
| REQ-004 | GET /:code (increment) |

---

## tasks.md (excerpt)

## T-001 — schema + migration
- **Satisfies:** REQ-001, REQ-004 · **Depends on:** — · **Files:** `migrations/001_links.sql`
- **Do:** Create `links` table with unique `code`, default `clicks = 0`.
- **Accept:** Migration runs clean; inserting duplicate `code` is rejected by the DB.

## T-002 — code generator
- **Satisfies:** REQ-001 (collision rule) · **Depends on:** T-001 · **Files:** `src/code.ts`
- **Do:** Generate a 7-char base62 code; regenerate on unique-constraint violation.
- **Accept:** Unit test: 10k codes are all 7 chars and unique.

## T-003 — POST /links
- **Satisfies:** REQ-001, REQ-002 · **Depends on:** T-002 · **Files:** `src/routes/create.ts`
- **Do:** Validate URL; on valid, store and return `{ code, short_url }`; on invalid, 400 with reason.
- **Accept:** Valid URL → 200 with 7-char code; `"not a url"` → 400 naming the failure.

## T-004 — GET /:code
- **Satisfies:** REQ-003, REQ-004 · **Depends on:** T-001 · **Files:** `src/routes/redirect.ts`
- **Do:** Look up code; 302 to original and increment `clicks` by 1; unknown code → 404.
- **Accept:** Known code → 302 with correct `Location` AND count goes N→N+1; unknown → 404.

---

Notice: four requirements, four small tasks, each ending in a check. No task says "build the API". Every task points back to a `REQ`. That traceability is what lets you (or a reviewer) confirm the build matches intent without reading the code line by line.
