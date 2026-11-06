"""Independent source and explicit human mapping gates, no GF simulation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

SPEC=importlib.util.spec_from_file_location('dik_sa_v09',Path(__file__).parents[3]/'tools/build_dik_semantik_lexicon.py')
MODULE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write(p,obj):
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return hashlib.sha256(p.read_bytes()).hexdigest()


def seed(tmp_path, accepted=False):
    source=tmp_path/'dik';source.mkdir()
    row={'semantic_ref':'wikidata:lexeme:L101','language':'fr','lexical_ref':'L101',
         'source_kind':'wikidata','binding_kind':'lexeme_ref','use_for':'knowledge',
         'source_ref':'wikidata:lexeme:L101','properties':{'status':'candidate_observation_only'}}
    lex={'schema_version':'1.1','source_kind':'wikidata','entries':[row]}
    review={'schema_id':'dik.gf-human-mapping-decisions','schema_version':'1.0','locale':'fr',
            'source_candidate_sha256':'a'*64,'decisions':[{'source_lexeme_id':'L101',
            'semantic_ref':'wikidata:lexeme:L101','decision':'pending','gf_function':None,'gf_category':None}]}
    lh=_write(source/'semantik.knowledge.json',lex)
    th=_write(source/'gf-mapping-review.template.json',review)
    _write(source/'manifest.json',{'schema_id':'dik.semantik-knowledge-handoff/1.0-candidate',
           'released':False,'gf_bindings':0,'locale':'fr','entries':1,'lexicon_sha256':lh,
           'review_template_sha256':th,'source_candidate_sha256':'a'*64})
    if accepted:
        review['decisions'][0].update(decision='accept',gf_function='Cat_N',gf_category='N',
            reviewer='a-test-reviewer',mapping_reviewed=True,license_reviewed=True,
            target_semantic_ref='example:cat',semantic_authority_ref='example:source',
            semantic_identity_reviewed=True)
    rf=tmp_path/'decisions.json';_write(rf,review)
    return source,rf


def test_unreviewed_no_binding(tmp_path):
    source,rf=seed(tmp_path)
    out=MODULE.build(dik_bundle=source,decisions_file=rf,output_dir=tmp_path/'out')
    assert out['knowledge_entries']==1 and out['human_reviewed_binding_candidates']==0
    assert MODULE.audit(tmp_path/'out')['gf_verified'] is False


def test_explicit_review_candidate(tmp_path):
    source,rf=seed(tmp_path,accepted=True)
    res=MODULE.build(dik_bundle=source,decisions_file=rf,output_dir=tmp_path/'out')
    assert res['human_reviewed_binding_candidates']==1
    rows=json.loads((tmp_path/'out'/'lexicon.candidate.json').read_text())['entries']
    assert rows[1]['semantic_ref']=='example:cat'
    assert rows[1]['source_ref']=='wikidata:lexeme:L101'
    assert rows[1]['properties']['gf_artifact_verified'] is False
    assert MODULE.audit(tmp_path/'out')['binding_candidates']==1


def test_approval_requires_semantic_owner(tmp_path):
    source,rf=seed(tmp_path,accepted=True)
    doc=json.loads(rf.read_text());doc['decisions'][0]['semantic_identity_reviewed']=False;_write(rf,doc)
    with pytest.raises(ValueError,match='authorized target'):
        MODULE.build(dik_bundle=source,decisions_file=rf,output_dir=tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_untrusted_source_digest_refused(tmp_path):
    source,rf=seed(tmp_path,accepted=True)
    (source/'semantik.knowledge.json').write_text('{}')
    with pytest.raises(ValueError,match='digest'):
        MODULE.build(dik_bundle=source,decisions_file=rf,output_dir=tmp_path/'out')
