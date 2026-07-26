from __future__ import annotations

from pathlib import PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Any

import pytest

from gf_wordbench.diagnostics.classification.blockers import (
    BlockerCycle,
    BlockerGraphError,
    BlockerGraphResolution,
    BlockerResolution,
    DuplicateBlockerIdentityError,
    UnknownBlockerSubjectError,
    collapse_blocker_roots,
    normalize_blocker_identities,
    normalize_blocker_identity,
    resolve_blocker_graph,
    validate_blocked_by,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("src/Grammar.gf", "src/Grammar.gf"),
        ("src\\Grammar.gf", "src/Grammar.gf"),
        ("./src/./Grammar.gf", "src/Grammar.gf"),
        ("src//nested///Grammar.gf", "src/nested/Grammar.gf"),
        (PurePosixPath("src/Grammar.gf"), "src/Grammar.gf"),
        (PureWindowsPath("src\\Grammar.gf"), "src/Grammar.gf"),
        ("validation/scenarios/parse-basic.gfs", "validation/scenarios/parse-basic.gfs"),
        ("Unicode/GrammaireÉté.gf", "Unicode/GrammaireÉté.gf"),
    ],
)
def test_normalize_blocker_identity_returns_portable_project_relative_path(
    value: str | PurePosixPath | PureWindowsPath,
    expected: str,
) -> None:
    assert normalize_blocker_identity(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        " src/Grammar.gf",
        "src/Grammar.gf ",
        "../src/Grammar.gf",
        "src/../Grammar.gf",
        "/src/Grammar.gf",
        r"\\server\share\Grammar.gf",
        "C:\\src\\Grammar.gf",
        "~/src/Grammar.gf",
        "$PROJECT_ROOT/src/Grammar.gf",
        "${PROJECT_ROOT}/src/Grammar.gf",
        "%PROJECT_ROOT%/src/Grammar.gf",
        "src/Gram\x00mar.gf",
    ],
)
def test_normalize_blocker_identity_rejects_unsafe_values(value: str) -> None:
    with pytest.raises(BlockerGraphError):
        normalize_blocker_identity(value)


@pytest.mark.parametrize("value", [None, 1, 1.5, object(), b"src/Grammar.gf"])
def test_normalize_blocker_identity_rejects_non_path_values(value: Any) -> None:
    with pytest.raises(TypeError, match="string or PurePath"):
        normalize_blocker_identity(value)


def test_normalize_blocker_identities_deduplicates_filters_self_and_sorts() -> None:
    result = normalize_blocker_identities(
        (
            "src/Z.gf",
            "src/A.gf",
            "src/Z.gf",
            "src/Self.gf",
            PureWindowsPath("src\\B.gf"),
        ),
        subject_id="src/Self.gf",
    )

    assert result == ("src/A.gf", "src/B.gf", "src/Z.gf")


def test_normalize_blocker_identities_detects_case_insensitive_collision() -> None:
    with pytest.raises(DuplicateBlockerIdentityError, match="identity collision"):
        normalize_blocker_identities(
            ("src/Grammar.gf", "SRC/GRAMMAR.GF"),
            case_sensitive=False,
        )


@pytest.mark.parametrize(
    "values",
    ["src/A.gf", b"src/A.gf", PurePosixPath("src/A.gf")],
)
def test_normalize_blocker_identities_requires_collection(
    values: str | bytes | PurePosixPath,
) -> None:
    with pytest.raises(TypeError, match="must be an iterable"):
        normalize_blocker_identities(values)


def test_validate_blocked_by_requires_at_least_one_non_self_blocker() -> None:
    with pytest.raises(BlockerGraphError, match="requires blockers"):
        validate_blocked_by(
            "src/Self.gf",
            ("src/Self.gf",),
            require_non_empty=True,
        )


def test_validate_blocked_by_returns_canonical_persistable_tuple() -> None:
    result = validate_blocked_by(
        "src/Dependent.gf",
        (
            "src\\Root.gf",
            "src/Root.gf",
            "src/Other.gf",
        ),
        require_non_empty=True,
    )

    assert result == ("src/Other.gf", "src/Root.gf")


def test_simple_chain_collapses_to_terminal_root() -> None:
    resolution = resolve_blocker_graph(
        {
            "src/App.gf": ("src/Concrete.gf",),
            "src/Concrete.gf": ("src/Abstract.gf",),
            "src/Abstract.gf": (),
        }
    )

    assert resolution.subjects == (
        "src/Abstract.gf",
        "src/App.gf",
        "src/Concrete.gf",
    )
    assert resolution.immediate_blockers["src/App.gf"] == ("src/Concrete.gf",)
    assert resolution.root_blockers["src/App.gf"] == ("src/Abstract.gf",)
    assert resolution.root_blockers["src/Concrete.gf"] == ("src/Abstract.gf",)
    assert resolution.root_blockers["src/Abstract.gf"] == ()
    assert resolution.cycles == ()
    assert resolution.external_blockers == ()
    assert resolution.has_unresolved_cycles is False


def test_branching_graph_returns_unique_sorted_roots() -> None:
    resolution = resolve_blocker_graph(
        {
            "src/App.gf": (
                "src/ZConcrete.gf",
                "src/AConcrete.gf",
            ),
            "src/ZConcrete.gf": ("src/ZAbstract.gf",),
            "src/AConcrete.gf": ("src/AAbstract.gf",),
            "src/ZAbstract.gf": (),
            "src/AAbstract.gf": (),
        }
    )

    assert resolution.roots_for("src/App.gf") == (
        "src/AAbstract.gf",
        "src/ZAbstract.gf",
    )


def test_known_subjects_add_isolated_nodes_to_resolution() -> None:
    resolution = resolve_blocker_graph(
        {"src/App.gf": ("src/Root.gf",)},
        known_subjects=(
            "src/App.gf",
            "src/Root.gf",
            "src/Unused.gf",
        ),
    )

    assert resolution.subjects == (
        "src/App.gf",
        "src/Root.gf",
        "src/Unused.gf",
    )
    assert resolution.immediate_blockers["src/Unused.gf"] == ()
    assert resolution.root_blockers["src/Unused.gf"] == ()


def test_unknown_references_are_recorded_but_not_confirmed() -> None:
    resolution = resolve_blocker_graph(
        {
            "src/App.gf": (
                "src/Existing.gf",
                "src/Missing.gf",
            ),
            "src/Existing.gf": (),
        }
    )

    subject = resolution.resolution_for("src/App.gf")
    assert subject.immediate_blockers == ("src/Existing.gf",)
    assert subject.root_blockers == ("src/Existing.gf",)
    assert subject.unknown_references == ("src/Missing.gf",)
    assert subject.is_downstream_candidate is True


def test_external_blocker_is_a_terminal_root() -> None:
    resolution = resolve_blocker_graph(
        {
            "validation/scenario": ("toolchain/gf",),
        },
        external_blockers=("toolchain/gf",),
    )

    assert resolution.external_blockers == ("toolchain/gf",)
    assert resolution.immediate_blockers["validation/scenario"] == (
        "toolchain/gf",
    )
    assert resolution.root_blockers["validation/scenario"] == (
        "toolchain/gf",
    )
    assert resolution.unknown_references["validation/scenario"] == ()


def test_subject_identity_wins_over_duplicate_external_identity() -> None:
    resolution = resolve_blocker_graph(
        {
            "src/App.gf": ("src/Root.gf",),
            "src/Root.gf": (),
        },
        external_blockers=("src/Root.gf", "toolchain/gf"),
    )

    assert resolution.external_blockers == ("toolchain/gf",)
    assert resolution.root_blockers["src/App.gf"] == ("src/Root.gf",)


def test_unresolved_cycle_is_reported_without_invented_root() -> None:
    resolution = resolve_blocker_graph(
        {
            "src/A.gf": ("src/B.gf",),
            "src/B.gf": ("src/A.gf",),
        }
    )

    assert resolution.root_blockers["src/A.gf"] == ()
    assert resolution.root_blockers["src/B.gf"] == ()
    assert resolution.cycles == (
        BlockerCycle(
            members=("src/A.gf", "src/B.gf"),
            root_blockers=(),
        ),
    )
    assert resolution.has_unresolved_cycles is True

    subject = resolution.resolution_for("src/A.gf")
    assert subject.cycle_members == ("src/A.gf", "src/B.gf")
    assert subject.root_blockers == ()
    assert subject.has_unresolved_cycle is True
    assert subject.is_downstream_candidate is False


def test_cycle_with_external_exit_resolves_to_external_root() -> None:
    resolution = resolve_blocker_graph(
        {
            "src/A.gf": ("src/B.gf",),
            "src/B.gf": ("src/A.gf", "toolchain/gf"),
        },
        external_blockers=("toolchain/gf",),
    )

    expected_cycle = BlockerCycle(
        members=("src/A.gf", "src/B.gf"),
        root_blockers=("toolchain/gf",),
    )
    assert resolution.cycles == (expected_cycle,)
    assert resolution.root_blockers["src/A.gf"] == ("toolchain/gf",)
    assert resolution.root_blockers["src/B.gf"] == ("toolchain/gf",)
    assert resolution.has_unresolved_cycles is False
    assert resolution.resolution_for("src/A.gf").has_unresolved_cycle is False


def test_cycle_with_internal_exit_resolves_to_terminal_subject() -> None:
    resolution = resolve_blocker_graph(
        {
            "src/A.gf": ("src/B.gf",),
            "src/B.gf": ("src/A.gf", "src/Root.gf"),
            "src/Root.gf": (),
        }
    )

    assert resolution.root_blockers["src/A.gf"] == ("src/Root.gf",)
    assert resolution.root_blockers["src/B.gf"] == ("src/Root.gf",)
    assert resolution.cycles[0].root_blockers == ("src/Root.gf",)


def test_self_reference_is_removed_before_graph_resolution() -> None:
    resolution = resolve_blocker_graph(
        {
            "src/A.gf": ("src/A.gf", "src/B.gf"),
            "src/B.gf": (),
        }
    )

    assert resolution.immediate_blockers["src/A.gf"] == ("src/B.gf",)
    assert resolution.root_blockers["src/A.gf"] == ("src/B.gf",)
    assert resolution.cycles == ()


def test_case_insensitive_graph_preserves_canonical_spelling_and_lookup() -> None:
    resolution = resolve_blocker_graph(
        {
            "Src/App.gf": ("SRC/ROOT.GF",),
            "src/root.gf": (),
        },
        case_sensitive=False,
    )

    assert resolution.subjects == ("Src/App.gf", "src/root.gf")
    assert resolution.immediate_blockers["Src/App.gf"] == ("src/root.gf",)
    assert resolution.roots_for("SRC/APP.GF") == ("src/root.gf",)
    assert resolution.resolution_for(PureWindowsPath("src\\APP.gf")).subject_id == (
        "Src/App.gf"
    )


def test_case_insensitive_subject_collision_is_rejected() -> None:
    with pytest.raises(DuplicateBlockerIdentityError, match="subject collision"):
        resolve_blocker_graph(
            {
                "src/App.gf": (),
                "SRC/APP.GF": (),
            },
            case_sensitive=False,
        )


def test_equivalent_normalized_mapping_keys_are_rejected() -> None:
    with pytest.raises(DuplicateBlockerIdentityError, match="duplicate subject"):
        resolve_blocker_graph(
            {
                "src/A.gf": (),
                "src\\A.gf": (),
            }
        )


def test_unknown_subject_lookup_raises_specific_error() -> None:
    resolution = resolve_blocker_graph({"src/A.gf": ()})

    with pytest.raises(
        UnknownBlockerSubjectError,
        match="unknown blocker subject",
    ):
        resolution.resolution_for("src/Missing.gf")


def test_collapse_blocker_roots_matches_full_resolution() -> None:
    graph = {
        "src/App.gf": ("src/Concrete.gf",),
        "src/Concrete.gf": ("src/Abstract.gf",),
        "src/Abstract.gf": (),
    }

    assert collapse_blocker_roots("src/App.gf", graph) == (
        "src/Abstract.gf",
    )


def test_resolution_mappings_are_immutable() -> None:
    resolution = resolve_blocker_graph(
        {
            "src/App.gf": ("src/Root.gf",),
            "src/Root.gf": (),
        }
    )

    assert isinstance(resolution.immediate_blockers, MappingProxyType)
    assert isinstance(resolution.root_blockers, MappingProxyType)
    assert isinstance(resolution.unknown_references, MappingProxyType)

    with pytest.raises(TypeError):
        resolution.immediate_blockers["src/App.gf"] = ()  # type: ignore[index]


def test_graph_output_is_deterministic_across_input_order() -> None:
    first = resolve_blocker_graph(
        {
            "src/Z.gf": ("src/A.gf", "external/z"),
            "src/A.gf": (),
            "src/M.gf": ("src/Z.gf",),
        },
        external_blockers=("external/z",),
    )
    second = resolve_blocker_graph(
        {
            "src/M.gf": ("src/Z.gf",),
            "src/A.gf": (),
            "src/Z.gf": ("external/z", "src/A.gf"),
        },
        external_blockers=("external/z",),
    )

    assert first == second
    assert first.subjects == ("src/A.gf", "src/M.gf", "src/Z.gf")
    assert first.root_blockers["src/M.gf"] == (
        "external/z",
        "src/A.gf",
    )


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"max_nodes": 0}, ValueError, "max_nodes must be positive"),
        ({"max_nodes": True}, TypeError, "max_nodes must be an integer"),
        ({"max_edges": 0}, ValueError, "max_edges must be positive"),
        ({"max_edges": 1.5}, TypeError, "max_edges must be an integer"),
        ({"case_sensitive": 1}, TypeError, "case_sensitive must be a bool"),
    ],
)
def test_graph_option_validation(
    kwargs: dict[str, object],
    error: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error, match=message):
        resolve_blocker_graph({"src/A.gf": ()}, **kwargs)  # type: ignore[arg-type]


def test_max_nodes_limit_is_enforced() -> None:
    with pytest.raises(BlockerGraphError, match="exceeds max_nodes=2"):
        resolve_blocker_graph(
            {
                "src/A.gf": (),
                "src/B.gf": (),
                "src/C.gf": (),
            },
            max_nodes=2,
        )


def test_max_edges_limit_is_enforced_after_normalization() -> None:
    with pytest.raises(BlockerGraphError, match="exceeds max_edges=1"):
        resolve_blocker_graph(
            {
                "src/A.gf": ("src/B.gf", "src/C.gf"),
                "src/B.gf": (),
                "src/C.gf": (),
            },
            max_edges=1,
        )


def test_duplicate_edges_do_not_consume_additional_edge_budget() -> None:
    resolution = resolve_blocker_graph(
        {
            "src/A.gf": (
                "src/B.gf",
                "src/B.gf",
                "src/B.gf",
            ),
            "src/B.gf": (),
        },
        max_edges=1,
    )

    assert resolution.immediate_blockers["src/A.gf"] == ("src/B.gf",)


def test_blocker_cycle_model_requires_multiple_unique_members() -> None:
    with pytest.raises(ValueError, match="at least two members"):
        BlockerCycle(members=("src/A.gf",))

    with pytest.raises(ValueError, match="must not contain duplicates"):
        BlockerCycle(members=("src/A.gf", "src/A.gf"))


def test_blocker_resolution_rejects_self_as_blocker_or_root() -> None:
    with pytest.raises(ValueError, match="cannot block itself"):
        BlockerResolution(
            subject_id="src/A.gf",
            immediate_blockers=("src/A.gf",),
            root_blockers=(),
        )

    with pytest.raises(ValueError, match="cannot block itself"):
        BlockerResolution(
            subject_id="src/A.gf",
            immediate_blockers=(),
            root_blockers=("src/A.gf",),
        )


def test_graph_resolution_requires_identical_subject_sets() -> None:
    with pytest.raises(
        ValueError,
        match="must contain identical subjects",
    ):
        BlockerGraphResolution(
            immediate_blockers={"src/A.gf": ()},
            root_blockers={"src/B.gf": ()},
            unknown_references={"src/A.gf": ()},
            cycles=(),
            external_blockers=(),
        )


def test_graph_resolution_validates_cycle_types_and_boolean_flag() -> None:
    with pytest.raises(TypeError, match="cycles must contain"):
        BlockerGraphResolution(
            immediate_blockers={"src/A.gf": ()},
            root_blockers={"src/A.gf": ()},
            unknown_references={"src/A.gf": ()},
            cycles=("not-a-cycle",),  # type: ignore[arg-type]
            external_blockers=(),
        )

    with pytest.raises(TypeError, match="case_sensitive must be a bool"):
        BlockerGraphResolution(
            immediate_blockers={"src/A.gf": ()},
            root_blockers={"src/A.gf": ()},
            unknown_references={"src/A.gf": ()},
            cycles=(),
            external_blockers=(),
            case_sensitive=1,  # type: ignore[arg-type]
        )


def test_graph_requires_mapping_and_iterable_blocker_values() -> None:
    with pytest.raises(TypeError, match="must be a mapping"):
        resolve_blocker_graph([("src/A.gf", ())])  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="blockers for .* must be an iterable"):
        resolve_blocker_graph({"src/A.gf": "src/B.gf"})


def test_external_blockers_require_a_collection() -> None:
    with pytest.raises(
        TypeError,
        match="external blocker values must be an iterable",
    ):
        resolve_blocker_graph(
            {"src/A.gf": ()},
            external_blockers="toolchain/gf",
        )
