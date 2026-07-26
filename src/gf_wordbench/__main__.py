"""Execute the GF Wordbench command-line interface as a Python module."""

from __future__ import annotations

from gf_wordbench.entrypoints.cli.main import main


if __name__ == "__main__":
    raise SystemExit(main())
