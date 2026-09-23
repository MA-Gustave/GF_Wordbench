from __future__ import annotations

import argparse
import ast
import base64
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Final, TypeAlias
import zlib

EXIT_OK: Final[int] = 0
EXIT_VALIDATION_FAILED: Final[int] = 1
EXIT_USAGE_ERROR: Final[int] = 2
EXIT_RUNTIME_ERROR: Final[int] = 3

EXPECTED_TOTAL: Final[int] = 409
EXPECTED_RUNTIME: Final[int] = 231
EXPECTED_SUPPORT: Final[int] = 15
EXPECTED_TESTS: Final[int] = 163
CANONICAL_DOCUMENT: Final[str] = "docs/architecture/CANONICAL_FILE_ARCHITECTURE.md"

_MANIFEST_B85: Final[str] = (
    'c-ozt+m@^-5{B>h!_;2$64Q^+mn>3AlP(1}hpNhX`Uwyfm4L8s`cQnoi4Z_U5Pl5Oz5L_%w>F>8QGeUte>@+hdw;yA@z=+t)d)Va'
    ';fc16f?I*KI$@pN+T@_L5x@TWFZ)}Y{vlNNV%odeJ2vTFFsFxM6d&{Z``5^QXzfP%@!)R#-@z~cJHKb6{}G-0a2lR%J0oXje@i7D'
    'TU+M$_V-B+hC5MeGQx_Y<_m_T528*hXLtv%QEIi_OHBOOCX9T(88_WaI(Vu#A~u`u_wZ!j>zn^(EcTZnjT4s&X?$qyEOcrvwnB%W'
    'a;QH(F}-+lKc-hh7@@wT(P|RP)vz#uWA#C^5uNDaFQP`lgy<25u*me1g9%wDJ6nIh9PCDJt$fOkJE_&b);&hueF|gm>N@W2vb=5z'
    'VP(bturE2^{#7f?mqbRoB6E6X!Wd0>&8JkoR6`rASVoS`+*o)XeSTI!FM2<Z=?%y#n9XH$$%=_PSnP(*!^)DQRD!ISjhwi7lX>bS'
    'Z@h!Oe4@OubHXTlXD*VW)6+zng`J<}NS(SQn&C8}!$x<)T5;pGZ6_2rQWGTFI0EG#V4qFQX+7Q;^92`Q65mq`_>btk(}su>*X{xv'
    'F-S16HxW-~D4{Q3uvQ;_#Fhq}Oy)gnsa#|9a*)F)Ot{_UC^#YX=LVSj9@wxHxauuQB7UNx7c_k2YVdpz_kJX}6lBoB8UVYx_X~?R'
    'M?%A<gzTmlbaBt<T>(FlK4SrnPM#h|LWcql#yRSN)(_I42XN*}jP_o?lZG27pPP?L6lE*yjtnMa04MFPX7jI!68H(!Gesn6L!m6`'
    'pfX-LISCSL9SpIbN$i&t-!YyUN%*(y2SI$%Z}7SFHw}dt4D(i{dKwNpwU5C`-QrFx?AMd*nA8-w6*`>oryPZSTPG$8{g2g(*bi8%'
    '1Nc7_G<gfR#$?qjK`OF^Aezbniztlv<6~5PN8^>c*RPtZh)BS9nxw+l-${n9y)y?9J~q!_;jr@Sla-iCRI?IaV5e0=_SI(aA751f'
    '&O10b<p1z7T0zI1$6VI5nKo>6qxMzBc+Y2t*uln!XU1N(z|{w#c4X%(Mqi+DAG-t_{Sagr_se%$^S(6_OMXeWD8gIgCbT0O`Yc70'
    'Y7QFZ?PGeZX);R^tj@$`OftZFTrj^s+<O-NwZ(|=(#;gYj&aFm-hB#pUr>#@ih`d`m>HRplE4TBc882rCa8LTJJ$=xWy`y~;@?KP'
    'W*>qpOnq=<`2Zf|z@4xZdX!Jmy}MCR;B*+V+WB>o7}3K3VmtB)wjEat_5IJVf5f=uQ@lw$oO!B}#@cC!f?!ZA*>E@h;pNyjCv?Mm'
    '(LvN*$&(c{FK%C$vsJ(+0dWWmOPc%(m5sDO2Y*Sz94jnlDQIE}UpB`H-()ie-(^pbeKmhD-8N9CeZ@nP4JPp+(KPf`vyKJ(`VUnR'
    'PeFpItb%I3=!#oEh3qK3LydSa6D&_A4{O3>1VY*&R|Wjz69TxKs&q1<@8MgS+DP!Zo+OXZ!{fnd1iFwD8pp<CLOMk%-=LllE#Q7;'
    'L|$MZ8nci9gk#vDRvn1O@ez<^Lm`Y|0+*|*CWbq6IaNz^L{1y9=WyMJxkQm_{MZa$ud0o7WiN}(Mm$G3yj%^bB!(8EvKNN-Whhwn'
    'kO~}xM}uJ1RCb7<8kvm+Y3y1F!cUw92#eNA)KnL!;wJA~RlUy{m))HFD^1;VL`2mLETRFX=JzA2%8=s<KgN7D{7KwV&HzQDyCbSy'
    'z9ABDD=hq*;X!I9oY2dF44UOE&@0BALsxeW;mb3l;M5MQ{EpdWlIV)yTUkX^^<T=mO6*=1)UJ3D1<6cPk<5(&TX^ulrNz$B0x#fi'
    'o;J9P;9mEu4qL{DAW1a?@sa@Cwofd0DDtHKZ}{yOFtDT8`>(Ocn$Z(3-O`_Tb>7ahliJgNkhqU+cj7ljV^xrknoMG$U*T_zK4%y0'
    'jo<5~?KJGqH-2XEKM1RHmkfIB*|G(Sn<_ttdNaBxgc{iWPgy`*N-M9lnd-^xqO5Z5TjZ(c30qWm%NN=ePdPfuP;CO@P;ET43Pah}'
    'HpT6?cHE$WTP|=*(Li3(c)=GhCA7uz&3OE36)s0&Jtu=ml0}aeM-CN=WuzNrsOMy05b0DebJ;aD%Z8;4uayE#aEr1Ds8{S9gO$mB'
    'pjqyit+0BA|2q6-nT9m1X_sXB8zQw(^@pOpm_vG4b#E9RvzUOz>1+fKQ(vUBOWTdc;U6cIJ#W)RG`ojtJ~l2eLSNTxZ}Wiw_Hdwr'
    'U3%5?N-y_Plh$wV7DQmdgxXYQK5cj@1t`7xON=wv&*>OEwxtle(DLM;f*oq+PVMq1_$6%1H!RJeUML09v1Dhl=)4Z9!G`BEz_Rkw'
    '3XK&gT_vzinA2d@ecE<jqWg?>64A<NqJ0J35Y1sh^D$0-N_A~#B}MICEEPldY^(Rm3Q^k6_~T{wd85b4&#x$k=XtMsg#EMfUaKO7'
    '<?PAjnEcu{Y<<_Ij1mq<ON8|R<7H>wi58v*`#83GAnf4g;k;L}YYy8b0Z>4FGVy)N;nlkJN~I!*9}J|TrZ|EjBZc>Sl?C$*>u$;H'
    'HsGrH?S&xGLIyvr1r-hUoK$Y$>#pyN5Cq)1UMdn7t_-0wvqKH^AP57keYW%Nxx{rw(jCe%$ykQhlZV1a?~6vJOOq12hV^N__Rm$e'
    'jw5WZyEwPYSp^&0u+?}KXsMvP<H+o!KLx^sOYdOor-gZ7*4-(cKs&YG_e3fNOM9lZKy0&8rwRjh05(^%_LOZGNuN2@VYh!#gdu4<'
    '&k*cBZvBELd5HU$JqU9A9tVN)&v7#3P|Y13{_N|R8h8BOq)9JjxhxiVw&2TmAT>DudZor~A92JzGUf*lJ8@aHeo4^cE}!_+;8fBO'
    'J97AXr6vlc_J^C2CVX||F?hcCYLUz<QIi{(m)h6J5EEYAIh;LK&9~@1^-v>2OnNK_Z_&qs-;6$2GRDEk3uqhcu^_eq$J^+vSh9hy'
    'hiG23N|fXks8q>TfJzi(^*cnxsr)okrJ~B^FuE94-g*jZF71~BPK?XyH#1}}hC4WTCvUKX=6BdQwOx0hNM5OkLtA<aMM?v8Bo0-4'
    '8MT);EX!dnc&lTn9xbbzz}Zm`iL-TZa|E&rX9ArU2jTdkqzA{AgPdJ%xS9%Nn?A$IUpSVKw0UIwyxLQM>q)yrnJAf6loZ>`zW*6I'
    ')sqyVLpe#2$f`+-?Q1bfJYq{GzN6TR+=+6^@C0RL8Rho8?4n3qYbJ`=wPYg0mhuGD?L9NcVuvzQbWo9N@k2(z-q0YfLQQfl5+Di-'
    'X@jQbl3H#mkOaY5w_V<)ooTx?rQq?Vkex3l>B__1<PF*3YLcRB4&Q!DL^YwaqL3nONVbc@v`G|PN?csXB{dZ18$-Hizc3_evim|3'
    'f4Tl6soGPz-)JQd*wuS=<nx<0lHhKKvU|2Nzibwl+n*w~*O4^ACH1k@%>N(v*f??'
)


def _decode_manifest() -> frozenset[str]:
    raw = zlib.decompress(base64.b85decode(_MANIFEST_B85.encode("ascii"))).decode("utf-8")
    return frozenset(line for line in raw.splitlines() if line)


EXPECTED_PATHS: Final[frozenset[str]] = _decode_manifest()
EXPECTED_MANIFEST_SHA256: Final[str] = (
    "d9013a3afb724391b729da9aa17c9210daeede24a371b5a6095a511263c74a1a"
)

_PRODUCTION_ROOT: Final[PurePosixPath] = PurePosixPath("src/gf_wordbench")
_FORBIDDEN_AREA_IMPORTS: Final[Mapping[str, frozenset[str]]] = {
    "kernel": frozenset(
        {
            "config",
            "state",
            "projects",
            "runs",
            "validation",
            "diagnostics",
            "reporting",
            "infrastructure",
            "entrypoints",
            "bootstrap",
        }
    ),
    "config": frozenset(
        {
            "state",
            "projects",
            "runs",
            "validation",
            "diagnostics",
            "reporting",
            "infrastructure",
            "entrypoints",
            "bootstrap",
        }
    ),
    "infrastructure": frozenset(
        {
            "config",
            "state",
            "projects",
            "runs",
            "validation",
            "diagnostics",
            "reporting",
            "entrypoints",
            "bootstrap",
        }
    ),
    "state": frozenset(
        {"projects", "runs", "validation", "diagnostics", "reporting", "entrypoints", "bootstrap"}
    ),
    "projects": frozenset({"runs", "validation", "diagnostics", "reporting", "entrypoints"}),
    "validation": frozenset({"reporting", "entrypoints"}),
    "diagnostics": frozenset({"reporting", "entrypoints"}),
    "reporting": frozenset({"entrypoints"}),
}
_APPROVED_SUBPROCESS_MODULES: Final[frozenset[str]] = frozenset(
    {
        "gf_wordbench.infrastructure.process.launcher",
        "gf_wordbench.infrastructure.process.requests",
        "gf_wordbench.infrastructure.process.termination",
    }
)
_ENTRYPOINT_INTERNAL_PREFIXES: Final[tuple[str, ...]] = (
    "gf_wordbench.infrastructure",
    "gf_wordbench.projects.filesystem_adapter",
    "gf_wordbench.projects.initializer",
    "gf_wordbench.projects.loader",
    "gf_wordbench.projects.migrator",
    "gf_wordbench.projects.resetter",
    "gf_wordbench.projects.toml_adapter",
    "gf_wordbench.projects.validator",
    "gf_wordbench.validation.compilation",
    "gf_wordbench.validation.regression",
    "gf_wordbench.validation.release",
    "gf_wordbench.validation.scanning",
    "gf_wordbench.validation.scenarios",
    "gf_wordbench.validation.selection",
    "gf_wordbench.validation.pipeline",
    "gf_wordbench.diagnostics.classification",
    "gf_wordbench.diagnostics.parsing",
    "gf_wordbench.diagnostics.patterns",
    "gf_wordbench.diagnostics.tools",
    "gf_wordbench.reporting.ai_packet",
    "gf_wordbench.reporting.details",
    "gf_wordbench.reporting.logs",
    "gf_wordbench.reporting.manifest",
    "gf_wordbench.reporting.schemas",
    "gf_wordbench.reporting.summary",
)
_REPORT_EXECUTION_PREFIXES: Final[tuple[str, ...]] = (
    "gf_wordbench.infrastructure.process",
    "gf_wordbench.validation.pipeline",
    "gf_wordbench.validation.compilation.gf_adapter",
    "gf_wordbench.validation.compilation.module_compile",
    "gf_wordbench.validation.compilation.pgf_build",
    "gf_wordbench.validation.compilation.service",
    "gf_wordbench.validation.scanning.service",
    "gf_wordbench.validation.scenarios.execution",
    "gf_wordbench.validation.scenarios.service",
)
_DIAGNOSTIC_EXECUTION_PREFIXES: Final[tuple[str, ...]] = (
    "gf_wordbench.validation.pipeline",
    "gf_wordbench.validation.compilation.gf_adapter",
    "gf_wordbench.validation.compilation.module_compile",
    "gf_wordbench.validation.compilation.pgf_build",
    "gf_wordbench.validation.compilation.service",
    "gf_wordbench.validation.scenarios.execution",
)
_NORMAL_VALIDATION_MODULES: Final[frozenset[str]] = frozenset(
    {
        "gf_wordbench.validation.pipeline",
        "gf_wordbench.validation.scenarios.execution",
        "gf_wordbench.validation.scenarios.service",
    }
)
_IGNORED_PARTS: Final[frozenset[str]] = frozenset(
    {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
)
_DOC_TREE_RE: Final[re.Pattern[str]] = re.compile(
    r"## 3\. Canonical fixed tree\s*```text\n(.*?)\n```", re.DOTALL
)
_TREE_LINE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?P<prefix>(?:│   |    )*)(?:├── |└── )(?P<name>.+)$"
)

Severity: TypeAlias = str


@dataclass(frozen=True, slots=True, order=True)
class Finding:
    severity: Severity
    code: str
    path: str
    line: int | None
    message: str

    def render(self) -> str:
        location = self.path
        if self.line is not None:
            location = f"{location}:{self.line}"
        return f"{self.severity.upper()} {self.code} {location}: {self.message}"


@dataclass(frozen=True, slots=True)
class VerificationResult:
    root: str
    expected_count: int
    present_count: int
    missing_count: int
    unexpected_count: int
    error_count: int
    warning_count: int
    manifest_sha256: str
    findings: tuple[Finding, ...]

    @property
    def passed(self) -> bool:
        return self.error_count == 0

    def to_json(self) -> dict[str, object]:
        payload = asdict(self)
        payload["passed"] = self.passed
        return payload


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the canonical GF Wordbench file and dependency architecture."
    )
    parser.add_argument("--root", type=Path, help="Repository root; defaults to auto-discovery.")
    parser.add_argument("--json", action="store_true", help="Emit one JSON result object.")
    parser.add_argument("--manifest-only", action="store_true", help="Skip Python import analysis.")
    parser.add_argument("--warnings-as-errors", action="store_true")
    parser.add_argument("--quiet", action="store_true", help="Print only failures and summary.")
    return parser.parse_args(argv)


def discover_root(explicit: Path | None) -> Path:
    if explicit is not None:
        candidate = explicit.expanduser().resolve()
        if not _looks_like_root(candidate):
            raise ValueError(f"not a GF Wordbench repository root: {candidate}")
        return candidate
    starts = (Path.cwd(), Path(__file__).resolve().parent)
    seen: set[Path] = set()
    for start in starts:
        for candidate in (start, *start.parents):
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if _looks_like_root(resolved):
                return resolved
    raise ValueError("could not locate a repository containing pyproject.toml and src/gf_wordbench")


def _looks_like_root(path: Path) -> bool:
    return (
        path.is_dir()
        and (path / "pyproject.toml").is_file()
        and (path / "src/gf_wordbench").is_dir()
    )


def verify(root: Path, *, manifest_only: bool = False) -> VerificationResult:
    findings: list[Finding] = []
    _verify_embedded_manifest(findings)
    actual = _collect_fixed_zone_files(root)
    missing = EXPECTED_PATHS - actual
    unexpected = actual - EXPECTED_PATHS
    for path in sorted(missing):
        findings.append(
            Finding("error", "ARCH_PATH_MISSING", path, None, "required canonical file is missing")
        )
    for path in sorted(unexpected):
        findings.append(
            Finding(
                "error",
                "ARCH_PATH_UNEXPECTED",
                path,
                None,
                "file is not in the canonical fixed architecture",
            )
        )
    _verify_document_manifest(root, findings)
    if not manifest_only:
        _verify_python_architecture(root, findings)
    findings.sort(key=lambda item: (item.severity != "error", item.path, item.line or 0, item.code))
    errors = sum(item.severity == "error" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)
    return VerificationResult(
        root=str(root),
        expected_count=len(EXPECTED_PATHS),
        present_count=len(EXPECTED_PATHS & actual),
        missing_count=len(missing),
        unexpected_count=len(unexpected),
        error_count=errors,
        warning_count=warnings,
        manifest_sha256=_manifest_digest(EXPECTED_PATHS),
        findings=tuple(findings),
    )


def _verify_embedded_manifest(findings: list[Finding]) -> None:
    counts = Counter(_category(path) for path in EXPECTED_PATHS)
    expected = {"runtime": EXPECTED_RUNTIME, "support": EXPECTED_SUPPORT, "tests": EXPECTED_TESTS}
    if len(EXPECTED_PATHS) != EXPECTED_TOTAL or counts != expected:
        findings.append(
            Finding(
                "error",
                "ARCH_MANIFEST_INTERNAL",
                "scripts/verify_architecture.py",
                None,
                f"embedded counts are invalid: total={len(EXPECTED_PATHS)} categories={dict(counts)}",
            )
        )
    digest = _manifest_digest(EXPECTED_PATHS)
    if digest != EXPECTED_MANIFEST_SHA256:
        findings.append(
            Finding(
                "error",
                "ARCH_MANIFEST_DIGEST",
                "scripts/verify_architecture.py",
                None,
                "embedded fixed-path manifest digest does not match",
            )
        )


def _category(path: str) -> str:
    if path.startswith("src/gf_wordbench/"):
        return "runtime"
    if path.startswith("tests/"):
        return "tests"
    return "support"


def _manifest_digest(paths: Iterable[str]) -> str:
    payload = "\n".join(sorted(paths)).encode("utf-8") + b"\n"
    return hashlib.sha256(payload).hexdigest()


def _collect_fixed_zone_files(root: Path) -> frozenset[str]:
    found: set[str] = set()
    for base, suffixes, excluded in (
        (root / "src/gf_wordbench", None, frozenset()),
        (root / "tests", frozenset({".py"}), frozenset({"fixtures"})),
        (root / "scripts", frozenset({".py"}), frozenset()),
        (root / ".github/workflows", frozenset({".yml", ".yaml"}), frozenset()),
    ):
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or any(part in _IGNORED_PARTS for part in path.parts):
                continue
            relative_to_base = path.relative_to(base)
            if relative_to_base.parts and relative_to_base.parts[0] in excluded:
                continue
            if suffixes is not None and path.suffix.lower() not in suffixes:
                continue
            found.add(path.relative_to(root).as_posix())
    for path in root.iterdir():
        if not path.is_file():
            continue
        if path.name == ".gitignore" or path.suffix.lower() in {
            ".py",
            ".pyw",
            ".bat",
            ".cmd",
            ".toml",
            ".yml",
            ".yaml",
        }:
            found.add(path.name)
    return frozenset(found)


def _verify_document_manifest(root: Path, findings: list[Finding]) -> None:
    document = root / CANONICAL_DOCUMENT
    if not document.is_file():
        findings.append(
            Finding(
                "error",
                "ARCH_DOCUMENT_MISSING",
                CANONICAL_DOCUMENT,
                None,
                "canonical architecture document is missing",
            )
        )
        return
    try:
        paths = _parse_document_tree(document.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        findings.append(
            Finding(
                "error",
                "ARCH_DOCUMENT_INVALID",
                CANONICAL_DOCUMENT,
                None,
                str(exc),
            )
        )
        return
    missing = EXPECTED_PATHS - paths
    extra = paths - EXPECTED_PATHS
    if missing or extra:
        findings.append(
            Finding(
                "error",
                "ARCH_DOCUMENT_DRIFT",
                CANONICAL_DOCUMENT,
                None,
                (
                    "fixed tree differs from verifier manifest: "
                    f"missing={len(missing)} extra={len(extra)}"
                ),
            )
        )


def _parse_document_tree(text: str) -> frozenset[str]:
    match = _DOC_TREE_RE.search(text.replace("\r\n", "\n"))
    if match is None:
        raise ValueError("Section 3 canonical fixed tree was not found")
    stack: list[str] = []
    paths: set[str] = set()
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if line.strip() == "GF_Wordbench/":
            continue
        tree = _TREE_LINE_RE.fullmatch(line)
        if tree is None:
            raise ValueError(f"unrecognized canonical-tree line: {line!r}")
        depth = len(tree.group("prefix")) // 4
        name = tree.group("name")
        stack = stack[:depth]
        if name.endswith("/"):
            stack.append(name[:-1])
        else:
            paths.add("/".join((*stack, name)))
    if len(paths) != EXPECTED_TOTAL:
        raise ValueError(f"canonical tree contains {len(paths)} files; expected {EXPECTED_TOTAL}")
    return frozenset(paths)


def _verify_python_architecture(root: Path, findings: list[Finding]) -> None:
    source_root = root / _PRODUCTION_ROOT
    modules: dict[str, Path] = {}
    trees: dict[str, ast.Module] = {}
    for path in sorted(source_root.rglob("*.py")):
        if any(part in _IGNORED_PARTS for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        module = _module_name(path, source_root)
        modules[module] = path
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=relative)
        except (OSError, UnicodeError, SyntaxError) as exc:
            line = exc.lineno if isinstance(exc, SyntaxError) else None
            findings.append(Finding("error", "ARCH_PYTHON_INVALID", relative, line, str(exc)))
            continue
        trees[module] = tree
        _check_file_boundaries(relative, tree, module, findings)
    edges: dict[str, set[str]] = {module: set() for module in modules}
    for module, tree in trees.items():
        path = modules[module]
        relative = path.relative_to(root).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            imports = _import_targets(module, path.name == "__init__.py", node)
            _check_import_rules(module, relative, node, imports, findings)
            for target in imports:
                resolved = _existing_module(target, modules)
                if resolved is not None and resolved != module:
                    edges[module].add(resolved)
    for cycle in _strongly_connected_cycles(edges):
        findings.append(
            Finding(
                "error",
                "ARCH_IMPORT_CYCLE",
                modules[cycle[0]].relative_to(root).as_posix(),
                None,
                "dependency cycle: " + " -> ".join((*cycle, cycle[0])),
            )
        )


def _check_file_boundaries(
    relative: str,
    tree: ast.Module,
    module: str,
    findings: list[Finding],
) -> None:
    if relative.endswith("/__init__.py"):
        for statement in tree.body:
            if (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            ):
                continue
            if isinstance(
                statement,
                (
                    ast.Import,
                    ast.ImportFrom,
                    ast.Assign,
                    ast.AnnAssign,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Pass,
                ),
            ):
                continue
            findings.append(
                Finding(
                    "error",
                    "ARCH_INIT_SIDE_EFFECT",
                    relative,
                    getattr(statement, "lineno", None),
                    "package initializer contains executable top-level control flow",
                )
            )
    if (
        module in _NORMAL_VALIDATION_MODULES
        and "gf_wordbench.validation.scenarios.gold_update"
        in _all_import_names(module, relative.endswith("/__init__.py"), tree)
    ):
        findings.append(
            Finding(
                "error",
                "ARCH_GOLD_UPDATE_PATH",
                relative,
                None,
                "normal validation path imports explicit gold-update behavior",
            )
        )


def _check_import_rules(
    module: str,
    relative: str,
    node: ast.Import | ast.ImportFrom,
    imports: tuple[str, ...],
    findings: list[Finding],
) -> None:
    line = getattr(node, "lineno", None)
    for target in imports:
        if target == "tests" or target.startswith("tests."):
            findings.append(
                Finding(
                    "error",
                    "ARCH_PRODUCTION_IMPORTS_TESTS",
                    relative,
                    line,
                    f"production module imports {target}",
                )
            )
        if target == "gf_portfolio" or target.startswith("gf_portfolio."):
            findings.append(
                Finding(
                    "error",
                    "ARCH_PORTFOLIO_DEPENDENCY",
                    relative,
                    line,
                    f"Wordbench imports {target}",
                )
            )
    if isinstance(node, ast.ImportFrom):
        if any(alias.name == "*" for alias in node.names):
            findings.append(
                Finding(
                    "error",
                    "ARCH_WILDCARD_IMPORT",
                    relative,
                    line,
                    "wildcard imports are prohibited",
                )
            )
        for alias in node.names:
            if (
                alias.name.startswith("_")
                and alias.name not in {"__version__"}
                and not alias.name.endswith("__")
            ):
                findings.append(
                    Finding(
                        "error",
                        "ARCH_PRIVATE_IMPORT",
                        relative,
                        line,
                        f"imports private symbol {alias.name!r}",
                    )
                )
    area = _module_area(module)
    for target in imports:
        target_area = _module_area(target)
        if target_area in _FORBIDDEN_AREA_IMPORTS.get(area, frozenset()):
            findings.append(
                Finding(
                    "error", "ARCH_DIRECTION", relative, line, f"{area} must not import {target}"
                )
            )
        if area == "entrypoints" and target.startswith(_ENTRYPOINT_INTERNAL_PREFIXES):
            findings.append(
                Finding(
                    "error",
                    "ARCH_ENTRYPOINT_BYPASS",
                    relative,
                    line,
                    f"entrypoint bypasses a public application boundary: {target}",
                )
            )
        if area == "reporting" and target.startswith(_REPORT_EXECUTION_PREFIXES):
            findings.append(
                Finding(
                    "error",
                    "ARCH_REPORT_EXECUTION",
                    relative,
                    line,
                    f"reporting imports execution behavior: {target}",
                )
            )
        if area == "diagnostics" and target.startswith(_DIAGNOSTIC_EXECUTION_PREFIXES):
            findings.append(
                Finding(
                    "error",
                    "ARCH_DIAGNOSTIC_EXECUTION",
                    relative,
                    line,
                    f"diagnostics imports execution internals: {target}",
                )
            )
    if "subprocess" in imports and module not in _APPROVED_SUBPROCESS_MODULES:
        findings.append(
            Finding(
                "error",
                "ARCH_DIRECT_SUBPROCESS",
                relative,
                line,
                "direct subprocess access is outside the approved process adapter",
            )
        )


def _module_name(path: Path, source_root: Path) -> str:
    parts = ["gf_wordbench", *path.relative_to(source_root).with_suffix("").parts]
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _module_area(module: str) -> str:
    parts = module.split(".")
    return parts[1] if len(parts) > 1 else "package_root"


def _import_targets(
    module: str, is_package: bool, node: ast.Import | ast.ImportFrom
) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if node.level:
        package = module.split(".") if is_package else module.split(".")[:-1]
        climb = node.level - 1
        if climb > len(package):
            return ()
        if climb:
            package = package[:-climb]
        base = ".".join((*package, *((node.module,) if node.module else ())))
    else:
        base = node.module or ""
    targets: list[str] = []
    if base:
        targets.append(base)
    if node.module is None:
        targets.extend(
            f"{base}.{alias.name}" if base else alias.name
            for alias in node.names
            if alias.name != "*"
        )
    return tuple(dict.fromkeys(targets))


def _all_import_names(module: str, is_package: bool, tree: ast.Module) -> frozenset[str]:
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            values.update(_import_targets(module, is_package, node))
    return frozenset(values)


def _existing_module(target: str, modules: Mapping[str, Path]) -> str | None:
    candidate = target
    while candidate:
        if candidate in modules:
            return candidate
        candidate = candidate.rpartition(".")[0]
    return None


def _strongly_connected_cycles(edges: Mapping[str, set[str]]) -> tuple[tuple[str, ...], ...]:
    index = 0
    stack: list[str] = []
    stacked: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    cycles: list[tuple[str, ...]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        stacked.add(node)
        for target in sorted(edges.get(node, set())):
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in stacked:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] != indices[node]:
            return
        component: list[str] = []
        while stack:
            target = stack.pop()
            stacked.remove(target)
            component.append(target)
            if target == node:
                break
        if len(component) > 1:
            cycles.append(tuple(sorted(component)))

    for node in sorted(edges):
        if node not in indices:
            visit(node)
    return tuple(sorted(cycles))


def render_text(result: VerificationResult, *, quiet: bool) -> str:
    lines: list[str] = []
    for finding in result.findings:
        if quiet and finding.severity != "error":
            continue
        lines.append(finding.render())
    status = "PASS" if result.passed else "FAIL"
    lines.append(
        f"{status} architecture: present={result.present_count}/{result.expected_count} "
        f"missing={result.missing_count} unexpected={result.unexpected_count} "
        f"errors={result.error_count} warnings={result.warning_count}"
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        root = discover_root(args.root)
        result = verify(root, manifest_only=args.manifest_only)
    except ValueError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return EXIT_USAGE_ERROR
    except Exception as exc:
        print(
            f"architecture verification failed unexpectedly: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return EXIT_RUNTIME_ERROR
    if args.json:
        print(
            json.dumps(result.to_json(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )
    else:
        print(render_text(result, quiet=args.quiet))
    failed = not result.passed or (args.warnings_as_errors and result.warning_count > 0)
    return EXIT_VALIDATION_FAILED if failed else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
