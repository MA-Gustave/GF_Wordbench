"""Regression tests for the standalone diagnostic control-panel launcher."""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys


def _load_control_panel(repo_root: Path, monkeypatch):
    diagnostics_root = repo_root / "tools" / "diagnostics"
    monkeypatch.syspath_prepend(str(diagnostics_root))
    loader = SourceFileLoader(
        "gf_wordbench_test_diagnostic_control_panel",
        str(diagnostics_root / "00-control_panel.pyw"),
    )
    spec = spec_from_loader(loader.name, loader)
    assert spec is not None
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_control_panel_logs_adr0015_paths_without_legacy_project_root(
    monkeypatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    module = _load_control_panel(repo_root, monkeypatch)

    class FakeRoot:
        def title(self, _value: str) -> None:
            pass

        def geometry(self, _value: str) -> None:
            pass

        def minsize(self, _width: int, _height: int) -> None:
            pass

    class FakeStringVar:
        def __init__(self, *, value: str) -> None:
            self.value = value

    tkinter = ModuleType("tkinter")
    tkinter.Tk = FakeRoot  # type: ignore[attr-defined]
    tkinter.StringVar = FakeStringVar  # type: ignore[attr-defined]
    tkinter.messagebox = object()  # type: ignore[attr-defined]
    tkinter.ttk = object()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tkinter", tkinter)

    config = SimpleNamespace(
        repo_root=repo_root,
        language_path=None,
        validation_profile=None,
    )
    messages: list[str] = []
    monkeypatch.setattr(module, "load_config", lambda: config)
    monkeypatch.setattr(module.ControlPanel, "_build", lambda self: None)
    monkeypatch.setattr(
        module.ControlPanel,
        "log",
        lambda self, message: messages.append(message),
    )

    module.ControlPanel()

    assert messages == [
        f"Repository: {repo_root}",
        "Language path: not configured",
        "Validation profile: not configured",
    ]


def test_batch_launcher_retries_visibly_after_pythonw_failure() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    launcher = (
        repo_root / "tools" / "diagnostics" / "launch_diagnostics.bat"
    ).read_text(encoding="utf-8")

    assert 'pyw "%~dp0\\00-control_panel.pyw"' in launcher
    assert ":console_fallback" in launcher
    assert 'py "%~dp0\\00-control_panel.pyw"' in launcher
    assert "pause" in launcher
