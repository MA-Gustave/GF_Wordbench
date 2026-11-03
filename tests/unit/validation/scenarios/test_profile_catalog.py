"""Focused tests for profile-owned scenario tag composition."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from gf_wordbench.projects.models import ProjectConfig
from gf_wordbench.validation.scenarios import profile_catalog


def _profile(language_code: str) -> ProjectConfig:
    value = SimpleNamespace(identity=SimpleNamespace(language_code=language_code))
    return cast("ProjectConfig", value)


def test_albanian_profile_opts_into_surface_hygiene_contracts() -> None:
    tags = profile_catalog._profile_tags(_profile("albanian"), scenario_id="alb-verb-06")

    assert tags == (
        "albanian",
        "verb",
        "require-nonempty-cases",
        "forbid-visible-bind",
    )


def test_other_language_profile_does_not_inherit_albanian_surface_contracts() -> None:
    tags = profile_catalog._profile_tags(_profile("german"), scenario_id="ger-verb-01")

    assert tags == ("german", "verb")
