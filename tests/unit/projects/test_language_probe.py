"""Unit tests for path-resolved GF language probing."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from gf_wordbench.projects.languages.models import (
    LanguageCapability,
    LanguageProbeRequest,
    LanguageProbeResult,
    LanguageProbeSeverity,
    LanguageProbeStatus,
    LanguageResolutionSource,
    SelectedPathKind,
)
from gf_wordbench.projects.languages.probe import (
    LanguageProbeService,
    probe_language_path,
)


def _write_gf(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"-- test fixture for {path.stem}\n",
        encoding="utf-8",
    )
    return path.resolve()


def _make_rgl_language(
    tmp_path: Path,
    *,
    relative_language: str = "english",
    modules: tuple[str, ...] = (
        "LangEng.gf",
        "GrammarEng.gf",
        "AllEng.gf",
        "AdjectiveEng.gf",
    ),
) -> tuple[Path, Path, Path, tuple[Path, ...]]:
    rgl_root = (tmp_path / "gf-rgl").resolve()
    source_root = rgl_root / "src"
    for shared in ("abstract", "api", "common", "prelude"):
        (source_root / shared).mkdir(parents=True, exist_ok=True)

    language_directory = source_root.joinpath(*Path(relative_language).parts)
    language_directory.mkdir(parents=True, exist_ok=True)
    files = tuple(_write_gf(language_directory / module) for module in modules)
    return rgl_root, source_root, language_directory.resolve(), files


def _diagnostic_codes(result: LanguageProbeResult) -> tuple[str, ...]:
    diagnostics = result.diagnostics
    return tuple(diagnostic.code for diagnostic in diagnostics)


class _RecordingSourceSelector:
    """Minimal source-inventory test double for the projects-layer port."""

    def __init__(self, selected: tuple[Path, ...]) -> None:
        self._selected = selected
        self.calls: list[tuple[Path, Path, int]] = []

    def select_source_tree(
        self,
        source_root: Path,
        *,
        containment_root: Path,
        max_files: int = 0,
    ) -> tuple[tuple[Path, ...], tuple[object, ...]]:
        self.calls.append((source_root, containment_root, max_files))
        selected = self._selected
        if max_files:
            selected = selected[:max_files]
        return selected, ()


def test_directory_selection_resolves_standard_language_context(
    tmp_path: Path,
) -> None:
    rgl_root, source_root, language_directory, _files = _make_rgl_language(tmp_path)

    result = probe_language_path(language_directory)

    assert result.status is LanguageProbeStatus.RESOLVED
    assert result.resolved is True
    assert result.context is not None

    context = result.context
    assert context.language_key == "english"
    assert context.display_name == "english"
    assert context.selected_path == language_directory
    assert context.selected_path_kind is SelectedPathKind.DIRECTORY
    assert context.language_directory == language_directory
    assert context.rgl_source_root == source_root
    assert context.rgl_root == rgl_root
    assert context.selected_file is None
    assert context.focused_target is None
    assert context.module_suffix == "Eng"
    assert context.module_suffix_candidates == ("Eng",)
    assert tuple(path.name for path in context.entrypoint_paths) == (
        "LangEng.gf",
        "GrammarEng.gf",
        "AllEng.gf",
    )
    assert tuple(path.name for path in context.source_inventory) == (
        "AdjectiveEng.gf",
        "AllEng.gf",
        "GrammarEng.gf",
        "LangEng.gf",
    )
    assert context.gf_path_requirements == (
        language_directory,
        source_root / "abstract",
        source_root / "api",
        source_root / "common",
        source_root / "prelude",
    )
    source_capability = context.capability(LanguageCapability.SOURCE_READY)
    scan_capability = context.capability(LanguageCapability.SCAN_READY)
    assert source_capability is not None
    assert source_capability.available is True
    assert scan_capability is not None
    assert scan_capability.available is True

    provenance_sources = {item.source for item in context.resolution_provenance}
    assert {
        LanguageResolutionSource.EXPLICIT_SELECTED_PATH,
        LanguageResolutionSource.LANGUAGE_PROBE,
        LanguageResolutionSource.MODULE_CLASSIFICATION,
    } <= provenance_sources


def test_selected_gf_file_remains_the_focused_target(
    tmp_path: Path,
) -> None:
    _rgl_root, _source_root, language_directory, _files = _make_rgl_language(tmp_path)
    focused = language_directory / "AdjectiveEng.gf"

    result = probe_language_path(focused)

    assert result.status is LanguageProbeStatus.RESOLVED
    assert result.context is not None
    assert result.context.selected_path_kind is SelectedPathKind.FILE
    assert result.context.selected_path == focused
    assert result.context.selected_file == focused
    assert result.context.focused_target == focused
    assert focused in result.context.source_inventory
    assert tuple(path.name for path in result.context.entrypoint_paths) == (
        "LangEng.gf",
        "GrammarEng.gf",
        "AllEng.gf",
    )


def test_probe_does_not_require_project_toml_catalog_or_language_bundle(
    tmp_path: Path,
) -> None:
    rgl_root, _source_root, language_directory, _files = _make_rgl_language(tmp_path)

    assert not (rgl_root / "project" / "project.toml").exists()
    assert not (rgl_root / "rgl-language-catalog.json").exists()
    assert not (rgl_root / "wordbench" / "languages").exists()

    result = probe_language_path(language_directory)

    assert result.status is LanguageProbeStatus.RESOLVED


@pytest.mark.parametrize("explicit_kind", ["repository", "source"])
def test_explicit_rgl_root_accepts_repository_or_source_root(
    tmp_path: Path,
    explicit_kind: str,
) -> None:
    rgl_root, source_root, language_directory, _files = _make_rgl_language(tmp_path)
    explicit_root = rgl_root if explicit_kind == "repository" else source_root

    result = probe_language_path(
        language_directory,
        explicit_rgl_root=explicit_root,
    )

    assert result.status is LanguageProbeStatus.RESOLVED
    assert result.context is not None
    assert result.context.rgl_root == rgl_root
    assert result.context.rgl_source_root == source_root
    provenance_sources = {item.source for item in result.context.resolution_provenance}
    assert LanguageResolutionSource.EXPLICIT_RGL_ROOT in provenance_sources


def test_missing_selected_path_is_rejected(tmp_path: Path) -> None:
    missing = (tmp_path / "gf-rgl" / "src" / "english").resolve()

    result = probe_language_path(missing)

    assert result.status is LanguageProbeStatus.INVALID_SELECTION
    assert result.context is None
    assert result.resolved is False
    assert _diagnostic_codes(result) == ("GF-WB-PATH-250",)
    assert result.diagnostics[0].severity is LanguageProbeSeverity.ERROR


def test_non_gf_file_is_rejected(tmp_path: Path) -> None:
    _rgl_root, _source_root, language_directory, _files = _make_rgl_language(tmp_path)
    selected = language_directory / "README.md"
    selected.write_text("not GF\n", encoding="utf-8")

    result = probe_language_path(selected)

    assert result.status is LanguageProbeStatus.INVALID_SELECTION
    assert result.context is None
    assert _diagnostic_codes(result) == ("GF-WB-CONFIG-254",)


def test_invalid_gf_filename_is_rejected(tmp_path: Path) -> None:
    _rgl_root, _source_root, language_directory, _files = _make_rgl_language(tmp_path)
    selected = _write_gf(language_directory / "bad-name.gf")

    result = probe_language_path(selected)

    assert result.status is LanguageProbeStatus.INVALID_SELECTION
    assert _diagnostic_codes(result) == ("GF-WB-CONFIG-255",)


def test_language_outside_supported_src_layout_is_rejected(
    tmp_path: Path,
) -> None:
    language_directory = (tmp_path / "workspace" / "english").resolve()
    _write_gf(language_directory / "LangEng.gf")

    result = probe_language_path(language_directory)

    assert result.status is LanguageProbeStatus.UNSUPPORTED_LAYOUT
    assert result.context is None
    assert _diagnostic_codes(result) == ("GF-WB-PATH-253",)


def test_empty_language_directory_is_rejected(tmp_path: Path) -> None:
    _rgl_root, _source_root, language_directory, _files = _make_rgl_language(
        tmp_path,
        modules=(),
    )

    result = probe_language_path(language_directory)

    assert result.status is LanguageProbeStatus.INVALID_SELECTION
    assert result.context is None
    assert _diagnostic_codes(result) == ("GF-WB-CONFIG-251",)


def test_language_without_standard_roles_remains_source_ready(
    tmp_path: Path,
) -> None:
    _rgl_root, _source_root, language_directory, _files = _make_rgl_language(
        tmp_path,
        modules=("CustomModule.gf", "AnotherModule.gf"),
    )

    result = probe_language_path(language_directory)

    assert result.status is LanguageProbeStatus.RESOLVED
    assert result.context is not None
    assert result.context.module_suffix is None
    assert result.context.module_suffix_candidates == ()
    assert result.context.entrypoint_paths == ()
    source_capability = result.context.capability(LanguageCapability.SOURCE_READY)
    scan_capability = result.context.capability(LanguageCapability.SCAN_READY)
    assert source_capability is not None
    assert source_capability.available is True
    assert scan_capability is not None
    assert scan_capability.available is True
    assert _diagnostic_codes(result) == (
        "GF-WB-CONFIG-259",
        "GF-WB-CONFIG-253",
    )


def test_ambiguous_suffix_is_reported_without_blocking_source_use(
    tmp_path: Path,
) -> None:
    _rgl_root, _source_root, language_directory, _files = _make_rgl_language(
        tmp_path,
        modules=(
            "LangEng.gf",
            "GrammarEng.gf",
            "LangFre.gf",
            "GrammarFre.gf",
        ),
    )

    result = probe_language_path(language_directory)

    assert result.status is LanguageProbeStatus.RESOLVED
    assert result.context is not None
    assert result.context.module_suffix is None
    assert result.context.module_suffix_candidates == ("Eng", "Fre")
    assert _diagnostic_codes(result) == ("GF-WB-CONFIG-260",)
    assert result.diagnostics[0].severity is LanguageProbeSeverity.WARNING
    assert result.diagnostics[0].candidates == ("Eng", "Fre")


def test_required_unambiguous_suffix_returns_explicit_choices(
    tmp_path: Path,
) -> None:
    _rgl_root, _source_root, language_directory, _files = _make_rgl_language(
        tmp_path,
        modules=(
            "LangEng.gf",
            "GrammarEng.gf",
            "LangFre.gf",
            "GrammarFre.gf",
        ),
    )

    result = probe_language_path(
        language_directory,
        require_unambiguous_suffix=True,
    )

    assert result.status is LanguageProbeStatus.NEEDS_USER_INPUT
    assert result.context is None
    assert tuple(choice.value for choice in result.choices) == ("Eng", "Fre")
    assert tuple(tuple(path.name for path in choice.entrypoints) for choice in result.choices) == (
        ("LangEng.gf", "GrammarEng.gf"),
        ("LangFre.gf", "GrammarFre.gf"),
    )
    assert _diagnostic_codes(result) == ("GF-WB-CONFIG-260",)


def test_focused_standard_file_disambiguates_multiple_suffixes(
    tmp_path: Path,
) -> None:
    _rgl_root, _source_root, language_directory, _files = _make_rgl_language(
        tmp_path,
        modules=(
            "LangEng.gf",
            "GrammarEng.gf",
            "LangFre.gf",
            "GrammarFre.gf",
        ),
    )
    focused = language_directory / "LangFre.gf"

    result = probe_language_path(
        focused,
        require_unambiguous_suffix=True,
    )

    assert result.status is LanguageProbeStatus.RESOLVED
    assert result.context is not None
    assert result.context.module_suffix == "Fre"
    assert result.context.module_suffix_candidates == ("Eng", "Fre")
    assert tuple(path.name for path in result.context.entrypoint_paths) == (
        "LangFre.gf",
        "GrammarFre.gf",
    )
    assert _diagnostic_codes(result) == ("GF-WB-CONFIG-257",)


def test_source_limit_is_delegated_and_deterministic(tmp_path: Path) -> None:
    _rgl_root, _source_root, language_directory, _files = _make_rgl_language(
        tmp_path,
        modules=(
            "ZuluEng.gf",
            "AlphaEng.gf",
            "MiddleEng.gf",
        ),
    )

    result = probe_language_path(
        language_directory,
        max_source_files=2,
    )

    assert result.status is LanguageProbeStatus.RESOLVED
    assert result.context is not None
    assert tuple(path.name for path in result.context.source_inventory) == (
        "AlphaEng.gf",
        "MiddleEng.gf",
    )


def test_probe_delegates_inventory_to_injected_source_selector(
    tmp_path: Path,
) -> None:
    _rgl_root, source_root, language_directory, files = _make_rgl_language(tmp_path)
    selected = tuple(
        sorted(
            files,
            key=lambda path: (path.name.casefold(), str(path)),
        )
    )
    selector = _RecordingSourceSelector(selected)

    result = LanguageProbeService(source_selector=selector).probe(
        LanguageProbeRequest(selected_path=language_directory)
    )

    assert result.status is LanguageProbeStatus.RESOLVED
    assert result.context is not None
    assert result.context.source_inventory == selected
    assert selector.calls == [(language_directory, language_directory, 0)]


def test_external_language_accepts_explicit_disjoint_rgl_dependency_root(
    tmp_path: Path,
) -> None:
    rgl_root, source_root, _stock_language, _stock_files = _make_rgl_language(
        tmp_path / "dependencies"
    )
    external_language = (
        tmp_path / "external-project" / "GF" / "lib" / "src" / "albanian"
    ).resolve()
    _write_gf(external_language / "LangSqi.gf")
    _write_gf(external_language / "GrammarSqi.gf")
    _write_gf(external_language.parent / "SyntaxSqi.gf")

    result = probe_language_path(
        external_language,
        explicit_rgl_root=rgl_root,
    )

    assert result.status is LanguageProbeStatus.RESOLVED
    assert result.context is not None
    assert result.context.language_directory == external_language
    assert result.context.rgl_root == rgl_root
    assert result.context.rgl_source_root == source_root
    assert result.context.language_key == "albanian"
    assert external_language in result.context.gf_path_requirements
    assert external_language.parent in result.context.gf_path_requirements
    assert source_root / "abstract" in result.context.gf_path_requirements
    assert all(path.is_relative_to(external_language) for path in result.context.source_inventory)


def test_explicit_rgl_root_must_be_a_supported_checkout(tmp_path: Path) -> None:
    external_language = (tmp_path / "external" / "albanian").resolve()
    _write_gf(external_language / "LangSqi.gf")
    unrelated_root = (tmp_path / "not-rgl").resolve()
    unrelated_root.mkdir(parents=True)

    result = probe_language_path(
        external_language,
        explicit_rgl_root=unrelated_root,
    )

    assert result.status is LanguageProbeStatus.UNSUPPORTED_LAYOUT
    assert _diagnostic_codes(result) == ("GF-WB-PATH-252",)


def test_ancestor_search_respects_the_configured_bound(tmp_path: Path) -> None:
    _rgl_root, source_root, language_directory, _files = _make_rgl_language(
        tmp_path,
        relative_language="families/germanic/english",
    )

    too_shallow = probe_language_path(
        language_directory,
        max_ancestor_depth=2,
    )
    sufficient = probe_language_path(
        language_directory,
        max_ancestor_depth=3,
    )

    assert too_shallow.status is LanguageProbeStatus.UNSUPPORTED_LAYOUT
    assert sufficient.status is LanguageProbeStatus.RESOLVED
    assert sufficient.context is not None
    assert sufficient.context.rgl_source_root == source_root
    assert sufficient.context.language_key == "families/germanic/english"


def test_request_rejects_invalid_discovery_limits(tmp_path: Path) -> None:
    selected = (tmp_path / "english").resolve()

    with pytest.raises(ValueError, match="at least 1"):
        LanguageProbeRequest(
            selected_path=selected,
            max_ancestor_depth=0,
        )

    with pytest.raises(ValueError, match="must not be negative"):
        LanguageProbeRequest(
            selected_path=selected,
            max_source_files=-1,
        )

    with pytest.raises(TypeError, match="must be a bool"):
        LanguageProbeRequest(
            selected_path=selected,
            require_unambiguous_suffix=1,  # type: ignore[arg-type]
        )


def test_resolved_context_is_immutable(tmp_path: Path) -> None:
    _rgl_root, _source_root, language_directory, _files = _make_rgl_language(tmp_path)
    result = probe_language_path(language_directory)
    assert result.context is not None

    with pytest.raises(FrozenInstanceError):
        result.context.language_key = "french"  # type: ignore[misc]
