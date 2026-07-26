"""Public application façade for active-project use cases.

Entrypoints and bootstrap code import project operations from this module rather
than depending on loader, validator, path-resolution, or lifecycle internals.
The façade performs no I/O and owns no policy; it exposes the stable application
boundary implemented by the surrounding ``projects`` package.
"""

from __future__ import annotations

from gf_wordbench.projects.initializer import initialize_project
from gf_wordbench.projects.loader import load_project_config
from gf_wordbench.projects.migrator import migrate_project, plan_project_migration
from gf_wordbench.projects.models import ProjectConfig
from gf_wordbench.projects.paths import resolve_project_paths
from gf_wordbench.projects.resetter import plan_project_reset, reset_project
from gf_wordbench.projects.validator import check_project

__all__ = [
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
