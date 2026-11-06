"""The Git root may live in an outer *directory*, not an outer checkout."""
from __future__ import annotations

from pathlib import Path
import pytest

from gf_wordbench.entrypoints.gui.workspace_layout import (
    workspace_from_repository,
    sibling_from_repository,
)

ROOT = Path(__file__).resolve().parents[2]


def test_checkout_is_self_contained() -> None:
    assert not (ROOT / "GF_Wordbench").exists()
    assert (ROOT / "pyproject.toml").is_file()
    assert (ROOT / "src/gf_wordbench/practical/batch.py").is_file()
    assert (ROOT / "Qualification_Langues_Utiles.pyw").is_file()


def test_real_nested_git_checkout_resolves_correct_compiler(tmp_path: Path) -> None:
    checkout = tmp_path / "GF_Wordbench" / "GF_Wordbench"
    checkout.mkdir(parents=True)
    assert workspace_from_repository(checkout) == tmp_path.resolve()
    assert sibling_from_repository(checkout, "gf-3.12-windows") == tmp_path / "gf-3.12-windows"
    assert sibling_from_repository(checkout, "gf-rgl") == tmp_path / "gf-rgl"


def test_portable_flat_checkout_also_resolves(tmp_path: Path) -> None:
    checkout = tmp_path / "GF_Wordbench"
    checkout.mkdir()
    assert workspace_from_repository(checkout) == tmp_path.resolve()


@pytest.mark.parametrize("invalid", ["", ".", "..", "../gf-rgl", "sub/dir", r"sub\dir"])
def test_sibling_rejects_traversal(tmp_path: Path, invalid: str) -> None:
    with pytest.raises(ValueError):
        sibling_from_repository(tmp_path / "GF_Wordbench" / "GF_Wordbench", invalid)


def test_workspace_argument_type_is_checked() -> None:
    with pytest.raises(TypeError):
        workspace_from_repository("GF_Wordbench")  # type: ignore[arg-type]
