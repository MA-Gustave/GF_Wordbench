from __future__ import annotations

from collections.abc import Mapping
from dataclasses import (
    MISSING,
    FrozenInstanceError,
    fields,
    is_dataclass,
    replace,
)
from datetime import UTC, datetime, timedelta
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

import pytest

from gf_wordbench.entrypoints.gui.view_model import (
    ActivityItem,
    ArtifactAction,
    FailureCounts,
    GuiRunRequest,
    GuiSnapshot,
    GuiViewModel,
    LanguageView,
    ProgressView,
    ResultView,
    RunPresentationState,
    StatusCounts,
    language_view_from_context,
)
from gf_wordbench.kernel.events import EventLevel, ProgressEvent
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.projects.languages.models import (
    ResolvedLanguageContext,
    SelectedPathKind,
)
from gf_wordbench.state.models import (
    AppState,
    EnvironmentState,
    LastRunState,
    SelectionState,
)
from gf_wordbench.state.schema import (
    APP_STATE_SCHEMA_ID,
    APP_STATE_SCHEMA_VERSION,
)

pytestmark = pytest.mark.unit

_FIXED_TIME: Final[datetime] = datetime(2026, 7, 31, 10, 0, tzinfo=UTC)


def _state() -> AppState:
    return AppState(
        schema_id=APP_STATE_SCHEMA_ID,
        schema_version=APP_STATE_SCHEMA_VERSION,
        producer=ProducerInfo(
            name="gf-wordbench",
            version="1.0.0",
        ),
        environment=EnvironmentState(
            last_selected_language_path=(
                "C:/gf/gf-rgl/src/example/GrammarEx.gf"
            ),
            last_selected_validation_profile=None,
            rgl_root="C:/gf/gf-rgl",
            gf_executable="C:/gf/bin/gf.exe",
            output_root="C:/work/GF_Wordbench/runs",
        ),
        selection=SelectionState(
            mode=ValidationMode.QUICK,
            target_file="GrammarEx.gf",
            timeout_sec=90,
            max_files=25,
            keep_ok_details=True,
            diff_previous=True,
            skip_version_probe=False,
            no_compile=False,
            emit_cpu_stats=True,
        ),
        last_run=LastRunState(
            run_dir="C:/work/GF_Wordbench/runs/run_previous",
            summary_path=(
                "C:/work/GF_Wordbench/runs/run_previous/summary.json"
            ),
            status_message="Validation completed with failures",
        ),
    )


def _language_context(tmp_path: Path) -> ResolvedLanguageContext:
    rgl_root = (tmp_path / "gf-rgl").resolve()
    rgl_source_root = rgl_root / "src"
    language_directory = rgl_source_root / "example"
    selected_file = language_directory / "GrammarEx.gf"
    common_directory = rgl_source_root / "common"

    for directory in (language_directory, common_directory):
        directory.mkdir(parents=True, exist_ok=True)

    source_inventory = (
        language_directory / "AllEx.gf",
        language_directory / "GrammarEx.gf",
        language_directory / "LangEx.gf",
        language_directory / "MorphologyEx.gf",
    )
    for source in source_inventory:
        source.write_text(
            f"resource {source.stem} = {{}} ;\n",
            encoding="utf-8",
        )

    return ResolvedLanguageContext(
        language_key="example",
        selected_path=selected_file,
        selected_path_kind=SelectedPathKind.FILE,
        language_directory=language_directory,
        rgl_source_root=rgl_source_root,
        rgl_root=rgl_root,
        selected_file=selected_file,
        focused_target=Path("GrammarEx.gf"),
        module_suffix="Ex",
        available_entrypoints=(
            Path("LangEx.gf"),
            Path("GrammarEx.gf"),
            Path("AllEx.gf"),
        ),
        source_inventory=source_inventory,
        gf_path_requirements=(
            language_directory,
            common_directory,
        ),
        structural_diagnostics=(),
        capability_statuses=MappingProxyType(
            {
                "source-ready": True,
                "scan-ready": True,
            }
        ),
        resolution_provenance=(),
    )


def _required_dataclass_kwargs(
    cls: type[Any],
    *,
    total: int | None = 4,
) -> dict[str, object]:
    values: dict[str, object] = {}
    for item in fields(cls):
        if item.default is not MISSING or item.default_factory is not MISSING:
            continue

        name = item.name
        lowered = name.casefold()
        if lowered in {"started_at", "start_time", "created_at"}:
            values[name] = _FIXED_TIME
        elif lowered in {
            "updated_at",
            "finished_at",
            "timestamp",
            "last_event_at",
        }:
            values[name] = _FIXED_TIME + timedelta(seconds=5)
        elif lowered == "completed":
            values[name] = 2 if total is not None else 0
        elif lowered == "total":
            values[name] = total
        elif "warning" in lowered or "failure" in lowered:
            values[name] = 1
        elif lowered in {"ok", "fail", "error", "skipped"}:
            values[name] = 0
        elif lowered in {"direct", "downstream", "ambiguous"}:
            values[name] = 0
        elif lowered == "stage":
            values[name] = "compile"
        elif lowered == "subject":
            values[name] = "GrammarEx.gf"
        elif lowered == "message":
            values[name] = "Compiling GrammarEx.gf"
        elif lowered == "run_id":
            values[name] = "run_20260731T100000Z_example"
        elif lowered.endswith("_path") or lowered.endswith("_dir"):
            values[name] = Path("/tmp/gf-wordbench")
        elif lowered.endswith("_id"):
            values[name] = "example"
        elif lowered in {"label", "title", "name", "status_message"}:
            values[name] = "Example"
        elif lowered in {"enabled", "required", "available"}:
            values[name] = True
        elif lowered in {"metadata", "details"}:
            values[name] = MappingProxyType({})
        else:
            raise AssertionError(
                f"test fixture has no value for required "
                f"{cls.__name__}.{name}"
            )
    return values


def _progress(*, total: int | None = 4) -> ProgressView:
    return ProgressView(
        **_required_dataclass_kwargs(
            ProgressView,
            total=total,
        )
    )


def _view_model(state: AppState) -> GuiViewModel:
    signature = inspect.signature(GuiViewModel)
    positional: list[object] = []
    keywords: dict[str, object] = {}

    for parameter in signature.parameters.values():
        if parameter.name in {"state", "app_state", "initial_state"}:
            value: object = state
        elif parameter.name in {"clock", "now", "utc_now"}:
            value = lambda: _FIXED_TIME
        elif parameter.name in {
            "activity_limit",
            "max_activity_items",
            "maximum_activity_items",
        }:
            value = 3
        elif parameter.default is not inspect.Parameter.empty:
            continue
        else:
            raise AssertionError(
                "unsupported required GuiViewModel constructor parameter: "
                f"{parameter.name}"
            )

        if parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
            positional.append(value)
        else:
            keywords[parameter.name] = value

    return GuiViewModel(*positional, **keywords)


def _call_begin_run(model: GuiViewModel) -> None:
    signature = inspect.signature(model.begin_run)
    positional: list[object] = []
    keywords: dict[str, object] = {}

    for parameter in signature.parameters.values():
        if parameter.name == "run_id":
            value: object = "run_20260731T100000Z_example"
        elif parameter.name in {"started_at", "timestamp", "now"}:
            value = _FIXED_TIME
        elif parameter.name in {"message", "status_message"}:
            value = "Validation started"
        elif parameter.default is not inspect.Parameter.empty:
            continue
        else:
            raise AssertionError(
                "unsupported required begin_run parameter: "
                f"{parameter.name}"
            )

        if parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
            positional.append(value)
        else:
            keywords[parameter.name] = value

    model.begin_run(*positional, **keywords)


def _flatten_dataclass(value: object) -> tuple[object, ...]:
    flattened: list[object] = []
    for item in fields(value):
        member = getattr(value, item.name)
        if isinstance(member, Mapping):
            flattened.extend(member.keys())
            flattened.extend(member.values())
        elif isinstance(member, tuple):
            flattened.extend(member)
        else:
            flattened.append(member)
    return tuple(flattened)


def test_gui_request_round_trips_only_permitted_application_state() -> None:
    state = _state()

    request = GuiRunRequest.from_state(state)

    assert request.environment_state() == state.environment
    assert request.selection_state() == state.selection

    forbidden_language_truth = {
        "language_key",
        "language_directory",
        "module_suffix",
        "source_inventory",
        "available_entrypoints",
        "capability_statuses",
    }
    assert forbidden_language_truth.isdisjoint(
        {item.name for item in fields(request)}
    )

    for item in fields(request):
        value = getattr(request, item.name)
        if isinstance(value, Mapping):
            assert isinstance(value, MappingProxyType)
            with pytest.raises(TypeError):
                value["mutated"] = True  # type: ignore[index]


def test_gui_request_is_immutable_and_normalizes_state_paths() -> None:
    request = GuiRunRequest.from_state(_state())

    with pytest.raises(FrozenInstanceError):
        request.target_file = "changed.gf"  # type: ignore[misc]

    environment = request.environment_state()
    assert environment.last_selected_language_path == (
        "C:/gf/gf-rgl/src/example/GrammarEx.gf"
    )
    assert environment.last_selected_validation_profile is None
    assert environment.gf_executable == "C:/gf/bin/gf.exe"
    assert environment.rgl_root == "C:/gf/gf-rgl"
    assert environment.output_root == "C:/work/GF_Wordbench/runs"


def test_progress_view_exposes_known_and_indeterminate_progress() -> None:
    known = _progress(total=4)

    assert not known.indeterminate
    assert known.fraction == pytest.approx(0.5)
    assert known.elapsed_seconds == pytest.approx(5.0)

    unknown = _progress(total=None)

    assert unknown.indeterminate
    assert unknown.fraction is None
    assert unknown.elapsed_seconds == pytest.approx(5.0)


@pytest.mark.parametrize("cls", (StatusCounts, FailureCounts))
def test_count_views_reject_negative_counts(cls: type[Any]) -> None:
    kwargs = {item.name: 0 for item in fields(cls)}
    assert cls(**kwargs) is not None

    first = fields(cls)[0].name
    kwargs[first] = -1
    with pytest.raises(ValueError):
        cls(**kwargs)


def test_presentation_value_objects_are_frozen_and_slotted() -> None:
    public_values = (
        GuiRunRequest,
        LanguageView,
        ProgressView,
        StatusCounts,
        FailureCounts,
        ResultView,
        ArtifactAction,
        ActivityItem,
        GuiSnapshot,
    )

    for cls in public_values:
        assert is_dataclass(cls)
        parameters = cls.__dataclass_params__
        assert parameters.frozen
        assert hasattr(cls, "__slots__")


def test_language_context_does_not_embed_validation_profile_policy() -> None:
    field_names = {item.name for item in fields(ResolvedLanguageContext)}

    assert "validation_profile" not in field_names
    assert "required_scenarios" not in field_names
    assert "checkpoints" not in field_names
    assert "release_gates" not in field_names


def test_language_view_comes_only_from_resolved_language_context(
    tmp_path: Path,
) -> None:
    context = _language_context(tmp_path)

    view = language_view_from_context(context)

    assert isinstance(view, LanguageView)
    flattened = _flatten_dataclass(view)

    assert context.language_key in flattened
    assert context.module_suffix in flattened
    assert any(
        value in {
            context.language_directory,
            context.language_directory.as_posix(),
        }
        for value in flattened
    )
    assert any(
        value in {
            context.rgl_source_root,
            context.rgl_source_root.as_posix(),
        }
        for value in flattened
    )
    for entrypoint in context.available_entrypoints:
        assert entrypoint in flattened or entrypoint.as_posix() in flattened


def test_initial_snapshot_is_idle_without_loaded_language() -> None:
    state = _state()
    model = _view_model(state)

    assert model.request == GuiRunRequest.from_state(state)
    assert model.persistable_state() == state

    snapshot = model.snapshot()

    assert isinstance(snapshot, GuiSnapshot)
    assert snapshot.request == model.request
    assert snapshot.run_state is RunPresentationState.IDLE
    assert snapshot.language is None
    assert snapshot.progress is None
    assert snapshot.result is None
    assert snapshot.artifact_actions == ()
    assert snapshot.activity == ()
    assert snapshot.notices == ()


def test_request_and_language_changes_are_allowed_only_while_idle(
    tmp_path: Path,
) -> None:
    model = _view_model(_state())
    context = _language_context(tmp_path)

    updated = replace(
        model.request,
        target_file="MorphologyEx.gf",
    )
    model.update_request(updated)
    assert model.request == updated

    model.load_language_context(context)
    assert model.snapshot().language == language_view_from_context(context)

    _call_begin_run(model)

    running = model.snapshot()
    assert running.run_state is RunPresentationState.RUNNING
    assert running.progress is not None

    with pytest.raises(RuntimeError):
        model.update_request(
            replace(updated, target_file="OtherEx.gf")
        )

    with pytest.raises(RuntimeError):
        model.clear_language_context()

    with pytest.raises(RuntimeError):
        model.load_language_context(context)


def test_clearing_language_context_does_not_erase_remembered_path(
    tmp_path: Path,
) -> None:
    state = _state()
    model = _view_model(state)
    model.load_language_context(_language_context(tmp_path))

    model.clear_language_context()

    snapshot = model.snapshot()
    assert snapshot.language is None
    assert model.persistable_state().environment.last_selected_language_path == (
        state.environment.last_selected_language_path
    )


def test_structured_progress_updates_snapshot_and_bounded_activity(
    tmp_path: Path,
) -> None:
    model = _view_model(_state())
    model.load_language_context(_language_context(tmp_path))
    _call_begin_run(model)

    for index in range(5):
        model.apply_progress(
            ProgressEvent(
                timestamp=_FIXED_TIME + timedelta(seconds=index + 1),
                message=f"Compiled subject {index}",
                severity=(
                    EventLevel.WARN
                    if index == 3
                    else EventLevel.INFO
                ),
                run_id="run_20260731T100000Z_example",
                stage="compile",
                subject=f"Module{index}.gf",
                completed=index + 1,
                total=5,
            )
        )

    snapshot = model.snapshot()

    assert snapshot.run_state is RunPresentationState.RUNNING
    assert snapshot.progress is not None
    assert snapshot.progress.stage == "compile"
    assert snapshot.progress.subject == "Module4.gf"
    assert snapshot.progress.completed == 5
    assert snapshot.progress.total == 5
    assert len(snapshot.activity) == 3
    assert snapshot.activity[-1].message == "Compiled subject 4"
    assert any(
        item.level is EventLevel.WARN
        for item in snapshot.activity
    )


def test_cancellation_request_is_idempotent_and_disables_repeat_request(
    tmp_path: Path,
) -> None:
    model = _view_model(_state())
    model.load_language_context(_language_context(tmp_path))
    _call_begin_run(model)

    first = model.request_cancellation()
    after_first = model.snapshot()
    second = model.request_cancellation()
    after_second = model.snapshot()

    assert after_first.run_state is RunPresentationState.CANCELLING
    assert after_second.run_state is RunPresentationState.CANCELLING
    assert after_second.activity == after_first.activity
    if isinstance(first, bool):
        assert first
    if isinstance(second, bool):
        assert not second


def test_notices_and_activity_are_presentation_only() -> None:
    state = _state()
    model = _view_model(state)

    model.add_notice("State could not be saved.")
    assert model.snapshot().notices == ("State could not be saved.",)
    assert model.persistable_state() == state

    model.clear_notices()
    model.clear_activity()

    snapshot = model.snapshot()
    assert snapshot.notices == ()
    assert snapshot.activity == ()
    assert model.persistable_state() == state
