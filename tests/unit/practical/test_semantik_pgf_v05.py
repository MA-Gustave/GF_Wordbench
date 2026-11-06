"""Dev-builder envelope tested with a STUB executable, not an actual PGF test."""
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import sys

TOOLS=Path(__file__).resolve().parents[3]/'tools'/'build_semantik_profile3_candidate.py'
SPEC=importlib.util.spec_from_file_location('build_semantik_profile3_candidate_v05',TOOLS)
assert SPEC and SPEC.loader
MODULE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_stage_hashes_and_backup_without_fake_release(tmp_path):
    profile=tmp_path/'sa'/'profiles'/'konstellation-explorer-3'
    profile.mkdir(parents=True)
    for file in MODULE.SOURCE_FILES:
        (profile/file).write_text('fixture-'+file,encoding='utf-8')
    gf=tmp_path/'gf'
    gf.write_text('#!/usr/bin/env python3\nfrom pathlib import Path\nPath("Konstellation.pgf").write_bytes(b"STUB-NOT-A-COMPILED-PGF")\n')
    gf.chmod(0o755)
    target=tmp_path/'candidate'
    first=MODULE.build(sa_root=tmp_path/'sa',gf_exe=gf,destination=target)
    assert first['pgf_compiled'] is True and first['released'] is False and first['activated'] is False
    lock=json.loads((target/'pipeline.lock.json').read_text())
    for name,expected in lock['inputs'].items():
        assert hashlib.sha256((target/name).read_bytes()).hexdigest()==expected
    # The builder must never allow accidental replacement.
    try:
        MODULE.build(sa_root=tmp_path/'sa',gf_exe=gf,destination=target)
    except FileExistsError: pass
    else: raise AssertionError('Existing candidate overwritten without --force')
    second=MODULE.build(sa_root=tmp_path/'sa',gf_exe=gf,destination=target,force=True)
    assert Path(second['previous_candidate_backup']).is_dir()
