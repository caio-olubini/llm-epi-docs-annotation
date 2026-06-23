import argparse
import json
import sys
from pathlib import Path

from epi_annotation.annotate import annotate
from epi_annotation.config import load_config, discover_documents, ModelCfg
from epi_annotation.extract import extract_text
from epi_annotation.fingerprint import fingerprint_prompt


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="epi-annotate",
        description="LLM epidemiological bulletin annotation pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    subparsers.add_parser("run", help="Start a new annotation run")

    resume_parser = subparsers.add_parser("resume", help="Resume an existing run")
    resume_parser.add_argument("run_id", help="Run ID to resume")

    status_parser = subparsers.add_parser("status", help="Show run status counts")
    status_parser.add_argument("run_id", help="Run ID to inspect")

    subparsers.add_parser("list-runs", help="List all runs newest first")

    demo_parser = subparsers.add_parser(
        "demo",
        help="Annotate a single pre-extracted text file with one model",
    )
    demo_parser.add_argument(
        "text_file",
        metavar="TEXT_FILE",
        help="Path to a pre-extracted .txt file (e.g. outputs/extract/cache/text/bulletin.txt)",
    )
    demo_parser.add_argument(
        "--config", default="config.yml", metavar="PATH",
        help="Config file (default: config.yml)",
    )
    demo_parser.add_argument(
        "--model", default=None, metavar="NAME",
        help="Model name from config to use (default: first model in config)",
    )
    demo_parser.add_argument(
        "--prompt", default=None, metavar="VERSION",
        help="Prompt version from config to use (default: prompt.active in config)",
    )
    demo_parser.add_argument(
        "--out-dir", default="outputs/demo", metavar="DIR",
        help="Directory to write the annotation JSON (default: outputs/demo)",
    )

    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract text from all PDFs and write cache files",
    )
    extract_parser.add_argument(
        "--config", default="config.yml", metavar="PATH",
        help="Config file (default: config.yml)",
    )
    extract_parser.add_argument(
        "--out-dir", default="outputs/extract", metavar="DIR",
        help="Directory to write cache files under (default: outputs/extract)",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "demo":
        _run_demo(args.text_file, args.config, args.model, args.prompt, args.out_dir)
        return

    if args.command == "extract":
        _run_extract(args.config, args.out_dir)
        return

    # Remaining subcommands are implemented in T-008 / T-009.
    print(f"Command '{args.command}' is not yet implemented.")
    sys.exit(1)


def _run_demo(
    text_file: str,
    config_path: str,
    model_name: str | None,
    prompt_version: str | None,
    out_dir: str,
) -> None:
    text_path = Path(text_file)
    if not text_path.exists():
        print(f"Text file not found: {text_file}", file=sys.stderr)
        sys.exit(1)

    cfg = load_config(config_path)
    model_cfg = _select_model(cfg.models, model_name)
    version = prompt_version or cfg.prompt.active
    prompt_path = _select_prompt_path(cfg.prompt.versions, version)
    fingerprint = fingerprint_prompt(version, prompt_path)
    system_prompt = Path(prompt_path).read_text(encoding="utf-8")

    print(f"Document : {text_path.stem}")
    print(f"Model    : {model_cfg.name} ({model_cfg.model_id})")
    print(f"Prompt   : {fingerprint.version} ({fingerprint.sha256[:8]})")
    print(f"Output   : {out_dir}/")
    print()

    text = text_path.read_text(encoding="utf-8")
    result = annotate(text, model_cfg, system_prompt)

    record = {
        "document_id": text_path.stem,
        "model": model_cfg.name,
        "prompt_version": fingerprint.version,
        "prompt_path": fingerprint.path,
        "prompt_sha256": fingerprint.sha256,
        "annotation": result.annotation.model_dump(mode="json"),
    }

    out_path = Path(out_dir) / f"{text_path.stem}__{model_cfg.name}__{fingerprint.version}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Annotation written → {out_path}")
    if result.input_tokens is not None:
        print(f"Tokens: {result.input_tokens} in / {result.output_tokens} out")


def _select_model(models: list[ModelCfg], name: str | None) -> ModelCfg:
    if name is None:
        return models[0]
    for model in models:
        if model.name == name:
            return model
    available = ", ".join(m.name for m in models)
    print(f"Model '{name}' not found in config. Available: {available}", file=sys.stderr)
    sys.exit(1)


def _select_prompt_path(versions: dict[str, str], name: str) -> str:
    if name in versions:
        return versions[name]
    available = ", ".join(versions)
    print(f"Prompt version '{name}' not found in config. Available: {available}", file=sys.stderr)
    sys.exit(1)


def _run_extract(config_path: str, out_dir: str) -> None:
    cfg = load_config(config_path)
    docs = discover_documents(cfg)

    if not docs:
        print("No PDFs found. Check data_dirs and glob in your config.")
        sys.exit(1)

    print(f"Extracting {len(docs)} document(s) → {out_dir}")

    failed = []
    for doc in docs:
        try:
            text = extract_text(doc, cfg, out_dir)
            cache_path = Path(out_dir) / "cache" / "text" / f"{doc.document_id}.txt"
            print(f"  ok  {doc.document_id}  ({len(text):,} chars)  → {cache_path}")
        except Exception as exc:
            print(f"  ERR {doc.document_id}: {exc}", file=sys.stderr)
            failed.append(doc.document_id)

    if failed:
        print(f"\n{len(failed)} extraction(s) failed.", file=sys.stderr)
        sys.exit(1)

    print(f"\nDone. Cache written to {out_dir}/cache/text/")
