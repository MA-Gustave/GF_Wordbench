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
    ProgressView,
    ProjectView,
    ResultView,
    RunPresentationState,
    StatusCounts,
    project_view_from_config,
)
from gf_wordbench.kernel.events import EventLevel, ProgressEvent
from gf_wordbench.kernel.serialization import ProducerInfo
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.projects.models import (
    GFProjectConfig,
    ModuleTargets,
    PROJECT_SCHEMA_ID,
    PROJECT_SCHEMA_VERSION,
    ProjectConfig,
    ProjectIdentity,
    SourceConfig,
    ValidationPolicy,
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

_FIXED_TIME: Final[datetime] = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)


def _state() -> AppState:
    return AppState(
        schema_id=APP_STATE_SCHEMA_ID,
        schema_version=APP_STATE_SCHEMA_VERSION,
        producer=ProducerInfo(
            name="gf-wordbench",
            version="1.0.0",
        ),
        environment=EnvironmentState(
            project_root="C:/work/GF_Wordbench/project",
            rgl_root="C:/gf/rgl",
            gf_executable="C:/gf/bin/gf.exe",
            output_root="C:/work/GF_Wordbench/runs",
        ),
        selection=SelectionState(
            mode=ValidationMode.CHECKPOINT,
            target_file="lib/src/example/GrammarEx.gf",
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


def _project(tmp_path: Path) -> ProjectConfig:
    root = (tmp_path / "project").resolve()
    source_directory = Path("lib/src/example")
    return ProjectConfig(
        schema_id=PROJECT_SCHEMA_ID,
        schema_version=PROJECT_SCHEMA_VERSION,
        identity=ProjectIdentity(
            id="example",
            name="Example Language",
            language_code="ex",
            root=Path("."),
        ),
        sources=SourceConfig(
            directory=source_directory,
            glob="*.gf",
            include_regex=r".*\.gf$",
            exclude_regex=r"(?:^|/)attic(?:/|$)",
        ),
        gf=GFProjectConfig(
            path_parts=("lib/src/example", "lib/src/common"),
            minimum_version="3.11",
        ),
        modules=ModuleTargets(
            entrypoints=(Path("GrammarEx.gf"),),
            checkpoints=(Path("MorphologyEx.gf"),),
        ),
        validation=ValidationPolicy(
            required_scenarios=("smoke",),
            optional_scenarios=("regression",),
            release_requires_pgf=True,
        ),
        project_file=root / "project.toml",
        project_root=root,
        source_root=root / source_directory,
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
        elif lowered == "direct":
            values[name] = 0
        elif lowered == "downstream":
            values[name] = 0
        elif lowered == "ambiguous":
            values[name] = 0
        elif lowered == "stage":
            values[name] = "compile"
        elif lowered == "subject":
            values[name] = "GrammarEx.gf"
        elif lowered == "message":
            values[name] = "Compiling GrammarEx.gf"
        elif lowered == "run_id":
            values[name] = "run_20260725T120000Z_example"
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
            value: object = "run_20260725T120000Z_example"
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


def test_gui_request_round_trips_only_permitted_application_state() -> None:
    state = _state()

    request = GuiRunRequest.from_state(state)

    assert request.environment_state() == state.environment
    assert request.selection_state() == state.selection

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
    assert environment.project_root == "C:/work/GF_Wordbench/project"
    assert environment.gf_executable == "C:/gf/bin/gf.exe"
    assert environment.rgl_root == "C:/gf/rgl"
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
    kwargs = {
        item.name: 0
        for item in fields(cls)
    }
    assert cls(**kwargs) is not None

    first = fields(cls)[0].name
    kwargs[first] = -1
    with pytest.raises(ValueError):
        cls(**kwargs)


def test_presentation_value_objects_are_frozen_and_slotted() -> None:
    public_values = (
        GuiRunRequest,
        ProjectView,
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


def test_project_view_comes_only_from_project_configuration(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)

    view = project_view_from_config(project)

    assert isinstance(view, ProjectView)
    values = {
        item.name: getattr(view, item.name)
        for item in fields(view)
    }
    flattened: list[object] = []
    for value in values.values():
        if isinstance(value, tuple):
            flattened.extend(value)
        else:
            flattened.append(value)

    assert project.identity.id in flattened
    assert project.identity.name in flattened
    assert project.identity.language_code in flattened
    assert any(
        value in {
            project.project_root,
            project.project_root.as_posix(),
        }
        for value in flattened
    )
    assert any(
        value in {
            project.source_root,
            project.source_root.as_posix(),
        }
        for value in flattened
    )


def test_initial_snapshot_is_idle_and_preserves_last_completed_run() -> None:
    state = _state()
    model = _view_model(state)

    assert model.request == GuiRunRequest.from_state(state)
    assert model.persistable_state() == state

    snapshot = model.snapshot()

    assert isinstance(snapshot, GuiSnapshot)
    assert snapshot.request == model.request
    assert snapshot.run_state is RunPresentationState.IDLE
    assert snapshot.project is None
    assert snapshot.progress is None
    assert snapshot.result is None
    assert snapshot.artifact_actions == ()
    assert snapshot.activity == ()
    assert snapshot.notices == ()


def test_request_and_project_changes_are_allowed_only_while_idle(
    tmp_path: Path,
) -> None:
    model = _view_model(_state())
    project = _project(tmp_path)

    updated = replace(
        model.request,
        target_file="lib/src/example/MorphologyEx.gf",
    )
    model.update_request(updated)
    assert model.request == updated

    model.load_project(project)
    assert model.snapshot().project == project_view_from_config(project)

    _call_begin_run(model)

    running = model.snapshot()
    assert running.run_state is RunPresentationState.RUNNING
    assert running.progress is not None

    with pytest.raises(RuntimeError):
        model.update_request(
            replace(updated, target_file="lib/src/example/Other.gf")
        )

    with pytest.raises(RuntimeError):
        model.clear_project()


def test_structured_progress_updates_snapshot_and_bounded_activity(
    tmp_path: Path,
) -> None:
    model = _view_model(_state())
    model.load_project(_project(tmp_path))
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
                run_id="run_20260725T120000Z_example",
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
    model.load_project(_project(tmp_path))
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
