# Plan: LLM Epidemiological Bulletin Annotation Pipeline

> Implements: spec.md · Last updated: 2026-06-15

This plan answers *how* we satisfy the spec. It records decisions and their rationale so a later
change does not quietly undo a deliberate choice. Requirements are referenced by ID, not restated.

## Tech stack & key decisions

| Decision | Choice | Rationale |
|---|---|---|
| Language / runtime | Python 3.12 | Available locally (3.12.7); first-class `instructor`/provider SDK support. |
| Env & packaging | `uv` + `pyproject.toml` | Required. Fast, reproducible lockfile; provides the `epi-annotate` console script. |
| LLM interface | `instructor` | One unified `response_model=` call across OpenAI/Anthropic/Google → satisfies REQ-005 with minimal provider-specific code. |
| Schema / validation | `pydantic` v2 | The annotation contract (REQ-004) and `instructor`'s validation layer are both Pydantic. |
| Config loading | `pyyaml` + `pydantic` model | YAML is human-friendly (REQ-001); a Pydantic config model gives fail-fast validation with field-named errors. |
| Secrets | `.env` + `python-dotenv`, read via `os.environ` | Keys never touch `config.yml` or artifacts (REQ-002). |
| PDF text | `pymupdf` (primary), `pdftotext` CLI (fallback) | PyMuPDF is fast and pip-installable; `pdftotext` already exists on the machine as a fallback (REQ-003). |
| Retries | `tenacity` (or `instructor`'s `max_retries`) | Declarative bounded backoff (REQ-007) without hand-rolled loops. |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` | Tasks are I/O-bound (API calls); threads are simple and obvious — no async complexity for a junior reader. |
| Run records | Plain files: YAML snapshot + JSONL log + JSON outputs | Transparent, diffable, no DB to corrupt; append-only log + atomic writes give trustworthiness (REQ-008/009). |
| CLI | `argparse` (stdlib) or `typer` | A handful of subcommands (REQ-012); stdlib keeps the dependency surface small — `argparse` is the default. |
| Console output | `rich` | Readable progress and a legible status table; cosmetic only. |
| Tests | `pytest` | Schema, resume, and extraction checks (see tasks). |

**Guiding principle (from spec NFRs):** legibility > cleverness. Prefer a longer obvious function over a
short clever one. No metaclasses, no dynamic dispatch, no plugin registries. A reader should be able to
follow one task from PDF to stored JSON by reading files top to bottom. The binding standard for all
code and tests is the `coding-philosophy` skill
([`.claude/skills/coding-philosophy/SKILL.md`](../.claude/skills/coding-philosophy/SKILL.md)).

## Architecture

Data flows in one direction; each module has a single job.

```
config.yml ──▶ config.py ──▶ Config (validated)
                                  │
                                  ▼
                runner.py: build Task grid = documents × models
                                  │  (for each Task, on a thread pool)
                                  ▼
  extract.py ──▶ text ──▶ annotate.py ──▶ models.py (instructor client)
   (+cache)                    │                 │
                               ▼                 ▼
                    DocumentAnnotation     provider API (OpenAI/Anthropic/Google)
                               │
                               ▼
                  ledger.py: atomic write annotations/<model>/<doc>.json
                             + append AuditEntry to log.jsonl
```

- **`config.py`** — load `config.yml`, parse into the `Config` Pydantic model, validate, fail fast
  with field-named errors. Resolves input PDFs from `data_dirs` + `glob`. (REQ-001)
- **`schema.py`** — `Disease`/`LocationLevel` enums, `EpiObservation`, `DocumentAnnotation`. The
  contract; no logic. (REQ-004, REQ-004a)
- **`extract.py`** — `extract_text(document, cfg) -> str`: PyMuPDF or `pdftotext`, apply `max_chars`,
  read/write a text cache under the run dir. Raises a clear error on empty text. (REQ-003)
- **`models.py`** — `build_client(model_cfg) -> instructor client` and the provider→key-env mapping.
  The *only* place provider differences live. Missing key → clear error. (REQ-002, REQ-005)
- **`annotate.py`** — `annotate(text, model_cfg, system_prompt) -> DocumentAnnotation`: build messages,
  call `client.chat.completions.create(response_model=DocumentAnnotation, max_retries=...)`, return
  the validated object plus usage metadata. Provider-agnostic. (REQ-004, REQ-007)
- **`ledger.py`** — run-dir helpers: `run_id` creation, `config.snapshot.yml` + prompt snapshot,
  `atomic_write_json`, `append_log`, `is_done(run_dir, doc, model)` (file exists *and* re-validates),
  and status counting. The trust layer. (REQ-008, REQ-009, REQ-010, REQ-011)
- **`runner.py`** — build the grid, decide new-run vs resume, skip done tasks, dispatch the rest on the
  thread pool with bounded retries, continue on failure, print a summary. (REQ-006, REQ-007, REQ-010)
- **`cli.py`** — `run`, `resume <run_id>`, `status <run_id>`, `list-runs`. Thin; delegates to runner
  and ledger. (REQ-012)

## Data model

### Annotation schema (`schema.py`) — the contract sent to and validated from every model

```python
from enum import Enum
from datetime import date
from pydantic import BaseModel, Field

class Disease(str, Enum):
    dengue = "dengue"
    chikungunya = "chikungunya"
    zika = "zika"
    febre_amarela = "febre_amarela"
    outro = "outro"

class LocationLevel(str, Enum):
    national = "national"
    region = "region"        # e.g. "Centro-Oeste"
    state = "state"          # UF
    municipality = "municipality"

class EpiObservation(BaseModel):
    disease: Disease = Field(description="Doença referida nesta observação.")
    location_name: str = Field(description="Local: 'Brasil', uma região, um estado (UF) ou 'Município/UF'.")
    location_level: LocationLevel = Field(description="Granularidade geográfica do local.")
    epi_week_start: int | None = Field(None, description="Primeira semana epidemiológica (SE) do período, 1–53.")
    epi_week_end: int | None = Field(None, description="Última semana epidemiológica (SE) do período, 1–53.")
    reference_year: int | None = Field(None, description="Ano de referência dos dados.")
    probable_cases: int | None = Field(None, description="Número de casos prováveis.")
    confirmed_cases: int | None = Field(None, description="Número de casos confirmados.")
    deaths: int | None = Field(None, description="Número de óbitos.")
    incidence_per_100k: float | None = Field(None, description="Taxa de incidência por 100 mil habitantes.")
    data_source: str | None = Field(None, description="Fonte dos dados, ex.: 'Sinan On-line', 'Sinan Net'.")

class DocumentAnnotation(BaseModel):
    diseases_covered: list[Disease] = Field(description="Doenças tratadas no boletim.")
    reference_year: int | None = Field(None, description="Ano principal de referência do boletim.")
    publication_date: date | None = Field(None, description="Data de publicação do boletim.")
    bulletin_volume: str | None = Field(None, description="Volume do boletim, ex.: '53'.")
    bulletin_number: str | None = Field(None, description="Número/edição do boletim, ex.: '21'.")
    observations: list[EpiObservation] = Field(default_factory=list, description="Todas as observações epidemiológicas extraídas.")
```

Field descriptions are in Portuguese on purpose: they are sent to the model as part of the schema and
the source documents are Portuguese. Only `disease`, `location_name`, `location_level` (within an
observation) and the two list fields are required — everything else is optional so a model never has to
invent a number it cannot find (REQ-004a).

### On-disk layout of a run

```
outputs/runs/<run_id>/
  config.snapshot.yml                 # frozen Config at run start (reproducibility, resume source)
  prompt.snapshot.md                  # frozen system prompt used by this run
  log.jsonl                           # append-only; one AuditEntry per attempt
  cache/text/<document>.txt           # extracted text cache (REQ-003)
  annotations/<model>/<document>.json # one validated DocumentAnnotation per successful task
```

`run_id = "<UTC YYYYMMDD-HHMMSS>-<first 8 chars of sha256(config.snapshot.yml)>"` — sortable and tied
to the exact config.

### AuditEntry (one JSON object per line in `log.jsonl`)

```
timestamp      str    ISO-8601 UTC
run_id         str
document       str    document_id
model          str    model name
status         str    "done" | "failed"
attempt        int    1-based attempt count when this entry was written
latency_ms     int
input_tokens   int | null
output_tokens  int | null
est_cost       float | null   USD estimate from configured per-token rates (null if unknown)
error          str | null     short message when status == "failed"
```

The log is for audit/metrics only; **"done" is decided by `ledger.is_done`** (the output file exists
and re-parses), never by the log alone — so a crash between writing the file and writing the log line
is self-healing on resume (REQ-009/010).

## Interfaces & contracts

Signatures an implementer builds against.

```python
# config.py
def load_config(path: str = "config.yml") -> Config: ...
class Config(BaseModel):
    input: InputCfg            # data_dirs: list[str]; glob: str = "*.pdf"
    pdf: PdfCfg                # extractor: Literal["pymupdf","pdftotext"]; max_chars: int | None
    models: list[ModelCfg]    # name, provider, model_id, temperature=0.0, max_tokens: int | None,
                              #   input_cost_per_1k: float | None, output_cost_per_1k: float | None
    run: RunCfg               # max_retries: int = 3; concurrency: int = 4; output_dir: str = "outputs/runs"
    prompt: PromptCfg         # active: str; versions: dict[str, str] (name -> path); active must be a known version
def discover_documents(cfg: Config) -> list[Document]: ...   # {document_id, source_dir, path}

# extract.py
def extract_text(doc: Document, cfg: Config, run_dir: str) -> str: ...   # caches under run_dir/cache/text

# models.py
def build_client(model_cfg: ModelCfg): ...                  # instructor-wrapped provider client
PROVIDER_KEY_ENV = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "google": "GOOGLE_API_KEY"}

# annotate.py
@dataclass
class AnnotateResult:
    annotation: DocumentAnnotation
    input_tokens: int | None
    output_tokens: int | None
def annotate(text: str, model_cfg: ModelCfg, system_prompt: str) -> AnnotateResult: ...

# ledger.py
def new_run_dir(cfg: Config) -> str: ...                    # creates dir, writes snapshots, returns path
def resolve_run_dir(run_id: str, cfg: Config) -> str: ...
def load_snapshot(run_dir: str) -> Config: ...
def is_done(run_dir: str, document_id: str, model_name: str) -> bool: ...   # file exists AND re-validates
def atomic_write_json(path: str, obj: dict) -> None: ...    # temp file + os.replace
def append_log(run_dir: str, entry: dict) -> None: ...      # open("a"), write line, flush
def status_counts(run_dir: str, cfg: Config) -> dict: ...   # {done, failed, pending, total}

# runner.py
def run(cfg: Config, run_dir: str | None = None) -> None: ...   # None -> new run; path -> resume

# cli.py  ->  console_scripts entrypoint "epi-annotate"
#   run | resume <run_id> | status <run_id> | list-runs
```

### `config.yml` contract (authoritative)

```yaml
input:
  data_dirs: [data/raw/golden_standard_base]
  glob: "*.pdf"

pdf:
  extractor: pymupdf            # pymupdf | pdftotext
  max_chars: 60000              # null = no limit

models:
  - name: gpt-4o
    provider: openai
    model_id: gpt-4o
    temperature: 0
    max_tokens: 4096
    input_cost_per_1k: 0.005    # optional; enables est_cost
    output_cost_per_1k: 0.015
  - name: claude-sonnet
    provider: anthropic
    model_id: claude-sonnet-4-6
    temperature: 0
  - name: gemini-pro
    provider: google
    model_id: gemini-1.5-pro

run:
  max_retries: 3
  concurrency: 4
  output_dir: outputs/runs

prompt:
  active: v1
  versions:
    v1: src/epi_annotation/prompts/system.md
```

## Dependencies

- **External (runtime):** `instructor`, `pydantic>=2`, `pyyaml`, `python-dotenv`, `pymupdf`,
  `tenacity`, `rich`, `openai`, `anthropic`, `google-generativeai`. Fallback extractor uses the
  system `pdftotext` (poppler-utils), already present.
- **External (dev):** `pytest`.
- **Internal:** none — greenfield. Reads PDFs already under `data/raw/`; does not touch
  `manifest.csv` / `failures.csv`.

## Risks & mitigations

- **Risk:** a model emits malformed structured output. — **Mitigation:** `instructor` re-asks within
  `max_retries`; after the cap the task is failed (REQ-004/007), never written invalid.
- **Risk:** crash between writing an output file and its log line. — **Mitigation:** "done" is defined
  by the validated file, not the log; resume re-derives state from disk (REQ-010).
- **Risk:** corrupt file from a mid-write crash. — **Mitigation:** atomic temp-file + `os.replace`
  (REQ-009).
- **Risk:** provider rate limits on wide grids. — **Mitigation:** bounded backoff (`tenacity`),
  configurable `concurrency`, continue-on-failure so a throttled task is simply retried on resume.
- **Risk:** bulletins exceed context window. — **Mitigation:** `max_chars` truncation now; chunking is
  a noted future extension, deliberately deferred to keep the first build legible.
- **Risk:** provider SDK/model-id drift. — **Mitigation:** model ids live only in `config.yml`;
  provider wiring is isolated to `models.py`.
- **Risk:** silently editing `config.yml` then resuming changes the experiment. — **Mitigation:**
  resume loads `config.snapshot.yml`, not the live file (REQ-010).

## Traceability

| Requirement | Satisfied by |
|---|---|
| REQ-001 Config-driven | `config.py` (`load_config`, `Config`) |
| REQ-002 Secrets via env | `models.py` (`PROVIDER_KEY_ENV`), `.env` + dotenv |
| REQ-003 PDF extraction + cache | `extract.py` |
| REQ-004 / REQ-004a Schema-enforced | `schema.py`, `annotate.py` (`response_model`) |
| REQ-005 Multi-provider unified | `models.py`, `annotate.py` |
| REQ-006 Continue on failure | `runner.py` |
| REQ-007 Bounded retries | `annotate.py` + `tenacity` in `runner.py` |
| REQ-008 Persistent run records | `ledger.py` (snapshots, log), run-dir layout |
| REQ-009 Crash-safe writes | `ledger.py` (`atomic_write_json`) |
| REQ-010 Resume | `runner.py` + `ledger.py` (`is_done`, `load_snapshot`) |
| REQ-011 Status visibility | `ledger.py` (`status_counts`), `cli.py status` |
| REQ-012 CLI surface | `cli.py`, `pyproject.toml` entrypoint |
