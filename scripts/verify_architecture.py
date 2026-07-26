from __future__ import annotations

import argparse
import ast
import base64
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zlib
from typing import Final, TypeAlias

EXIT_OK: Final[int] = 0
EXIT_VALIDATION_FAILED: Final[int] = 1
EXIT_USAGE_ERROR: Final[int] = 2
EXIT_RUNTIME_ERROR: Final[int] = 3

EXPECTED_TOTAL: Final[int] = 393
EXPECTED_RUNTIME: Final[int] = 222
EXPECTED_SUPPORT: Final[int] = 14
EXPECTED_TESTS: Final[int] = 157
CANONICAL_DOCUMENT_CANDIDATES: Final[tuple[str, ...]] = (
    "docs/architecture/CANONICAL_FILE_ARCHITECTURE.md",
    "docs/GF_WORDBENCH_CANONICAL_FILE_ARCHITECTURE.md",
)

_MANIFEST_B85: Final[str] = (
    'c-ozt+m@^-'
    '42JLLVY=5mk&8mgVj9H_*xfZxKjEOF5{PrN55@Oe2q6TL`WU2pEsxJ1ZN8pL|Jctz3scg)Ki;GI>*LaD1XJDcL|c_$Rv@iTS'
    'ZB93IZWD!zZ6?0{_41r9}ni%{|-'
    'z1@BE&P{zq{4;WX$hH*$9NQ%=%#Ys>uJJ|E>^m=mQYBdjQDzTtIyFXDP~hH>a(snznA7}>E+82Nm6%<z|V@YKbK&}{hU@a*8'
    'd`-gy+`RuyT-wtUUnVgWuht|$Qr{-cSboeQU`r{MRizi!DdNqU*)3-'
    'Ew8pY&l*r<D<st=lt;G&05M2&(8(F%sJ$n=tdc~~d8t-'
    'oIma>cBbPsy2+divkGhtm8@7<*U8*<$0;xhaHI6aHaea=!hoR+w*zjC4ij^xO$!G~qR$a_Z$Yw84sH<k-'
    'xNh3C=dXBG6KUuKowfUJVqjH63djLgAeH*_9WmQ-'
    '>QWW{Xc$jqC}Qzv=j9r)>y^2W{yGub<HkrZ5yBWV_PewK<lbxAbCPD6){=E7QW<Fzdp6Ejj1B-%IvwLHK+o0!vD-'
    '5B$Ti*Jeh)B^r1_~Nu7;>5KZVIu|!CiW)cX%8jz<r~)OV^P@BfSt*_XDuh!7`+^1FbX4XcR30{2>rPpW=jvOUkYsMElDDNgQ'
    '6ES+y@6_(1A6Bh1~0qUfjGm66)Ox;ukMy47BK7fryVj_8t!5npTR?A&-NZDLv5oK^k-q&TJCO-'
    's^YLFyrKNi#Ca(Y^~gp!DI{&Zr#;vkup&NUxCJ$h$OiN%Hs5@Zz+Dd;HpUYkL(9Q?9dNHIr@i&!iffp59RbU41D7fjstbeII'
    '-X%N69;>DR3)TKjBZQgne5lMhg9p)f2HFu%-'
    'rxI4Ee^pKp!Hs)@%!WT_*X%9e&GjQF#JGwL19GEMjTRSV7#2}CQSobYvWk~ujF5(j5$Y@WfwVTINwD>0RG#7caFomL6iSDPV'
    'XdsPA0m%zcxfAKL|LC4&J1&PV&HEeXF_Epufp3M%igN^sk483fDO0&Mj#JdjNqVPqqG5Fx_h=#aUiYA2x$vc8a$Qu)`YMO%?'
    'FJ$UWFmTe;)MM27{o&rT=&vnC_?K=TXLpRrZf5*Txch?Y37{zW<-*L!l#~QUOkj7&SY?80?6Pyca7?!1qbvSnq-'
    '*xU2XoX12bK*G0}adxOQDr~3jXFwP~haIyP9V|NsQ=W05M;6f-PrLheoewczJ}#`%An@JnRNj<w|9zA&!SZv1G&D_{Snu-'
    '<;45?*)ewVCBxHpm{O-!orXOJ_?AWJHMpK-%xR+1=>dv66ScqqV9qwTqn!sIN?q<V{k8fg6ymLh3V#-'
    'I_)d&FMMDU9}>M1y=vC6=)V7^D#9*EFqKtMy}P*Lb{YLm9lb-'
    '16HO+FPbLp*!b5CM@{p?n{`i8U%}rI>8PWGxTDOLQcr5q{ECAeJSg6XqV5H!zFQ=tJJt0KKgR6kNVD2?G`5y2)tV0df6OEn0'
    'Bhgn7h9`kBBhtk1I4!4Yr|`gO1E%V;N?5cLsK%GgilOJ82;goiG#l|$a(KBKQn|H=M8(bd_Ba$>b^q}koCyZeRc}oFv7vFCk'
    '4VEIB?#Y4BH-7fm8hvks1gD1UZ~#ZjLR<Q|Cgp76e6PP^&p}FrWVp8s>+b#ibaLXRQO2TQO*Dbqq`%j<#-'
    'SYL<|=G_F3&mQ#hh`&KWezS)iG$oI_W44&lo)qhLe!tNf1HWs(qO;I6D9s)i<IUFBF_7Su9{h=OFMsm|iYfJGicYiY4Pw7?7'
    'aY@rQq6x{26H5SWwfBu=8XY7&yBC;>+Tu|gm{onB0FJQo<*!!;$WzB;TF5T|@?&=mhOD^?7|3ac4+fuJLMq^cwx0+01p<n*9'
    'jy`7>?Tzp2rR5s@^Np{G@dsgb?vg>PzKbqU+*B>IFKeQU{3!xUdXxpkrL^*sHe>w;w<xRRB#S)NJi$frTd~ltcuM6cL$wKrL'
    '$&eHDh$P~ZHn7(?U+FiZn+>t&d18R3m&5s-'
    'xewW!}hBupAiTpfgPLYE=06Aawvo=BV0*eHrRndq+PwtWjWL?8<sM>rm>sgc7P_J%ha9EU}bV2=q?Y;R(N{)e;q!F(~yQWdC'
    '3mW{xAhEIiqMVW`FZL@iz>Qi6&riIvc^m)EDV2Q@PPN{OiPI&u+SiX33Z4W5WU?^mV<+Z9Wjd9yV04%Vp|WrI&jhMC-eE3nH'
    '*!LTxHDpEexx-'
    '=$Z72{nWLoVLMZTRLJFTAu7nbcfQcQ@i~2aY?t`H^gRN%#se$p`IjKbY5=LVEywuz_KdG3XN6ITqUqhI;X*^`{Z_Bf`5hLfM'
    '8`b(Y}Iih-SZ_nF^DiuDZ6pvaSBJNd9%>+fs~PQ4G(spLuxSSLxHLNJr}K$)rj#X&bf+=jk>Ghl3S?ExT7|XU0Vf&kyQ2wnh'
    ')#Aw<LZWs<x(Y?s4(0bS(2-n}iy+tLOMTd8r&T&DJlf-'
    'rN#GOn5V27A7!ZQ!dXbw&sRZe1@Y66Z5)(3#nxhI0`3QV6|d-fX|0TUUNcIUFzU%JAyVDQt*nXk^MUl-TvCoaSr)rNP#5gzY'
    'sCa~u6XIE!H`7Anwkg6=BS*-?K9gz-6IAMKqM%z;_GM)K-'
    'AwWdb`6%HW#?PY=3W~ELQ2J8TA;alw~+v<*$kPX=FKL){&G@WM%yn<VQ{E(uq{YM!Ha{MU;0_DG?$dE%JZU~~YA2!su<4*-'
    'z^rb4l2Is#esBv3KeQ<l>8ZDi7YO1xayTx68a8ZL(Qa^O$@LPhK$QM2z5(-WD8t-'
    'E8d<kg+nO7;MXelpzu95!ebd7p&_E^K*qW2Sejr2#iV@Yp|J{E&!^ts9{3`SmD*<g>wk_|ZIW3xiK2EOi#c|jvll2<2EC0lV'
    'KQIJ)z5EZA=#7vb6?&AJ(F|54x6#HM=FU5Trm(})V$X*WSp+o)_r?#tp6v+$laA>>QL6OqiABjV8T1M?z`)K299akMoWmZ`^'
    '0M05sB+k~sZNtuztpqx+dBO2Rr3#M44Y#{wcbW>s_nzUjuOBNT+B`CT%NqV=H4?@4a^!u6P8AYG=ujY0B(nO5V*6Si5q86p;'
    'qEB5&UT`F33h_ALW6R9UPw?Ru2ld<>{<knVKL#32AyZ-n7%JF#qbbG^d8RH_J#)8)oYS#+M6gW9HyI^%VlX(fgGF9x-'
    'A`*{LPjIq~Ia<)t%FAbmbx2c0+bZwo!D=;oI{bR1-'
    'QY3YUHj$(H&`PNER~;o`y#OG9zafzd^K3XG)5GGHYBlF%Zl+EcpcXi~81>b*MhdG3fLxZ9yDb5!P|v$*6lir8Km(FEhg!&cz'
    '^A4^>nYy'
)


def _decode_manifest() -> frozenset[str]:
    raw = zlib.decompress(base64.b85decode(_MANIFEST_B85.encode("ascii"))).decode("utf-8")
    return frozenset(line for line in raw.splitlines() if line)


EXPECTED_PATHS: Final[frozenset[str]] = _decode_manifest()
EXPECTED_MANIFEST_SHA256: Final[str] = "2261e217a68600a1cbbf56bad888b134a0d482385eb9e8ba615b2de524f3d348"

_PRODUCTION_ROOT: Final[PurePosixPath] = PurePosixPath("src/gf_wordbench")
_FORBIDDEN_AREA_IMPORTS: Final[Mapping[str, frozenset[str]]] = {
    "kernel": frozenset({"config", "state", "projects", "runs", "validation", "diagnostics", "reporting", "infrastructure", "entrypoints", "bootstrap"}),
    "config": frozenset({"state", "projects", "runs", "validation", "diagnostics", "reporting", "infrastructure", "entrypoints", "bootstrap"}),
    "infrastructure": frozenset({"config", "state", "projects", "runs", "validation", "diagnostics", "reporting", "entrypoints", "bootstrap"}),
    "state": frozenset({"projects", "runs", "validation", "diagnostics", "reporting", "entrypoints", "bootstrap"}),
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
_DECLARATIVE_PREFIXES: Final[tuple[str, ...]] = (
    "src/gf_wordbench/diagnostics/patterns/",
    "src/gf_wordbench/reporting/schemas/",
    "src/gf_wordbench/validation/scanning/rules/",
)
_DECLARATIVE_FILES: Final[frozenset[str]] = frozenset(
    {"src/gf_wordbench/projects/schema.py", "src/gf_wordbench/state/schema.py"}
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
    return path.is_dir() and (path / "pyproject.toml").is_file() and (path / "src/gf_wordbench").is_dir()


def verify(root: Path, *, manifest_only: bool = False) -> VerificationResult:
    findings: list[Finding] = []
    _verify_embedded_manifest(findings)
    actual = _collect_fixed_zone_files(root)
    missing = EXPECTED_PATHS - actual
    unexpected = actual - EXPECTED_PATHS
    for path in sorted(missing):
        findings.append(Finding("error", "ARCH_PATH_MISSING", path, None, "required canonical file is missing"))
    for path in sorted(unexpected):
        findings.append(Finding("error", "ARCH_PATH_UNEXPECTED", path, None, "file is not in the canonical fixed architecture"))
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
        findings.append(Finding("error", "ARCH_MANIFEST_INTERNAL", "scripts/verify_architecture.py", None, f"embedded counts are invalid: total={len(EXPECTED_PATHS)} categories={dict(counts)}"))
    digest = _manifest_digest(EXPECTED_PATHS)
    if digest != EXPECTED_MANIFEST_SHA256:
        findings.append(Finding("error", "ARCH_MANIFEST_DIGEST", "scripts/verify_architecture.py", None, "embedded fixed-path manifest digest does not match"))


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
        if path.name == ".gitignore" or path.suffix.lower() in {".py", ".pyw", ".bat", ".cmd", ".toml", ".yml", ".yaml"}:
            found.add(path.name)
    return frozenset(found)


def _verify_document_manifest(root: Path, findings: list[Finding]) -> None:
    documents = [root / candidate for candidate in CANONICAL_DOCUMENT_CANDIDATES if (root / candidate).is_file()]
    if not documents:
        findings.append(Finding("error", "ARCH_DOCUMENT_MISSING", CANONICAL_DOCUMENT_CANDIDATES[0], None, "canonical architecture document is missing"))
        return
    parsed: list[tuple[Path, frozenset[str]]] = []
    for document in documents:
        try:
            paths = _parse_document_tree(document.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            findings.append(Finding("error", "ARCH_DOCUMENT_INVALID", document.relative_to(root).as_posix(), None, str(exc)))
            continue
        parsed.append((document, paths))
        missing = EXPECTED_PATHS - paths
        extra = paths - EXPECTED_PATHS
        if missing or extra:
            findings.append(Finding("error", "ARCH_DOCUMENT_DRIFT", document.relative_to(root).as_posix(), None, f"fixed tree differs from verifier manifest: missing={len(missing)} extra={len(extra)}"))
    if len(parsed) > 1 and len({paths for _, paths in parsed}) > 1:
        findings.append(Finding("error", "ARCH_DOCUMENT_CONFLICT", "docs", None, "canonical and legacy architecture documents declare different fixed trees"))


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
        _check_file_boundaries(relative, text, tree, module, findings)
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
        findings.append(Finding("error", "ARCH_IMPORT_CYCLE", modules[cycle[0]].relative_to(root).as_posix(), None, "dependency cycle: " + " -> ".join((*cycle, cycle[0]))))


def _check_file_boundaries(relative: str, text: str, tree: ast.Module, module: str, findings: list[Finding]) -> None:
    lines = len(text.splitlines())
    declarative = relative in _DECLARATIVE_FILES or relative.startswith(_DECLARATIVE_PREFIXES)
    hard_limit = 900 if declarative else 600
    soft_limit = 900 if declarative else 450
    if lines > hard_limit:
        findings.append(Finding("error", "ARCH_FILE_TOO_LARGE", relative, None, f"{lines} physical lines exceeds hard limit {hard_limit}"))
    elif lines > soft_limit:
        findings.append(Finding("warning", "ARCH_FILE_LARGE", relative, None, f"{lines} physical lines exceeds normal limit {soft_limit}"))
    if relative.endswith("/__init__.py"):
        for statement in tree.body:
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                continue
            if isinstance(statement, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Pass)):
                continue
            findings.append(Finding("error", "ARCH_INIT_SIDE_EFFECT", relative, getattr(statement, "lineno", None), "package initializer contains executable top-level control flow"))
    if module in _NORMAL_VALIDATION_MODULES and "gf_wordbench.validation.scenarios.gold_update" in _all_import_names(module, relative.endswith("/__init__.py"), tree):
        findings.append(Finding("error", "ARCH_GOLD_UPDATE_PATH", relative, None, "normal validation path imports explicit gold-update behavior"))


def _check_import_rules(module: str, relative: str, node: ast.Import | ast.ImportFrom, imports: tuple[str, ...], findings: list[Finding]) -> None:
    line = getattr(node, "lineno", None)
    for target in imports:
        if target == "tests" or target.startswith("tests."):
            findings.append(Finding("error", "ARCH_PRODUCTION_IMPORTS_TESTS", relative, line, f"production module imports {target}"))
        if target == "gf_portfolio" or target.startswith("gf_portfolio."):
            findings.append(Finding("error", "ARCH_PORTFOLIO_DEPENDENCY", relative, line, f"Wordbench imports {target}"))
    if isinstance(node, ast.ImportFrom):
        if any(alias.name == "*" for alias in node.names):
            findings.append(Finding("error", "ARCH_WILDCARD_IMPORT", relative, line, "wildcard imports are prohibited"))
        for alias in node.names:
            if alias.name.startswith("_") and alias.name not in {"__version__"} and not alias.name.endswith("__"):
                findings.append(Finding("error", "ARCH_PRIVATE_IMPORT", relative, line, f"imports private symbol {alias.name!r}"))
    area = _module_area(module)
    for target in imports:
        target_area = _module_area(target)
        if target_area in _FORBIDDEN_AREA_IMPORTS.get(area, frozenset()):
            findings.append(Finding("error", "ARCH_DIRECTION", relative, line, f"{area} must not import {target}"))
        if area == "entrypoints" and target.startswith(_ENTRYPOINT_INTERNAL_PREFIXES):
            findings.append(Finding("error", "ARCH_ENTRYPOINT_BYPASS", relative, line, f"entrypoint bypasses a public application boundary: {target}"))
        if area == "reporting" and target.startswith(_REPORT_EXECUTION_PREFIXES):
            findings.append(Finding("error", "ARCH_REPORT_EXECUTION", relative, line, f"reporting imports execution behavior: {target}"))
        if area == "diagnostics" and target.startswith(_DIAGNOSTIC_EXECUTION_PREFIXES):
            findings.append(Finding("error", "ARCH_DIAGNOSTIC_EXECUTION", relative, line, f"diagnostics imports execution internals: {target}"))
    if "subprocess" in imports and module not in _APPROVED_SUBPROCESS_MODULES:
        findings.append(Finding("error", "ARCH_DIRECT_SUBPROCESS", relative, line, "direct subprocess access is outside the approved process adapter"))


def _module_name(path: Path, source_root: Path) -> str:
    parts = ["gf_wordbench", *path.relative_to(source_root).with_suffix("").parts]
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _module_area(module: str) -> str:
    parts = module.split(".")
    return parts[1] if len(parts) > 1 else "package_root"


def _import_targets(module: str, is_package: bool, node: ast.Import | ast.ImportFrom) -> tuple[str, ...]:
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
        targets.extend(f"{base}.{alias.name}" if base else alias.name for alias in node.names if alias.name != "*")
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
        print(f"architecture verification failed unexpectedly: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_RUNTIME_ERROR
    if args.json:
        print(json.dumps(result.to_json(), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print(render_text(result, quiet=args.quiet))
    failed = not result.passed or (args.warnings_as_errors and result.warning_count > 0)
    return EXIT_VALIDATION_FAILED if failed else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
