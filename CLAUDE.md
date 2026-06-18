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
  schema.py       # Disease/LocationLevel enums, EpiObservation, DocumentAnnotation
  extract.py      # extract_text() — PyMuPDF/pdftotext + cache
  models.py       # build_client() — instructor-wrapped OpenAI/Anthropic/Google clients
  annotate.py     # annotate() → AnnotateResult (annotation + token usage)
  prompts/
    system.md     # Portuguese system prompt sent to every model
  # ledger.py     (T-007, pending)
  # runner.py     (T-008, pending)
tests/
  test_schema.py
  test_config.py
  test_extract.py
  test_models.py
  test_annotate.py
```

## Implemented tasks

| Task | Status | What it built |
|---|---|---|
| T-001 | done | `pyproject.toml`, package scaffold, CLI stub |
| T-002 | done | `schema.py` — annotation contract |
| T-003 | done | `config.py` — Config model + `load_config` + `discover_documents` |
| T-004 | done | `extract.py` — PDF extraction + cache; `extract` CLI subcommand |
| T-005 | done | `models.py` — `build_client` for OpenAI / Anthropic / Google |
| T-006 | done | `annotate.py` — `annotate()` + `system.md` prompt |
| T-007 | pending | `ledger.py` — run dirs, atomic writes, resume logic |
| T-008 | pending | `runner.py` — grid execution, concurrency, continue-on-failure |
| T-009 | pending | remaining CLI subcommands: `run`, `resume`, `status`, `list-runs` |
| T-010 | pending | trust-critical path tests (ledger, resume) |
| T-011 | pending | README |

## CLI subcommands

```bash
uv run epi-annotate --help

# Extract text from all PDFs in config data_dirs
uv run epi-annotate extract [--config config.yml] [--out-dir outputs/extract]

# Annotate a single pre-extracted text file (for manual testing / demos)
uv run epi-annotate demo <TEXT_FILE> [--config config.yml] [--model NAME] [--out-dir outputs/demo]

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
  --out-dir outputs/demo
```

Output: `outputs/demo/boletim_epidemiologico_svs_20__claude-sonnet.json`

## Key invariants (don't break these)

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
```

Only the providers you actually use need a key.
