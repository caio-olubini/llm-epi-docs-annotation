import argparse
import sys
from pathlib import Path

from epi_annotation.config import load_config, discover_documents
from epi_annotation.extract import extract_text


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

    if args.command == "extract":
        _run_extract(args.config, args.out_dir)
        return

    # Remaining subcommands are implemented in T-008 / T-009.
    print(f"Command '{args.command}' is not yet implemented.")
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
