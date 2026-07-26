"""Run N01 through N04 headlessly, stopping only after all reports are produced."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from diag_core import console_python, detect_repo_root

SCRIPTS = (
    "01-environment.pyw",
    "02-repository_integrity.pyw",
    "03-contracts.pyw",
    "04-runtime_smoke.pyw",
)


def main() -> int:
    suite_root = Path(__file__).resolve().parent
    repo_root = detect_repo_root(suite_root)
    worst = 0
    for filename in SCRIPTS:
        script = suite_root / filename
        print(f"\n=== {filename} ===", flush=True)
        completed = subprocess.run(
            [sys.executable, str(script), "--headless"],
            cwd=str(repo_root),
        )
        worst = max(worst, int(completed.returncode))
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
