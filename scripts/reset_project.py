"""Thin maintenance entrypoint for the canonical project-reset command."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import sys
from typing import Final

_COMMAND_PREFIX: Final[tuple[str, str]] = ("project", "reset")
_SOURCE_DIRECTORY: Final[str] = "src"
_PACKAGE_DIRECTORY: Final[Path] = Path("gf_wordbench")


def _repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _make_source_checkout_importable() -> None:
    repository_root = _repository_root()
    source_root = repository_root / _SOURCE_DIRECTORY
    package_root = source_root / _PACKAGE_DIRECTORY

    if not package_root.is_dir():
        return

    source_text = str(source_root)
    if source_text not in sys.path:
        sys.path.insert(0, source_text)


def _arguments(argv: Sequence[str] | None) -> tuple[str, ...]:
    values = sys.argv[1:] if argv is None else argv
    result = tuple(values)

    if any(not isinstance(value, str) for value in result):
        raise TypeError("argv must contain only strings")
    if any("\x00" in value for value in result):
        raise ValueError("argv must not contain NUL characters")

    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Run ``gf-wordbench project reset`` and preserve its exact exit code."""

    _make_source_checkout_importable()

    from gf_wordbench.entrypoints.cli.main import main as cli_main

    exit_code = cli_main([*_COMMAND_PREFIX, *_arguments(argv)])
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        raise TypeError("the GF Wordbench CLI main function must return an integer")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
