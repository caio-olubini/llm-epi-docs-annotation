# CLAUDE.md — epi-annotation project context

## What this project does

Runs a grid of LLM models over a set of Brazilian epidemiological bulletins (PDFs), extracts
structured annotation data from each, and writes validated JSON outputs. The pipeline is
config-driven, crash-safe, and resumable.

## Stack

- **Runtime:** Python 3.12, managed with `uv`
- **LLM interface:** `instructor` (unified `response_model=` across providers)
- **Schema / validation:** Pydantic v2
- **Config:** `pyyaml` + Pydantic model (`config.yml`)
- **PDF extraction:** PyMuPDF (primary), `pdftotext` CLI (fallback)
- **Retries / backoff:** `tenacity`
- **Concurrency:** `ThreadPoolExecutor` (I/O-bound API calls)
- **CLI:** `argparse` — entrypoint `epi-annotate`
- **Tests:** `pytest`

## Source layout

```
src/epi_annotation/
  __init__.py
  cli.py          # argparse entrypoint — all subcommands
  config.py       # Config Pydantic model, load_config(), discover_documents()
  schema.py       # Disease/Trend/Concern/Serotype/Intervention enums, NationalSignal,
                  #   TerritorySignal, SerotypeSignal, ActionSignal, DocumentAnnotation
  extract.py      # extract_text() — PyMuPDF/pdftotext + cache
  models.py       # build_client() — instructor-wrapped OpenAI-compatible clients
  annotate.py     # annotate() → AnnotateResult (annotation + token usage)
  fingerprint.py  # fingerprint_prompt() → PromptFingerprint (version + path + sha256)
  _tasks.py       # run_tests() — backs the `uv run test` script
  prompts/
    system.md     # v1 — original PT-BR system prompt
    system_v2.md  # v2 — refined signal/noise calibration + 3 few-shot examples
    system_v3.md  # v3 (active) — full schema prose + 4 richer few-shot examples (EXAMPLE INPUT/OUTPUT)
  # ledger.py     (T-007, pending)
  # runner.py     (T-008, pending)
tests/
  test_schema.py
  test_config.py
  test_extract.py
  test_models.py
  test_annotate.py
  test_fingerprint.py
```

## Implemented tasks

| Task | Status | What it built |
|---|---|---|
| T-001 | done | `pyproject.toml`, package scaffold, CLI stub |
| T-002 | done | `schema.py` — annotation contract |
| T-003 | done | `config.py` — Config model + `load_config` + `discover_documents` |
| T-004 | done | `extract.py` — PDF extraction + cache; `extract` CLI subcommand |
| T-005 | done | `models.py` — `build_client` for OpenAI-compatible providers (openai, anthropic, google, deepseek, deepinfra) |
| T-006 | done | `annotate.py` — `annotate()` + `system.md` prompt |
| T-007 | pending | `ledger.py` — run dirs, atomic writes, resume logic |
| T-008 | pending | `runner.py` — grid execution, concurrency, continue-on-failure |
| T-009 | pending | remaining CLI subcommands: `run`, `resume`, `status`, `list-runs` |
| T-010 | pending | trust-critical path tests (ledger, resume) |
| T-011 | pending | README |

## Running tests

```bash
uv run test                      # whole suite
uv run test -k fingerprint       # extra args forward to pytest
uv run test tests/test_config.py
```

`test` is a project script backed by `_tasks.py:run_tests`, which shells out to `pytest`
and forwards any arguments.

## CLI subcommands

```bash
uv run epi-annotate --help

# Extract text from all PDFs in config data_dirs
uv run epi-annotate extract [--config config.yml] [--out-dir outputs/extract]

# Annotate a single pre-extracted text file (for manual testing / demos)
uv run epi-annotate demo <TEXT_FILE> [--config config.yml] [--model NAME] [--prompt VERSION] [--out-dir outputs/demo]

# Full pipeline (T-009, not yet implemented)
uv run epi-annotate run
uv run epi-annotate resume <run_id>
uv run epi-annotate status <run_id>
uv run epi-annotate list-runs
```

### `demo` usage example

```bash
uv run epi-annotate demo \
  outputs/extract/cache/text/boletim_epidemiologico_svs_20.txt \
  --model claude-sonnet \
  --prompt v1 \
  --out-dir outputs/demo
```

Output: `outputs/demo/boletim_epidemiologico_svs_20__claude-sonnet__v1.json`

The output is a record wrapping the annotation with its provenance:

```json
{
  "document_id": "boletim_epidemiologico_svs_20",
  "model": "claude-sonnet",
  "prompt_version": "v1",
  "prompt_path": "src/epi_annotation/prompts/system.md",
  "prompt_sha256": "…",
  "annotation": { /* DocumentAnnotation */ }
}
```

## Prompt versioning

Prompts are named in `config.yml` under `prompt.versions` (name → path); `prompt.active`
selects which one a run uses. `load_config` rejects an `active` that names no known version.

```yaml
prompt:
  active: v3
  versions:
    v1: src/epi_annotation/prompts/system.md
    v2: src/epi_annotation/prompts/system_v2.md
    v3: src/epi_annotation/prompts/system_v3.md
```

`fingerprint.py:fingerprint_prompt(version, path)` returns the version name, path, and a
sha256 of the prompt **content** — so editing a prompt in place without renaming the version
is still detectable when comparing outputs. Every annotation output carries this fingerprint.
`demo --prompt VERSION` overrides `prompt.active` for one-off comparisons.

## Model config (`ModelCfg`)

Each entry under `models:` in `config.yml` accepts these fields:

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | str | yes | Friendly name used in output filenames and logs |
| `provider` | str | yes | `openai` · `anthropic` · `google` · `deepseek` · `deepinfra` |
| `model_id` | str | yes | Exact model string sent to the API |
| `temperature` | float | no (default 0) | |
| `mode` | str | **yes** | `instructor.Mode` value (e.g. `tools_strict`, `json_mode`, `json_schema_mode`). `build_client` exits with a clear error if absent or invalid. |
| `max_tokens` | int | no | Passed as `max_tokens=` to the completion call when set; omit to use provider default. |
| `input_cost_per_1k` | float | no | For cost accounting (not yet used by runner) |
| `output_cost_per_1k` | float | no | For cost accounting (not yet used by runner) |

All providers are reached via an `openai.OpenAI` client with `base_url` swapped — one code path,
no per-provider SDK. `PROVIDER_BASE_URL` and `PROVIDER_KEY_ENV` in `models.py` are the only
place to add a new provider.

## Key invariants (don't break these)

- **Annotation provenance is wrapper metadata, never in `DocumentAnnotation`** — `prompt_version`
  / `prompt_sha256` etc. live in the output record around the annotation, never as schema fields,
  so they are pipeline-known facts and are never sent to or filled by the model.

- **"Done" is defined by the validated output file**, never by the log alone (`ledger.is_done`
  re-parses the JSON into `DocumentAnnotation`). A corrupt file means not done.
- **Atomic writes only** — `atomic_write_json` uses a temp file + `os.replace` so a crash
  mid-write never leaves a partial file that `is_done` would silently accept.
- **Provider code lives only in `models.py`** — `annotate.py` and `runner.py` are provider-agnostic.
- **API keys come from env / `.env` only** — never from `config.yml` or any artifact on disk.
- **Resume loads `config.snapshot.yml`**, not the live `config.yml`, so editing config between
  runs does not silently change a resumed experiment.

## Run-dir layout (once T-007 is done)

```
outputs/runs/<run_id>/
  config.snapshot.yml
  prompt.snapshot.md
  log.jsonl
  cache/text/<document>.txt
  annotations/<model>/<document>.json
```

`run_id = "<UTC YYYYMMDD-HHMMSS>-<sha256[:8] of config snapshot>"`

## Coding standard

All code follows `.claude/skills/coding-philosophy/SKILL.md` — binding for every contribution.
Short version: simplicity over cleverness, names over comments, tests guard failure modes not
happy paths, no abstraction before the second use.

## Data

PDFs live in `data/raw/golden_standard_base/`. Pre-extracted text cache is at
`outputs/extract/cache/text/` (produced by `epi-annotate extract`).

## Secrets

Copy `.env.example` → `.env` and fill in the keys you need:

```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_KEY=
DEEPINFRA_KEY=
```

Only the providers you actually use need a key.
