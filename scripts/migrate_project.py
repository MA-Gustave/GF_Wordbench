"""Development wrapper for the canonical GF Wordbench project migration command."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

_COMMAND_PREFIX: Final[tuple[str, ...]] = ("project", "migrate")
_SOURCE_DIRECTORY: Final[Path] = Path("src")


def main(argv: Sequence[str] | None = None) -> int:
    """Run ``gf-wordbench project migrate`` with the supplied arguments."""

    arguments = _normalize_arguments(argv)
    _ensure_local_package_importable()

    from gf_wordbench.entrypoints.cli.main import main as cli_main

    return cli_main((*_COMMAND_PREFIX, *arguments))


def _normalize_arguments(argv: Sequence[str] | None) -> tuple[str, ...]:
    if argv is None:
        values = tuple(sys.argv[1:])
    else:
        if isinstance(argv, (str, bytes, bytearray)):
            raise TypeError("argv must be a sequence of strings")
        values = tuple(argv)

    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise TypeError(f"argv[{index}] must be a string")
        if "\x00" in value:
            raise ValueError(f"argv[{index}] must not contain NUL")

    return values


def _ensure_local_package_importable() -> None:
    try:
        __import__("gf_wordbench")
        return
    except ModuleNotFoundError as exc:
        if exc.name != "gf_wordbench":
            raise

    repository_root = Path(__file__).resolve().parent.parent
    source_root = repository_root / _SOURCE_DIRECTORY
    package_root = source_root / "gf_wordbench"

    if not package_root.is_dir():
        raise RuntimeError(
            "GF Wordbench is not installed and the repository source tree "
            f"was not found at {package_root}"
        )

    source_text = str(source_root)
    if source_text not in sys.path:
        sys.path.insert(0, source_text)


if __name__ == "__main__":
    raise SystemExit(main())
