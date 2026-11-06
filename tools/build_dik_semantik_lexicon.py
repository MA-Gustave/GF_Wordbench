"""Build a *candidate* SemantiK lexical bundle from diK observations and human mappings.

No GF source is generated. No function/paradigm or semantic sense is inferred.
Reviewed GF binding references still need real PGF/conformance before release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
from typing import Any

ID = re.compile(r'L[1-9][0-9]*\Z')
GF_ID = re.compile(r'[A-Za-z][A-Za-z_0-9]*\Z')
CATEGORIES = {'NP', 'AP', 'CN', 'N', 'N2', 'A', 'V', 'V2', 'V3', 'VV', 'VS', 'VA', 'Adv', 'Prep', 'Det', 'Numeral', 'PN'}
PROFILE = 'gf-wordbench.dik-semantik-lexicon/1.0-candidate'


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for buf in iter(lambda: f.read(1024 * 1024), b''):
            h.update(buf)
    return h.hexdigest()


def load(path: Path) -> dict:
    result = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(result, dict):
        raise ValueError('Expected a JSON object: ' + str(path))
    return result


def _source(bundle: Path) -> tuple[dict, dict]:
    if bundle.is_symlink():
        raise ValueError('Symbolic source directory prohibited')
    manifest = load(bundle/'manifest.json')
    if manifest.get('schema_id') != 'dik.semantik-knowledge-handoff/1.0-candidate' or manifest.get('released') is not False or manifest.get('gf_bindings') != 0:
        raise ValueError('Expected diK knowledge-only handoff')
    for name, key in (('semantik.knowledge.json', 'lexicon_sha256'), ('gf-mapping-review.template.json', 'review_template_sha256')):
        p = bundle/name
        if p.is_symlink() or digest(p) != manifest[key]:
            raise ValueError('Untrusted diK input digest: ' + name)
    lexical = load(bundle/'semantik.knowledge.json')
    template = load(bundle/'gf-mapping-review.template.json')
    rows = lexical.get('entries')
    if (lexical.get('schema_version') != '1.1' or lexical.get('source_kind') != 'wikidata' or not isinstance(rows, list)
            or len(rows) != manifest['entries'] or template.get('source_candidate_sha256') != manifest['source_candidate_sha256']
            or len(template.get('decisions', [])) != len(rows)):
        raise ValueError('diK knowledge candidate mismatch')
    seen = set()
    for row, placeholder in zip(rows, template['decisions']):
        lid = row.get('lexical_ref')
        if (not isinstance(lid, str) or not ID.fullmatch(lid) or lid in seen
                or row.get('semantic_ref') != 'wikidata:lexeme:' + lid
                or row.get('source_kind') != 'wikidata' or row.get('use_for') != 'knowledge'
                or row.get('binding_kind') != 'lexeme_ref' or row.get('language') != manifest['locale']
                or placeholder.get('source_lexeme_id') != lid or placeholder.get('gf_function') is not None):
            raise ValueError('Untrusted or duplicated diK candidate row')
        seen.add(lid)
    return manifest, lexical


def build(*, dik_bundle: Path, decisions_file: Path, output_dir: Path) -> dict[str, Any]:
    source, knowledge = _source(Path(dik_bundle))
    path = Path(decisions_file)
    if path.is_symlink():
        raise ValueError('Mapping decisions symlink prohibited')
    decisions = load(path)
    if (decisions.get('schema_id') != 'dik.gf-human-mapping-decisions' or decisions.get('schema_version') != '1.0'
            or decisions.get('source_candidate_sha256') != source['source_candidate_sha256']
            or decisions.get('locale') != source['locale']):
        raise ValueError('Review document belongs to another lexical source')
    rows = decisions.get('decisions')
    if not isinstance(rows, list):
        raise ValueError('Expected reviewed decisions array')
    index = {r['lexical_ref']:r for r in knowledge['entries']}
    seen = set()
    bindings = []
    rejected = pending = 0
    for decision in rows:
        if not isinstance(decision, dict):
            raise ValueError('Invalid review row')
        lid = decision.get('source_lexeme_id')
        if not isinstance(lid, str) or lid in seen or lid not in index:
            raise ValueError('Duplicate or unknown source lexeme in review')
        seen.add(lid)
        source_row = index[lid]
        if decision.get('semantic_ref') != source_row['semantic_ref']:
            raise ValueError('Semantic identity cannot be silently altered in GF review')
        status = decision.get('decision')
        if status == 'pending':
            pending += 1
            continue
        if status == 'reject':
            rejected += 1
            continue
        if status != 'accept':
            raise ValueError('Review decision must be accept/reject/pending')
        if not (decision.get('mapping_reviewed') is True and decision.get('license_reviewed') is True
                and isinstance(decision.get('reviewer'), str) and len(decision['reviewer'].strip()) >= 2):
            raise ValueError('Accept requires named reviewer plus explicit mapping and license review')
        target_semantic_ref = decision.get('target_semantic_ref')
        semantic_authority_ref = decision.get('semantic_authority_ref')
        if (decision.get('semantic_identity_reviewed') is not True
                or not isinstance(target_semantic_ref, str) or not target_semantic_ref.strip()
                or len(target_semantic_ref) > 512 or target_semantic_ref.startswith('wikidata:lexeme:')
                or not isinstance(semantic_authority_ref, str) or not semantic_authority_ref.strip()):
            raise ValueError('Accept requires an explicit authorized target semantic reference, not a guessed Lexeme sense')
        function, category = decision.get('gf_function'), decision.get('gf_category')
        if (not isinstance(function, str) or not GF_ID.fullmatch(function) or not isinstance(category, str) or category not in CATEGORIES):
            raise ValueError('Invalid GF function/category in explicit review')
        bindings.append({
            'semantic_ref': target_semantic_ref,
            'language': source_row['language'],
            'lexical_ref': function,
            'binding_kind': 'gf_expr',
            'category': category,
            'source_kind': 'project',
            'use_for': 'binding',
            'source_ref': source_row['source_ref'],
            'properties': {
                'gf_mapping_status': 'human_reviewed_candidate',
                'source_lexeme_id': lid,
                'reviewer': decision['reviewer'].strip(),
                'semantic_authority_ref': semantic_authority_ref.strip(),
                'source_candidate_sha256': source['source_candidate_sha256'],
                'gf_artifact_verified': False,
                'qualification': 'development_only',
            },
        })
    if len({(b['semantic_ref'], b['language']) for b in bindings}) != len(bindings):
        raise ValueError('Two reviewed GF mappings claim the same target semantic identity')
    # Knowledge records remain knowledge-only; even a mapped entry requires PGF verification.
    artifact = {
        'schema_version':'1.1',
        'lexicon_id':'wordbench-dik-candidate-'+source['source_candidate_sha256'][:16],
        'source_kind':'wikidata',
        'source_ref':'dik:gf-handoff:sha256:'+source['source_candidate_sha256'],
        'entries':knowledge['entries'] + bindings,
    }
    target = Path(output_dir)
    if target.exists() or target.is_symlink():
        raise FileExistsError('Output exists; immutable candidate bundles cannot be overwritten')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.wb-dik-sa-', dir=str(target.parent)) as temp:
        stage = Path(temp)
        artifact_file = stage/'lexicon.candidate.json'
        artifact_file.write_text(json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')
        report = {
            'schema_id':PROFILE, 'status':'DEVELOPMENT_CANDIDATE',
            'released':False, 'activated':False, 'gf_verified':False,
            'locale':source['locale'],
            'knowledge_entries':len(knowledge['entries']),
            'human_reviewed_binding_candidates':len(bindings),
            'rejected':rejected, 'pending':pending,
            'source_candidate_sha256':source['source_candidate_sha256'],
            'source_bundle_manifest_sha256':digest(Path(dik_bundle)/'manifest.json'),
            'mapping_decisions_sha256':digest(path),
            'lexicon_sha256':digest(artifact_file),
            'note':'Requires GF PGF binding verification, SemantiK conformance, license authorization and release gates.',
        }
        (stage/'manifest.json').write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')
        stage.rename(target)
    return {**report, 'output':str(target)}


def audit(bundle_dir: Path) -> dict[str, Any]:
    d = Path(bundle_dir)
    if d.is_symlink():
        raise ValueError('Symbolic bundle directory prohibited')
    manifest = load(d/'manifest.json')
    if (manifest.get('schema_id') != PROFILE or manifest.get('status') != 'DEVELOPMENT_CANDIDATE'
            or manifest.get('released') is not False or manifest.get('activated') is not False
            or manifest.get('gf_verified') is not False or (d/'lexicon.candidate.json').is_symlink()
            or digest(d/'lexicon.candidate.json') != manifest['lexicon_sha256']):
        raise ValueError('Invalid or tampered WordBench lexical bundle')
    a = load(d/'lexicon.candidate.json')
    knowledge = binding = 0
    seen = set()
    for e in a.get('entries', []):
        key = (e.get('semantic_ref'), e.get('language'), e.get('use_for'))
        if key in seen:
            raise ValueError('Duplicate knowledge or binding entry')
        seen.add(key)
        if e.get('source_kind') == 'wikidata' and e.get('use_for') == 'knowledge' and e.get('binding_kind') == 'lexeme_ref':
            knowledge += 1
        elif (e.get('source_kind') == 'project' and e.get('use_for') == 'binding' and e.get('binding_kind') == 'gf_expr'
              and e.get('properties', {}).get('gf_artifact_verified') is False):
            binding += 1
        else:
            raise ValueError('Unsupported or elevated candidate lexical entry')
    if (knowledge != manifest['knowledge_entries'] or binding != manifest['human_reviewed_binding_candidates']):
        raise ValueError('Manifest lexical entry counts do not match')
    return {'valid':True, 'status':'DEVELOPMENT_CANDIDATE', 'knowledge_entries':knowledge,
            'binding_candidates':binding, 'released':False, 'gf_verified':False}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description='diK → SemantiK lexical candidate bridge, no release')
    sub = p.add_subparsers(dest='cmd',required=True)
    b = sub.add_parser('build')
    b.add_argument('--dik-bundle',required=True)
    b.add_argument('--decisions',required=True)
    b.add_argument('--output',required=True)
    v = sub.add_parser('audit');v.add_argument('--bundle',required=True)
    args = p.parse_args(argv)
    try:
        result = build(dik_bundle=Path(args.dik_bundle), decisions_file=Path(args.decisions), output_dir=Path(args.output)) if args.cmd=='build' else audit(Path(args.bundle))
        print(json.dumps(result, ensure_ascii=False, indent=2));return 0
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False));return 2


if __name__ == '__main__':
    raise SystemExit(main())
