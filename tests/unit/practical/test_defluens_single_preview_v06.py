"""Single probe delegates to existing WordBench; no claim of SA conformance."""
from pathlib import Path
import importlib.util

SCRIPT=Path(__file__).resolve().parents[3]/'tools'/'preview_defluens_capability.py'
SPEC=importlib.util.spec_from_file_location('defluens_preview_v06', SCRIPT)
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_all_15_intents_present():
    assert len(mod.INTENTS)==15
    assert 'conditional-instruction' in mod.INTENTS


def test_only_one_selected_probe_and_no_sa_release(monkeypatch,tmp_path):
    seen=[]
    def fake_run(language,**kw):
        seen.append((language,kw))
        return {'run_id':'test','archive_path':'/tmp/evidence.zip','scenarios':[
            {'id':'factual-negation','status':'candidate_for_review',
             'candidate':"Mira n' &+ est pas prête",'reason':'gold_and_linguistic_review_missing',
             'meaning_en':'Mira is not ready.','source_sha256':'a','script_sha256':'b'}]}
    monkeypatch.setattr(mod,'run_pilot',fake_run)
    out=mod.run_one(language='Fre',capability='factual-negation',
                    gf_executable=tmp_path/'gf.exe',rgl_root=tmp_path/'rgl',output_root=tmp_path/'out')
    assert len(seen)==1 and seen[0][1]['scenarios']==('factual-negation',)
    assert out['gf_executed'] and out['candidate']=="Mira n' &+ est pas prête"
    assert out['sa_semantic_request_executed'] is False
    assert out['sa_bridge_verified'] is False and out['released'] is False


def test_unknown_intent_is_rejected(tmp_path):
    try:
        mod.run_one(language='Fre',capability='not-a-capability',
            gf_executable=tmp_path/'gf',rgl_root=tmp_path,output_root=tmp_path)
    except ValueError:pass
    else:raise AssertionError('unlisted intent admitted')
