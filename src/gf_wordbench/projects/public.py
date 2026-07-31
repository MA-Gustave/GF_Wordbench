"""Public application façade for language and validation-profile use cases.

Entrypoints and bootstrap code import project-owned operations from this module
rather than depending on language-probe, loader, validator, path-resolution, or
lifecycle internals.

The façade performs no I/O and owns no policy. It exposes the stable application
boundary implemented by the surrounding ``projects`` package.

Path-resolved language startup is the normal startup model. Existing project
operations remain available for explicit optional validation profiles and their
authoring lifecycle.
"""

from __future__ import annotations

from gf_wordbench.projects.initializer import initialize_project
from gf_wordbench.projects.languages.models import SelectedPathKind
from gf_wordbench.projects.languages.public import (
    LanguageCandidate,
    LanguageCapability,
    LanguageProbeDiagnostic,
    LanguageProbeRequest,
    LanguageProbeResult,
    LanguageProbeService,
    ResolvedLanguageContext,
    probe_language_path,
)
from gf_wordbench.projects.loader import load_project_config
from gf_wordbench.projects.migrator import (
    migrate_project,
    plan_project_migration,
)
from gf_wordbench.projects.models import ProjectConfig
from gf_wordbench.projects.paths import resolve_project_paths
from gf_wordbench.projects.resetter import (
    plan_project_reset,
    reset_project,
)
from gf_wordbench.projects.validator import check_project

__all__ = [
    # Path-resolved language startup.
    "SelectedPathKind",
    "LanguageCandidate",
    "LanguageCapability",
    "LanguageProbeDiagnostic",
    "LanguageProbeRequest",
    "LanguageProbeResult",
    "LanguageProbeService",
    "ResolvedLanguageContext",
    "probe_language_path",
    # Optional validation-profile lifecycle.
    "ProjectConfig",
    "check_project",
    "initialize_project",
    "load_project_config",
    "migrate_project",
    "plan_project_migration",
    "plan_project_reset",
    "reset_project",
    "resolve_project_paths",
]