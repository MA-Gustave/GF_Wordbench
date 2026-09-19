"""Static scenario-assertion registry for GF Wordbench."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from hashlib import sha256
import re
from types import MappingProxyType
from typing import Final, Generic, Protocol, TypeVar

from gf_wordbench.kernel.errors import (
    ConfigurationError,
    ContractViolationError,
)

SpecT = TypeVar("SpecT", contravariant=True)
ContextT = TypeVar("ContextT", contravariant=True)
ResultT = TypeVar("ResultT", covariant=True)
RegistrySpecT = TypeVar("RegistrySpecT")
RegistryContextT = TypeVar("RegistryContextT")
RegistryResultT = TypeVar("RegistryResultT")

ASSERTION_REGISTRY_VERSION: Final[str] = "1.0.0"

_ASSERTION_TYPE_ID_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")
_SERIALIZATION_NAME_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$"
)


@unique
class AssertionFamily(StrEnum):
    PROCESS = "process"
    SECTION = "section"
    DIAGNOSTIC = "diagnostic"
    TEXT = "text"
    COUNT = "count"
    ARTIFACT = "artifact"
    GOLD = "gold"


@unique
class AssertionInputSource(StrEnum):
    PROCESS_RESULT = "process_result"
    SECTION = "section"
    DIAGNOSTICS = "diagnostics"
    RAW_STDOUT = "raw_stdout"
    RAW_STDERR = "raw_stderr"
    NORMALIZED_SECTION = "normalized_section"
    NORMALIZED_OUTPUT = "normalized_output"
    PARSED_COUNT = "parsed_count"
    ARTIFACT = "artifact"
    GOLD_COMPARISON = "gold_comparison"


class AssertionEvaluator(
    Protocol[SpecT, ContextT, ResultT],
):
    def __call__(
        self,
        spec: SpecT,
        context: ContextT,
        /,
    ) -> ResultT: ...


class AssertionRegistryError(ContractViolationError):
    pass


class InvalidAssertionTypeError(AssertionRegistryError):
    pass


class DuplicateAssertionTypeError(AssertionRegistryError):
    pass


class UnknownAssertionTypeError(ConfigurationError):
    pass


class AssertionEvaluatorBindingError(AssertionRegistryError):
    pass


def _require_text(
    name: str,
    value: object,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL")
    return value


def _require_non_negative_int(
    name: str,
    value: object,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _normalize_sources(
    sources: Iterable[AssertionInputSource],
) -> tuple[AssertionInputSource, ...]:
    if isinstance(sources, (str, bytes)):
        raise TypeError("input_sources must be an iterable of AssertionInputSource values")

    try:
        normalized = tuple(sources)
    except TypeError as exc:
        raise TypeError("input_sources must be an iterable of AssertionInputSource values") from exc

    if not normalized:
        raise ValueError("input_sources must not be empty")

    seen: set[AssertionInputSource] = set()

    for index, source in enumerate(normalized):
        if not isinstance(source, AssertionInputSource):
            raise TypeError(f"input_sources[{index}] must be an AssertionInputSource")
        if source in seen:
            raise ValueError(f"duplicate assertion input source: {source.value}")
        seen.add(source)

    return normalized


@dataclass(frozen=True, slots=True)
class AssertionTypeDescriptor:
    type_id: str
    family: AssertionFamily
    input_sources: tuple[AssertionInputSource, ...]
    order: int
    comparison_semantics: str
    failure_representation: str
    serialization_name: str
    report_label: str

    def __post_init__(self) -> None:
        type_id = _require_text("type_id", self.type_id)

        if _ASSERTION_TYPE_ID_RE.fullmatch(type_id) is None:
            raise ValueError("type_id must use lowercase dotted or kebab syntax")

        if not isinstance(self.family, AssertionFamily):
            raise TypeError("family must be an AssertionFamily")

        if not type_id.startswith(f"{self.family.value}."):
            raise ValueError(
                f"type_id {type_id!r} must begin with {self.family.value!r} followed by a dot"
            )

        object.__setattr__(
            self,
            "input_sources",
            _normalize_sources(self.input_sources),
        )
        _require_non_negative_int("order", self.order)
        _require_text(
            "comparison_semantics",
            self.comparison_semantics,
        )
        _require_text(
            "failure_representation",
            self.failure_representation,
        )

        serialization_name = _require_text(
            "serialization_name",
            self.serialization_name,
        )
        if _SERIALIZATION_NAME_RE.fullmatch(serialization_name) is None:
            raise ValueError("serialization_name must use lowercase dotted snake-case syntax")

        _require_text("report_label", self.report_label)

    def to_serializable(self) -> dict[str, object]:
        return {
            "type_id": self.type_id,
            "family": self.family.value,
            "input_sources": [source.value for source in self.input_sources],
            "order": self.order,
            "comparison_semantics": self.comparison_semantics,
            "failure_representation": self.failure_representation,
            "serialization_name": self.serialization_name,
            "report_label": self.report_label,
        }


@dataclass(frozen=True, slots=True)
class RegisteredAssertionType(
    Generic[RegistrySpecT, RegistryContextT, RegistryResultT],
):
    descriptor: AssertionTypeDescriptor
    evaluator: AssertionEvaluator[
        RegistrySpecT,
        RegistryContextT,
        RegistryResultT,
    ]

    def __post_init__(self) -> None:
        if not isinstance(
            self.descriptor,
            AssertionTypeDescriptor,
        ):
            raise TypeError("descriptor must be an AssertionTypeDescriptor")
        if not callable(self.evaluator):
            raise TypeError("evaluator must be callable")


def _reject_text_iterable(
    value: object,
    *,
    field_name: str,
    item_name: str,
) -> None:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of {item_name} values")


class AssertionRegistry(
    Generic[RegistrySpecT, RegistryContextT, RegistryResultT],
):
    __slots__ = (
        "_by_id",
        "_descriptors",
        "_entries",
        "_fingerprint",
    )

    def __init__(
        self,
        entries: Iterable[
            RegisteredAssertionType[
                RegistrySpecT,
                RegistryContextT,
                RegistryResultT,
            ]
        ],
    ) -> None:
        _reject_text_iterable(
            entries,
            field_name="entries",
            item_name="RegisteredAssertionType",
        )

        try:
            supplied = tuple(entries)
        except TypeError as exc:
            raise TypeError(
                "entries must be an iterable of RegisteredAssertionType values"
            ) from exc

        if not supplied:
            raise ValueError("assertion registry must contain at least one type")

        by_id: dict[
            str,
            RegisteredAssertionType[
                RegistrySpecT,
                RegistryContextT,
                RegistryResultT,
            ],
        ] = {}
        order_owners: dict[int, str] = {}

        for index, entry in enumerate(supplied):
            if not isinstance(entry, RegisteredAssertionType):
                raise TypeError(f"entries[{index}] must be a RegisteredAssertionType")

            descriptor = entry.descriptor

            if descriptor.type_id in by_id:
                raise DuplicateAssertionTypeError(
                    "duplicate assertion type ID",
                    code="GF-WB-SCENARIO-001",
                    detail=descriptor.type_id,
                    stage="scenario",
                    operation="build_assertion_registry",
                    subject=descriptor.type_id,
                )

            existing = order_owners.get(descriptor.order)
            if existing is not None:
                raise DuplicateAssertionTypeError(
                    "duplicate assertion type order",
                    code="GF-WB-SCENARIO-002",
                    detail=(
                        f"order {descriptor.order} is used by "
                        f"{existing!r} and {descriptor.type_id!r}"
                    ),
                    stage="scenario",
                    operation="build_assertion_registry",
                    subject=descriptor.type_id,
                )

            by_id[descriptor.type_id] = entry
            order_owners[descriptor.order] = descriptor.type_id

        ordered = tuple(
            sorted(
                supplied,
                key=lambda item: (
                    item.descriptor.order,
                    item.descriptor.type_id,
                ),
            )
        )

        self._entries = ordered
        self._descriptors = tuple(entry.descriptor for entry in ordered)
        self._by_id = MappingProxyType(by_id)
        self._fingerprint = _registry_fingerprint(self._descriptors)

    @property
    def entries(
        self,
    ) -> tuple[
        RegisteredAssertionType[
            RegistrySpecT,
            RegistryContextT,
            RegistryResultT,
        ],
        ...,
    ]:
        return self._entries

    @property
    def descriptors(
        self,
    ) -> tuple[AssertionTypeDescriptor, ...]:
        return self._descriptors

    @property
    def type_ids(self) -> tuple[str, ...]:
        return tuple(descriptor.type_id for descriptor in self._descriptors)

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    def __contains__(
        self,
        type_id: object,
    ) -> bool:
        return isinstance(type_id, str) and type_id in self._by_id

    def __len__(self) -> int:
        return len(self._entries)

    def resolve(
        self,
        type_id: str,
    ) -> RegisteredAssertionType[
        RegistrySpecT,
        RegistryContextT,
        RegistryResultT,
    ]:
        candidate = _require_text("type_id", type_id)

        try:
            return self._by_id[candidate]
        except KeyError as exc:
            supported = ", ".join(self.type_ids)
            raise UnknownAssertionTypeError(
                "unknown scenario assertion type",
                code="GF-WB-SCENARIO-003",
                detail=(f"received {candidate!r}; supported types: {supported}"),
                stage="scenario",
                operation="resolve_assertion_type",
                subject=candidate,
            ) from exc

    def descriptor(
        self,
        type_id: str,
    ) -> AssertionTypeDescriptor:
        return self.resolve(type_id).descriptor

    def by_family(
        self,
        family: AssertionFamily,
    ) -> tuple[
        RegisteredAssertionType[
            RegistrySpecT,
            RegistryContextT,
            RegistryResultT,
        ],
        ...,
    ]:
        if not isinstance(family, AssertionFamily):
            raise TypeError("family must be an AssertionFamily")

        return tuple(entry for entry in self._entries if entry.descriptor.family is family)

    def evaluate(
        self,
        type_id: str,
        spec: RegistrySpecT,
        context: RegistryContextT,
    ) -> RegistryResultT:
        return self.resolve(type_id).evaluator(
            spec,
            context,
        )

    def to_serializable(self) -> dict[str, object]:
        return {
            "registry_version": ASSERTION_REGISTRY_VERSION,
            "fingerprint": self.fingerprint,
            "assertion_types": [descriptor.to_serializable() for descriptor in self._descriptors],
        }


def _descriptor(
    type_id: str,
    family: AssertionFamily,
    input_sources: tuple[AssertionInputSource, ...],
    order: int,
    comparison_semantics: str,
    report_label: str,
) -> AssertionTypeDescriptor:
    return AssertionTypeDescriptor(
        type_id=type_id,
        family=family,
        input_sources=input_sources,
        order=order,
        comparison_semantics=comparison_semantics,
        failure_representation=(
            "A completed false comparison is failed; an unevaluable comparison is error."
        ),
        serialization_name=type_id.replace("-", "_"),
        report_label=report_label,
    )


CANONICAL_ASSERTION_TYPES: Final[tuple[AssertionTypeDescriptor, ...]] = (
    _descriptor(
        "process.completed",
        AssertionFamily.PROCESS,
        (AssertionInputSource.PROCESS_RESULT,),
        10,
        "The external process reached a completed execution state.",
        "Process completed",
    ),
    _descriptor(
        "process.exit-code",
        AssertionFamily.PROCESS,
        (AssertionInputSource.PROCESS_RESULT,),
        20,
        "The recorded process exit code equals the declared value.",
        "Exit code",
    ),
    _descriptor(
        "process.not-timed-out",
        AssertionFamily.PROCESS,
        (AssertionInputSource.PROCESS_RESULT,),
        30,
        "The process did not exceed its configured timeout.",
        "No timeout",
    ),
    _descriptor(
        "process.not-cancelled",
        AssertionFamily.PROCESS,
        (AssertionInputSource.PROCESS_RESULT,),
        40,
        "The process was not cancelled.",
        "Not cancelled",
    ),
    _descriptor(
        "process.output-within-limit",
        AssertionFamily.PROCESS,
        (AssertionInputSource.PROCESS_RESULT,),
        50,
        "Captured output did not exceed the configured bound.",
        "Output within limit",
    ),
    _descriptor(
        "process.capture-complete",
        AssertionFamily.PROCESS,
        (AssertionInputSource.PROCESS_RESULT,),
        60,
        "Required stdout and stderr capture completed.",
        "Capture complete",
    ),
    _descriptor(
        "section.exists",
        AssertionFamily.SECTION,
        (AssertionInputSource.SECTION,),
        100,
        "The declared section exists in parsed marker evidence.",
        "Section exists",
    ),
    _descriptor(
        "section.completed",
        AssertionFamily.SECTION,
        (AssertionInputSource.SECTION,),
        110,
        "The declared section has one valid begin and end transition.",
        "Section completed",
    ),
    _descriptor(
        "section.ordered",
        AssertionFamily.SECTION,
        (AssertionInputSource.SECTION,),
        120,
        "The declared section appears in the required deterministic order.",
        "Section order",
    ),
    _descriptor(
        "section.no-unexpected",
        AssertionFamily.SECTION,
        (AssertionInputSource.SECTION,),
        130,
        "No undeclared section appears in parsed marker evidence.",
        "No unexpected section",
    ),
    _descriptor(
        "section.non-empty",
        AssertionFamily.SECTION,
        (
            AssertionInputSource.SECTION,
            AssertionInputSource.NORMALIZED_SECTION,
        ),
        140,
        "The declared section contains non-empty output.",
        "Section non-empty",
    ),
    _descriptor(
        "diagnostic.no-fatal",
        AssertionFamily.DIAGNOSTIC,
        (AssertionInputSource.DIAGNOSTICS,),
        200,
        "No recognized fatal diagnostic is present.",
        "No fatal diagnostic",
    ),
    _descriptor(
        "diagnostic.expected",
        AssertionFamily.DIAGNOSTIC,
        (AssertionInputSource.DIAGNOSTICS,),
        210,
        "A specifically declared diagnostic is present.",
        "Expected diagnostic",
    ),
    _descriptor(
        "diagnostic.absent",
        AssertionFamily.DIAGNOSTIC,
        (AssertionInputSource.DIAGNOSTICS,),
        220,
        "A specifically prohibited diagnostic is absent.",
        "Diagnostic absent",
    ),
    _descriptor(
        "text.contains",
        AssertionFamily.TEXT,
        (
            AssertionInputSource.RAW_STDOUT,
            AssertionInputSource.RAW_STDERR,
            AssertionInputSource.NORMALIZED_SECTION,
            AssertionInputSource.NORMALIZED_OUTPUT,
        ),
        300,
        "The declared input contains the required literal text.",
        "Text contains",
    ),
    _descriptor(
        "text.excludes",
        AssertionFamily.TEXT,
        (
            AssertionInputSource.RAW_STDOUT,
            AssertionInputSource.RAW_STDERR,
            AssertionInputSource.NORMALIZED_SECTION,
            AssertionInputSource.NORMALIZED_OUTPUT,
        ),
        310,
        "The declared input does not contain the prohibited literal text.",
        "Text excludes",
    ),
    _descriptor(
        "text.equals",
        AssertionFamily.TEXT,
        (
            AssertionInputSource.NORMALIZED_SECTION,
            AssertionInputSource.NORMALIZED_OUTPUT,
        ),
        320,
        "The normalized input equals the declared text exactly.",
        "Text equals",
    ),
    _descriptor(
        "text.matches",
        AssertionFamily.TEXT,
        (
            AssertionInputSource.RAW_STDOUT,
            AssertionInputSource.RAW_STDERR,
            AssertionInputSource.NORMALIZED_SECTION,
            AssertionInputSource.NORMALIZED_OUTPUT,
        ),
        330,
        "The declared input satisfies the approved bounded pattern.",
        "Text matches",
    ),
    _descriptor(
        "text.one-of",
        AssertionFamily.TEXT,
        (
            AssertionInputSource.NORMALIZED_SECTION,
            AssertionInputSource.NORMALIZED_OUTPUT,
        ),
        340,
        "The normalized input equals one member of the approved set.",
        "Text is approved",
    ),
    _descriptor(
        "count.equals",
        AssertionFamily.COUNT,
        (AssertionInputSource.PARSED_COUNT,),
        400,
        "The parsed count equals the declared integer.",
        "Count equals",
    ),
    _descriptor(
        "count.minimum",
        AssertionFamily.COUNT,
        (AssertionInputSource.PARSED_COUNT,),
        410,
        "The parsed count is at least the declared minimum.",
        "Count minimum",
    ),
    _descriptor(
        "count.maximum",
        AssertionFamily.COUNT,
        (AssertionInputSource.PARSED_COUNT,),
        420,
        "The parsed count is at most the declared maximum.",
        "Count maximum",
    ),
    _descriptor(
        "count.range",
        AssertionFamily.COUNT,
        (AssertionInputSource.PARSED_COUNT,),
        430,
        "The parsed count is inside the declared inclusive range.",
        "Count range",
    ),
    _descriptor(
        "artifact.exists",
        AssertionFamily.ARTIFACT,
        (AssertionInputSource.ARTIFACT,),
        500,
        "The declared artifact exists at its owned path.",
        "Artifact exists",
    ),
    _descriptor(
        "artifact.non-empty",
        AssertionFamily.ARTIFACT,
        (AssertionInputSource.ARTIFACT,),
        510,
        "The declared artifact exists and has non-zero size.",
        "Artifact non-empty",
    ),
    _descriptor(
        "artifact.current",
        AssertionFamily.ARTIFACT,
        (AssertionInputSource.ARTIFACT,),
        520,
        "Artifact evidence proves current-run provenance.",
        "Artifact current",
    ),
    _descriptor(
        "artifact.contained",
        AssertionFamily.ARTIFACT,
        (AssertionInputSource.ARTIFACT,),
        530,
        "The artifact resolves inside its declared owned root.",
        "Artifact contained",
    ),
    _descriptor(
        "gold.matches",
        AssertionFamily.GOLD,
        (AssertionInputSource.GOLD_COMPARISON,),
        600,
        "Normalized actual output equals the reviewed gold output.",
        "Gold matches",
    ),
)


def _canonical_descriptor_map() -> Mapping[str, AssertionTypeDescriptor]:
    return MappingProxyType(
        {descriptor.type_id: descriptor for descriptor in CANONICAL_ASSERTION_TYPES}
    )


CANONICAL_ASSERTION_TYPE_BY_ID: Final[Mapping[str, AssertionTypeDescriptor]] = (
    _canonical_descriptor_map()
)


def _registry_fingerprint(
    descriptors: Iterable[AssertionTypeDescriptor],
) -> str:
    lines = [
        ASSERTION_REGISTRY_VERSION,
    ]

    for descriptor in descriptors:
        lines.extend(
            (
                descriptor.type_id,
                descriptor.family.value,
                ",".join(source.value for source in descriptor.input_sources),
                str(descriptor.order),
                descriptor.comparison_semantics,
                descriptor.failure_representation,
                descriptor.serialization_name,
                descriptor.report_label,
            )
        )

    payload = "\n".join(lines).encode("utf-8")
    return sha256(payload).hexdigest()


def canonical_assertion_descriptor(
    type_id: str,
) -> AssertionTypeDescriptor:
    candidate = _require_text("type_id", type_id)

    try:
        return CANONICAL_ASSERTION_TYPE_BY_ID[candidate]
    except KeyError as exc:
        supported = ", ".join(CANONICAL_ASSERTION_TYPE_BY_ID)
        raise UnknownAssertionTypeError(
            "unknown scenario assertion type",
            code="GF-WB-SCENARIO-003",
            detail=(f"received {candidate!r}; supported types: {supported}"),
            stage="scenario",
            operation="resolve_assertion_type",
            subject=candidate,
        ) from exc


def bind_canonical_assertion_registry(
    evaluators: Mapping[
        str,
        AssertionEvaluator[
            RegistrySpecT,
            RegistryContextT,
            RegistryResultT,
        ],
    ],
) -> AssertionRegistry[
    RegistrySpecT,
    RegistryContextT,
    RegistryResultT,
]:
    if not isinstance(evaluators, Mapping):
        raise TypeError("evaluators must be a mapping")

    supplied_ids = set(evaluators)
    canonical_ids = set(CANONICAL_ASSERTION_TYPE_BY_ID)
    missing = tuple(
        descriptor.type_id
        for descriptor in CANONICAL_ASSERTION_TYPES
        if descriptor.type_id not in supplied_ids
    )
    unexpected = tuple(sorted(supplied_ids - canonical_ids))

    if missing or unexpected:
        detail_parts: list[str] = []

        if missing:
            detail_parts.append("missing evaluators: " + ", ".join(missing))
        if unexpected:
            detail_parts.append("unexpected evaluator IDs: " + ", ".join(unexpected))

        raise AssertionEvaluatorBindingError(
            "canonical assertion evaluator binding is incomplete",
            code="GF-WB-SCENARIO-004",
            detail="; ".join(detail_parts),
            stage="scenario",
            operation="bind_assertion_registry",
        )

    entries: list[
        RegisteredAssertionType[
            RegistrySpecT,
            RegistryContextT,
            RegistryResultT,
        ]
    ] = []

    for descriptor in CANONICAL_ASSERTION_TYPES:
        evaluator = evaluators[descriptor.type_id]

        if not callable(evaluator):
            raise AssertionEvaluatorBindingError(
                "scenario assertion evaluator is not callable",
                code="GF-WB-SCENARIO-005",
                detail=descriptor.type_id,
                stage="scenario",
                operation="bind_assertion_registry",
                subject=descriptor.type_id,
            )

        entries.append(
            RegisteredAssertionType(
                descriptor=descriptor,
                evaluator=evaluator,
            )
        )

    return AssertionRegistry(entries)


__all__ = (
    "ASSERTION_REGISTRY_VERSION",
    "CANONICAL_ASSERTION_TYPES",
    "CANONICAL_ASSERTION_TYPE_BY_ID",
    "AssertionEvaluator",
    "AssertionEvaluatorBindingError",
    "AssertionFamily",
    "AssertionInputSource",
    "AssertionRegistry",
    "AssertionRegistryError",
    "AssertionTypeDescriptor",
    "DuplicateAssertionTypeError",
    "InvalidAssertionTypeError",
    "RegisteredAssertionType",
    "UnknownAssertionTypeError",
    "bind_canonical_assertion_registry",
    "canonical_assertion_descriptor",
)
