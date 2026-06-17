import argparse
import sys


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

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Subcommand implementations live here once runner and ledger are built (T-008, T-009).
    print(f"Command '{args.command}' is not yet implemented.")
    sys.exit(1)
