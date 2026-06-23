import subprocess
import sys


def run_tests() -> None:
    """Entry point for `uv run test` — forwards any extra args to pytest.

    e.g. `uv run test`, `uv run test -k fingerprint`, `uv run test tests/test_config.py`.
    """
    completed = subprocess.run(["pytest", *sys.argv[1:]])
    sys.exit(completed.returncode)
