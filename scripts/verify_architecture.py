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

EXPECTED_TOTAL: Final[int] = 404
EXPECTED_RUNTIME: Final[int] = 229
EXPECTED_SUPPORT: Final[int] = 14
EXPECTED_TESTS: Final[int] = 161
CANONICAL_DOCUMENT: Final[str] = "docs/architecture/CANONICAL_FILE_ARCHITECTURE.md"

_MANIFEST_B85: Final[str] = (
    "c-ozt+m@^-"
    "42JLLVY=5m5sN~~Vp_!w*xfZxKjEOF5{Pp%hvxe&gb)IWAH8y~<?;EW&DV3#Klby_!UyHvAMbJa>*LaDBp+D+L|X^RtwdU#w9amA"
    "s-Luxe+_(@#EXeReLT2Z|F>V_|IY8(=zpYeA5MeL3ZrIcKh>lhTU+M$_V-cshC5kmGSbST<{MtO^CF=qXSjeamRhZN$&nx1q*2c|"
    "<3_xcgQqS=hGru^`zM3<?j90e=996|UxqY}Tun&hLu+TDQ**HuI{Z|9{qc$E<dZK$dNqWR)3-"
    "8u8s+3_*r+=>R39`ODP#wKku?e?L=P~8MW$06%)>e*Z2kRmPz>B!^;Cj8rKkU`dkk89Nn`Ko1Yc}iIyZ%|YQlfmmzr<?s+HzjAtP"
    "OpIXyFJj3&J1Q%#+k`Zidxj2xS}vG6?l{H%gbcFR1ZHz2EEHsk1$6(e`B*bSYBm8AwXNwQ)#YUJik=Bbms@ecg-NO@!Dq?zoUxkw"
    "73$B{G(J3p&|I(11j!%jnojTX{cdE>RMkP|mb6C~O=0<}EAKAV`+dbly>5trWz_o)T^SBk}HL&S+|H^N5t3QX)x#M2&1=*u^()yF"
    "bmO9OT$^PaVuTx0Zdki#g9xZUL_1R?b2dYCUAuzo4<sk0=B{0)ju((r*#{la^B??-${K?WVH0kErkzn~X4FOGzIr-"
    "XRZ3mU^SdRHJ$q|ca#Ly)J3fzTn3gK-YJr}cw0=pLN;BnNx1-$}!bQ_n3%C5o~Yc1H%2(L<1SSF^>}L<#%^8kr)J<WML}+N-"
    "RCVOwSr`>o^;3(k;)|ER8)#LoXf9HoC~D4dzF2vki^!@>J5;lNS1q7w@~cvONZO@Uj-ffN2zgS2n!<Vd0av3er*1J+*;F%1Px5x}"
    "i6SvB$CiMRzsQ`s~Tg^_=ja0<SoS*Gb;ziQzhB7t~lR1?0YPBN!PN#fwtj?FVzIIQOSWF@9@Qdx;_u+u7`x@t4Tgs&<9dl+m6>R)"
    "_}R?u;`U}0!-kPRE%sC`v2-"
    "tpNXcChjOnW2|0aE&Xd9ohMc(HCeuZZ5$_KO`B(W9^;Rylag_yfe}*ityIB3GIl6J}cRznuA7p`*7veG?{p@RcFF7CK+Ho)}P-"
    "W?mf%y+G3=C>E^Y-j&a3iF21C@FQ}fRih^Gu&5TS*Nnqpzc882rCa6YpJJ(6aRV!k=;y*^YW*>ZbOMP%)c@I%x&z-asdQeX(-"
    "eQmxIBiC(wtt-@Ms_fOm`6UrR`7|T@%$NH9^owVCEp|-"
    "_PnWbHMP@lvVlRdWW(L~$D)R=IiVZgNdYJ6%H3B%^Wye}1zQDtlyJ6Seo2#mq2fpjw2zk*%<+VsLkgO3Ew7s6gge=c!M*GWvajY3"
    "rVIjg+E?6PoWUeM6neFM)vRN|zW=5w!Y)WKl~qu^1G?gN8U2kXy+e&NUM7f7CJ$@E!wH1sAy)<b;|mUOH&tn8MBig+-M$9mvEb*-"
    "00@7DGgR(ZBc&(k+|r<)a1g*l$bh_H?lm^~9`HM?Lk-pwjh(?G(N_?LCxJ1u)Wq;OEvIVt5`ohOOx0)SuxKYxjUSsKpq*+XU2#*P"
    "*~sUh`j@LAm3y2>RNS0zk3+$#`;X_~<kL%5y?OSBqsFC0L>dk$LHK480lyxtLQOS7l?ZtELiIjpT$bqgUz&PQh={5ericcZT1bzm"
    "DnpJdmLXg(!=L0G<qS|Tx;vs;t_+bt#9-"
    "my3_pKn!V$f@&!Ab&63qza9J;!52w$EV1sk$o<#)_3lY}S(cV!h(H8d&fD#!A&pq7zE6eKfE^(r?8Eb<UqD~s)+1zy767TVxO!M*"
    "NRW3i0)=bx#0#x4mUBKyM51x23J{|&$W0tP&az5g0f);t*D((PvRu5Pij5=t-hA0+y*Eroq!G*$(9tH~r5`sM$|=yP__-"
    "uS&vS)su{-}spre-KvZF6s5qvFHNjP1Q2{@-Vu{pCYi-PFX-)N-"
    "IBUGuH2^i?T|Vw#ZY>6I_(I6$|Z(ry3k(s5Sv{s5Ty2rJ=aBO>z6J9XIH~Ef=_$<IgJ)FL;bnd|Rlb4BM}seBL9JRx&=%EJU<8aw"
    "sS)BVtg#{E~q|q+PwtWm#pG4NDnb6Z=hYJ3tfAWn$+uSee`hn&pAn3Qte}Ux&ZMX-LDGyd;COKTN?(%_!Q*+28z5;tj)Nq6t`>&P"
    "MPs^+h_%$8IzZ|2jF@vzsoWS&FIo*s#C|eO)hdn-2uAgAEnza+x|_>E&J-"
    "()#V)f(R^_P@Brkrwzv}f9cg<a+tw>PTSzIEgi87El>U>*`dVk)UJMgT*9{dhS==Od(uHVRM<p|&dZh>tbaZOEUOl+&{#duRRZgT"
    "ISp3bCAagE;wzLu1S_M7_7!wPH2Ve3hcNl+s%zUTDQfp(sdl+zTX|MiW72-"
    "cpGAqU8$C{Oenrtg&%Wy6{b%L9Rz*6NvnN+Wifh}jU4%$CN;n)W5!M5Ymz}wgEj&N$<JcO3utS)K^UI_}bJ#8y00neOCcaNOyqZ|"
    "EB^80UGrxf16>S5q+R<LD5vICd#<l37!Jco28~EzJosp7&Ti2<H#QC%ybY^y_r5yym%0w@j3*9dTS9g>09LL+jGQ4gf6gGrWG%_V"
    "NO6+<*PxG~ZCbD%LVLL6t+{R4@JXF8cVHIdKL3f9N*-"
    "?K<gz<@KZ?vZsc3@UFleUtbT5~di3a6g^%Ctaivr?xD19kwmn6dVh%^k#o)CTPKFL^K|P3IW`H{#YWS5m0Ae^G-"
    "V$M0YeDE|y5Lk?BcA#%^YN~v+j?>w4xEQe*Gu(AbTzQ3r!`Bx(~Zu@v5_{eb4cW|j?)mp*d;x3=o)ZkQh5IS=BYNRIeCGLlmM-"
    "#qA<QP0(g04X3)uJh$%S+sAq(9tU<1(B*R;#z@{SKi<`orb147)`ii*hsiTx}QzBQJ7ou*ag+1{^ZRSwUk1UpLXbu#_mtt3;`itw"
    "@w8$ZBkeic^Vbrb>m6aWlFYR^EC#om|>4MV1(s)mUc8Ua)qE)J|bt3C)wyIJM<1P$aJ=#G&n;3Pnl-btDdzb{VyoAjIXc7Nym(R5"
    "O;<HsI`_`^4EgxCH`P=9oa|1w1%@D7(S2xRJ9<s;a3#-"
    "1Hev@xrmpqs=4Zx2$1hR`5}5FGuue=v3}egbvjnMItNqD7LS)9%17w8Sai^>ue{=H+m;1tC}dc=T#9!;#$&B#I6+$85XMt&|vn=9"
    "BUEEOfl?4vet(KzrCSB0)U$2n!_gw3#a;~=5q7fR3PW~vu?|+C4aN!G%0vU<gs(^kghzW4sXZ~nL~=MIedE(hiXD+Md1dsA=&bH$"
    "w?FfMO<9C>S-v>2|c=K&*zaeSvrrzU$S!~ReMVJgj0%ZUA<RFK2L;^1a~`>rNPR4bQYK7OcC45Jepv<(AcWg{{wVp<Wm"
)


def _decode_manifest() -> frozenset[str]:
    raw = zlib.decompress(base64.b85decode(_MANIFEST_B85.encode("ascii"))).decode("utf-8")
    return frozenset(line for line in raw.splitlines() if line)


EXPECTED_PATHS: Final[frozenset[str]] = _decode_manifest()
EXPECTED_MANIFEST_SHA256: Final[str] = (
    "50ae962a49493cc64258b5dfdec14f95a0401e4f64908373558bddf404c59559"
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
