"""Shared runtime for the GF Wordbench mini diagnostic suite.

The module intentionally depends only on the Python standard library.  It
launches Wordbench's public CLI and existing repository checks as child
processes; it does not reimplement GF compilation, scenarios, gold
comparison, diagnostics classification, or release policy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import traceback
from typing import Any, Callable, Iterable, Mapping, Sequence

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
SKIP = "SKIP"
BLOCKED = "BLOCKED"
PARTIAL = "PARTIAL"
ERROR = "ERROR"
INFRA_ERROR = "INFRA_ERROR"
CONFIG_ERROR = "CONFIG_ERROR"

_STATUS_ORDER = {
    PASS: 0,
    SKIP: 1,
    WARN: 2,
    PARTIAL: 3,
    FAIL: 4,
    BLOCKED: 4,
    INFRA_ERROR: 5,
    CONFIG_ERROR: 5,
    ERROR: 6,
}

LogFn = Callable[[str], None]
CheckFn = Callable[["DiagConfig", "DiagReport", LogFn], None]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_slug(value: str) -> str:
    result = []
    for char in value.strip().lower():
        if char.isalnum():
            result.append(char)
        elif char in {"-", "_", " ", "/", "\\", "."}:
            result.append("-")
    slug = "".join(result).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "item"


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = _deep_merge(dict(merged[key]), value)
        else:
            merged[key] = value
    return merged


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def detect_repo_root(start: Path | None = None) -> Path:
    explicit = os.environ.get("WORDBENCH_DIAG_REPO_ROOT")
    if explicit:
        return Path(explicit).expanduser().resolve()

    origin = (start or Path(__file__).resolve()).resolve()
    if origin.is_file():
        origin = origin.parent
    for candidate in (origin, *origin.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "src" / "gf_wordbench"
        ).is_dir():
            return candidate

    # Expected location after extracting at the Wordbench repository root.
    expected = Path(__file__).resolve().parents[2]
    return expected


@dataclass(frozen=True, slots=True)
class DiagConfig:
    suite_root: Path
    repo_root: Path
    app_name: str
    artifact_root: Path
    project_root: Path
    output_root: Path | None
    gf_executable: str
    rgl_root: Path | None
    raw: dict[str, Any]
    config_path: Path | None = None

    def get(self, dotted: str, default: Any = None) -> Any:
        current: Any = self.raw
        for part in dotted.split("."):
            if not isinstance(current, Mapping) or part not in current:
                return default
            current = current[part]
        return current

    def timeout(self, name: str, default: int) -> int:
        value = self.get(f"timeouts.{name}", default)
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default


def load_config() -> DiagConfig:
    suite_root = Path(__file__).resolve().parent
    repo_root = detect_repo_root(suite_root)
    defaults: dict[str, Any] = {
        "schema": "wordbench.minidiag.config.v1",
        "app_name": "GF Wordbench Mini Diagnostics",
        "artifact_dir": ".wordbench-diagnostics",
        "project_root": "project",
        "output_root": "",
        "gf_executable": "gf",
        "rgl_root": "",
        "wordbench_command": ["{python}", "-m", "gf_wordbench"],
        "required_paths": [
            "pyproject.toml",
            "src/gf_wordbench",
            "tests",
            "scripts",
            "project",
        ],
        "summary_globs": [
            "runs/run_*/summary.json",
            "run_*/summary.json",
            "project/runs/run_*/summary.json",
            "project/run_*/summary.json",
        ],
        "timeouts": {
            "short": 30,
            "normal": 180,
            "tests": 1200,
            "quick": 900,
            "release": 7200,
        },
        "runtime_smoke": {
            "run_quick": False,
            "target": "",
            "strict": False,
        },
        "release": {
            "require_pgf": None,
            "required_files": [
                "summary.json",
                "summary.md",
                "AI_READY.md",
                "top_errors.txt",
                "manifest.json",
            ],
        },
    }

    chosen: Path | None = None
    local = suite_root / "diag.config.local.json"
    example = suite_root / "diag.config.example.json"
    raw = defaults
    if example.is_file():
        raw = _deep_merge(raw, _read_json(example))
    if local.is_file():
        chosen = local
        raw = _deep_merge(raw, _read_json(local))

    root_override = os.environ.get("WORDBENCH_DIAG_REPO_ROOT")
    if root_override:
        repo_root = Path(root_override).expanduser().resolve()

    def root_path(value: Any, default: str) -> Path:
        text = str(value if value not in (None, "") else default)
        path = Path(text).expanduser()
        return path.resolve() if path.is_absolute() else (repo_root / path).resolve()

    artifact_dir = os.environ.get(
        "WORDBENCH_DIAG_ARTIFACT_DIR", str(raw.get("artifact_dir", ".wordbench-diagnostics"))
    )
    project_dir = os.environ.get(
        "WORDBENCH_DIAG_PROJECT_ROOT", str(raw.get("project_root", "project"))
    )
    output_value = os.environ.get(
        "WORDBENCH_DIAG_OUTPUT_ROOT", str(raw.get("output_root", ""))
    ).strip()
    rgl_value = os.environ.get(
        "WORDBENCH_DIAG_RGL_ROOT", str(raw.get("rgl_root", ""))
    ).strip()
    gf_executable = os.environ.get(
        "WORDBENCH_DIAG_GF_EXECUTABLE", str(raw.get("gf_executable", "gf"))
    )

    return DiagConfig(
        suite_root=suite_root,
        repo_root=repo_root,
        app_name=str(raw.get("app_name", defaults["app_name"])),
        artifact_root=root_path(artifact_dir, ".wordbench-diagnostics"),
        project_root=root_path(project_dir, "project"),
        output_root=root_path(output_value, "runs") if output_value else None,
        gf_executable=gf_executable,
        rgl_root=root_path(rgl_value, rgl_value) if rgl_value else None,
        raw=raw,
        config_path=chosen,
    )


def build_env(config: DiagConfig) -> dict[str, str]:
    env = os.environ.copy()
    source_root = config.repo_root / "src"
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(source_root) + (os.pathsep + existing if existing else "")
    env["WORDBENCH_DIAG_REPO_ROOT"] = str(config.repo_root)
    if config.output_root is not None:
        env.setdefault("GF_WORDBENCH_OUTPUT_ROOT", str(config.output_root))
    if config.rgl_root is not None:
        env.setdefault("GF_WORDBENCH_RGL_ROOT", str(config.rgl_root))
    return env


def console_python() -> str:
    """Return python.exe when the current process is pythonw.exe on Windows."""
    executable = Path(sys.executable)
    if executable.name.lower() == "pythonw.exe":
        candidate = executable.with_name("python.exe")
        if candidate.is_file():
            return str(candidate)
    return str(executable)


def _token_map(config: DiagConfig) -> dict[str, str]:
    return {
        "python": console_python(),
        "repo": str(config.repo_root),
        "project": str(config.project_root),
        "artifacts": str(config.artifact_root),
        "output": str(config.output_root or ""),
        "gf": config.gf_executable,
        "rgl": str(config.rgl_root or ""),
    }


def expand_command(config: DiagConfig, command: Sequence[str]) -> list[str]:
    mapping = _token_map(config)
    expanded: list[str] = []
    for part in command:
        text = str(part)
        for key, value in mapping.items():
            text = text.replace("{" + key + "}", value)
        expanded.append(text)
    return expanded


def wordbench_command(config: DiagConfig, *arguments: str) -> list[str]:
    raw = config.get("wordbench_command", ["{python}", "-m", "gf_wordbench"])
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("wordbench_command must be a JSON array of command parts")
    return [*expand_command(config, [str(item) for item in raw]), *arguments]


def common_path_arguments(config: DiagConfig, *, include_output: bool) -> list[str]:
    args = ["--project-root", str(config.project_root)]
    if config.gf_executable:
        args.extend(["--gf-executable", config.gf_executable])
    if config.rgl_root is not None:
        args.extend(["--rgl-root", str(config.rgl_root)])
    if include_output and config.output_root is not None:
        args.extend(["--output-root", str(config.output_root)])
    return args


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def executable_available(value: str) -> bool:
    path = Path(value).expanduser()
    if path.is_absolute() or path.parent != Path("."):
        return path.is_file()
    return shutil.which(value) is not None


@dataclass(slots=True)
class StepResult:
    name: str
    command: list[str]
    cwd: str
    status: str
    exit_code: int | None
    started_at: str
    ended_at: str
    duration_seconds: float
    output: str = ""
    exception: str | None = None

    def to_dict(self, *, include_output: bool = False) -> dict[str, Any]:
        data = asdict(self)
        if not include_output:
            data["output"] = self.output[-8000:]
        return data


def run_command(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout: int,
    env: Mapping[str, str] | None = None,
    name: str = "command",
) -> StepResult:
    started = datetime.now()
    started_at = started.isoformat(timespec="seconds")
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd),
            env=dict(env) if env is not None else None,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            shell=False,
        )
        status = PASS if completed.returncode == 0 else FAIL
        exit_code: int | None = completed.returncode
        output = completed.stdout or ""
        exception = None
    except subprocess.TimeoutExpired as exc:
        status = INFRA_ERROR
        exit_code = None
        output = exc.stdout if isinstance(exc.stdout, str) else ""
        output += f"\n[TIMEOUT after {timeout} seconds]"
        exception = "TimeoutExpired"
    except (FileNotFoundError, PermissionError, OSError) as exc:
        status = INFRA_ERROR
        exit_code = None
        output = f"{type(exc).__name__}: {exc}"
        exception = type(exc).__name__
    ended = datetime.now()
    return StepResult(
        name=name,
        command=list(command),
        cwd=str(cwd),
        status=status,
        exit_code=exit_code,
        started_at=started_at,
        ended_at=ended.isoformat(timespec="seconds"),
        duration_seconds=round((ended - started).total_seconds(), 3),
        output=output,
        exception=exception,
    )


@dataclass(slots=True)
class Finding:
    id: str
    severity: str
    category: str
    message: str
    evidence: str | None = None
    recommendation: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Artifact:
    kind: str
    path: str
    description: str = ""


@dataclass(slots=True)
class DiagReport:
    schema: str
    suite: str
    level: str
    name: str
    purpose: str
    started_at: str
    finished_at: str
    repo_root: str
    project_root: str
    verdict: str
    artifact_dir: Path = field(repr=False)
    findings: list[Finding] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    steps: list[StepResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        config: DiagConfig,
        *,
        level: str,
        name: str,
        purpose: str,
    ) -> "DiagReport":
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        artifact_dir = (
            config.artifact_root / f"{level}-{_safe_slug(name)}" / stamp
        )
        artifact_dir.mkdir(parents=True, exist_ok=True)
        now = _now()
        return cls(
            schema="wordbench.minidiag.report.v1",
            suite="GF Wordbench Mini Diagnostics",
            level=level,
            name=name,
            purpose=purpose,
            started_at=now,
            finished_at=now,
            repo_root=str(config.repo_root),
            project_root=str(config.project_root),
            verdict=PASS,
            artifact_dir=artifact_dir,
            metadata={
                "python": sys.version,
                "platform": sys.platform,
                "config_path": str(config.config_path) if config.config_path else None,
            },
        )

    def add(
        self,
        finding_id: str,
        severity: str,
        category: str,
        message: str,
        *,
        evidence: str | None = None,
        recommendation: str | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> None:
        normalized = severity if severity in _STATUS_ORDER else ERROR
        self.findings.append(
            Finding(
                id=finding_id,
                severity=normalized,
                category=category,
                message=message,
                evidence=evidence,
                recommendation=recommendation,
                data=dict(data or {}),
            )
        )
        self.recompute()

    def add_artifact(self, kind: str, path: Path, description: str = "") -> None:
        self.artifacts.append(Artifact(kind, str(path), description))

    def recompute(self) -> None:
        self.finished_at = _now()
        if not self.findings:
            self.verdict = PASS
            return
        self.verdict = max(
            (item.severity for item in self.findings),
            key=lambda status: _STATUS_ORDER.get(status, _STATUS_ORDER[ERROR]),
        )

    def summary(self) -> dict[str, int]:
        result = {status.lower(): 0 for status in _STATUS_ORDER}
        for item in self.findings:
            result[item.severity.lower()] = result.get(item.severity.lower(), 0) + 1
        return result

    def to_dict(self) -> dict[str, Any]:
        self.recompute()
        return {
            "schema": self.schema,
            "suite": self.suite,
            "level": self.level,
            "name": self.name,
            "purpose": self.purpose,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "repo_root": self.repo_root,
            "project_root": self.project_root,
            "verdict": self.verdict,
            "summary": self.summary(),
            "findings": [asdict(item) for item in self.findings],
            "artifacts": [asdict(item) for item in self.artifacts],
            "steps": [item.to_dict() for item in self.steps],
            "metadata": self.metadata,
        }

    def write(self) -> tuple[Path, Path]:
        json_path = self.artifact_dir / f"{self.level}-report.json"
        txt_path = self.artifact_dir / f"{self.level}-report.txt"
        json_path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        lines = [
            f"GF Wordbench Mini Diagnostics — {self.level} {self.name}",
            f"Verdict: {self.verdict}",
            f"Repository: {self.repo_root}",
            f"Project: {self.project_root}",
            f"Started: {self.started_at}",
            f"Finished: {self.finished_at}",
            "",
            "Findings:",
        ]
        for finding in self.findings:
            lines.append(f"- [{finding.severity}] {finding.id}: {finding.message}")
            if finding.evidence:
                lines.append(f"  evidence: {finding.evidence}")
            if finding.recommendation:
                lines.append(f"  recommendation: {finding.recommendation}")
        txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.add_artifact("report-json", json_path, "Structured diagnostic report")
        self.add_artifact("report-text", txt_path, "Human-readable diagnostic report")
        # Rewrite JSON once so the report artifact list includes itself.
        json_path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return json_path, txt_path


def _command_text(command: Sequence[str]) -> str:
    return subprocess.list2cmdline(list(command))


def execute_step(
    config: DiagConfig,
    report: DiagReport,
    log: LogFn,
    *,
    step_id: str,
    title: str,
    command: Sequence[str],
    timeout: int,
    accepted_codes: Iterable[int] = (0,),
    required: bool = True,
    cwd: Path | None = None,
) -> StepResult:
    expanded = expand_command(config, command)
    log(f"RUN {title}: {_command_text(expanded)}")
    result = run_command(
        expanded,
        cwd=cwd or config.repo_root,
        timeout=timeout,
        env=build_env(config),
        name=title,
    )
    report.steps.append(result)
    log_path = report.artifact_dir / f"{_safe_slug(step_id)}.log"
    log_path.write_text(result.output, encoding="utf-8", errors="replace")
    report.add_artifact("command-log", log_path, title)

    if result.status == INFRA_ERROR:
        severity = BLOCKED if required else WARN
        message = f"{title} could not be executed"
        recommendation = "Install or configure the required tool, then rerun this level."
    elif result.exit_code in set(accepted_codes):
        severity = PASS
        message = f"{title} completed successfully"
        recommendation = None
    else:
        severity = FAIL
        message = f"{title} returned exit code {result.exit_code}"
        recommendation = f"Review {log_path} and correct the failing Wordbench check."

    tail = result.output[-2000:].strip() or None
    report.add(
        step_id,
        severity,
        "command",
        message,
        evidence=tail,
        recommendation=recommendation,
        data={
            "command": expanded,
            "cwd": result.cwd,
            "exit_code": result.exit_code,
            "duration_seconds": result.duration_seconds,
            "log": str(log_path),
        },
    )
    log(f"{severity} {title} ({result.duration_seconds:.3f}s)")
    return result


def execute_python_module(
    config: DiagConfig,
    report: DiagReport,
    log: LogFn,
    *,
    module: str,
    arguments: Sequence[str],
    step_id: str,
    title: str,
    timeout: int,
    required: bool,
) -> StepResult | None:
    if not module_available(module):
        severity = BLOCKED if required else WARN
        report.add(
            step_id,
            severity,
            "tooling",
            f"Python module {module!r} is not installed",
            recommendation=f"Install the Wordbench development dependencies providing {module}.",
        )
        log(f"{severity} {title}: module {module!r} unavailable")
        return None
    return execute_step(
        config,
        report,
        log,
        step_id=step_id,
        title=title,
        command=[sys.executable, "-m", module, *arguments],
        timeout=timeout,
        required=required,
    )


def find_summary_files(config: DiagConfig) -> list[Path]:
    found: dict[str, Path] = {}
    if config.output_root is not None and config.output_root.exists():
        for path in config.output_root.glob("run_*/summary.json"):
            found[str(path.resolve())] = path.resolve()
    for pattern in config.get("summary_globs", []):
        if not isinstance(pattern, str) or not pattern:
            continue
        for path in config.repo_root.glob(pattern):
            if path.is_file():
                found[str(path.resolve())] = path.resolve()
    return sorted(found.values(), key=lambda item: item.stat().st_mtime_ns)


def summary_snapshot(config: DiagConfig) -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    for path in find_summary_files(config):
        try:
            stat = path.stat()
        except OSError:
            continue
        result[str(path)] = (stat.st_mtime_ns, stat.st_size)
    return result


def newest_changed_summary(
    config: DiagConfig,
    before: Mapping[str, tuple[int, int]],
) -> Path | None:
    changed: list[Path] = []
    for path in find_summary_files(config):
        try:
            stat = path.stat()
        except OSError:
            continue
        identity = (stat.st_mtime_ns, stat.st_size)
        if before.get(str(path)) != identity:
            changed.append(path)
    return max(changed, key=lambda item: item.stat().st_mtime_ns) if changed else None


def _first_value(data: Mapping[str, Any], paths: Sequence[Sequence[str]]) -> Any:
    for parts in paths:
        current: Any = data
        for part in parts:
            if not isinstance(current, Mapping) or part not in current:
                current = None
                break
            current = current[part]
        if current is not None:
            return current
    return None


def inspect_summary(
    report: DiagReport,
    summary_path: Path,
    *,
    expected_mode: str | None,
    require_success: bool,
) -> dict[str, Any] | None:
    try:
        data = _read_json(summary_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report.add(
            "run.summary.read",
            FAIL,
            "evidence",
            f"Could not read structured run summary: {exc}",
            evidence=str(summary_path),
        )
        return None

    report.add_artifact("wordbench-summary", summary_path, "Wordbench structured run summary")
    mode = _first_value(
        data,
        (("mode",), ("validation_mode",), ("request", "mode"), ("context", "mode")),
    )
    status = _first_value(
        data,
        (("overall_status",), ("status",), ("result", "overall_status")),
    )
    report.add(
        "run.summary.read",
        PASS,
        "evidence",
        "Structured run summary is readable",
        evidence=str(summary_path),
    )
    if expected_mode is not None:
        if str(mode).lower() == expected_mode.lower():
            report.add(
                "run.summary.mode",
                PASS,
                "evidence",
                f"Run summary records mode {expected_mode!r}",
            )
        else:
            report.add(
                "run.summary.mode",
                FAIL,
                "evidence",
                f"Expected mode {expected_mode!r}, found {mode!r}",
            )
    if require_success:
        if str(status).upper() in {"OK", "PASS", "SUCCESS", "READY"}:
            report.add(
                "run.summary.status",
                PASS,
                "evidence",
                f"Run summary records successful status {status!r}",
            )
        else:
            report.add(
                "run.summary.status",
                FAIL,
                "evidence",
                f"Run summary does not record success: {status!r}",
            )
    elif status is None:
        report.add(
            "run.summary.status",
            WARN,
            "evidence",
            "Run summary status field was not recognized by the mini-suite",
        )
    return data


def open_path(path: Path) -> None:
    target = path.resolve()
    if sys.platform.startswith("win"):
        os.startfile(str(target))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])


def report_exit_code(verdict: str) -> int:
    if verdict in {PASS, SKIP, WARN}:
        return 0
    if verdict in {FAIL, BLOCKED, PARTIAL}:
        return 2
    if verdict == INFRA_ERROR:
        return 3
    if verdict == CONFIG_ERROR:
        return 4
    return 5


def run_headless(
    level_id: str,
    level_name: str,
    purpose: str,
    run_checks: CheckFn,
) -> int:
    config = load_config()
    report = DiagReport.create(
        config,
        level=level_id,
        name=level_name,
        purpose=purpose,
    )

    def log(message: str) -> None:
        print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)

    try:
        run_checks(config, report, log)
    except Exception as exc:  # Diagnostic tools must report their own bugs.
        report.add(
            "level.exception",
            ERROR,
            "mini-suite",
            f"{type(exc).__name__}: {exc}",
            evidence=traceback.format_exc(),
        )
    json_path, txt_path = report.write()
    log(f"Verdict: {report.verdict}")
    log(f"JSON report: {json_path}")
    log(f"Text report: {txt_path}")
    return report_exit_code(report.verdict)


class LevelWindow:
    def __init__(
        self,
        level_id: str,
        level_name: str,
        purpose: str,
        run_checks: CheckFn,
    ) -> None:
        try:
            import tkinter as tk
            from tkinter import messagebox, ttk
        except ImportError as exc:
            raise RuntimeError("Tkinter is required for graphical diagnostic windows") from exc

        self.tk = tk
        self.ttk = ttk
        self.messagebox = messagebox
        self.root = tk.Tk()
        self.level_id = level_id
        self.level_name = level_name
        self.purpose = purpose
        self.run_checks = run_checks
        self.config = load_config()
        self.report: DiagReport | None = None
        self.status_var = tk.StringVar(value="Ready")
        self.root.title(f"Wordbench Diagnostics {level_id} — {level_name}")
        self.root.geometry("980x680")
        self.root.minsize(780, 520)
        self._build()
        self.log(f"Repository: {self.config.repo_root}")
        self.log(f"Project: {self.config.project_root}")
        self.log(f"Configuration: {self.config.config_path or 'built-in defaults'}")

    def _build(self) -> None:
        outer = self.ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)
        self.ttk.Label(
            outer,
            text=f"{self.level_id} — {self.level_name}",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        self.ttk.Label(outer, text=self.purpose, wraplength=920).pack(
            anchor="w", pady=(2, 10)
        )
        bar = self.ttk.Frame(outer)
        bar.pack(fill="x", pady=(0, 8))
        self.run_button = self.ttk.Button(bar, text="Run", command=self.run_async)
        self.run_button.pack(side="left")
        self.ttk.Button(
            bar,
            text="Open artifacts",
            command=lambda: open_path(self.config.artifact_root),
        ).pack(side="left", padx=6)
        self.ttk.Button(bar, text="Copy log", command=self.copy_log).pack(
            side="left", padx=6
        )
        self.ttk.Label(bar, textvariable=self.status_var).pack(side="right")
        frame = self.ttk.LabelFrame(outer, text="Log")
        frame.pack(fill="both", expand=True)
        self.log_text = self.tk.Text(frame, wrap="word", font=("Consolas", 9))
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar = self.ttk.Scrollbar(frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def log(self, message: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {message}\n"

        def append() -> None:
            self.log_text.insert("end", line)
            self.log_text.see("end")

        try:
            self.root.after(0, append)
        except RuntimeError:
            pass

    def copy_log(self) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log_text.get("1.0", "end").strip())

    def run_async(self) -> None:
        self.run_button.configure(state="disabled")
        self.status_var.set("RUNNING")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self) -> None:
        report = DiagReport.create(
            self.config,
            level=self.level_id,
            name=self.level_name,
            purpose=self.purpose,
        )
        self.report = report
        try:
            self.run_checks(self.config, report, self.log)
        except Exception as exc:
            report.add(
                "level.exception",
                ERROR,
                "mini-suite",
                f"{type(exc).__name__}: {exc}",
                evidence=traceback.format_exc(),
            )
            self.log(traceback.format_exc())
        json_path, txt_path = report.write()
        self.log(f"Verdict: {report.verdict}")
        self.log(f"JSON report: {json_path}")
        self.log(f"Text report: {txt_path}")

        def finished() -> None:
            self.status_var.set(report.verdict)
            self.run_button.configure(state="normal")

        self.root.after(0, finished)

    def mainloop(self) -> None:
        self.root.mainloop()


def run_level_app(
    level_id: str,
    level_name: str,
    purpose: str,
    run_checks: CheckFn,
) -> int:
    if "--headless" in sys.argv[1:]:
        return run_headless(level_id, level_name, purpose, run_checks)
    window = LevelWindow(level_id, level_name, purpose, run_checks)
    window.mainloop()
    return 0


def launch_script(script: Path, *, headless: bool, wait: bool = False) -> subprocess.Popen[str]:
    executable = sys.executable
    command = [executable, str(script)]
    if headless:
        command.append("--headless")
    kwargs: dict[str, Any] = {
        "cwd": str(detect_repo_root(script)),
        "env": build_env(load_config()),
        "text": True,
    }
    if sys.platform.startswith("win") and not headless and not wait:
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        if pythonw.is_file():
            command[0] = str(pythonw)
    process = subprocess.Popen(command, **kwargs)
    if wait:
        process.wait()
    return process
