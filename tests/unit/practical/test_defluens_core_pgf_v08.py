"""v0.8 builder tests exercise process + hashing with a FAKE GF executable only.
They do not verify actual GF syntax/linguistic linearization.
"""
from pathlib import Path
import importlib.util
import json
import pytest

TOOLS=Path(__file__).resolve().parents[3]/'tools'/'build_semantik_profile3_candidate.py'
SPEC=importlib.util.spec_from_file_location('defluens_core_builder',TOOLS)
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

@pytest.mark.parametrize('language,profile,concrete', [('fr',mod.CORE_FR,'DefluensCoreFre'),('en',mod.CORE_EN,'DefluensCoreEng')])
def test_typed_candidate_builder_stages_immutable_artifacts(language,profile,concrete,tmp_path):
    sa=tmp_path/'sa';source=sa/'profiles'/mod.CORE_SOURCE;source.mkdir(parents=True)
    for fn in [mod.CORE_ABSTRACT+'.gf',concrete+'.gf',
               f'bridge.{language}.json',f'lexicon.{language}.json',
               f'profile.{language}.json',f'conformance.{language}.suite.json']:
        (source/fn).write_text('test-'+fn,encoding='utf-8')
    rgl=tmp_path/'rgl'
    for sub in ('api','abstract', 'english' if language=='en' else 'french','common','prelude',*(() if language=='en' else ('romance',))):
        (rgl/'src'/sub).mkdir(parents=True,exist_ok=True)
    gf=tmp_path/'gf'
    gf.write_text('#!/usr/bin/env python3\nfrom pathlib import Path\nPath("DefluensCore.pgf").write_bytes(b"FAKE-GF-DOES-NOT-CERTIFY-LINGUISTICS")\n')
    gf.chmod(0o755)
    result=mod.build(sa_root=sa,gf_exe=gf,rgl_root=rgl,destination=tmp_path/'out',profile_id=profile)
    assert result['pgf_compiled'] and not result['released'] and result['language']==language
    lock=json.loads((tmp_path/'out/pipeline.lock.json').read_text())
    assert lock['language']==language and lock['concrete']==concrete and lock['runtime_set_id']==profile
    assert (tmp_path/'out/bridge.json').read_text()=='test-bridge.'+language+'.json'
    assert (tmp_path/'out/grammar.pgf').read_bytes().startswith(b'FAKE-GF')
    assert all(len(x)==64 for x in lock['inputs'].values())


def test_core_builder_requires_explicit_rgl(tmp_path):
    with pytest.raises(ValueError,match='RGL root'):
        mod.build(sa_root=tmp_path/'na',gf_exe=tmp_path/'gf',destination=tmp_path/'out',profile_id=mod.CORE_FR)
