"""Path-resolved language probing for GF Wordbench.

The probe starts from one explicit user-selected GF directory or ``.gf`` file.
It resolves one bounded source context and publishes one immutable language
context for a monolingual Wordbench runtime.

This module owns orchestration only.  Domain contracts live in ``models.py``.
Concrete source-selection adapters may be injected by bootstrap code; the
built-in selector is a bounded read-only fallback for standalone probing.

The probe does not invoke GF, parse GF source syntax, build subprocess commands,
write application state, load an implicit ``project.toml``, or generate reports.
Capability-specific environment and GF validation remain run-configuration and
preflight responsibilities.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from inspect import Parameter, Signature
import os
from pathlib import Path
import re
from typing import Final, Protocol, TypeAlias, runtime_checkable

from gf_wordbench.projects.languages.models import (
    CapabilityAvailability,
    LanguageCandidate,
    LanguageCapability,
    LanguageCapabilityStatus,
    LanguageModuleCandidate,
    LanguageModuleRole,
    LanguageProbeChoice,
    LanguageProbeDiagnostic,
    LanguageProbeRequest,
    LanguageProbeResult,
    LanguageProbeSeverity,
    LanguageProbeStatus,
    LanguageResolutionProvenance,
    LanguageResolutionSource,
    ResolvedLanguageContext,
    SelectedPathKind,
)
from gf_wordbench.projects.languages.ports import (
    LanguageGFPathResolutionPort,
    LanguageSourceSelectionPort,
    LanguageStructuralPreflightPort,
    LanguageVerificationPort,
)

__all__ = (
    "LanguageProbeService",
    "probe_language_path",
)
PathInput: TypeAlias = str | os.PathLike[str]
ModuleNameExtractor: TypeAlias = Callable[[Path], str]

_STANDARD_SOURCE_ROOT_NAME: Final[str] = "src"
_STANDARD_SOURCE_MARKERS: Final[tuple[str, ...]] = (
    "abstract",
    "api",
    "common",
    "prelude",
)
_GF_FILE_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z][A-Za-z0-9_]*\.gf$")
_STANDARD_MODULE_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<role>"
    r"Lang|Grammar|All|Syntax|Lexicon|Paradigms|Morpho|Cat|Noun|Verb|Structural"
    r")(?P<suffix>[A-Z][A-Za-z0-9_]*)$"
)
_ROLE_BY_PREFIX: Final[dict[str, LanguageModuleRole]] = {
    "Lang": LanguageModuleRole.LANG,
    "Grammar": LanguageModuleRole.GRAMMAR,
    "All": LanguageModuleRole.ALL,
    "Syntax": LanguageModuleRole.SYNTAX,
    "Lexicon": LanguageModuleRole.LEXICON,
    "Paradigms": LanguageModuleRole.PARADIGMS,
    "Morpho": LanguageModuleRole.MORPHO,
    "Cat": LanguageModuleRole.CAT,
    "Noun": LanguageModuleRole.NOUN,
    "Verb": LanguageModuleRole.VERB,
    "Structural": LanguageModuleRole.STRUCTURAL,
}
_ENTRYPOINT_ORDER: Final[dict[LanguageModuleRole, int]] = {
    LanguageModuleRole.LANG: 0,
    LanguageModuleRole.GRAMMAR: 1,
    LanguageModuleRole.ALL: 2,
}


@runtime_checkable
class LanguageSourceSelector(Protocol):
    """Return deterministic eligible GF sources beneath one language directory."""

    def select_source_tree(
        self,
        source_root: Path,
        *,
        containment_root: Path,
        max_files: int = 0,
    ) -> tuple[Sequence[Path], Sequence[object]]:
        """Return selected sources and optional exclusion evidence."""
        ...


@runtime_checkable
class LanguageProbeFilesystem(Protocol):
    """Filesystem operations required by the bounded startup probe."""

    def resolve(self, path: Path, *, strict: bool) -> Path: ...

    def exists(self, path: Path) -> bool: ...

    def is_file(self, path: Path) -> bool: ...

    def is_directory(self, path: Path) -> bool: ...

    def is_readable(self, path: Path) -> bool: ...


class _LocalLanguageProbeFilesystem:
    __slots__ = ()

    def resolve(self, path: Path, *, strict: bool) -> Path:
        return path.expanduser().resolve(strict=strict)

    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def is_directory(self, path: Path) -> bool:
        return path.is_dir()

    def is_readable(self, path: Path) -> bool:
        return os.access(path, os.R_OK)


class _LocalLanguageSourceSelector:
    """Bounded read-only fallback used outside composed application startup.

    Production bootstrap code may inject the repository's canonical source
    selection adapter.  This fallback deliberately implements only the narrow
    language-loader requirement: readable ``.gf`` files contained beneath the
    explicitly selected language directory.
    """

    __slots__ = ()

    def select_source_tree(
        self,
        source_root: Path,
        *,
        containment_root: Path,
        max_files: int = 0,
    ) -> tuple[Sequence[Path], Sequence[object]]:
        source_root = source_root.resolve(strict=True)
        containment_root = containment_root.resolve(strict=True)
        if not source_root.is_dir():
            raise ValueError("source_root must be a directory")
        if not source_root.is_relative_to(containment_root):
            raise ValueError("source_root must remain inside containment_root")
        if type(max_files) is not int:
            raise TypeError("max_files must be an integer")
        if max_files < 0:
            raise ValueError("max_files must not be negative")

        selected: list[Path] = []
        pending = [source_root]
        while pending:
            directory = pending.pop()
            children = sorted(directory.iterdir(), key=lambda item: item.name.casefold())
            for child in children:
                if child.is_symlink():
                    continue
                if child.is_dir():
                    pending.append(child)
                    continue
                if not child.name.casefold().endswith(".gf"):
                    continue
                candidate = child.resolve(strict=True)
                if not candidate.is_relative_to(source_root):
                    continue
                if not candidate.is_file() or not os.access(candidate, os.R_OK):
                    continue
                selected.append(candidate)

        selected.sort(key=lambda path: path.relative_to(source_root).as_posix().casefold())
        if max_files:
            selected = selected[:max_files]
        return tuple(selected), ()


_LOCAL_FILESYSTEM: Final[LanguageProbeFilesystem] = _LocalLanguageProbeFilesystem()
_LOCAL_SOURCE_SELECTOR: Final[LanguageSourceSelector] = _LocalLanguageSourceSelector()


@dataclass(frozen=True, slots=True)
class _RootResolution:
    source_root: Path
    repository_root: Path
    provenance: LanguageResolutionSource


@dataclass(frozen=True, slots=True)
class _ModuleClassification:
    candidates: tuple[LanguageModuleCandidate, ...]
    suffixes: tuple[str, ...]
    selected_suffix: str | None
    entrypoints: tuple[LanguageModuleCandidate, ...]
    diagnostics: tuple[LanguageProbeDiagnostic, ...]


@dataclass(frozen=True, slots=True)
class LanguageProbeService:
    """Resolve one explicit path before constructing one monolingual runtime."""

    source_selector: LanguageSourceSelector = field(default=_LOCAL_SOURCE_SELECTOR)
    filesystem: LanguageProbeFilesystem = field(default=_LOCAL_FILESYSTEM)
    module_name_extractor: ModuleNameExtractor = field(default=lambda path: path.stem)
    max_ancestor_depth: int = 12
    max_source_files: int = 0
    require_unambiguous_suffix: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.source_selector, LanguageSourceSelector):
            raise TypeError("source_selector must satisfy LanguageSourceSelector")
        if not isinstance(self.filesystem, LanguageProbeFilesystem):
            raise TypeError("filesystem must satisfy LanguageProbeFilesystem")
        if not callable(self.module_name_extractor):
            raise TypeError("module_name_extractor must be callable")
        _require_positive_int(
            self.max_ancestor_depth,
            field="max_ancestor_depth",
        )
        _require_non_negative_int(
            self.max_source_files,
            field="max_source_files",
        )
        if type(self.require_unambiguous_suffix) is not bool:
            raise TypeError("require_unambiguous_suffix must be a bool")

    def probe(self, request: LanguageProbeRequest) -> LanguageProbeResult:
        """Resolve one selected path into one immutable language context."""

        if not isinstance(request, LanguageProbeRequest):
            raise TypeError("request must be a LanguageProbeRequest")

        try:
            return self._probe(request)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return LanguageProbeResult(
                status=LanguageProbeStatus.INTERNAL_ERROR,
                diagnostics=(
                    _diagnostic(
                        code="GF-WB-INTERNAL-251",
                        severity=LanguageProbeSeverity.ERROR,
                        subject=str(request.selected_path),
                        message="The language probe could not complete.",
                        detail=f"{type(exc).__name__}: {exc}",
                        remediation=(
                            "Review the selected path and the configured language-probe adapters."
                        ),
                        path=request.selected_path,
                    ),
                ),
            )

    def _probe(self, request: LanguageProbeRequest) -> LanguageProbeResult:
        selected = self._resolve_selected_path(request.selected_path)
        if isinstance(selected, LanguageProbeResult):
            return selected
        (
            selected_path,
            selected_kind,
            language_directory,
            focused_target,
        ) = selected

        roots = self._resolve_roots(
            language_directory=language_directory,
            explicit_rgl_root=request.explicit_rgl_root,
        )
        if isinstance(roots, LanguageProbeResult):
            return roots

        inventory_result = self.source_selector.select_source_tree(
            language_directory,
            # The selected language directory is the source-ownership boundary.
            # For an external GF project the RGL dependency root is deliberately
            # disjoint and must never become a containment authority.
            containment_root=language_directory,
            max_files=self.max_source_files,
        )
        inventory = _normalize_inventory(
            inventory_result[0],
            language_directory=language_directory,
        )
        if not inventory:
            return _failure_result(
                status=LanguageProbeStatus.INVALID_SELECTION,
                code="GF-WB-CONFIG-251",
                subject=str(language_directory),
                message=("The selected language directory contains no eligible GF source files."),
                remediation=(
                    "Select a directory containing readable .gf files or "
                    "select one .gf file directly."
                ),
                path=language_directory,
            )
        if focused_target is not None and focused_target not in inventory:
            return _failure_result(
                status=LanguageProbeStatus.INVALID_SELECTION,
                code="GF-WB-CONFIG-252",
                subject=str(focused_target),
                message=(
                    "The explicitly selected GF file was excluded from the "
                    "language source inventory."
                ),
                remediation=("Select an eligible readable .gf file inside the language directory."),
                path=focused_target,
            )

        classification = _classify_modules(
            inventory,
            module_name_extractor=self.module_name_extractor,
            focused_target=focused_target,
            requested_suffix=request.module_suffix_choice,
            requested_entrypoint=request.entrypoint_choice,
            require_unambiguous=self.require_unambiguous_suffix,
        )
        language_key = _language_key(
            language_directory,
            source_root=roots.source_root,
        )
        gf_path_requirements = _gf_path_requirements(
            language_directory,
            source_root=roots.source_root,
            filesystem=self.filesystem,
        )
        candidate = LanguageCandidate(
            selected_path=selected_path,
            selected_path_kind=selected_kind,
            language_directory=language_directory,
            rgl_source_root=roots.source_root,
            rgl_root=roots.repository_root,
            focused_target=focused_target,
            candidate_language_key=language_key,
            module_suffixes=classification.suffixes,
            module_candidates=classification.candidates,
            source_inventory=inventory,
            gf_path_requirements=gf_path_requirements,
            diagnostics=classification.diagnostics,
        )

        if (
            classification.selected_suffix is None
            and len(classification.suffixes) > 1
            and self.require_unambiguous_suffix
        ):
            return LanguageProbeResult(
                status=LanguageProbeStatus.NEEDS_USER_INPUT,
                candidate=candidate,
                diagnostics=classification.diagnostics,
                choices=_module_suffix_choices(
                    classification.suffixes,
                    candidates=classification.candidates,
                ),
            )

        if request.verify_with_gf:
            diagnostic = _diagnostic(
                code="GF-WB-CAPABILITY-251",
                severity=LanguageProbeSeverity.ERROR,
                subject=str(selected_path),
                message=("GF verification is unavailable during language startup."),
                remediation=(
                    "Resolve the language first, then run capability preflight "
                    "through the approved GF execution boundary."
                ),
                path=selected_path,
            )
            return LanguageProbeResult(
                status=LanguageProbeStatus.CAPABILITY_UNAVAILABLE,
                candidate=candidate,
                diagnostics=(*classification.diagnostics, diagnostic),
            )

        context = ResolvedLanguageContext(
            language_key=language_key,
            selected_path=selected_path,
            selected_path_kind=selected_kind,
            language_directory=language_directory,
            rgl_source_root=roots.source_root,
            rgl_root=roots.repository_root,
            focused_target=focused_target,
            module_suffix=classification.selected_suffix,
            available_entrypoints=classification.entrypoints,
            source_inventory=inventory,
            gf_path_requirements=gf_path_requirements,
            structural_diagnostics=classification.diagnostics,
            capability_statuses=_base_capability_statuses(),
            resolution_provenance=_resolution_provenance(
                selected_path=selected_path,
                language_directory=language_directory,
                roots=roots,
                language_key=language_key,
                selected_suffix=classification.selected_suffix,
            ),
        )
        return LanguageProbeResult(
            status=LanguageProbeStatus.RESOLVED,
            candidate=candidate,
            context=context,
            diagnostics=classification.diagnostics,
        )

    def _resolve_selected_path(
        self,
        selected_path: Path,
    ) -> tuple[Path, SelectedPathKind, Path, Path | None] | LanguageProbeResult:
        try:
            resolved = self.filesystem.resolve(selected_path, strict=True)
        except (FileNotFoundError, OSError, RuntimeError) as exc:
            return _failure_result(
                status=LanguageProbeStatus.INVALID_SELECTION,
                code="GF-WB-PATH-250",
                subject=str(selected_path),
                message="The selected language path is not usable.",
                detail=f"{type(exc).__name__}: {exc}",
                remediation=("Select an existing readable language directory or .gf file."),
                path=selected_path,
            )

        if not self.filesystem.exists(resolved):
            return _failure_result(
                status=LanguageProbeStatus.INVALID_SELECTION,
                code="GF-WB-PATH-251",
                subject=str(resolved),
                message="The selected language path does not exist.",
                remediation=("Select an existing readable language directory or .gf file."),
                path=resolved,
            )
        if not self.filesystem.is_readable(resolved):
            return _failure_result(
                status=LanguageProbeStatus.INVALID_SELECTION,
                code="GF-WB-IO-250",
                subject=str(resolved),
                message="The selected language path is not readable.",
                remediation=("Grant read access or select another language path."),
                path=resolved,
            )
        if self.filesystem.is_file(resolved):
            if resolved.suffix.casefold() != ".gf":
                return _failure_result(
                    status=LanguageProbeStatus.INVALID_SELECTION,
                    code="GF-WB-CONFIG-254",
                    subject=str(resolved),
                    message="The selected file is not a .gf source file.",
                    remediation="Select a GF source file ending in .gf.",
                    path=resolved,
                )
            if _GF_FILE_RE.fullmatch(resolved.name) is None:
                return _failure_result(
                    status=LanguageProbeStatus.INVALID_SELECTION,
                    code="GF-WB-CONFIG-255",
                    subject=str(resolved),
                    message=("The selected .gf filename is not a valid module-file candidate."),
                    remediation=(
                        "Select a .gf file whose filename is a valid GF module identifier."
                    ),
                    path=resolved,
                )
            return (
                resolved,
                SelectedPathKind.FILE,
                resolved.parent,
                resolved,
            )
        if self.filesystem.is_directory(resolved):
            return (
                resolved,
                SelectedPathKind.DIRECTORY,
                resolved,
                None,
            )
        return _failure_result(
            status=LanguageProbeStatus.INVALID_SELECTION,
            code="GF-WB-CONFIG-256",
            subject=str(resolved),
            message=("The selected path is neither a regular .gf file nor a directory."),
            remediation=("Select a readable language directory or regular .gf file."),
            path=resolved,
        )

    def _resolve_roots(
        self,
        *,
        language_directory: Path,
        explicit_rgl_root: Path | None,
    ) -> _RootResolution | LanguageProbeResult:
        if explicit_rgl_root is not None:
            explicit = self._resolve_explicit_root(
                explicit_rgl_root,
                language_directory=language_directory,
            )
            if explicit is not None:
                return explicit
            return _failure_result(
                status=LanguageProbeStatus.UNSUPPORTED_LAYOUT,
                code="GF-WB-PATH-252",
                subject=str(explicit_rgl_root),
                message=("The explicit RGL root is not a supported readable RGL checkout."),
                remediation=(
                    "Select the matching gf-rgl repository root or its src directory. "
                    "The language sources may live in a separate external project."
                ),
                path=explicit_rgl_root,
            )

        for depth, ancestor in enumerate(
            language_directory.parents,
            start=1,
        ):
            if depth > self.max_ancestor_depth:
                break
            if ancestor.name.casefold() != _STANDARD_SOURCE_ROOT_NAME:
                continue
            if language_directory == ancestor:
                continue
            if not language_directory.is_relative_to(ancestor):
                continue
            if not self._is_standard_source_root(ancestor):
                continue
            return _RootResolution(
                source_root=ancestor,
                repository_root=ancestor.parent,
                provenance=LanguageResolutionSource.LANGUAGE_PROBE,
            )

        return _failure_result(
            status=LanguageProbeStatus.UNSUPPORTED_LAYOUT,
            code="GF-WB-PATH-253",
            subject=str(language_directory),
            message=("A supported RGL source root could not be derived from the selected path."),
            remediation=("Select a language below <gf-rgl>/src or provide an explicit RGL root."),
            path=language_directory,
        )

    def _resolve_explicit_root(
        self,
        value: Path,
        *,
        language_directory: Path,
    ) -> _RootResolution | None:
        try:
            root = self.filesystem.resolve(value, strict=True)
        except (FileNotFoundError, OSError, RuntimeError):
            return None
        if not self.filesystem.is_directory(root):
            return None
        if not self.filesystem.is_readable(root):
            return None

        candidates: list[tuple[Path, Path]] = []
        if root.name.casefold() == _STANDARD_SOURCE_ROOT_NAME:
            candidates.append((root, root.parent))
        candidates.append((root / _STANDARD_SOURCE_ROOT_NAME, root))

        for source_root, repository_root in candidates:
            try:
                resolved_source = self.filesystem.resolve(
                    source_root,
                    strict=True,
                )
            except (FileNotFoundError, OSError, RuntimeError):
                continue
            if not self.filesystem.is_directory(resolved_source):
                continue
            if not self.filesystem.is_readable(resolved_source):
                continue
            if language_directory == resolved_source:
                continue
            if not self._is_standard_source_root(resolved_source):
                continue
            return _RootResolution(
                source_root=resolved_source,
                repository_root=repository_root.resolve(strict=False),
                provenance=LanguageResolutionSource.EXPLICIT_RGL_ROOT,
            )
        return None

    def _is_standard_source_root(self, source_root: Path) -> bool:
        if self.filesystem.is_file(source_root / "languages.csv"):
            return True
        markers = sum(
            self.filesystem.is_directory(source_root / name) for name in _STANDARD_SOURCE_MARKERS
        )
        return markers >= 2


def probe_language_path(
    request: LanguageProbeRequest | PathInput,
    source_selector: LanguageSourceSelectionPort | LanguageSourceSelector | None = None,
    gf_path_resolver: LanguageGFPathResolutionPort | object | None = None,
    structural_preflight: LanguageStructuralPreflightPort | object | None = None,
    verifier: LanguageVerificationPort | object | None = None,
    **legacy: object,
) -> LanguageProbeResult:
    """Resolve one explicit selection through injected startup ports.

    The five canonical parameters are stable. Legacy keyword-only tuning values
    are accepted temporarily so existing direct probe callers remain source
    compatible while composition roots migrate to ``LanguageProbeRequest``.
    """

    if isinstance(request, LanguageProbeRequest):
        probe_request = request
    else:
        selected = _coerce_path(request, field="selected_path")
        explicit_root_value = legacy.pop("explicit_rgl_root", None)
        entrypoint_value = legacy.pop("entrypoint_choice", None)
        module_suffix_value = legacy.pop("module_suffix_choice", None)
        verify_with_gf_value = legacy.pop("verify_with_gf", False)
        if module_suffix_value is not None and not isinstance(module_suffix_value, str):
            raise TypeError("module_suffix_choice must be a string or None")
        if type(verify_with_gf_value) is not bool:
            raise TypeError("verify_with_gf must be a bool")
        probe_request = LanguageProbeRequest(
            selected_path=selected,
            explicit_rgl_root=_optional_path_input(
                explicit_root_value,
                field="explicit_rgl_root",
            ),
            module_suffix_choice=module_suffix_value,
            entrypoint_choice=_optional_path_input(
                entrypoint_value,
                field="entrypoint_choice",
            ),
            verify_with_gf=verify_with_gf_value,
        )

    selection_service = legacy.pop("selection_service", None)
    if source_selector is not None and selection_service is not None:
        raise ValueError("source_selector and selection_service cannot both be supplied")
    selected_source_port = source_selector or selection_service or _LOCAL_SOURCE_SELECTOR
    selector = _adapt_source_selector(selected_source_port)

    filesystem_value = legacy.pop("filesystem", None)
    filesystem = _LOCAL_FILESYSTEM if filesystem_value is None else filesystem_value
    if not isinstance(filesystem, LanguageProbeFilesystem):
        raise TypeError("filesystem must satisfy LanguageProbeFilesystem")

    extractor_value = legacy.pop("module_name_extractor", None)
    module_name_extractor: ModuleNameExtractor
    if extractor_value is None:
        module_name_extractor = _module_name
    elif callable(extractor_value):
        module_name_extractor = extractor_value
    else:
        raise TypeError("module_name_extractor must be callable")

    max_ancestor_depth = _legacy_int_option(
        legacy.pop("max_ancestor_depth", probe_request.max_ancestor_depth),
        field="max_ancestor_depth",
    )
    max_source_files = _legacy_int_option(
        legacy.pop("max_source_files", probe_request.max_source_files),
        field="max_source_files",
    )
    require_unambiguous_suffix = _legacy_bool_option(
        legacy.pop(
            "require_unambiguous_suffix",
            probe_request.require_unambiguous_suffix,
        ),
        field="require_unambiguous_suffix",
    )
    if legacy:
        unexpected = ", ".join(sorted(legacy))
        raise TypeError(f"unexpected probe options: {unexpected}")

    # Verification is delegated after structural resolution when a verifier is
    # present; the built-in service retains its fail-closed legacy behavior.
    service_request = probe_request
    if verifier is not None and probe_request.verify_with_gf:
        service_request = replace(probe_request, verify_with_gf=False)

    result = LanguageProbeService(
        source_selector=selector,
        filesystem=filesystem,
        module_name_extractor=module_name_extractor,
        max_ancestor_depth=max_ancestor_depth,
        max_source_files=max_source_files,
        require_unambiguous_suffix=require_unambiguous_suffix,
    ).probe(service_request)

    if not result.is_resolved or result.context is None:
        return result

    context = result.context
    if gf_path_resolver is not None:
        observation = _invoke_flexible_port(
            gf_path_resolver,
            ("resolve_language_gf_path", "resolve_gf_path", "resolve"),
            language_directory=context.language_directory,
            rgl_source_root=context.rgl_source_root,
        )
        entries = _observation_paths(observation)
        if entries:
            context = replace(context, gf_path_requirements=entries)

    if structural_preflight is not None:
        _invoke_flexible_port(
            structural_preflight,
            ("preflight", "validate", "check"),
            context=context,
            language_directory=context.language_directory,
            rgl_source_root=context.rgl_source_root,
        )

    if verifier is not None and probe_request.verify_with_gf:
        _invoke_flexible_port(
            verifier,
            ("verify", "check"),
            context=context,
            target=context.focused_target,
        )

    if context is result.context:
        return result
    return replace(result, context=context)


# Publish the canonical introspection contract while retaining bounded legacy
# keyword compatibility in the implementation.
setattr(
    probe_language_path,
    "__signature__",
    Signature(
        parameters=(
        Parameter("request", Parameter.POSITIONAL_OR_KEYWORD),
        Parameter("source_selector", Parameter.POSITIONAL_OR_KEYWORD, default=None),
        Parameter("gf_path_resolver", Parameter.POSITIONAL_OR_KEYWORD, default=None),
        Parameter("structural_preflight", Parameter.POSITIONAL_OR_KEYWORD, default=None),
            Parameter("verifier", Parameter.POSITIONAL_OR_KEYWORD, default=None),
        )
    ),
)


def _adapt_source_selector(value: object) -> LanguageSourceSelector:
    if isinstance(value, LanguageSourceSelector):
        return value

    class _Adapter:
        __slots__ = ("_value",)

        def __init__(self, wrapped: object) -> None:
            self._value = wrapped

        def select_source_tree(
            self,
            source_root: Path,
            *,
            containment_root: Path,
            max_files: int = 0,
        ) -> tuple[Sequence[Path], Sequence[object]]:
            observation = _invoke_flexible_port(
                self._value,
                ("select_language_sources", "select_sources", "enumerate_sources", "select"),
                language_directory=source_root,
                containment_root=containment_root,
                max_files=max_files,
            )
            paths = _observation_paths(observation)
            if max_files:
                paths = paths[:max_files]
            diagnostics = tuple(getattr(observation, "diagnostics", ()))
            return paths, diagnostics

    return _Adapter(value)


def _invoke_flexible_port(
    port: object,
    methods: tuple[str, ...],
    **kwargs: object,
) -> object:
    callback = port if callable(port) else None
    if callback is None:
        for name in methods:
            candidate = getattr(port, name, None)
            if callable(candidate):
                callback = candidate
                break
    if callback is None:
        raise TypeError("injected language port must be callable")
    try:
        return callback(**kwargs)
    except TypeError as keyword_error:
        path_values = tuple(value for value in kwargs.values() if isinstance(value, Path))
        try:
            return callback(*path_values)
        except TypeError:
            raise keyword_error


def _observation_paths(observation: object) -> tuple[Path, ...]:
    for name in (
        "included_files",
        "entries",
        "paths",
        "path_parts",
        "effective_paths",
        "files",
    ):
        value = getattr(observation, name, None)
        if value is None:
            continue
        try:
            return tuple(Path(item).resolve(strict=False) for item in value)
        except TypeError:
            continue
    if isinstance(observation, (tuple, list)):
        return tuple(Path(item).resolve(strict=False) for item in observation)
    if isinstance(observation, Iterable) and not isinstance(
        observation,
        (str, bytes, bytearray, Mapping),
    ):
        try:
            return tuple(_path_from_object(item).resolve(strict=False) for item in observation)
        except TypeError:
            return ()
    return ()


def _classify_modules(
    inventory: tuple[Path, ...],
    *,
    module_name_extractor: ModuleNameExtractor,
    focused_target: Path | None,
    requested_suffix: str | None,
    requested_entrypoint: Path | None,
    require_unambiguous: bool,
) -> _ModuleClassification:
    candidates: list[LanguageModuleCandidate] = []
    for path in inventory:
        module_name = module_name_extractor(path)
        if not isinstance(module_name, str) or not module_name:
            raise ValueError("module_name_extractor must return a non-empty string")
        match = _STANDARD_MODULE_RE.fullmatch(module_name)
        if match is None:
            continue
        role = _ROLE_BY_PREFIX[match.group("role")]
        candidates.append(
            LanguageModuleCandidate(
                file_path=path,
                role=role,
                module_suffix=match.group("suffix"),
            )
        )

    ordered_candidates = tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                candidate.module_suffix.casefold(),
                _ENTRYPOINT_ORDER.get(candidate.role, 100),
                candidate.file_path.name.casefold(),
            ),
        )
    )
    suffixes = tuple(dict.fromkeys(candidate.module_suffix for candidate in ordered_candidates))

    selected_suffix = _selected_suffix(
        suffixes,
        candidates=ordered_candidates,
        focused_target=focused_target,
        requested_suffix=requested_suffix,
        requested_entrypoint=requested_entrypoint,
    )
    diagnostics: list[LanguageProbeDiagnostic] = []

    if not ordered_candidates:
        diagnostics.append(
            _diagnostic(
                code="GF-WB-CONFIG-259",
                severity=LanguageProbeSeverity.INFO,
                subject="module_roles",
                message=("No standard RGL module-role filenames were detected."),
                detail=(
                    "The language remains source-ready; standard module roles "
                    "are assistance metadata, not startup requirements."
                ),
            )
        )

    entrypoints = tuple(
        candidate
        for candidate in ordered_candidates
        if candidate.entrypoint_priority is not None
        and (selected_suffix is None or candidate.module_suffix == selected_suffix)
    )
    if not entrypoints:
        diagnostics.append(
            _diagnostic(
                code="GF-WB-CONFIG-253",
                severity=LanguageProbeSeverity.INFO,
                subject="entrypoints",
                message="No standard Lang, Grammar, or All entrypoint was found.",
                detail=(
                    "The language remains source-ready and may use an explicit "
                    "non-standard validation target later."
                ),
            )
        )

    if len(suffixes) > 1:
        if selected_suffix is None:
            diagnostics.append(
                _diagnostic(
                    code="GF-WB-CONFIG-260",
                    severity=(
                        LanguageProbeSeverity.ERROR
                        if require_unambiguous
                        else LanguageProbeSeverity.WARNING
                    ),
                    subject="module_suffix",
                    message=("Several standard language suffixes were detected."),
                    remediation=(
                        "Choose one suffix explicitly before starting the runtime."
                        if require_unambiguous
                        else ""
                    ),
                    choices=suffixes,
                )
            )
        else:
            diagnostics.append(
                _diagnostic(
                    code="GF-WB-CONFIG-257",
                    severity=LanguageProbeSeverity.INFO,
                    subject="module_suffix",
                    message=("Standard module-role evidence resolved a multi-suffix language directory."),
                    detail=f"Selected suffix: {selected_suffix}",
                    choices=suffixes,
                )
            )

    return _ModuleClassification(
        candidates=ordered_candidates,
        suffixes=suffixes,
        selected_suffix=selected_suffix,
        entrypoints=entrypoints,
        diagnostics=tuple(diagnostics),
    )


def _module_suffix_choices(
    suffixes: tuple[str, ...],
    *,
    candidates: tuple[LanguageModuleCandidate, ...],
) -> tuple[LanguageProbeChoice, ...]:
    """Build deterministic explicit choices for one ambiguous suffix set."""

    return tuple(
        LanguageProbeChoice(
            value=suffix,
            label=suffix,
            entrypoints=tuple(
                candidate.file_path
                for candidate in candidates
                if candidate.module_suffix == suffix and candidate.entrypoint_priority is not None
            ),
        )
        for suffix in suffixes
    )


def _selected_suffix(
    suffixes: tuple[str, ...],
    *,
    candidates: tuple[LanguageModuleCandidate, ...],
    focused_target: Path | None,
    requested_suffix: str | None,
    requested_entrypoint: Path | None,
) -> str | None:
    explicit_suffixes: list[str] = []

    if requested_suffix is not None:
        if requested_suffix not in suffixes:
            raise ValueError("module_suffix_choice must identify a detected suffix")
        explicit_suffixes.append(requested_suffix)

    for path in (requested_entrypoint, focused_target):
        if path is None:
            continue
        matching = next(
            (candidate.module_suffix for candidate in candidates if candidate.file_path == path),
            None,
        )
        if matching is not None:
            explicit_suffixes.append(matching)

    if explicit_suffixes:
        if len(set(explicit_suffixes)) != 1:
            raise ValueError("explicit module suffix and entrypoint choices disagree")
        return explicit_suffixes[0]
    if len(suffixes) == 1:
        return suffixes[0]

    supported = _uniquely_supported_suffix(candidates)
    if supported is not None:
        return supported
    return None


def _uniquely_supported_suffix(
    candidates: tuple[LanguageModuleCandidate, ...],
) -> str | None:
    """Return one suffix when standard RGL role evidence uniquely supports it.

    Helper modules can legally begin with a standard role prefix while adding a
    descriptive tail to the real language suffix, for example
    ``AllSqiAbs`` or ``StructuralSqiRes``.  Treating every such tail as an
    independent language suffix makes a normal language directory look
    ambiguous.  The startup ADR permits suffix inference when one candidate is
    uniquely supported by standard module roles, so score each observed suffix
    by its distinct roles and accept only a unique maximum.  Equal support
    remains ambiguous and still requires explicit user selection.
    """

    roles_by_suffix: dict[str, set[LanguageModuleRole]] = {}
    for candidate in candidates:
        roles_by_suffix.setdefault(candidate.module_suffix, set()).add(candidate.role)
    if len(roles_by_suffix) < 2:
        return next(iter(roles_by_suffix), None)

    support = {suffix: len(roles) for suffix, roles in roles_by_suffix.items()}
    strongest = max(support.values(), default=0)
    winners = tuple(suffix for suffix, count in support.items() if count == strongest)
    if len(winners) != 1:
        return None
    return winners[0]


def _normalize_inventory(
    values: Sequence[Path],
    *,
    language_directory: Path,
) -> tuple[Path, ...]:
    normalized: dict[str, Path] = {}
    for index, value in enumerate(values):
        if not isinstance(value, Path):
            raise TypeError(f"source inventory item {index} must be a pathlib.Path")
        path = value.expanduser().resolve(strict=True)
        if path.suffix.casefold() != ".gf":
            continue
        if not path.is_relative_to(language_directory):
            raise ValueError("source inventory must remain inside language_directory")
        normalized[path.as_posix().casefold()] = path

    return tuple(
        sorted(
            normalized.values(),
            key=lambda path: path.relative_to(language_directory).as_posix().casefold(),
        )
    )


def _gf_path_requirements(
    language_directory: Path,
    *,
    source_root: Path,
    filesystem: LanguageProbeFilesystem,
) -> tuple[Path, ...]:
    result = [language_directory]

    # External projects commonly keep API/wrapper modules next to the language
    # directory (for example ``lib/src/albanian`` plus ``lib/src/SyntaxSqi.gf``).
    # Add that project source directory only for a disjoint external tree; doing
    # so for a standard RGL checkout would expose every sibling language and
    # violate the no-all-language-path rule.
    if not language_directory.is_relative_to(source_root):
        project_source_root = language_directory.parent
        if filesystem.is_directory(project_source_root):
            result.append(project_source_root)

    result.extend(
        source_root / marker
        for marker in _STANDARD_SOURCE_MARKERS
        if filesystem.is_directory(source_root / marker)
    )
    return tuple(dict.fromkeys(result))


def _base_capability_statuses() -> tuple[LanguageCapabilityStatus, ...]:
    return (
        LanguageCapabilityStatus(
            capability=LanguageCapability.SOURCE_READY,
            availability=CapabilityAvailability.AVAILABLE,
        ),
        LanguageCapabilityStatus(
            capability=LanguageCapability.SCAN_READY,
            availability=CapabilityAvailability.AVAILABLE,
        ),
        LanguageCapabilityStatus(
            capability=LanguageCapability.COMPILE_READY,
            availability=CapabilityAvailability.UNKNOWN,
            reason="GF verification has not run.",
        ),
        LanguageCapabilityStatus(
            capability=LanguageCapability.SCENARIO_READY,
            availability=CapabilityAvailability.UNKNOWN,
            reason="Scenario preflight has not run.",
        ),
        LanguageCapabilityStatus(
            capability=LanguageCapability.RELEASE_READY,
            availability=CapabilityAvailability.UNKNOWN,
            reason="Release validation has not run.",
        ),
    )


def _resolution_provenance(
    *,
    selected_path: Path,
    language_directory: Path,
    roots: _RootResolution,
    language_key: str,
    selected_suffix: str | None,
) -> tuple[LanguageResolutionProvenance, ...]:
    values = [
        LanguageResolutionProvenance(
            field="selected_path",
            value=str(selected_path),
            source=LanguageResolutionSource.EXPLICIT_SELECTED_PATH,
        ),
        LanguageResolutionProvenance(
            field="language_directory",
            value=str(language_directory),
            source=LanguageResolutionSource.LANGUAGE_PROBE,
        ),
        LanguageResolutionProvenance(
            field="rgl_source_root",
            value=str(roots.source_root),
            source=roots.provenance,
        ),
        LanguageResolutionProvenance(
            field="rgl_root",
            value=str(roots.repository_root),
            source=roots.provenance,
        ),
        LanguageResolutionProvenance(
            field="language_key",
            value=language_key,
            source=LanguageResolutionSource.LANGUAGE_PROBE,
        ),
    ]
    if selected_suffix is not None:
        values.append(
            LanguageResolutionProvenance(
                field="module_suffix",
                value=selected_suffix,
                source=LanguageResolutionSource.MODULE_CLASSIFICATION,
            )
        )
    return tuple(values)


def _language_key(
    language_directory: Path,
    *,
    source_root: Path,
) -> str:
    try:
        relative = language_directory.relative_to(source_root)
    except ValueError:
        # External GF project: the explicit RGL root supplies dependencies but
        # does not own the language source tree.  Keep the portable identity
        # local to the selected language directory rather than fabricating a
        # relationship to the RGL checkout.
        value = language_directory.name
    else:
        value = relative.as_posix()
    if not value or value == ".":
        raise ValueError("language_directory must identify a non-empty language key")
    return value


def _module_name(path: Path) -> str:
    return path.stem


def _diagnostic(
    *,
    code: str,
    severity: LanguageProbeSeverity,
    subject: str,
    message: str,
    remediation: str = "",
    detail: str = "",
    path: Path | None = None,
    choices: tuple[str, ...] = (),
) -> LanguageProbeDiagnostic:
    return LanguageProbeDiagnostic(
        code=code,
        severity=severity,
        stage="language_probe",
        subject=subject,
        message=message,
        detail=detail,
        remediation=remediation,
        relevant_path=path,
        candidates=choices,
    )


def _failure_result(
    *,
    status: LanguageProbeStatus,
    code: str,
    subject: str,
    message: str,
    remediation: str,
    path: Path | None = None,
    detail: str = "",
) -> LanguageProbeResult:
    return LanguageProbeResult(
        status=status,
        diagnostics=(
            _diagnostic(
                code=code,
                severity=LanguageProbeSeverity.ERROR,
                subject=subject,
                message=message,
                remediation=remediation,
                detail=detail,
                path=path,
            ),
        ),
    )


def _optional_path_input(value: object, *, field: str) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, (str, os.PathLike)):
        raise TypeError(f"{field} must be path-like or None")
    return _coerce_path(value, field=field)


def _path_from_object(value: object) -> Path:
    if not isinstance(value, (str, os.PathLike)):
        raise TypeError("path value must be path-like")
    return Path(value)


def _legacy_int_option(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    return value


def _legacy_bool_option(value: object, *, field: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field} must be a bool")
    return value


def _coerce_path(value: PathInput, *, field: str) -> Path:
    if isinstance(value, Path):
        path = value
    elif isinstance(value, (str, os.PathLike)):
        try:
            path = Path(value)
        except TypeError as exc:
            raise TypeError(f"{field} must be path-like") from exc
    else:
        raise TypeError(f"{field} must be path-like")
    if not str(path):
        raise ValueError(f"{field} must not be empty")
    return path.expanduser().resolve(strict=False)


def _require_positive_int(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 1:
        raise ValueError(f"{field} must be at least 1")
    return value


def _require_non_negative_int(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must not be negative")
    return value
