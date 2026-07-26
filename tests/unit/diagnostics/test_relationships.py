"""Unit tests for deterministic diagnostic blocker relationships."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from gf_wordbench.diagnostics.classification import relationships
from gf_wordbench.diagnostics.classification.relationships import (
    BlockerGraph,
    blocker_identity_key,
    build_blocker_graph,
    collapse_blocker_graph,
    find_blocker_cycles,
    has_blocker_path,
    is_blocker_eligible,
    normalize_blocker_identities,
    normalize_blocker_identity,
    relationship_fields,
    resolve_root_blockers,
    validate_relationship_fields,
)
from gf_wordbench.kernel.statuses import DiagnosticClass, ValidationStatus


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        (" lib\\src\\Grammar.gf ", "lib/src/Grammar.gf"),
        ("./lib//src/./Grammar.gf", "lib/src/Grammar.gf"),
        ("scenario:release", "scenario:release"),
    ),
)
def test_identity_normalization_is_portable_and_deterministic(
    raw: str,
    expected: str,
) -> None:
    assert normalize_blocker_identity(raw) == expected


@pytest.mark.parametrize(
    "raw",
    (
        "",
        "   ",
        "/absolute/path.gf",
        "C:/absolute/path.gf",
        "../escape.gf",
        "lib/../escape.gf",
        "~/home.gf",
        "%TEMP%/Grammar.gf",
        "$HOME/Grammar.gf",
        "${HOME}/Grammar.gf",
        "lib/source file.gf",
        "grammaire-é.gf",
        "bad\x00name.gf",
    ),
)
def test_identity_normalization_rejects_noncanonical_or_unsafe_values(
    raw: str,
) -> None:
    with pytest.raises(ValueError):
        normalize_blocker_identity(raw)


def test_identity_collections_exclude_self_deduplicate_and_sort() -> None:
    assert normalize_blocker_identities(
        (
            "lib\\Z.gf",
            "lib/A.gf",
            "lib//A.gf",
            "lib/Self.gf",
        ),
        self_identity="lib/Self.gf",
    ) == ("lib/A.gf", "lib/Z.gf")


def test_case_insensitive_identity_keys_preserve_canonical_spelling() -> None:
    assert blocker_identity_key(
        "LIB\\Grammar.gf",
        case_sensitive=False,
    ) == "lib/grammar.gf"
    assert normalize_blocker_identities(
        ("lib/grammar.gf", "LIB/Grammar.gf"),
        case_sensitive=False,
    ) == ("LIB/Grammar.gf",)


@pytest.mark.parametrize(
    ("status", "expected"),
    (
        (ValidationStatus.OK, False),
        (ValidationStatus.SKIPPED, False),
        (ValidationStatus.FAIL, True),
        (ValidationStatus.ERROR, True),
        ("FAIL", True),
    ),
)
def test_only_failed_or_error_subjects_are_blocker_eligible(
    status: ValidationStatus | str,
    expected: bool,
) -> None:
    assert is_blocker_eligible(status) is expected


@pytest.mark.parametrize(
    ("diagnostic_class", "expected_direct"),
    (
        (DiagnosticClass.OK, False),
        (DiagnosticClass.DIRECT, True),
        (DiagnosticClass.AMBIGUOUS, False),
        (DiagnosticClass.NOISE, False),
        (DiagnosticClass.SKIPPED, False),
    ),
)
def test_non_downstream_relationship_fields_require_no_blockers(
    diagnostic_class: DiagnosticClass,
    expected_direct: bool,
) -> None:
    assert relationship_fields(diagnostic_class) == (expected_direct, ())

    with pytest.raises(ValueError, match="requires empty blockers"):
        relationship_fields(diagnostic_class, ("lib/Provider.gf",))


def test_downstream_relationship_fields_require_canonical_blockers() -> None:
    assert relationship_fields(
        DiagnosticClass.DOWNSTREAM,
        (
            "lib\\ZProvider.gf",
            "lib/AProvider.gf",
            "lib/AProvider.gf",
            "lib/Current.gf",
        ),
        self_identity="lib/Current.gf",
    ) == (
        False,
        ("lib/AProvider.gf", "lib/ZProvider.gf"),
    )

    with pytest.raises(ValueError, match="requires blockers"):
        relationship_fields(DiagnosticClass.DOWNSTREAM)


def test_persisted_is_direct_must_match_diagnostic_class() -> None:
    assert validate_relationship_fields(
        DiagnosticClass.DIRECT,
        is_direct=True,
        blocked_by=(),
    ) == ()
    assert validate_relationship_fields(
        DiagnosticClass.DOWNSTREAM,
        is_direct=False,
        blocked_by=("lib/Provider.gf",),
    ) == ("lib/Provider.gf",)

    with pytest.raises(ValueError, match="is_direct must equal"):
        validate_relationship_fields(
            DiagnosticClass.DIRECT,
            is_direct=False,
            blocked_by=(),
        )


def test_graph_builder_closes_known_subjects_and_preserves_unknown_evidence() -> None:
    graph = build_blocker_graph(
        {
            "lib/C.gf": ("lib/B.gf", "external/Missing.gf"),
            "lib/B.gf": ("lib/A.gf",),
        },
        known_subjects=("lib/A.gf", "lib/B.gf", "lib/C.gf"),
    )

    assert graph.subjects == ("lib/A.gf", "lib/B.gf", "lib/C.gf")
    assert dict(graph.edges) == {
        "lib/A.gf": (),
        "lib/B.gf": ("lib/A.gf",),
        "lib/C.gf": ("lib/B.gf",),
    }
    assert dict(graph.unknown_references) == {
        "lib/C.gf": ("external/Missing.gf",),
    }
    assert graph.edge_count == 2
    assert graph.blockers_for("lib\\C.gf") == ("lib/B.gf",)
    assert graph.unknown_for("lib/C.gf") == ("external/Missing.gf",)


def test_graph_values_are_frozen_after_validation() -> None:
    graph = build_blocker_graph({"A": (), "B": ("A",)})

    with pytest.raises(TypeError):
        graph.edges["B"] = ()  # type: ignore[index]
    with pytest.raises(TypeError):
        graph.unknown_references["A"] = ("missing",)  # type: ignore[index]


def test_acyclic_chains_collapse_to_terminal_root_blockers() -> None:
    graph = build_blocker_graph(
        {
            "A": (),
            "B": ("A",),
            "C": ("B",),
            "D": ("B", "A"),
        }
    )
    resolution = collapse_blocker_graph(graph)

    assert dict(resolution.root_blockers) == {
        "A": (),
        "B": ("A",),
        "C": ("A",),
        "D": ("A",),
    }
    assert resolution.cycles == ()
    assert resolution.unresolved_subjects == ()


def test_cycles_are_reported_without_inventing_root_blockers() -> None:
    graph = build_blocker_graph({"A": ("B",), "B": ("A",)})
    resolution = collapse_blocker_graph(graph)

    assert find_blocker_cycles(graph) == (("A", "B"),)
    assert dict(resolution.root_blockers) == {"A": (), "B": ()}
    assert resolution.unresolved_subjects == ("A", "B")
    assert resolution.is_unresolved("A") is True


def test_cycle_with_an_exit_collapses_to_the_reachable_root() -> None:
    graph = build_blocker_graph(
        {
            "A": ("B",),
            "B": ("A", "Root"),
            "Root": (),
        }
    )
    resolution = collapse_blocker_graph(graph)

    assert resolution.cycles == (("A", "B"),)
    assert resolution.roots_for("A") == ("Root",)
    assert resolution.roots_for("B") == ("Root",)
    assert resolution.unresolved_subjects == ()


def test_unknown_only_relationship_evidence_remains_unresolved() -> None:
    graph = build_blocker_graph({"A": ("external/Missing.gf",)})
    resolution = collapse_blocker_graph(graph)

    assert graph.blockers_for("A") == ()
    assert graph.unknown_for("A") == ("external/Missing.gf",)
    assert resolution.roots_for("A") == ()
    assert resolution.unresolved_subjects == ("A",)


def test_blocker_path_queries_follow_transitive_edges() -> None:
    graph = build_blocker_graph(
        {
            "A": (),
            "B": ("A",),
            "C": ("B",),
            "D": (),
        }
    )

    assert has_blocker_path(graph, "C", "A") is True
    assert has_blocker_path(graph, "C", "B") is True
    assert has_blocker_path(graph, "C", "D") is False
    assert has_blocker_path(graph, "C", "C") is False

    with pytest.raises(KeyError, match="unknown blocker-graph subject"):
        has_blocker_path(graph, "missing", "A")


def test_root_resolution_convenience_api_matches_graph_resolution() -> None:
    immediate = {
        "A": (),
        "B": ("A",),
        "C": ("B",),
    }

    assert resolve_root_blockers("C", immediate) == ("A",)
    assert resolve_root_blockers(
        "C",
        immediate,
        root_subjects=("B",),
    ) == ("B",)


def test_public_surface_is_explicit_and_owned_by_relationships_module() -> None:
    expected = {
        "BlockerGraph",
        "BlockerGraphResolution",
        "BlockerIdentity",
        "BlockerMap",
        "BlockerSequence",
        "blocker_identity_key",
        "build_blocker_graph",
        "collapse_blocker_graph",
        "find_blocker_cycles",
        "has_blocker_path",
        "is_blocker_eligible",
        "normalize_blocker_identities",
        "normalize_blocker_identity",
        "relationship_fields",
        "resolve_root_blockers",
        "validate_relationship_fields",
    }

    assert set(relationships.__all__) == expected
    assert all(hasattr(relationships, name) for name in expected)
    assert all(
        callable(getattr(relationships, name))
        for name in expected
        if name not in {
            "BlockerIdentity",
            "BlockerMap",
            "BlockerSequence",
        }
    )
