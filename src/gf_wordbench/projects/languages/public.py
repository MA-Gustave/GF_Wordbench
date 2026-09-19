"""Public application façade for path-resolved language startup.

Entrypoints and bootstrap code import language-resolution operations from this
module rather than depending on probe, model, port, or adapter internals.

The façade performs no I/O and owns no policy. It re-exports the stable
application boundary directly from the canonical owner modules.
"""

from __future__ import annotations

from gf_wordbench.projects.languages.models import (
    LanguageCandidate,
    LanguageCapability,
    LanguageProbeDiagnostic,
    LanguageProbeRequest,
    LanguageProbeResult,
    ResolvedLanguageContext,
    SelectedPathKind,
)
from gf_wordbench.projects.languages.probe import (
    LanguageProbeService,
    probe_language_path,
)

__all__ = (
    "LanguageCandidate",
    "LanguageCapability",
    "LanguageProbeDiagnostic",
    "LanguageProbeRequest",
    "LanguageProbeResult",
    "LanguageProbeService",
    "ResolvedLanguageContext",
    "SelectedPathKind",
    "probe_language_path",
)
