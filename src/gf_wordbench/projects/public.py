"""Public application façade for project-owned use cases.

Entrypoints and bootstrap code import project operations and contracts from this
module rather than depending on language-probe, loader, validator,
path-resolution, or lifecycle internals.

The façade performs no I/O and owns no policy. It re-exports the stable
application boundary implemented by the surrounding
:mod:`gf_wordbench.projects` package.

Interactive startup first resolves one explicitly selected GF language path and
then composes one monolingual Wordbench runtime. Existing project operations
remain available for optional validation-profile authoring and lifecycle tasks.
"""

from __future__ import annotations

from gf_wordbench.projects.initializer import initialize_project
from gf_wordbench.projects.languages.models import (
    CapabilityAvailability,
    LanguageCandidate,
    LanguageCapability,
    LanguageCapabilityStatus,
    LanguageModuleCandidate,
    LanguageModuleRole,
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
from gf_wordbench.projects.languages.public import (
    LanguageProbeService,
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

__all__ = (
    # Explicit path-resolved language startup.
    "CapabilityAvailability",
    "LanguageCandidate",
    "LanguageCapability",
    "LanguageCapabilityStatus",
    "LanguageModuleCandidate",
    "LanguageModuleRole",
    "LanguageProbeDiagnostic",
    "LanguageProbeRequest",
    "LanguageProbeResult",
    "LanguageProbeService",
    "LanguageProbeSeverity",
    "LanguageProbeStatus",
    "LanguageResolutionProvenance",
    "LanguageResolutionSource",
    "ResolvedLanguageContext",
    "SelectedPathKind",
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
)
