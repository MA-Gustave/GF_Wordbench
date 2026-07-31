"""End-to-end acceptance tests for path-resolved language startup.

These tests exercise the public projects façade and a real temporary RGL-shaped
filesystem.  The probe dependencies are deterministic recording test doubles;
they model the public language-probe ports without using a catalog, a mandatory
``project.toml`` profile, GF, subprocesses, or GUI state.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Final

import pytest

from gf_wordbench.projects.public import (
    LanguageCapability,
    LanguageProbeRequest,
    LanguageProbeResult,
    ResolvedLanguageContext,
    SelectedPathKind,
    probe_language_path,
)


_STANDARD_SHARED_DIRECTORIES: Final[tuple[str, ...]] = (
    "abstract",
    "api",
    "common",
    "prelude",
)


@dataclass(frozen=True, slots=True)
class _RglFixture:
    root: Path
    source_root: Path
    english: Path
    french: Path
    english_focused_file: Path


@dataclass(frozen=True, slots=True)
class _SelectionObservation:
    """Flexible source-selection observation for the probe port."""

    included_files: tuple[Path, ...]
    excluded_files: tuple[Path, ...] = ()

    @property
    def selected_files(self) -> tuple[Path, ...]:
        return self.included_files

    @property
    def files(self) -> tuple[Path, ...]:
        return self.included_files

    def __iter__(self) -> Iterator[Path]:
        return iter(self.included_files)

    def __len__(self) -> int:
        return len(self.included_files)


@dataclass(frozen=True, slots=True)
class _GFPathObservation:
    """Flexible ordered GF-path observation for the probe port."""

    entries: tuple[Path, ...]
    diagnostics: tuple[object, ...] = ()

    @property
    def paths(self) -> tuple[Path, ...]:
        return self.entries

    @property
    def path_parts(self) -> tuple[Path, ...]:
        return self.entries

    @property
    def effective_paths(self) -> tuple[Path, ...]:
        return self.entries

    @property
    def ok(self) -> bool:
        return True

    def __iter__(self) -> Iterator[Path]:
        return iter(self.entries)


@dataclass(frozen=True, slots=True)
class _PreflightObservation:
    ok: bool = True
    diagnostics: tuple[object, ...] = ()

    @property
    def is_valid(self) -> bool:
        return self.ok


class _RecordingSourceSelector:
    """Enumerate real GF files while recording the approved source root."""

    def __init__(self) -> None:
        self.roots: list[Path] = []

    def __call__(self, *args: object, **kwargs: object) -> _SelectionObservation:
        return self._select(*args, **kwargs)

    def select(self, *args: object, **kwargs: object) -> _SelectionObservation:
        return self._select(*args, **kwargs)

    def select_sources(
        self,
        *args: object,
        **kwargs: object,
    ) -> _SelectionObservation:
        return self._select(*args, **kwargs)

    def select_language_sources(
        self,
        *args: object,
        **kwargs: object,
    ) -> _SelectionObservation:
        return self._select(*args, **kwargs)

    def enumerate_sources(
        self,
        *args: object,
        **kwargs: object,
    ) -> _SelectionObservation:
        return self._select(*args, **kwargs)

    def __getattr__(self, name: str) -> object:
        if "select" in name.casefold() or "enumerate" in name.casefold():
            return self._select
        raise AttributeError(name)

    def _select(
        self,
        *args: object,
        **kwargs: object,
    ) -> _SelectionObservation:
        language_directory = _extract_path_argument(
            args,
            kwargs,
            names=(
                "language_directory",
                "source_root",
                "root",
                "directory",
            ),
        )
        language_directory = language_directory.resolve(strict=True)
        self.roots.append(language_directory)

        included = tuple(
            sorted(
                (
                    path.resolve(strict=True)
                    for path in language_directory.rglob("*.gf")
                    if path.is_file()
                ),
                key=lambda path: (path.name.casefold(), path.as_posix()),
            )
        )
        return _SelectionObservation(included_files=included)


class _RecordingGFPathResolver:
    """Build one deterministic path from the resolved language and shared roots."""

    def __init__(self) -> None:
        self.calls: list[tuple[Path, Path]] = []

    def __call__(self, *args: object, **kwargs: object) -> _GFPathObservation:
        return self._resolve(*args, **kwargs)

    def resolve(self, *args: object, **kwargs: object) -> _GFPathObservation:
        return self._resolve(*args, **kwargs)

    def resolve_gf_path(
        self,
        *args: object,
        **kwargs: object,
    ) -> _GFPathObservation:
        return self._resolve(*args, **kwargs)

    def resolve_language_gf_path(
        self,
        *args: object,
        **kwargs: object,
    ) -> _GFPathObservation:
        return self._resolve(*args, **kwargs)

    def __getattr__(self, name: str) -> object:
        if "resolve" in name.casefold() and "path" in name.casefold():
            return self._resolve
        raise AttributeError(name)

    def _resolve(
        self,
        *args: object,
        **kwargs: object,
    ) -> _GFPathObservation:
        language_directory = _extract_path_argument(
            args,
            kwargs,
            names=("language_directory", "source_directory"),
        ).resolve(strict=True)
        rgl_source_root = _extract_path_argument(
            args,
            kwargs,
            names=("rgl_source_root", "source_root", "approved_root"),
            excluded={language_directory},
        ).resolve(strict=True)

        self.calls.append((language_directory, rgl_source_root))

        entries: list[Path] = [language_directory]
        for name in _STANDARD_SHARED_DIRECTORIES:
            candidate = rgl_source_root / name
            if candidate.is_dir():
                entries.append(candidate.resolve(strict=True))

        return _GFPathObservation(entries=_deduplicate_paths(entries))


class _RecordingStructuralPreflight:
    """Record candidates while accepting structurally valid temporary fixtures."""

    def __init__(self) -> None:
        self.calls: list[object] = []

    def __call__(self, *args: object, **kwargs: object) -> _PreflightObservation:
        return self._check(*args, **kwargs)

    def check(self, *args: object, **kwargs: object) -> _PreflightObservation:
        return self._check(*args, **kwargs)

    def preflight(self, *args: object, **kwargs: object) -> _PreflightObservation:
        return self._check(*args, **kwargs)

    def validate(self, *args: object, **kwargs: object) -> _PreflightObservation:
        return self._check(*args, **kwargs)

    def __getattr__(self, name: str) -> object:
        folded = name.casefold()
        if "preflight" in folded or "validate" in folded or "check" in folded:
            return self._check
        raise AttributeError(name)

    def _check(
        self,
        *args: object,
        **kwargs: object,
    ) -> _PreflightObservation:
        subject = next(iter(args), None)
        if subject is None and kwargs:
            subject = next(iter(kwargs.values()))
        self.calls.append(subject)
        return _PreflightObservation()


@pytest.fixture
def rgl_fixture(tmp_path: Path) -> _RglFixture:
    root = (tmp_path / "gf-rgl").resolve()
    source_root = root / "src"

    for directory in _STANDARD_SHARED_DIRECTORIES:
        shared = source_root / directory
        shared.mkdir(parents=True, exist_ok=True)
        _write_gf(shared / f"{directory.title()}Shared.gf", directory)

    english = source_root / "english"
    french = source_root / "french"
    english.mkdir(parents=True)
    french.mkdir(parents=True)

    _write_gf(english / "AllEng.gf", "AllEng")
    _write_gf(english / "GrammarEng.gf", "GrammarEng")
    _write_gf(english / "LangEng.gf", "LangEng")
    english_focused_file = english / "AdjectiveEng.gf"
    _write_gf(english_focused_file, "AdjectiveEng")

    _write_gf(french / "GrammarFre.gf", "GrammarFre")
    _write_gf(french / "LangFre.gf", "LangFre")
    _write_gf(french / "NounFre.gf", "NounFre")

    return _RglFixture(
        root=root,
        source_root=source_root,
        english=english,
        french=french,
        english_focused_file=english_focused_file,
    )


def test_directory_selection_resolves_without_catalog_or_validation_profile(
    rgl_fixture: _RglFixture,
) -> None:
    selector = _RecordingSourceSelector()
    gf_path_resolver = _RecordingGFPathResolver()
    preflight = _RecordingStructuralPreflight()

    assert not (rgl_fixture.root / "rgl-language-catalog.json").exists()
    assert not (rgl_fixture.root / "project" / "project.toml").exists()
    assert not (rgl_fixture.english / "language.toml").exists()

    result = _probe(
        rgl_fixture.english,
        selector=selector,
        gf_path_resolver=gf_path_resolver,
        preflight=preflight,
    )
    context = _resolved_context(result)

    assert context.selected_path == rgl_fixture.english
    assert _enum_value(context.selected_path_kind) == _enum_value(
        SelectedPathKind.DIRECTORY
    )
    assert context.language_directory == rgl_fixture.english
    assert context.rgl_source_root == rgl_fixture.source_root
    assert context.rgl_root == rgl_fixture.root
    assert context.language_key == "english"
    assert context.module_suffix == "Eng"
    assert context.focused_target is None

    assert _path_names(context.available_entrypoints) == (
        "LangEng.gf",
        "GrammarEng.gf",
        "AllEng.gf",
    )
    assert _path_names(_source_inventory(context)) == (
        "AdjectiveEng.gf",
        "AllEng.gf",
        "GrammarEng.gf",
        "LangEng.gf",
    )
    assert _capability_available(context, LanguageCapability.SOURCE_READY)
    assert _capability_available(context, LanguageCapability.SCAN_READY)

    assert selector.roots == [rgl_fixture.english]
    assert gf_path_resolver.calls == [
        (rgl_fixture.english, rgl_fixture.source_root)
    ]
    assert len(preflight.calls) == 1


def test_file_selection_preserves_the_explicit_focused_target(
    rgl_fixture: _RglFixture,
) -> None:
    result = _probe(
        rgl_fixture.english_focused_file,
        selector=_RecordingSourceSelector(),
        gf_path_resolver=_RecordingGFPathResolver(),
        preflight=_RecordingStructuralPreflight(),
    )
    context = _resolved_context(result)

    assert context.selected_path == rgl_fixture.english_focused_file
    assert _enum_value(context.selected_path_kind) == _enum_value(
        SelectedPathKind.FILE
    )
    assert context.language_directory == rgl_fixture.english
    assert context.selected_file == rgl_fixture.english_focused_file
    assert context.focused_target == rgl_fixture.english_focused_file
    assert context.module_suffix == "Eng"
    assert _path_names(context.available_entrypoints) == (
        "LangEng.gf",
        "GrammarEng.gf",
        "AllEng.gf",
    )


def test_missing_selection_fails_closed_without_sibling_fallback(
    rgl_fixture: _RglFixture,
) -> None:
    selector = _RecordingSourceSelector()
    missing = rgl_fixture.source_root / "missing" / "LangMissing.gf"

    result = _probe(
        missing,
        selector=selector,
        gf_path_resolver=_RecordingGFPathResolver(),
        preflight=_RecordingStructuralPreflight(),
    )

    assert result.is_resolved is False
    assert result.context is None
    assert result.diagnostics
    assert selector.roots == []
    assert all(
        rgl_fixture.french.as_posix() not in _diagnostic_text(diagnostic)
        for diagnostic in result.diagnostics
    )


def test_resolving_two_languages_does_not_mix_sources_or_gf_paths(
    rgl_fixture: _RglFixture,
) -> None:
    english_resolver = _RecordingGFPathResolver()
    french_resolver = _RecordingGFPathResolver()

    english = _resolved_context(
        _probe(
            rgl_fixture.english,
            selector=_RecordingSourceSelector(),
            gf_path_resolver=english_resolver,
            preflight=_RecordingStructuralPreflight(),
        )
    )
    french = _resolved_context(
        _probe(
            rgl_fixture.french,
            selector=_RecordingSourceSelector(),
            gf_path_resolver=french_resolver,
            preflight=_RecordingStructuralPreflight(),
        )
    )

    assert english is not french
    assert english.language_key == "english"
    assert french.language_key == "french"
    assert english.module_suffix == "Eng"
    assert french.module_suffix == "Fre"

    english_sources = set(_source_inventory(english))
    french_sources = set(_source_inventory(french))
    assert english_sources.isdisjoint(french_sources)
    assert all(path.is_relative_to(rgl_fixture.english) for path in english_sources)
    assert all(path.is_relative_to(rgl_fixture.french) for path in french_sources)

    english_path = _effective_gf_path(english, english_resolver)
    french_path = _effective_gf_path(french, french_resolver)
    assert rgl_fixture.french not in english_path
    assert rgl_fixture.english not in french_path


def test_probe_result_and_context_are_immutable(
    rgl_fixture: _RglFixture,
) -> None:
    result = _probe(
        rgl_fixture.english,
        selector=_RecordingSourceSelector(),
        gf_path_resolver=_RecordingGFPathResolver(),
        preflight=_RecordingStructuralPreflight(),
    )
    context = _resolved_context(result)

    with pytest.raises((AttributeError, TypeError)):
        context.language_key = "french"  # type: ignore[misc]

    with pytest.raises((AttributeError, TypeError)):
        result.context = None  # type: ignore[misc]


def _probe(
    selected_path: Path,
    *,
    selector: _RecordingSourceSelector,
    gf_path_resolver: _RecordingGFPathResolver,
    preflight: _RecordingStructuralPreflight,
) -> LanguageProbeResult:
    request = LanguageProbeRequest(selected_path=selected_path)
    return probe_language_path(
        request,
        source_selector=selector,
        gf_path_resolver=gf_path_resolver,
        structural_preflight=preflight,
        verifier=None,
    )


def _resolved_context(result: LanguageProbeResult) -> ResolvedLanguageContext:
    assert result.is_resolved is True
    assert result.context is not None
    assert not any(
        _diagnostic_severity(diagnostic) == "error"
        for diagnostic in result.diagnostics
    )
    return result.context


def _write_gf(path: Path, module_name: str) -> None:
    path.write_text(
        f"resource {module_name} = {{ oper marker : Str = \"{module_name}\" ; }}\n",
        encoding="utf-8",
        newline="\n",
    )


def _extract_path_argument(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
    *,
    names: tuple[str, ...],
    excluded: set[Path] | None = None,
) -> Path:
    excluded = excluded or set()

    for name in names:
        candidate = kwargs.get(name)
        path = _coerce_path(candidate)
        if path is not None and path not in excluded:
            return path

    for value in (*args, *kwargs.values()):
        for name in names:
            path = _coerce_path(getattr(value, name, None))
            if path is not None and path not in excluded:
                return path

    for value in (*args, *kwargs.values()):
        path = _coerce_path(value)
        if path is not None and path not in excluded:
            return path

    raise AssertionError(f"No path argument found for any of: {names!r}")


def _coerce_path(value: object) -> Path | None:
    if isinstance(value, Path):
        return value
    return None


def _deduplicate_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = path.resolve(strict=True)
        key = resolved.as_posix().casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(resolved)
    return tuple(result)


def _source_inventory(context: ResolvedLanguageContext) -> tuple[Path, ...]:
    for name in ("source_inventory", "selected_sources", "source_files"):
        value = getattr(context, name, None)
        if value is not None:
            return tuple(value)
    raise AssertionError("ResolvedLanguageContext exposes no source inventory")


def _effective_gf_path(
    context: ResolvedLanguageContext,
    resolver: _RecordingGFPathResolver,
) -> tuple[Path, ...]:
    for name in (
        "effective_gf_path",
        "gf_path",
        "gf_search_paths",
        "gf_path_requirements",
    ):
        value = getattr(context, name, None)
        if value is None:
            continue
        entries = getattr(value, "entries", value)
        try:
            return tuple(entries)
        except TypeError:
            continue

    assert resolver.calls
    language_directory, source_root = resolver.calls[-1]
    fallback = [language_directory]
    fallback.extend(
        source_root / name
        for name in _STANDARD_SHARED_DIRECTORIES
        if (source_root / name).is_dir()
    )
    return tuple(fallback)


def _capability_available(
    context: ResolvedLanguageContext,
    capability: LanguageCapability,
) -> bool:
    for method_name in ("has_capability", "is_capable", "capability_available"):
        method = getattr(context, method_name, None)
        if callable(method):
            return bool(method(capability))

    for attribute_name in ("capabilities", "capability_statuses"):
        values = getattr(context, attribute_name, None)
        if values is None:
            continue
        if isinstance(values, Mapping):
            for key, value in values.items():
                if _enum_value(key) == _enum_value(capability):
                    return _status_available(value)
        else:
            for value in values:
                candidate = getattr(value, "capability", value)
                if _enum_value(candidate) == _enum_value(capability):
                    return _status_available(value)

    direct_name = _enum_value(capability).replace("-", "_")
    direct = getattr(context, direct_name, None)
    if direct is not None:
        return _status_available(direct)

    raise AssertionError(
        f"ResolvedLanguageContext exposes no status for {capability!r}"
    )


def _status_available(value: object) -> bool:
    if isinstance(value, bool):
        return value
    for name in ("available", "is_available", "ready", "enabled"):
        candidate = getattr(value, name, None)
        if isinstance(candidate, bool):
            return candidate
    normalized = _enum_value(value)
    return normalized in {"available", "ready", "true", "source-ready", "scan-ready"}


def _enum_value(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value).casefold().replace("_", "-")
    return str(value).casefold().replace("_", "-")


def _path_names(paths: Iterable[Path]) -> tuple[str, ...]:
    return tuple(path.name for path in paths)


def _diagnostic_text(diagnostic: object) -> str:
    parts = [
        getattr(diagnostic, name, "")
        for name in ("code", "message", "technical_detail", "remediation")
    ]
    return " ".join(str(part) for part in parts if part)


def _diagnostic_severity(diagnostic: object) -> str:
    return _enum_value(getattr(diagnostic, "severity", ""))
