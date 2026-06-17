# Spec: LLM Epidemiological Bulletin Annotation Pipeline

> Status: Ready
> Owner: Caio · Last updated: 2026-06-15

## Purpose

Brazilian Ministry of Health epidemiological bulletins (*Boletins Epidemiológicos*) report arbovirus
surveillance data (dengue, chikungunya, zika, yellow fever) as free-running Portuguese prose mixed
with tables and figures. Reading them into structured data by hand does not scale. This project uses
LLMs to extract that data into a fixed structured schema, and — because it is the basis of an
academic paper comparing how well different models perform this task — it must run the **same
extraction across multiple models**, and produce **persistent, trustworthy, fully resumable** records
of every run.

## Scope

**In scope**
- Read PDF bulletins from configured folders under `data/raw/`.
- Extract plain text from each PDF.
- For each `(document, model)` pair, call an LLM via a unified interface and obtain a
  schema-validated structured annotation.
- Support multiple cloud providers (OpenAI, Anthropic, Google) selected entirely through config.
- Persist every annotation and a complete audit trail per run.
- Resume a crashed or partial run from exactly where it stopped, without redoing finished work.
- Drive everything through a small CLI under a `uv`-managed project.

**Out of scope**
- The quality-comparison study itself: agreement metrics, scoring against the golden standard,
  statistical analysis, report/figure generation. The pipeline is designed to *feed* that study but
  does not implement it. (Separate, later phase.)
- Multimodal / vision input (sending page images to models).
- Downloading, re-downloading, or repairing PDFs — acquisition is already handled and tracked in
  `data/raw/manifest.csv` / `failures.csv`.
- Fine-tuning, prompt-optimization search, or model hosting.

**Non-goals**
- Not a general document-classification system — the `dengue_related` / `not_dengue_related` folder
  split is an *input selector*, not a label the pipeline predicts.
- Not a real-time service — it is a batch tool run from the command line.
- Not a database application — run records live as plain files on disk for transparency and
  reproducibility.

## Users & stories

- As a **researcher**, I want to run the identical extraction across several LLMs with one command so
  that I can later compare their annotation quality on equal footing.
- As a **researcher**, I want every model's output stored as an inspectable, schema-valid file so that
  the data behind my paper is transparent and auditable.
- As a **researcher**, I want a long run that crashes (network error, rate limit, power loss) to
  resume and finish only the missing work, so that I never lose completed results or pay to redo them.
- As a **researcher**, I want to change models, input folders, and parameters by editing one config
  file so that experiments are reproducible and I never edit code to run a variant.
- As a **junior collaborator**, I want the codebase to be small and obvious so that I can understand
  and extend it without a guide.

## Functional requirements

Written in EARS. One requirement per ID; IDs are stable once assigned.

### REQ-001 — Configuration-driven execution
WHEN the pipeline starts, the system SHALL load all run parameters (input folders, PDF settings, the
list of models, run settings, prompt path) from `config.yml` and validate them before doing any work.

Acceptance:
- GIVEN a valid `config.yml` WHEN the pipeline starts THEN it proceeds using exactly those values and
  no value is hard-coded in source.
- GIVEN a `config.yml` with a missing required field or wrong type WHEN the pipeline starts THEN it
  exits non-zero with a message naming the offending field, before any model is called.

### REQ-002 — Secrets via environment, never in config
IF a provider requires an API key, THEN the system SHALL read it from an environment variable (loaded
from a gitignored `.env`) and SHALL NOT read or store keys in `config.yml` or any run artifact.

Acceptance:
- GIVEN a model whose provider key env var is unset WHEN that model's task runs THEN the system
  reports a clear "missing credential" error for that model and no key value is ever written to disk.

### REQ-003 — PDF text extraction
WHEN a document is processed, the system SHALL extract its text using the configured extractor, apply
the configured character limit if set, and cache the extracted text so a later resume does not
re-extract it.

Acceptance:
- GIVEN a PDF and `extractor: pymupdf` WHEN extraction runs THEN non-empty text is produced and cached
  on disk keyed by document.
- GIVEN a configured `max_chars: N` WHEN a document's text exceeds N THEN the text passed to the model
  is truncated to N characters.
- GIVEN a PDF from which no text can be extracted WHEN extraction runs THEN the document's tasks are
  recorded as failed with an explanatory error and the run continues.

### REQ-004 — Structured, schema-enforced annotation
WHEN a model is called for a document, the system SHALL request output conforming to the
`DocumentAnnotation` schema and SHALL only accept a result that validates against that schema.

Acceptance:
- GIVEN any successful task WHEN it completes THEN its stored output parses back into
  `DocumentAnnotation` without error.
- GIVEN a model returns data that cannot be coerced to the schema after the allowed retries WHEN the
  task ends THEN it is recorded as failed and no invalid output file is written.

### REQ-004a — Schema content (the contract)
The `DocumentAnnotation` schema SHALL capture, at document level: diseases covered, reference year,
publication date, bulletin volume, bulletin number; and a list of `EpiObservation` records each
capturing: disease, location name, location level, epidemiological week range, reference year,
probable cases, confirmed cases, deaths, incidence per 100k, and data source. Every field other than
`observations`, `diseases_covered`, and `location_name`/`disease`/`location_level` SHALL be optional.

Acceptance:
- GIVEN a model that cannot find a particular value WHEN it annotates THEN it may leave that field
  null without failing validation (no forced hallucination).

### REQ-005 — Multi-provider, unified interface
WHEN the configured models span different providers (OpenAI, Anthropic, Google), the system SHALL call
each through one uniform code path, isolating all provider-specific differences to a single module.

Acceptance:
- GIVEN models from two different providers in `config.yml` WHEN a run executes THEN both are invoked
  through the same `annotate(...)` function and produce outputs in the same schema and layout.
- GIVEN a new provider supported by the underlying library WHEN it is added THEN only the provider
  module changes — no change to extraction, runner, schema, or CLI.

### REQ-006 — Per-task isolation and continue-on-failure
WHEN an individual `(document, model)` task fails after its retries, the system SHALL record the
failure and continue processing the remaining tasks; one failed task SHALL NOT abort the run.

Acceptance:
- GIVEN a run where one document fails for one model WHEN the run finishes THEN every other
  `(document, model)` task has either a stored output or a recorded failure, and the process exits
  reporting counts.

### REQ-007 — Bounded retries with backoff
IF a task fails due to a transient error (rate limit, timeout, transport error, transient validation
failure), THEN the system SHALL retry up to the configured `max_retries` with backoff before marking
it failed.

Acceptance:
- GIVEN `max_retries: 3` WHEN a task hits transient errors THEN at most 3 retries occur, spaced by
  increasing delay, and each attempt is recorded in the audit log.

### REQ-008 — Persistent, self-contained run records
WHEN a run starts, the system SHALL create one run directory containing a frozen snapshot of the
config, an append-only audit log, and the annotation outputs, such that the directory alone fully
documents the run.

Acceptance:
- GIVEN a completed run WHEN its directory is inspected THEN it contains `config.snapshot.yml`, a
  `log.jsonl` with one line per attempt, and `annotations/<model>/<document>.json` for every
  successful task.
- GIVEN the rest of the project is deleted WHEN the run directory is examined THEN the parameters,
  per-attempt metrics, and results of that run are still fully recoverable from it.

### REQ-009 — Crash-safe writes
WHEN the system writes an annotation file, it SHALL write atomically so that a crash mid-write can
never leave a partial or corrupt annotation file.

Acceptance:
- GIVEN a process kill during output writing WHEN the run is later inspected THEN every annotation
  file present is complete and schema-valid (no truncated JSON).

### REQ-010 — Resume from point of failure
WHEN the pipeline is asked to resume a run, the system SHALL rebuild the task set from that run's
config snapshot, skip every task whose valid output already exists, and execute only the remaining
tasks.

Acceptance:
- GIVEN a run that completed 40 of 100 tasks then crashed WHEN it is resumed THEN exactly the 60
  unfinished tasks run, the 40 finished outputs are untouched, and the final result is identical to an
  uninterrupted run.
- GIVEN resume uses the snapshot config WHEN the live `config.yml` has since changed THEN the resumed
  run still uses the original snapshot, not the edited file.

### REQ-011 — Run status visibility
WHEN asked for a run's status, the system SHALL report counts of done, failed, and pending tasks
derived from the audit log and the outputs on disk.

Acceptance:
- GIVEN any run id WHEN status is requested THEN done/failed/pending counts are printed and the done
  count equals the number of valid annotation files on disk.

### REQ-012 — CLI surface
WHEN invoked, the system SHALL expose commands to start a run, resume a run, show a run's status, and
list past runs, runnable via the `uv`-installed entrypoint.

Acceptance:
- GIVEN the project is synced WHEN `uv run epi-annotate run|resume|status|list-runs` is invoked THEN
  each command performs its function and exits with a clear status code.

## Non-functional requirements

- **Reproducibility:** A run is fully determined by its `config.snapshot.yml` + prompt snapshot +
  input PDFs; `temperature` defaults to 0 for the comparison models. Re-running from a snapshot
  reproduces the same task grid.
- **Resumability:** Recovery requires no manual cleanup — resuming is always safe to run repeatedly
  (idempotent); a fully-completed run resumed again does zero work.
- **Trustworthiness:** The audit log is append-only and never rewritten; the source of truth for "done"
  is the validated output file on disk, so tracking can never silently disagree with reality.
- **Legibility:** Each source module fits one responsibility and is readable by a junior developer with
  no project-specific knowledge; no metaprogramming or clever indirection. Legibility outranks brevity
  and cleverness. The binding standard is the `coding-philosophy` skill
  ([`.claude/skills/coding-philosophy/SKILL.md`](../.claude/skills/coding-philosophy/SKILL.md)) — all
  code and tests must pass its review checklists.
- **Portability:** Runs offline-friendly aside from provider API calls; depends only on `uv`-resolved
  Python packages and the PDFs already on disk.
- **Cost transparency:** Token counts and an estimated cost are recorded per attempt so the paper can
  report spend per model.

## Domain entities

The shape of the data, independent of storage.

- **Document** — one PDF bulletin. `document_id: str` (filename stem), `source_dir: str`,
  `path: str` — the unit annotated.
- **Model** — one configured LLM. `name: str` (label used in paths), `provider: str`,
  `model_id: str`, `temperature: float`, `max_tokens: int | null`.
- **Task** — one `(Document, Model)` pair; the atomic unit of work, retry, and resume.
- **DocumentAnnotation** — a model's structured reading of one document: `diseases_covered: list`,
  `reference_year: int?`, `publication_date: date?`, `bulletin_volume: str?`,
  `bulletin_number: str?`, `observations: list[EpiObservation]`.
- **EpiObservation** — one epidemiological data point: `disease`, `location_name`, `location_level`,
  `epi_week_start?`, `epi_week_end?`, `reference_year?`, `probable_cases?`, `confirmed_cases?`,
  `deaths?`, `incidence_per_100k?`, `data_source?` — belongs to one DocumentAnnotation.
- **Run** — one execution over a Task grid. `run_id: str` (UTC timestamp + config hash), owns a
  config snapshot, an audit log, and the annotation files.
- **AuditEntry** — one attempt of one Task: `timestamp`, `run_id`, `document`, `model`, `status`,
  `attempt`, `latency_ms`, `input_tokens`, `output_tokens`, `est_cost`, `error?` — appended to
  `log.jsonl`.

## Assumptions & open questions

- **Assumption:** Plain extracted text carries enough of the surveillance numbers for a meaningful
  model comparison; data only present in figures/images is accepted as out of reach for this phase.
- **Assumption:** Each bulletin's text fits within the chosen models' context windows after the
  configured `max_chars` truncation; whole-document (no chunking) is sufficient for the first build.
- **Assumption:** Document identity is the PDF filename stem, which is unique within and across the
  input folders in `data/raw/`.
- **Assumption:** Default comparison set is OpenAI + Anthropic + Google models named in `config.yml`;
  exact model ids are a config choice, not a spec commitment.

## Success criteria

- One command runs the full `(documents × models)` grid and, on success, leaves one schema-valid
  annotation file per task plus a complete `log.jsonl`.
- Killing the process mid-run and resuming yields a final result identical to an uninterrupted run,
  with no completed task redone.
- Switching the model list or input folder requires editing only `config.yml`.
- A reviewer can open a run directory and reconstruct exactly what was run, against which inputs, with
  what per-attempt cost and latency, and read every model's structured output.
- A new contributor can read the source top to bottom and explain the data flow without assistance.
