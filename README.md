# LLM Epidemiological Bulletin Annotation

Extract structured arbovirus surveillance data (dengue, chikungunya, zika, yellow fever) from
Brazilian Ministry of Health *Boletins Epidemiológicos* (PDF, Portuguese) using LLMs, and do it
across several models so their annotation quality can be compared. Built for an academic paper, so
**every run is fully tracked and resumable** and every result is a transparent, schema-valid file.

> **Status:** design phase. The design docs below fully specify the system; the code is generated
> from them. Start at [`docs/spec.md`](docs/spec.md).

## How it works

For every `(document, model)` pair the pipeline extracts the PDF's text, asks the model — through
[`instructor`](https://python.useinstructor.com/) — to fill a fixed [Pydantic](https://docs.pydantic.dev)
schema, validates the result, and writes it to disk alongside an append-only audit log. A crashed run
resumes and finishes only the missing pairs.

```
PDF ─▶ extract text ─▶ LLM (schema-enforced) ─▶ validated annotation JSON + audit log
```

## Design docs (read in this order)

| Doc | What it covers |
|-----|----------------|
| [`docs/spec.md`](docs/spec.md) | WHAT & WHY — requirements (EARS), domain entities, success criteria. |
| [`docs/plan.md`](docs/plan.md) | HOW — tech choices, architecture, the schema, the `config.yml` contract, tracking & resume design. |
| [`docs/tasks.md`](docs/tasks.md) | Ordered, verifiable build tasks for an implementer/agent. |
| [`coding-philosophy` skill](.claude/skills/coding-philosophy/SKILL.md) | **Binding** coding & testing standard — how every line must be written. |

## Quick start (once the pipeline is built)

```bash
uv sync                              # install
cp .env.example .env                 # then add your API keys
$EDITOR config.yml                   # choose input folders and the models to compare

uv run epi-annotate run              # run the full documents × models grid
uv run epi-annotate status <run_id>  # done / failed / pending
uv run epi-annotate resume <run_id>  # finish a crashed/partial run
uv run epi-annotate list-runs        # list past runs
```

API keys live only in `.env` (gitignored) — never in `config.yml`.

## Configuration

Everything is set in [`config.yml`](docs/plan.md#configyml-contract-authoritative): input folders, the
PDF extractor, the list of models to compare (OpenAI / Anthropic / Google), retries, concurrency, and
the prompt path. Changing the experiment never means changing code. See plan.md for the full contract.

## Where results go

```
outputs/runs/<run_id>/
  config.snapshot.yml                 # the exact config this run used (frozen)
  prompt.snapshot.md                  # the exact prompt this run used (frozen)
  log.jsonl                           # append-only: one line per attempt (status, tokens, cost, latency)
  annotations/<model>/<document>.json # one validated annotation per successful task
```

A run directory is self-contained: it alone documents what was run, against which inputs, at what cost,
with what output. `run_id` is a UTC timestamp plus a hash of the config.

## Data

Input PDFs live under `data/raw/` (`golden_standard_base/`, `dengue_related/`, `not_dengue_related/`);
download bookkeeping is in `data/raw/manifest.csv`. Acquisition is already done and is out of scope for
this pipeline.

## Out of scope (this phase)

The quality-comparison study itself — agreement metrics, scoring against the golden standard, figures —
is a later phase. This pipeline produces the clean, comparable annotations that study will consume.
