"""Build a real GF *candidate*, using WordBench's own process/PGF boundary.

The GF sources, bridge, lexicon, profile and suite are owned by SemantiK
Architect (profiles/konstellation-explorer-3). This tool copies, compiles and
locks their hashes. It never fakes a PGF, certifies golds, activates or releases
any RuntimeSet. Requires the user's installed official gf.exe.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))

SOURCE_FILES = ('Konstellation.gf', 'KonstellationFre.gf', 'bridge.json',
                'lexicon.json', 'profile.json', 'conformance.suite.json')
LOCKED_FILES = ('grammar.pgf', 'bridge.json', 'lexicon.json',
                'profile.json', 'conformance.suite.json')
RUNTIME_SET = 'konstellation-fr-3'
PROFILE = 'konstellation-explorer-3'
CONCRETE = 'KonstellationFre'
ATTRIBUTE_PROFILE = 'defluens-attribute-fr-1'
ATTRIBUTE_SOURCE_FILES = ('DefluensAttribute.gf', 'DefluensAttributeFre.gf', 'bridge.json',
                          'lexicon.json', 'profile.json', 'conformance.suite.json')
ATTRIBUTE_CONCRETE = 'DefluensAttributeFre'
ATTRIBUTE_ABSTRACT = 'DefluensAttribute'
CORE_FR = 'defluens-core-fr-1'
CORE_EN = 'defluens-core-en-1'
CORE_SOURCE = 'defluens-core-1'
CORE_ABSTRACT = 'DefluensCore'

DEFAULT_GF = Path(r'C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe')
DEFAULT_SA = Path(r'C:\mycode\SemantiK_Architect\SemantiK_Architect')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _log_tail(path: Path, *, max_bytes: int = 16_384, max_chars: int = 5_000) -> str:
    """Bounded, lossy-tolerant diagnostic excerpt, not a replacement for raw logs."""
    try:
        with path.open('rb') as stream:
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(max(0, size - max_bytes))
            chunk = stream.read(max_bytes)
    except OSError:
        return ''
    result = chunk.decode('utf-8-sig', errors='replace')
    # Omit terminal control sequences except line breaks/tabs from JSON and CLI output.
    result = ''.join(c for c in result if c in '\n\r\t' or ord(c) >= 32)
    return result[-max_chars:]


def _compile_failure_reason(process: Any, pgf: Path) -> str:
    if process.launch_error_message:
        return 'GF_LAUNCH_ERROR'
    if process.exit_code is not None and process.exit_code != 0:
        return 'GF_EXIT_NONZERO'
    if not process.capture_complete:
        return 'GF_CAPTURE_INCOMPLETE'
    if not pgf.is_file() or pgf.stat().st_size <= 8:
        return 'PGF_MISSING_OR_INVALID'
    return 'GF_EXECUTION_NOT_COMPLETED'


def candidate_location(home: Path | None = None, profile_id: str = PROFILE) -> Path:
    return (home or Path.home()) / 'Downloads' / 'Ars_Magna_Defluens' / 'semantik_candidates' / (RUNTIME_SET if profile_id == PROFILE else profile_id)


def build(*, sa_root: Path, gf_exe: Path, destination: Path, timeout: float = 120,
          force: bool = False, profile_id: str = PROFILE, rgl_root: Path | None = None) -> dict[str, Any]:
    """Compile and stage one bounded candidate in an isolated directory.

    An existing candidate is never overwritten unless force is explicit; even
    then the previous candidate is retained as a timestamped backup.
    """
    sa_root, destination = sa_root.expanduser().resolve(), destination.expanduser().resolve()
    if profile_id not in (PROFILE, ATTRIBUTE_PROFILE, CORE_FR, CORE_EN):
        raise ValueError('Unknown SemantiK candidate profile')
    use_attribute = profile_id == ATTRIBUTE_PROFILE
    use_core = profile_id in (CORE_FR, CORE_EN)
    core_language = 'fr' if profile_id == CORE_FR else 'en'
    concrete = ('DefluensCoreFre' if core_language == 'fr' else 'DefluensCoreEng') if use_core else (ATTRIBUTE_CONCRETE if use_attribute else CONCRETE)
    abstract = CORE_ABSTRACT if use_core else (ATTRIBUTE_ABSTRACT if use_attribute else 'Konstellation')
    runtime_set = profile_id if (use_attribute or use_core) else RUNTIME_SET
    profile = sa_root / 'profiles' / (CORE_SOURCE if use_core else profile_id)
    source_map = (
        [(CORE_ABSTRACT+'.gf', CORE_ABSTRACT+'.gf'), (concrete+'.gf', concrete+'.gf'),
         (f'bridge.{core_language}.json', 'bridge.json'),
         (f'lexicon.{core_language}.json', 'lexicon.json'),
         (f'profile.{core_language}.json', 'profile.json'),
         (f'conformance.{core_language}.suite.json', 'conformance.suite.json')]
        if use_core else [(n,n) for n in (ATTRIBUTE_SOURCE_FILES if use_attribute else SOURCE_FILES)]
    )
    source_files = tuple(src for src,_ in source_map)
    rgl_search_paths: list[Path] = []
    if use_attribute or use_core:
        if rgl_root is None: raise ValueError('RGL root is required for the RGL-backed candidate grammar')
        rgl_root = rgl_root.expanduser().resolve()
        modules = ('api','abstract','english','common','prelude') if use_core and core_language=='en' else ('api','abstract','french','romance','common','prelude')
        for name in modules:
            path = rgl_root/'src'/name
            if not path.is_dir(): raise FileNotFoundError('RGL module directory is missing: '+str(path))
            rgl_search_paths.append(path)
    if not 1 <= timeout <= 600:
        raise ValueError('timeout must be 1–600 seconds')
    for name in source_files:
        file = profile / name
        if not file.is_file() or file.is_symlink() or file.stat().st_size > 2_000_000:
            raise FileNotFoundError('Missing/unsafe canonical SA profile artifact: ' + str(file))
    if not gf_exe.expanduser().is_file():
        raise FileNotFoundError('Official GF binary missing: ' + str(gf_exe))
    gf_exe = gf_exe.expanduser().resolve()
    if gf_exe.name.lower() not in ('gf', 'gf.exe'):
        raise ValueError('Expected gf or gf.exe, not an arbitrary executable')
    if destination.exists() and not force:
        raise FileExistsError('Candidate already exists (use --force to back it up): ' + str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='semantik-pgf-build-', dir=destination.parent))
    try:
        for src_name, dst_name in source_map:
            shutil.copy2(profile/src_name, work/dst_name)
        from gf_wordbench.validation.compilation.commands import GfCommandProfile, build_pgf_command
        from gf_wordbench.infrastructure.process.models import ProcessOperationKind, ProcessRequest
        from gf_wordbench.infrastructure.process.runner import run_process
        from gf_wordbench.kernel.statuses import ExecutionState

        command = build_pgf_command(
            executable=gf_exe, working_directory=work,
            entrypoints=[concrete+'.gf'], gf_search_paths=[work, *rgl_search_paths],
            profile=GfCommandProfile(profile_id='semantik-core-gf312' if use_core else ('semantik-attribute-gf312' if use_attribute else 'semantik-profile3-gf312'), path_separator=os.pathsep),
            output_dir=work, optimize=False)
        process = run_process(ProcessRequest(
            request_id='defluens-core-compile' if use_core else ('defluens-fr-attribute-compile' if use_attribute else 'defluens-fr-profile3-compile'), tool_id='gf',
            operation_id='semantik-core-pgf' if use_core else ('semantik-attribute-pgf' if use_attribute else 'semantik-profile3-pgf'),
            operation_kind=ProcessOperationKind.PGF_BUILD,
            executable=gf_exe, args=command.arguments, cwd=work,
            stdout_path=work/'gf-stdout.log', stderr_path=work/'gf-stderr.log',
            timeout_sec=timeout,
            approved_read_roots=(work, gf_exe.parent, *rgl_search_paths),
            approved_write_roots=(work,),
            evidence_policy='private-unqualified-candidate-v1',
            mutability_class='run_artifacts_only', network_policy='denied',
        ))
        pgf = work / (abstract+'.pgf')
        success = (process.execution_state is ExecutionState.COMPLETED and
                   process.exit_code == 0 and process.capture_complete and
                   pgf.is_file() and pgf.stat().st_size > 8)
        report = {
            'schema_id': 'defluens.semantik-candidate-build', 'schema_version': '1.0',
            'status': 'PGF_BUILT_CANDIDATE_ONLY' if success else 'BLOCKED_Gf_COMPILATION',
            'profile_id': profile_id, 'runtime_set_id': runtime_set, 'language': core_language if use_core else 'fr',
            'concrete': concrete, 'gf_executable': str(gf_exe),
            'source_path': str(profile), 'source_hashes': {n: sha(profile/n) for n in source_files},
            'gf_process_state': process.execution_state.value,
            'exit_code': process.exit_code,
            'capture_complete': process.capture_complete,
            'duration_ms': process.duration_ms,
            'gf_command_arguments': list(command.arguments),
            'pgf_compiled': bool(success), 'released': False, 'activated': False,
            'linguistically_certified': False,
            'limitation': ('RGL-backed six-operation candidate; no released runtime or full 15-capability coverage.' if use_core else ('Bounded RGL French attribute candidate; not the 15-capability product runtime.' if use_attribute else 'Existing 5-case French typed-expression profile; not the 15-capability product runtime.')),
        }
        if not success:
            # A GF compiler error is not a launch error. Show the captured evidence
            # and preserve the complete logs for precise source-line diagnostics.
            stdout_log, stderr_log = work/'gf-stdout.log', work/'gf-stderr.log'
            stderr_tail, stdout_tail = _log_tail(stderr_log), _log_tail(stdout_log)
            reason = _compile_failure_reason(process, pgf)
            report.update({
                'failure_reason': reason,
                'diagnostics_dir': str(work),
                'gf_stdout_log': str(stdout_log),
                'gf_stderr_log': str(stderr_log),
                'gf_stderr_tail': stderr_tail,
                'gf_stdout_tail': stdout_tail,
            })
            detail = process.launch_error_message or stderr_tail or stdout_tail
            report['error'] = (f'{reason}: ' + (detail[-1400:] if detail else
                               'GF provided no captured text; inspect logs and command arguments.'))
            (work/'build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
            # Never replace an existing candidate after a failed compilation.
            return report
        shutil.copyfile(pgf, work/'grammar.pgf')
        inputs = {n: sha(work/n) for n in LOCKED_FILES}
        lock = {'schema_version':'1.0','runtime_set_id':runtime_set,
                'language':core_language if use_core else 'fr','profile_id':profile_id,'concrete':concrete,
                'sa_gf_contract_version':'1.0','inputs':inputs}
        (work/'pipeline.lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
        report['pgf_sha256'] = inputs['grammar.pgf']
        report['pgf_bytes'] = (work/'grammar.pgf').stat().st_size
        (work/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        backup = None
        if destination.exists():
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            backup = destination.with_name(destination.name + '.backup-' + stamp)
            i=0
            while backup.exists():
                i += 1
                backup = destination.with_name(destination.name + '.backup-' + stamp + '-' + str(i))
            destination.rename(backup)
        try:
            work.rename(destination)
        except OSError:
            if backup and backup.exists():
                backup.rename(destination)
            raise
        report['candidate_dir'] = str(destination)
        if backup:
            report['previous_candidate_backup'] = str(backup)
        return report
    finally:
        if work.exists():
            # Failure workspaces keep logs intentionally. Success was renamed.
            if (work/'build-report.json').exists():
                try:
                    failed=json.loads((work/'build-report.json').read_text(encoding='utf-8'))
                except (ValueError, OSError):
                    failed={}
                if failed.get('status') == 'PGF_BUILT_CANDIDATE_ONLY':
                    shutil.rmtree(work, ignore_errors=True)
            else:
                shutil.rmtree(work, ignore_errors=True)


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--semantik-root',type=Path,default=DEFAULT_SA)
    p.add_argument('--gf-exe',type=Path,default=DEFAULT_GF)
    p.add_argument('--profile',choices=[PROFILE,ATTRIBUTE_PROFILE,CORE_FR,CORE_EN],default=PROFILE)
    p.add_argument('--rgl-root',type=Path,help='Required for RGL-backed attribute candidate')
    p.add_argument('--output',type=Path,default=None)
    p.add_argument('--timeout',type=float,default=120)
    p.add_argument('--force',action='store_true',help='Back up existing candidate before replacing it')
    a=p.parse_args(argv)
    try:
        result=build(sa_root=a.semantik_root,gf_exe=a.gf_exe,destination=a.output or candidate_location(profile_id=a.profile),timeout=a.timeout,force=a.force,
                     profile_id=a.profile,rgl_root=a.rgl_root)
    except (OSError,ValueError,RuntimeError) as exc:
        result={'status':'BLOCKED','error':f'{type(exc).__name__}: {exc}',
                'pgf_compiled':False,'released':False,'activated':False}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status']=='PGF_BUILT_CANDIDATE_ONLY' else 2

if __name__=='__main__':
    raise SystemExit(main())
