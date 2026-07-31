"""Public application façade for path-resolved language startup.

Entrypoints and bootstrap code import language-resolution operations from this
module rather than depending on probe, model, port, or adapter internals.

The façade performs no I/O and owns no policy. It exposes the stable application
boundary implemented by the surrounding ``projects.languages`` package.
"""

from __future__ import annotations

from gf_wordbench.projects.languages.models import (
    LanguageCandidate,
    LanguageCapability,
    LanguageProbeDiagnostic,
    LanguageProbeRequest,
    LanguageProbeResult,
    ResolvedLanguageContext,
)
from gf_wordbench.projects.languages.probe import (
    LanguageProbeService,
    probe_language_path,
)

__all__ = [
    "LanguageCandidate",
    "LanguageCapability",
    "LanguageProbeDiagnostic",
    "LanguageProbeRequest",
    "LanguageProbeResult",
    "LanguageProbeService",
    "ResolvedLanguageContext",
    "probe_language_path",
]