"""Regression: a compiler rejection is not a launch error.

These tests use a deliberately failing stub. They do not qualify real GF.
"""
import importlib.util
import json
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[3] / 'tools'


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = _module('builder_gf_diagnostics', TOOLS / 'build_semantik_profile3_candidate.py')
inspector = _module('inspector_gf_diagnostics', TOOLS / 'inspect_semantik_gf_failure.py')


@pytest.mark.parametrize('stream', ['stderr', 'stdout'])
def test_nonzero_compiler_preserves_candidate_and_surfaces_log(tmp_path, stream):
    sa = tmp_path / 'sa'
    profile = sa / 'profiles' / builder.CORE_SOURCE
    profile.mkdir(parents=True)
    for file in (
        'DefluensCore.gf', 'DefluensCoreFre.gf',
        'bridge.fr.json', 'lexicon.fr.json', 'profile.fr.json', 'conformance.fr.suite.json',
    ):
        (profile / file).write_text('fixture ' + file, encoding='utf-8')
    rgl = tmp_path / 'rgl'
    for module in ('api', 'abstract', 'french', 'romance', 'common', 'prelude'):
        (rgl / 'src' / module).mkdir(parents=True)
    gf = tmp_path / 'gf'
    gf.write_text('#!/usr/bin/env python3\nimport sys\nprint("Type mismatch in DefluensCoreFre.gf", file=sys.' + stream + ')\nsys.exit(1)\n', encoding='utf-8')
    gf.chmod(0o755)
    destination = tmp_path / 'semantik_candidates' / builder.CORE_FR
    destination.mkdir(parents=True)
    (destination / 'kept.txt').write_text('do not touch', encoding='utf-8')
    result = builder.build(sa_root=sa, gf_exe=gf, rgl_root=rgl,
                           destination=destination, profile_id=builder.CORE_FR, force=True)
    assert result['status'] == 'BLOCKED_Gf_COMPILATION'
    assert result['exit_code'] == 1
    assert result['capture_complete'] is True
    assert result['failure_reason'] == 'GF_EXIT_NONZERO'
    assert 'Type mismatch in DefluensCoreFre.gf' in result['error']
    assert (destination / 'kept.txt').read_text() == 'do not touch'
    assert not (destination / 'pipeline.lock.json').exists()
    diagnostic_dir = Path(result['diagnostics_dir'])
    assert diagnostic_dir.exists()
    assert json.loads((diagnostic_dir / 'build-report.json').read_text())['diagnostics_dir'] == str(diagnostic_dir)
    assert 'Type mismatch in DefluensCoreFre.gf' in inspector.inspect(destination.parent, builder.CORE_FR)


def test_failure_report_of_previous_version_can_still_be_inspected(tmp_path):
    run = tmp_path / 'semantik-pgf-build-abc'
    run.mkdir()
    (run / 'build-report.json').write_text(json.dumps({'status':'BLOCKED_Gf_COMPILATION','profile_id':builder.CORE_FR,'exit_code':1}))
    (run / 'gf-stdout.log').write_text('Error: old compiler log\n')
    (run / 'gf-stderr.log').write_text('')
    summary = inspector.inspect(tmp_path, builder.CORE_FR)
    assert 'old compiler log' in summary
    assert '(journal vide)' in summary


def test_log_tail_is_bounded_and_safe(tmp_path):
    p = tmp_path / 'gf-stderr.log'
    p.write_bytes(b'A' * 99_000 + b'\nGF error: invalid\x1b[2J\n')
    result = builder._log_tail(p)
    assert len(result) <= 5000
    assert 'GF error: invalid' in result
    assert '\x1b' not in result
