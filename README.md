# LLM Epidemiological Bulletin Annotation

> **Status:** working. 250 PDFs extracted, 112 pre-cached. Two models annotated one bulletin with two prompt versions; outputs are below.

Extract structured arbovirus surveillance signals (dengue, chikungunya, zika) from Brazilian Ministry
of Health *Boletins Epidemiológicos* (PDF, Portuguese) using LLMs, and run multiple models so their
annotation quality can be compared. Built for an academic paper — every run is fully tracked and
resumable, every result is a transparent, schema-valid file.

## How it works

For every `(document, model)` pair the pipeline extracts the PDF's text, asks the model — through
[`instructor`](https://python.useinstructor.com/) — to fill a fixed [Pydantic](https://docs.pydantic.dev)
schema, validates the result, and writes it to disk alongside an append-only audit log. A crashed run
resumes and finishes only the missing pairs.

```
PDF ─▶ extract text ─▶ LLM (schema-enforced) ─▶ validated annotation JSON + audit log
```

## Quick start

```bash
uv sync                              # install
cp .env.example .env                 # add your API keys
$EDITOR config.yml                   # choose input folders and the models to compare

uv run epi-annotate extract          # extract text from all PDFs
uv run epi-annotate demo <TEXT_FILE> --model gpt-4.1-mini  # annotate one document
uv run epi-annotate run              # run the full documents × models grid (T-009, in progress)
```

API keys live only in `.env` (gitignored) — never in `config.yml`.

## Schema

The annotation schema has four typed sections — national level, by-territory, serotypes, and actions:

```
DocumentAnnotation
  reference_year        int | null
  publication_date      str | null          # MM/YYYY
  diseases_in_focus     list[Disease]       # dengue | chikungunya | zika

  national              list[NationalSignal]
    disease             Disease
    trend               Trend               # queda | normal | alta
    concern             Concern             # baixa | normal | alta | muito_alta

  by_territory          list[TerritorySignal]
    territory           str                 # region, state (UF), or city
    disease             Disease
    trend               Trend
    concern             Concern

  serotypes             list[SerotypeSignal]
    territory           str
    serotype            Serotype            # DENV-1 | DENV-2 | DENV-3 | DENV-4
    trend               Trend

  actions               list[ActionSignal]
    territory           str
    actions             list[Intervention]  # vacinacao | controle_vetorial | mobilizacao | …
```

## Sample output

Running `epi-annotate demo` on *Boletim Epidemiológico SVS nº 20 (2021)* with prompt v2:

```json
{
  "document_id": "boletim_epidemiologico_svs_20",
  "model": "gpt-4.1-mini",
  "prompt_version": "v2",
  "prompt_sha256": "cc51d64d…",
  "annotation": {
    "reference_year": 2021,
    "publication_date": "05/2021",
    "diseases_in_focus": ["dengue", "chikungunya", "zika"],
    "national": [
      {"disease": "dengue",      "trend": "queda", "concern": "normal"},
      {"disease": "chikungunya", "trend": "queda", "concern": "normal"},
      {"disease": "zika",        "trend": "queda", "concern": "normal"}
    ],
    "by_territory": [
      {"territory": "Acre",         "disease": "dengue",      "trend": "alta", "concern": "alta"},
      {"territory": "Amazonas",     "disease": "dengue",      "trend": "alta", "concern": "alta"},
      {"territory": "São Paulo",    "disease": "chikungunya", "trend": "alta", "concern": "alta"},
      {"territory": "Minas Gerais", "disease": "chikungunya", "trend": "alta", "concern": "alta"}
    ],
    "serotypes": [
      {"territory": "Norte",     "serotype": "DENV-1", "trend": "alta"},
      {"territory": "Sudeste",   "serotype": "DENV-1", "trend": "alta"},
      {"territory": "Sul",       "serotype": "DENV-1", "trend": "alta"},
      {"territory": "Nordeste",  "serotype": "DENV-2", "trend": "alta"},
      {"territory": "Centro-Oeste", "serotype": "DENV-2", "trend": "alta"}
    ],
    "actions": [
      {"territory": "Brasil", "actions": ["intensificacao_vigilancia", "controle_vetorial", "mobilizacao"]},
      {"territory": "Acre",   "actions": ["intensificacao_vigilancia", "controle_vetorial", "mobilizacao"]}
    ]
  }
}
```

## Where models agree and where they diverge

Same document (*Boletim SVS nº 20, 2021*), same prompt (v2), two models:

| Field | gpt-4.1-mini | gemini-flash-lite | Agreement |
|---|---|---|---|
| reference_year | 2021 | 2021 | ✓ |
| publication_date | 05/2021 | 05/2021 | ✓ |
| diseases_in_focus | dengue, chikungunya, zika | dengue, chikungunya, zika | ✓ |
| dengue Brasil trend | queda | queda | ✓ |
| SP chikungunya trend + concern | alta / alta | alta / alta | ✓ |
| Acre dengue concern | **alta** | **normal** | ✗ |
| MG chikungunya concern | **alta** | **normal** | ✗ |
| Serotype granularity | regional (5 macro-regions) | state-level (14 states) | ✗ |
| Brasil actions | intensificacao + controle + mobilizacao | intensificacao_vigilancia only | ✗ |

The concern-level disagreements on Acre and Minas Gerais — and the serotype aggregation mismatch —
are exactly the inter-annotator gaps the pipeline is built to surface and study.

## Configuration

Everything is set in [`config.yml`](config.yml): input folders, the PDF extractor, models, retries,
concurrency, and the active prompt version. Changing the experiment never means changing code. Current
setup runs three models (gpt-4.1-mini, claude-sonnet-4-6, gemini-2.5-flash-lite) with prompt v2 active.

## Where results go

```
outputs/runs/<run_id>/
  config.snapshot.yml                 # the exact config this run used (frozen)
  prompt.snapshot.md                  # the exact prompt this run used (frozen)
  log.jsonl                           # append-only: one line per attempt (status, tokens, latency)
  annotations/<model>/<document>.json # one validated annotation per successful task
```

A run directory is self-contained: it alone documents what was run, against which inputs, at what cost,
with what output. `run_id` is a UTC timestamp plus a hash of the config.

## Data

250 PDFs across three folders under `data/raw/`: `golden_standard_base/`, `dengue_related/`,
`not_dengue_related/`. 112 documents already have pre-extracted text under
`outputs/extract/cache/text/`. Acquisition is done and out of scope for this pipeline.

## Design docs

| Doc | What it covers |
|-----|----------------|
| [`docs/spec.md`](docs/spec.md) | WHAT & WHY — requirements, domain entities, success criteria. |
| [`docs/plan.md`](docs/plan.md) | HOW — tech choices, architecture, schema, `config.yml` contract, tracking & resume design. |
| [`docs/tasks.md`](docs/tasks.md) | Ordered, verifiable build tasks. |
| [`coding-philosophy` skill](.claude/skills/coding-philosophy/SKILL.md) | **Binding** coding & testing standard. |

## Out of scope (this phase)

The quality-comparison study — agreement metrics, scoring against the golden standard, figures — is a
later phase. This pipeline produces the clean, comparable annotations that study will consume.
