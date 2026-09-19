"""Release checks for GF Wordbench documentation governance and anti-drift rules."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
import re
import tomllib

import pytest

pytestmark = pytest.mark.contract

_ALIGNMENT_AUTHORITY = "docs/DOCUMENTATION_ALIGNMENT_LOCK.md"
_OPTIONAL_ACTIVE_PROFILE_DOCUMENT = "project/docs/INTERFILE_CONTRACT_LOCK.md"

_REQUIRED_DOCUMENTS = {
    "docs/DOCUMENTATION_ALIGNMENT_LOCK.md": (
        "GF-WB-DOC-ALIGNMENT-LOCK",
        "Normative",
    ),
    "docs/DOCUMENTATION_MAP.md": (
        "GF-WB-DOCUMENTATION-MAP",
        "Normative navigation index",
    ),
    "docs/architecture/CANONICAL_FILE_ARCHITECTURE.md": (
        "GF-WB-CANONICAL-FILE-ARCHITECTURE",
        "Normative — final architecture",
    ),
    "docs/INTERFILE_CONTRACT_LOCK.md": (
        "GF-WB-ARCH-INTERFILE-LOCK",
        "Normative",
    ),
    "docs/EXTERNAL_TOOL_CONTRACT_LOCK.md": (
        "GF-WB-EXT-TOOL-LOCK",
        "Normative",
    ),
    "docs/PERSISTED_SCHEMA_LOCK.md": (
        "GF-WB-PERSISTED-SCHEMA-LOCK",
        "Normative",
    ),
    "templates/validation-profile/docs/INTERFILE_CONTRACT_LOCK.md": (
        "GF-WB-PROJECT-TEMPLATE-INTERFILE-LOCK",
        "Normative reusable template contract",
    ),
}

_ALIGNMENT_DELEGATES = (
    "docs/DOCUMENTATION_MAP.md",
    "docs/REPOSITORY_STRUCTURE.md",
    "docs/INTERFILE_CONTRACT_LOCK.md",
    "docs/EXTERNAL_TOOL_CONTRACT_LOCK.md",
    "docs/PERSISTED_SCHEMA_LOCK.md",
    "docs/architecture/ARCHITECTURE_OVERVIEW.md",
    "docs/architecture/ARTIFACT_MODEL.md",
    "docs/architecture/COMPONENT_MAP.md",
    "docs/architecture/DATA_MODEL.md",
    "docs/architecture/EXECUTION_FLOW.md",
    "docs/architecture/EXTENSION_BOUNDARIES.md",
    "docs/architecture/PRODUCT_BOUNDARIES.md",
    "docs/development/TESTING_GF_WORDBENCH.md",
    "docs/release/RELEASE_PROCESS.md",
    "templates/validation-profile/docs/INTERFILE_CONTRACT_LOCK.md",
)

_LOCKED_ALIGNMENT_STATEMENTS = (
    "A running GF Wordbench session has either:",
    "exactly one resolved language context",
    "Changing language ends the current runtime and resolves a new context.",
    "Normal startup begins from one explicit path supplied by the user, CLI or automation:",
    "Grammatical Framework is the authority for GF parsing",
    "Native `.gfs` scenarios remain the scenario execution format.",
    "The accepted target architecture is one deployable hexagonal modular monolith.",
    "Multi-workspace management, multilingual portfolio aggregation",
    "GF Wordbench MUST start, browse, scan, validate, report, release and pass "
    "its tests without `gf-portfolio` installed or reachable.",
)

_REQUIRED_LANGUAGE_LOADER_PATHS = (
    "src/gf_wordbench/entrypoints/gui/startup.py",
    "src/gf_wordbench/projects/languages/__init__.py",
    "src/gf_wordbench/projects/languages/models.py",
    "src/gf_wordbench/projects/languages/ports.py",
    "src/gf_wordbench/projects/languages/probe.py",
    "src/gf_wordbench/projects/languages/public.py",
    "tests/integration/end_to_end/test_path_resolved_language_startup.py",
    "tests/integration/gui/test_language_switching.py",
    "tests/unit/projects/test_language_probe.py",
)


def _repository_root() -> Path:
    root = Path(__file__).resolve().parents[2]
    if not (root / "pyproject.toml").is_file():
        raise AssertionError(f"Unable to locate repository root from {__file__!r}")
    return root


def _read_text(root: Path, relative_path: str) -> str:
    path = root / relative_path
    assert path.is_file(), f"Required documentation file is missing: {relative_path}"

    raw = path.read_bytes()
    assert b"\x00" not in raw, f"Documentation contains NUL bytes: {relative_path}"

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        pytest.fail(f"{relative_path} is not valid UTF-8: {error}")

    assert "\r" not in text, f"{relative_path} must use canonical LF line endings"
    return text


def _metadata_value(text: str, label: str) -> str:
    bold_pattern = rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$"
    table_pattern = rf"^\|\s*{re.escape(label)}\s*\|\s*(.+?)\s*\|$"
    match = re.search(bold_pattern, text, flags=re.MULTILINE)
    if match is None:
        match = re.search(table_pattern, text, flags=re.MULTILINE)
    assert match is not None, f"Missing metadata field: {label}"
    return match.group(1).strip().strip("`").strip("*")


def _text_blocks(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"```text\s*\n(.*?)\n```", text, flags=re.DOTALL))


def _canonical_paths(text: str) -> tuple[str, ...]:
    blocks = _text_blocks(text)
    assert blocks, "Canonical architecture does not contain a text tree"

    tree = blocks[0]
    stack: list[str] = []
    paths: list[str] = []

    for raw_line in tree.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue

        branch_positions = tuple(
            position for marker in ("├── ", "└── ") if (position := line.find(marker)) >= 0
        )

        if branch_positions:
            branch = min(branch_positions)
            depth = branch // 4
            entry = line[branch + 4 :].strip()
        else:
            depth = 0
            entry = line.strip()

        assert entry, f"Malformed canonical tree line: {raw_line!r}"

        if entry.endswith("/"):
            directory = entry[:-1]
            if len(stack) <= depth:
                stack.extend("" for _ in range(depth + 1 - len(stack)))
            stack[depth] = directory
            del stack[depth + 1 :]
            continue

        components = [*stack[:depth], entry]
        if components and components[0] == "GF_Wordbench":
            components.pop(0)

        path = "/".join(components)
        assert path and not path.startswith("/"), f"Invalid canonical path: {path!r}"
        paths.append(path)

    assert len(paths) == len(set(paths)), "Canonical architecture contains duplicate paths"
    return tuple(paths)


def _declared_fixed_counts(text: str) -> dict[str, int]:
    rows = re.findall(
        r"^\|\s*([^|]+?)\s*\|\s*[*`]*(\d+)[*`]*\s*\|$",
        text,
        flags=re.MULTILINE,
    )
    return {label.strip().strip("*`"): int(value) for label, value in rows}


def _markdown_links(text: str) -> Iterable[str]:
    for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
        target = match.group(1).strip()
        if target:
            yield target


def _ledger_exclusions(root: Path) -> frozenset[str]:
    ledger = _read_text(root, "docs/DOCUMENTATION_CORRECTION_LEDGER.md")
    section = ledger.partition("## 5. Repository reconciliation exclusions")[2]
    section = section.partition("\n## ")[0]
    return frozenset(re.findall(r"^\|\s*`([^`]+)`\s*\|", section, flags=re.MULTILINE))


def _repository_target(
    root: Path,
    source: Path,
    markdown_target: str,
) -> Path | None:
    target = markdown_target.split("#", 1)[0].strip()
    if not target or "://" in target or target.startswith(("mailto:", "data:")):
        return None

    resolved = (source.parent / target.replace("%20", " ")).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        pytest.fail(
            f"Documentation link escapes the repository: "
            f"{source.relative_to(root)} -> {markdown_target}"
        )
    return resolved


def _assert_document_identity(
    root: Path,
    relative_path: str,
    *,
    document_id: str,
    status: str,
) -> None:
    text = _read_text(root, relative_path)
    assert _metadata_value(text, "Document ID") == document_id
    assert _metadata_value(text, "Status") == status


def test_required_governance_documents_have_stable_identity() -> None:
    root = _repository_root()

    for relative_path, (document_id, status) in _REQUIRED_DOCUMENTS.items():
        _assert_document_identity(
            root,
            relative_path,
            document_id=document_id,
            status=status,
        )

    active_profile = root / "project" / "project.toml"
    if active_profile.is_file():
        _assert_document_identity(
            root,
            _OPTIONAL_ACTIVE_PROFILE_DOCUMENT,
            document_id="GF-WB-PROJECT-SQI-INTERFILE-LOCK",
            status="Normative active-project contract",
        )


def test_normative_delegates_point_to_the_alignment_lock() -> None:
    root = _repository_root()
    delegates = list(_ALIGNMENT_DELEGATES)

    if (root / _OPTIONAL_ACTIVE_PROFILE_DOCUMENT).is_file():
        delegates.append(_OPTIONAL_ACTIVE_PROFILE_DOCUMENT)

    for relative_path in delegates:
        text = _read_text(root, relative_path)
        authority = _metadata_value(text, "Alignment authority")
        assert authority == _ALIGNMENT_AUTHORITY, (
            f"{relative_path} delegates alignment to {authority!r}, "
            f"expected {_ALIGNMENT_AUTHORITY!r}"
        )


def test_alignment_lock_preserves_accepted_product_decisions() -> None:
    root = _repository_root()
    lock = _read_text(root, _ALIGNMENT_AUTHORITY)

    for statement in _LOCKED_ALIGNMENT_STATEMENTS:
        assert statement in lock, f"Alignment lock lost required statement: {statement}"

    labels = {
        "IMPLEMENTED",
        "PARTIALLY_IMPLEMENTED",
        "PLANNED",
        "PROPOSED",
        "HISTORICAL",
        "UNKNOWN",
    }
    for label in labels:
        assert f"`{label}`" in lock, f"Implementation-truth label is missing: {label}"


def test_canonical_file_architecture_counts_are_self_consistent() -> None:
    root = _repository_root()
    architecture_path = "docs/architecture/CANONICAL_FILE_ARCHITECTURE.md"
    architecture = _read_text(root, architecture_path)

    assert (
        "This document is the sole authority for the fixed implementation "
        "and test file architecture"
    ) in architecture

    paths = _canonical_paths(architecture)
    counts = _declared_fixed_counts(architecture)

    runtime = tuple(path for path in paths if path.startswith("src/gf_wordbench/"))
    tests = tuple(path for path in paths if path.startswith("tests/"))
    support = tuple(path for path in paths if not path.startswith(("src/gf_wordbench/", "tests/")))

    expected_labels = {
        "Runtime Python package",
        "Repository support, launch, script, and CI files",
        "Test modules and test helpers",
        "Total fixed coded files",
    }
    assert expected_labels <= counts.keys()

    assert counts["Runtime Python package"] == len(runtime)
    assert counts["Repository support, launch, script, and CI files"] == len(support)
    assert counts["Test modules and test helpers"] == len(tests)
    assert counts["Total fixed coded files"] == len(paths)
    assert len(paths) == len(runtime) + len(support) + len(tests)

    for required_path in _REQUIRED_LANGUAGE_LOADER_PATHS:
        assert required_path in paths, (
            f"Canonical architecture omits the explicit language-loader path: {required_path}"
        )

    assert "tests/release/test_documentation_alignment.py" in paths


def test_documentation_map_has_no_unrecorded_broken_repository_links() -> None:
    root = _repository_root()
    relative_path = "docs/DOCUMENTATION_MAP.md"
    source = root / relative_path
    text = _read_text(root, relative_path)
    exclusions = _ledger_exclusions(root)

    failures: list[str] = []
    for markdown_target in _markdown_links(text):
        resolved = _repository_target(root, source, markdown_target)
        if resolved is None or resolved.exists():
            continue

        repository_relative = resolved.relative_to(root).as_posix()
        if repository_relative in exclusions:
            continue

        failures.append(f"{markdown_target} -> {repository_relative}")

    assert not failures, "Unrecorded broken documentation-map links:\n" + "\n".join(
        sorted(set(failures))
    )


def test_validation_profile_template_identity_is_generic() -> None:
    root = _repository_root()
    template_path = "templates/validation-profile/project.toml"
    template_config = tomllib.loads(_read_text(root, template_path))
    assert template_config["schema_id"] == "gf-wordbench.project"
    template_profile = template_config["profile"]

    assert template_profile["id"] == "<PROFILE_ID>"
    assert template_profile["name"] == "<PROFILE_NAME>"
    assert template_config["compatibility"]["expected_language_key"] == ""

    active_path = root / "project" / "project.toml"
    if not active_path.is_file():
        return

    active_config = tomllib.loads(_read_text(root, "project/project.toml"))
    active_profile = active_config.get("profile", active_config.get("project"))
    assert isinstance(active_profile, Mapping)
    active_values = {
        str(active_profile["id"]).casefold(),
        str(active_profile["name"]).casefold(),
    }

    template_tree = root / "templates" / "validation-profile"
    leaked: list[str] = []
    for path in sorted(template_tree.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".toml", ".gfs"}:
            continue

        text = path.read_text(encoding="utf-8").casefold()
        for value in active_values:
            if len(value) >= 3 and value in text:
                leaked.append(f"{path.relative_to(root).as_posix()}: {value}")

    assert not leaked, "Active-profile identity leaked into reusable template:\n" + "\n".join(
        leaked
    )
