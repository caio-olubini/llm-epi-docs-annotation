# Tasks: LLM Epidemiological Bulletin Annotation Pipeline

> Implements: spec.md + plan.md · Last updated: 2026-06-15

Ordered units of work. Execute top to bottom, respecting dependencies. Each task names the
requirements and files it needs so it can be done without rereading the whole design. Keep modules
small and obvious (spec NFR: legibility > cleverness).

**Before writing any code or test, invoke the `coding-philosophy` skill
([`.claude/skills/coding-philosophy/SKILL.md`](../.claude/skills/coding-philosophy/SKILL.md)) — it is
binding.** Each task's **Accept** is the minimum bar; the philosophy's code- and test-review
checklists are the quality bar.

Status legend: `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked

---

## T-001 — Project scaffold (uv app + entrypoint)
- **Status:** [x]
- **Satisfies:** REQ-012
- **Depends on:** —
- **Files:** `pyproject.toml`, `src/epi_annotation/__init__.py`, `.gitignore`, `.env.example`
- **Do:** Create a `uv` project named `epi-annotation`, Python 3.12, with runtime deps
  (`instructor`, `pydantic`, `pyyaml`, `python-dotenv`, `pymupdf`, `tenacity`, `rich`, `openai`,
  `anthropic`, `google-generativeai`) and dev dep `pytest`. Declare console script
  `epi-annotate = "epi_annotation.cli:main"`. `.gitignore` excludes `.env`, `outputs/`, `__pycache__`,
  `.venv`. `.env.example` lists `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`.
- **Accept:** `uv sync` succeeds and `uv run epi-annotate --help` runs (even if it only prints usage).

## T-002 — Annotation schema (the contract)
- **Status:** [x]
- **Satisfies:** REQ-004, REQ-004a
- **Depends on:** T-001
- **Files:** `src/epi_annotation/schema.py`
- **Do:** Implement `Disease`, `LocationLevel` enums, `EpiObservation`, `DocumentAnnotation` exactly as
  in plan.md "Annotation schema", with Portuguese `Field(description=...)` on every field. Only
  `disease`, `location_name`, `location_level`, `diseases_covered`, `observations` are required.
- **Accept:** `pytest` test parses a hand-written sample dict (with some null fields) into
  `DocumentAnnotation` successfully, and a dict missing `disease` in an observation raises
  `ValidationError`.

## T-003 — Config model + loader
- **Status:** [x]
- **Satisfies:** REQ-001
- **Depends on:** T-001
- **Files:** `src/epi_annotation/config.py`, `config.yml`
- **Do:** Define `Config` and sub-models (`InputCfg`, `PdfCfg`, `ModelCfg`, `RunCfg`, `PromptCfg`) per
  plan.md interfaces, with defaults (`glob="*.pdf"`, `temperature=0.0`, `max_retries=3`,
  `concurrency=4`, `output_dir="outputs/runs"`). Implement `load_config(path)` (YAML → `Config`,
  validation errors surface the offending field). Implement `discover_documents(cfg)` returning
  `Document` records from `data_dirs` + `glob`. Write a starter `config.yml` matching plan.md.
- **Accept:** `load_config("config.yml")` returns a populated `Config`; a config with a bad type exits
  with a message naming the field; `discover_documents` finds the PDFs in
  `data/raw/golden_standard_base`.

## T-004 — PDF text extraction with cache
- **Status:** [x]
- **Satisfies:** REQ-003
- **Depends on:** T-003
- **Files:** `src/epi_annotation/extract.py`
- **Do:** Implement `extract_text(doc, cfg, run_dir)`: if cached text exists under
  `run_dir/cache/text/<document>.txt` return it; else extract via PyMuPDF (or `pdftotext` when
  `extractor == "pdftotext"`), truncate to `max_chars` if set, write the cache, return text. Raise a
  clear error if extracted text is empty.
- **Accept:** Running on one real bulletin PDF returns non-empty text and creates the cache file; a
  second call reads from cache (no re-extraction); empty-text input raises a descriptive error.

## T-005 — Provider client factory
- **Status:** [ ]
- **Satisfies:** REQ-002, REQ-005
- **Depends on:** T-003
- **Files:** `src/epi_annotation/models.py`
- **Do:** Implement `PROVIDER_KEY_ENV` and `build_client(model_cfg)` returning an `instructor`-wrapped
  client for `openai` / `anthropic` / `google`. Read the API key from the mapped env var (load `.env`
  via dotenv at startup); raise a clear "missing credential for <provider>" error if unset. This is the
  only module that imports provider SDKs.
- **Accept:** With a key set, `build_client` returns a usable client for each provider; with the key
  unset, it raises the named error and never logs the key value.

## T-006 — Annotate one document with one model
- **Status:** [ ]
- **Satisfies:** REQ-004, REQ-005, REQ-007
- **Depends on:** T-002, T-005
- **Files:** `src/epi_annotation/annotate.py`, `src/epi_annotation/prompts/system.md`
- **Do:** Write `system.md` (Portuguese instructions: extract structured arbovirus surveillance data
  into the schema, leave unknown fields null, do not invent values). Implement
  `annotate(text, model_cfg, system_prompt) -> AnnotateResult` calling
  `client.chat.completions.create(response_model=DocumentAnnotation, max_retries=...,
  temperature=model_cfg.temperature, ...)` and returning the validated annotation plus token usage.
- **Accept:** Given sample text and a configured model (or a mocked instructor client in tests),
  `annotate` returns an `AnnotateResult` whose `.annotation` is a valid `DocumentAnnotation`.

## T-007 — Ledger: run dirs, atomic writes, append-only log, done-check
- **Status:** [ ]
- **Satisfies:** REQ-008, REQ-009, REQ-010, REQ-011
- **Depends on:** T-003
- **Files:** `src/epi_annotation/ledger.py`
- **Do:** Implement `new_run_dir(cfg)` (build `run_id`, create dirs, write `config.snapshot.yml` and
  `prompt.snapshot.md`), `resolve_run_dir`, `load_snapshot`, `atomic_write_json` (temp + `os.replace`),
  `append_log` (append + flush), `is_done(run_dir, document_id, model_name)` (output file exists AND
  re-parses into `DocumentAnnotation`), and `status_counts(run_dir, cfg)`.
- **Accept:** `pytest` test: `atomic_write_json` then `is_done` returns True; a truncated/garbage output
  file makes `is_done` return False; `append_log` produces valid JSONL lines; `status_counts` returns
  done/failed/pending/total consistent with files + log.

## T-008 — Runner: grid, resume, concurrency, continue-on-failure
- **Status:** [ ]
- **Satisfies:** REQ-006, REQ-007, REQ-010
- **Depends on:** T-004, T-006, T-007
- **Files:** `src/epi_annotation/runner.py`
- **Do:** Implement `run(cfg, run_dir=None)`. If `run_dir is None`, create a new run; else resume
  (load snapshot config). Build the `documents × models` grid; skip tasks where `is_done` is True;
  execute the rest on a `ThreadPoolExecutor(max_workers=cfg.run.concurrency)`. Per task: extract text,
  `annotate` with bounded retries/backoff (`tenacity`), on success `atomic_write_json` then `append_log`
  status `done` (with latency/tokens/est_cost), on final failure `append_log` status `failed` and
  continue. Print a `rich` summary at the end. Compute `est_cost` from configured per-1k rates when
  present.
- **Accept:** A run over a small grid (can mock `annotate`) writes one annotation per task and a
  complete `log.jsonl`; injecting a failure for one task leaves all others done and the process exits
  reporting counts; killing mid-run then calling `run(cfg, run_dir=<that run>)` completes only the
  missing tasks and touches no existing output.

## T-009 — CLI commands
- **Status:** [ ]
- **Satisfies:** REQ-012, REQ-011
- **Depends on:** T-008
- **Files:** `src/epi_annotation/cli.py`
- **Do:** Implement `main()` with subcommands: `run` (load config → `runner.run(cfg)`),
  `resume <run_id>` (resolve dir → `runner.run(cfg, run_dir)`), `status <run_id>` (print
  `status_counts`), `list-runs` (list run dirs under `output_dir`, newest first). Clear exit codes.
- **Accept:** `uv run epi-annotate run|resume <id>|status <id>|list-runs` each perform their function;
  `status` prints done/failed/pending matching disk.

## T-010 — Tests for the trust-critical paths
- **Status:** [ ]
- **Satisfies:** REQ-009, REQ-010, REQ-004
- **Depends on:** T-002, T-007, T-008
- **Files:** `tests/test_schema.py`, `tests/test_ledger.py`, `tests/test_resume.py`,
  `tests/test_extract.py`
- **Do:** Cover: schema validation (valid/invalid), atomic write + `is_done` (incl. corrupt file),
  resume skips done and redoes pending and is identical to an uninterrupted run (with `annotate`
  mocked), and a real-PDF extraction smoke test (skipped if no sample PDF available).
- **Accept:** `uv run pytest` passes locally with no network/API keys required (provider calls mocked).

## T-011 — README and run-through docs
- **Status:** [ ]
- **Satisfies:** REQ-012 (usability)
- **Depends on:** T-009
- **Files:** `README.md`
- **Do:** Ensure `README.md` reflects the final CLI and config: install (`uv sync`), set up `.env`,
  edit `config.yml`, `uv run epi-annotate run`, resume, status, where outputs land.
- **Accept:** Following the README from scratch produces a run directory with annotations (given valid
  API keys), or a precise credential error if keys are absent.

---

## Execution notes

- Work in order; before each task read the REQs and the plan sections it references.
- After each task run its **Accept** check, then set status to `[x]`.
- Keep provider-specific code inside `models.py` only (REQ-005); keep "done" defined by the validated
  output file, never by the log (REQ-009/010).
- If a task can't be done as written, set `[!]`, state why, and stop — update spec/plan first, don't
  improvise scope.
