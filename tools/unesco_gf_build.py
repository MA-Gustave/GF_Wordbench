"""GF Wordbench-owned private UNESCO candidate PGF build.

Uses Wordbench's command builder and bounded process runner. Never publishes,
creates a release artifact, or updates a gold. Writes only in candidate dir.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))

GF_DEFAULT = Path(r'C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe')
CONCRETES = {'fr': 'UnescoPilotFre', 'en': 'UnescoPilotEng'}


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compile_candidate(candidate: Path, lang: str, gf_exe: Path, timeout: float = 90.0) -> dict:
    if lang not in CONCRETES:
        raise ValueError('langue inconnue')
    candidate = candidate.resolve(strict=True)
    if not candidate.is_dir() or candidate.is_symlink():
        raise ValueError('dossier candidat non fiable')
    expected = ('UnescoPilot.gf', CONCRETES[lang]+'.gf')
    for name in expected:
        p = candidate/name
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 1_000_000:
            raise ValueError('source GF manquante ou non sûre : '+name)

    report = {
        'format': 'gf-wordbench.unesco-pilot-build/1.0', 'status': 'BLOCKED',
        'language': lang, 'candidate': str(candidate), 'gf_executable': str(gf_exe),
        'source_sha256': {name:digest(candidate/name) for name in expected},
        'pgf_compiled': False, 'release_authorized': False,
        'notes': 'Compilateur GF réel, artefact candidat seulement. Aucun gold ni gate de release.'
    }
    dest = candidate / 'wordbench-build.json'
    try:
        gf_exe = gf_exe.expanduser().resolve(strict=True)
        if not gf_exe.is_file() or gf_exe.name.lower() not in {'gf.exe','gf'}:
            raise ValueError('gf.exe non trouvé ou invalide')
        from gf_wordbench.infrastructure.process.models import ProcessOperationKind, ProcessRequest, ArtifactExpectation, ArtifactKind
        from gf_wordbench.infrastructure.process.runner import run_process
        from gf_wordbench.validation.compilation.commands import GfCommandProfile, build_pgf_command
        from gf_wordbench.kernel.statuses import ExecutionState

        command = build_pgf_command(
            executable=gf_exe, working_directory=candidate,
            entrypoints=[CONCRETES[lang]+'.gf'], gf_search_paths=[candidate],
            profile=GfCommandProfile(profile_id='unesco-gf-312', path_separator=os.pathsep),
            output_dir=candidate, optimize=False)
        request = ProcessRequest(
            request_id='unesco-'+lang+'-candidate-compile',tool_id='gf',operation_id='unesco-'+lang+'-pgf',
            operation_kind=ProcessOperationKind.PGF_BUILD,
            executable=gf_exe, args=command.arguments, cwd=candidate,
            stdout_path=candidate/'gf-stdout.log', stderr_path=candidate/'gf-stderr.log',
            timeout_sec=timeout,
            approved_read_roots=(candidate, gf_exe.parent),
            approved_write_roots=(candidate,),
            evidence_policy='private-unqualified-candidate-v1',
            mutability_class='run_artifacts_only', network_policy='denied',
        )
        result = run_process(request)
        report.update({
            'process_state': result.execution_state.value, 'exit_code': result.exit_code,
            'capture_complete': result.capture_complete,
            'stdout_bytes': result.stdout_size_bytes, 'stderr_bytes': result.stderr_size_bytes,
            'duration_ms': result.duration_ms,
            'launch_error': result.launch_error_message[:800],
            'command_arguments': list(command.arguments),
        })
        pgf = candidate/'UnescoPilot.pgf'
        if (result.execution_state is not ExecutionState.COMPLETED or
                result.exit_code != 0 or not result.capture_complete or
                not pgf.is_file() or pgf.stat().st_size < 8):
            report['status'] = 'BLOCKED_COMPILATION_OR_ARTIFACT'
        else:
            shutil.copyfile(pgf, candidate/'grammar.pgf')
            report.update({'status':'PGF_BUILT_CANDIDATE_ONLY','pgf_compiled': True,
                           'pgf_sha256':digest(candidate/'grammar.pgf'),
                           'pgf_size': (candidate/'grammar.pgf').stat().st_size})
    except (OSError,ValueError,RuntimeError) as exc:
        report.update({'status':'BLOCKED','error':f'{type(exc).__name__}: {exc}'})
    finally:
        dest.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return report


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--lang',choices=sorted(CONCRETES),required=True)
    p.add_argument('--gf-exe',type=Path,default=GF_DEFAULT)
    p.add_argument('--timeout',type=float,default=90)
    a=p.parse_args(argv)
    if not 0<a.timeout<=600:
        p.error('timeout must be between 0 and 600 seconds')
    result=compile_candidate(a.candidate,a.lang,a.gf_exe,a.timeout)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status']=='PGF_BUILT_CANDIDATE_ONLY' else 2

if __name__ == '__main__':
    raise SystemExit(main())
