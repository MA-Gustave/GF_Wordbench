"""Build wiring checked using executable stub; real GF 3.12 must run on Windows."""
import importlib.util
import json
from pathlib import Path

TOOLS=Path(__file__).resolve().parents[3]/'tools'/'build_semantik_profile3_candidate.py'
SPEC=importlib.util.spec_from_file_location('semantik_builder_v07',TOOLS)
mod=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(mod)

def test_builder_uses_rgl_paths_and_profile_id(tmp_path):
    sa=tmp_path/'sa';pr=sa/'profiles'/mod.ATTRIBUTE_PROFILE;pr.mkdir(parents=True)
    for f in mod.ATTRIBUTE_SOURCE_FILES:(pr/f).write_text('fixture-'+f)
    rgl=tmp_path/'rgl'
    for sub in ('api','abstract','french','romance','common','prelude'):
        (rgl/'src'/sub).mkdir(parents=True)
    gf=tmp_path/'gf';gf.write_text('#!/usr/bin/env python3\nfrom pathlib import Path\nPath("DefluensAttribute.pgf").write_bytes(b"STUB-ONLY-NOT-REAL-PGF")\n');gf.chmod(0o755)
    out=tmp_path/'out';result=mod.build(sa_root=sa,gf_exe=gf,destination=out,
                   profile_id=mod.ATTRIBUTE_PROFILE,rgl_root=rgl)
    assert result['pgf_compiled'] is True and result['released'] is False
    lock=json.loads((out/'pipeline.lock.json').read_text())
    assert lock['runtime_set_id']==mod.ATTRIBUTE_PROFILE
    assert lock['concrete']=='DefluensAttributeFre'
    assert '--path=' in ' '.join(result['gf_command_arguments'])
    assert str(rgl/'src/french') in ' '.join(result['gf_command_arguments'])

def test_builder_requires_rgl_root(tmp_path):
    try:
        mod.build(sa_root=tmp_path/'sa',gf_exe=tmp_path/'gf',destination=tmp_path/'out',profile_id=mod.ATTRIBUTE_PROFILE)
    except ValueError as e:assert 'RGL root' in str(e)
    else:raise AssertionError('RGL-less candidate compile accepted')
