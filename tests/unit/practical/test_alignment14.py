"""RGL alignment is a *proposal*, never GF execution or linguistic certification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest

from gf_wordbench.practical.alignment14 import (
    PILOTS, read_policy, prepare_alignment, apply_alignment, _rgl_provenance,
)
from gf_wordbench.practical.pilot import _validate_pilot


@pytest.fixture
def rgl(tmp_path: Path) -> Path:
    root = tmp_path / 'rgl'
    # Minimal lexical source fixture. Production checks full real RGL files.
    for code, directory in [('Eng', 'english'), ('Por','portuguese')]:
        path = root/'src'/directory
        path.mkdir(parents=True)
        (path/f'Lexicon{code}.gf').write_text(
            'concrete Lexicon'+code+' of Lexicon = Cat'+code+' ** {\n'
            'lin\n  book_N = book ;\n  house_N = house ;\n'
            '  say_VS = say ;\n  ready_A = ready ;\n} ;\n',encoding='utf8')
        (path/f'Paradigms{code}.gf').write_text(
            'resource Paradigms'+code+' = { oper dummy : Str = "" ; } ;\n',encoding='utf8')
    return root


def _copy_langs(tmp_path: Path, langs: tuple[str,...]) -> Path:
    root = tmp_path/'pilots'
    root.mkdir()
    shutil.copy2(PILOTS/'language_catalog.json',root/'language_catalog.json')
    for lang in langs:
        shutil.copytree(PILOTS/lang,root/lang)
    return root


def test_focus14_has_fourteen_langs_and_15_signed_scenarios_each():
    policy=read_policy()
    assert len(policy['languages'])==14
    for lang in policy['languages']:
        assert _validate_pilot(lang)['scenario_count']==15


def test_proposals_are_read_only_and_sha_verified(rgl,tmp_path):
    pilots=_copy_langs(tmp_path,('Eng','Por'))
    gf=pilots/'Eng/validation/inputs/DefluensFactualPresentEng.gf'
    before=gf.read_bytes()
    report, changes=prepare_alignment(pilots_root=pilots,rgl_root=rgl,languages=('Eng','Por'))
    assert report['totals']['scenarios_examined']==30
    assert report['totals']['scenarios_modified']==0  # snapshots already aligned
    assert changes=={}
    assert gf.read_bytes()==before
    assert report['validation_status']=='pending_windows_gf_and_semantic_review'


def test_idempotent_apply_preserves_source_locks(rgl,tmp_path):
    pilots=_copy_langs(tmp_path,('Eng','Por'))
    before={p:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (rgl/'src').rglob('*.gf')}
    report=apply_alignment(pilots_root=pilots,rgl_root=rgl,languages=('Eng','Por'))
    assert report['totals']['scenarios_modified']==0
    assert report['files_written']==0
    for code in ('Eng','Por'):
        assert _validate_pilot(code,pilots_root=pilots)['scenario_count']==15
    assert before=={p:hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (rgl/'src').rglob('*.gf')}


def test_lexical_sources_used_in_proposed_module():
    p=PILOTS/'Por/validation/inputs/DefluensSourceAttributionPor.gf'
    text=p.read_text(encoding='utf-8')
    assert '(L = LexiconPor)' in text
    assert 'L.say_VS' in text
    assert 'L.ready_A' in text
    assert 'mkPN "Mira" feminine' in text
    assert _validate_pilot('Por')['status']=='preflight_ok'


def test_ambiguous_lexicon_missing_rejected(rgl,tmp_path):
    lex=rgl/'src/english/LexiconEng.gf'
    original=lex.read_text(encoding='utf8')
    lex.write_text(original.replace('  book_N =', '  book_REMOVED ='),encoding='utf8')
    with pytest.raises(ValueError,match='book_N'):
        _rgl_provenance(rgl/'src','Eng','english',ready=True)


def test_other_six_pilots_remain_static():
    policy=read_policy()
    other=set(json.loads((PILOTS/'language_catalog.json').read_text())['languages'])-set(policy['languages'])
    assert other=={'Cze','Pol','Sqi','Rus','Hrv','Gre'}
    for lang in other:
        assert _validate_pilot(lang)['scenario_count']==15
        assert 'alignment' not in json.loads((PILOTS/lang/'pilot_manifest.json').read_text())


def test_generated_grammar_cannot_silently_discard_alignment(tmp_path):
    tools_root=Path(__file__).resolve().parents[3]/'tools'
    sys.path.insert(0,str(tools_root))
    try:
        from generate_practical_pilots import build
        pilots=tmp_path/'pilots'
        (pilots/'Eng').mkdir(parents=True)
        (pilots/'Eng/pilot_manifest.json').write_text('{"alignment": {"status": "proposed"}}',encoding='utf8')
        with pytest.raises(RuntimeError,match='alignment already applied'):
            build(root=pilots)
    finally:
        sys.path.remove(str(tools_root))


def test_fresh_unaligned_english_module_can_be_repaired_and_relocked(rgl,tmp_path):
    """Actually exercises a source change, not only rerunning an aligned snapshot."""
    pilots=_copy_langs(tmp_path,('Eng',))
    target=pilots/'Eng/validation/inputs/DefluensQuantityEng.gf'
    source=target.read_text(encoding='utf8')
    source=source.replace('L.book_N','(mkN "book")')
    source=source.replace('open SyntaxEng, ParadigmsEng, (L = LexiconEng) in {',
                          'open SyntaxEng, ParadigmsEng in {')
    source=source.replace('-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED\n','')
    target.write_text(source,encoding='utf8')
    manifest_path=pilots/'Eng/pilot_manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf8'))
    entry=next(v for v in manifest['scenarios'] if v['id']=='quantity')
    oldhash=entry['source_sha256']
    newhash=hashlib.sha256(target.read_bytes()).hexdigest()
    entry['source_sha256']=newhash
    script=pilots/'Eng'/entry['script']
    content=script.read_text(encoding='utf8').replace(oldhash,newhash)
    script.write_text(content,encoding='utf8')
    entry['script_sha256']=hashlib.sha256(script.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    assert _validate_pilot('Eng',pilots_root=pilots)['status']=='preflight_ok'
    report=apply_alignment(pilots_root=pilots,rgl_root=rgl,languages=('Eng',))
    assert report['totals']['scenarios_modified']==1
    assert report['files_written']==3
    assert 'L.book_N' in target.read_text(encoding='utf8')
    assert _validate_pilot('Eng',pilots_root=pilots)['status']=='preflight_ok'


def test_compare_requires_current_210_source_locks_and_preserves_non_certification(tmp_path):
    from zipfile import ZipFile
    from gf_wordbench.practical.alignment_compare import BASELINE, compare_archive, locate_latest_matching_batch
    baseline=json.loads(BASELINE.read_text(encoding='utf8'))
    hashes={}
    for code in read_policy()['languages']:
        manifest=json.loads((PILOTS/code/'pilot_manifest.json').read_text(encoding='utf8'))
        hashes.update({(code,i['id']):(i['source_sha256'],i['script_sha256']) for i in manifest['scenarios']})
    rows=baseline['assessments']
    runname='defluens-batch-full-20261103T235959Z-example'
    path=tmp_path/(runname+'.zip')
    with ZipFile(path,'w') as z:
        for code in read_policy()['languages']:
            report={'schema_id':'defluens.pilot-run','language':code,'scenarios':[]}
            for entry in [a for a in rows if a['language']==code]:
                scenario=entry['scenario_id'];key=(code,scenario)
                candidate=entry['candidate']+' nouveau' if key==('Eng','factual-present') else entry['candidate']
                report['scenarios'].append({'id':scenario,'candidate':candidate,
                    'source_sha256':hashes[key][0],'script_sha256':hashes[key][1],
                    'status':'candidate_for_review'})
                z.writestr(f'{runname}/languages/defluens-pilot-{code}-a/scenarios/{scenario}.candidate.txt',candidate+'\n')
            z.writestr(f'{runname}/languages/defluens-pilot-{code}-a/pilot_run.json',json.dumps(report))
    result=compare_archive(path)
    assert result['totals']['scenarios']==210
    assert result['totals']['output_changed']==1
    assert result['gold_approved'] is False
    assert result['semantic_coverage_verified'] is False
    assert locate_latest_matching_batch(tmp_path)==path
