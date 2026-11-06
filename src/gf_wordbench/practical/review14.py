"""Ars Magna Defluens — 14-language technical evidence audit and HUMAN review.

Offline: reads an existing full batch ZIP; does NOT execute GF or certify
linguistic competence. A candidate is not a gold. Any review approval requires
an identifiable human decision bound to the exact raw output and its digest.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import html
import io
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
from zipfile import ZipFile, ZIP_DEFLATED

FOCUS14 = ('Eng', 'Fre', 'Spa', 'Ger', 'Dut', 'Swe', 'Dan', 'Nor', 'Nno', 'Fin', 'Est', 'Afr', 'Ita', 'Por')
EXPECTED_SCENARIOS = (
    'factual-present', 'past-event', 'past-state', 'future-reference',
    'factual-negation', 'temporal-order', 'condition-real', 'possibility',
    'source-attribution', 'quantity', 'location', 'instruction', 'prohibition',
    'obligation', 'conditional-instruction'
)
ROOT = Path(__file__).resolve().parents[3]
HINTS = ROOT / 'profiles' / 'defluens_review_hints_v1.json'
DEFAULT_DOWNLOADS = Path.home() / 'Downloads' / 'Ars_Magna_Defluens' / 'practical_pilot_runs'
SHA = re.compile(r'^[0-9a-f]{64}$')


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _member(z: ZipFile, name: str) -> bytes:
    info = z.getinfo(name)
    if info.file_size > 5_000_000:
        raise ValueError('Archive member exceeds 5 MB limit: ' + name)
    return z.read(info)


def _json_member(z: ZipFile, name: str) -> dict:
    obj = json.loads(_member(z, name).decode('utf-8-sig'))
    if not isinstance(obj, dict):
        raise ValueError('Expected JSON object in ' + name)
    return obj


def _safe_zip(z: ZipFile) -> list[str]:
    names = z.namelist()
    if len(names) > 4_000:
        raise ValueError('Too many members in archive')
    if len(set(names)) != len(names):
        raise ValueError('Duplicate archive entry')
    for name in names:
        p = PurePosixPath(name)
        if name.startswith('/') or '\\' in name or '..' in p.parts or not p.parts or (p.parts[0].endswith(':')):
            raise ValueError('Unsafe archive path: ' + name)
        info = z.getinfo(name)
        mode = info.external_attr >> 16
        if (mode & 0o170000) == 0o120000:
            raise ValueError('Symlink in archive: ' + name)
    return names


def _current_sources(code: str, scen: dict) -> str:
    """Confirm locks against checked-in snapshot when available, else unknown."""
    base = ROOT / 'pilots' / 'practical_generation_v1' / code
    src = base / 'validation' / 'inputs' / str(scen.get('module', ''))
    script = base / 'validation' / 'scenarios' / (str(scen.get('id', '')) + '.gfs')
    if not src.is_file() or not script.is_file():
        return 'not_available'
    return ('matching' if digest(src.read_bytes()) == scen.get('source_sha256')
            and digest(script.read_bytes()) == scen.get('script_sha256') else 'different')


def _hints() -> dict[tuple[str, str, str], str]:
    doc = json.loads(HINTS.read_text(encoding='utf-8'))
    if doc.get('schema_id') != 'defluens.review-hints':
        raise ValueError('Bad review hint schema')
    return {(x['language'], x['scenario'], x['candidate']): x['issue'] for x in doc['hints']}


def load_audit(batch: Path) -> dict:
    """Validate embedded evidence and isolate EXACTLY the successful 14 languages."""
    batch = batch.expanduser().resolve(strict=True)
    hint_index = _hints()
    with ZipFile(batch) as z:
        names = _safe_zip(z)
        summaries = [n for n in names if n.endswith('/batch_summary.json')]
        if len(summaries) != 1:
            raise ValueError('Batch archive must contain one batch_summary.json')
        summary = _json_member(z, summaries[0])
        if summary.get('schema_id') != 'defluens.pilot-batch' or summary.get('mode') != 'full':
            raise ValueError('Expected a completed FULL Defluens pilot batch')
        entries = {e.get('language'): e for e in summary.get('entries', []) if isinstance(e, dict)}
        if len(entries) != len(summary.get('entries', [])):
            raise ValueError('Duplicate/invalid language entries')
        candidates: list[dict] = []
        language_info: list[dict] = []
        for code in FOCUS14:
            entry = entries.get(code)
            if not entry:
                raise ValueError('Missing focus language: ' + code)
            totals = entry.get('totals', {})
            if totals.get('candidate_for_review') != 15 or entry.get('scenarios_attempted') != 15 or any(
                    totals.get(x, 0) for x in ('probe_failed', 'timeout', 'unverified')):
                raise ValueError(f'{code} does not have 15/15 candidates in this archive')
            pilots = [n for n in names if n.endswith('/pilot_run.json') and ('/defluens-pilot-' + code + '-') in n]
            if len(pilots) != 1:
                raise ValueError(f'Expected one {code} pilot_run.json')
            run = _json_member(z, pilots[0])
            if run.get('schema_id') != 'defluens.pilot-run' or run.get('language') != code or not run.get('run_id'):
                raise ValueError(f'Unexpected {code} pilot report identity')
            run_dir = pilots[0].rsplit('/', 1)[0]
            scenarios = run.get('scenarios', [])
            if len(scenarios) != 15 or set(s.get('id') for s in scenarios) != set(EXPECTED_SCENARIOS):
                raise ValueError(f'{code} scenario coverage is incomplete or duplicated')
            source_locks = []
            for scenario in scenarios:
                sid = scenario['id']
                raw = str(scenario.get('candidate') or '')
                if scenario.get('status') != 'candidate_for_review' or not raw.strip():
                    raise ValueError(f'{code}/{sid} is not a generated candidate')
                if not (SHA.fullmatch(str(scenario.get('source_sha256', ''))) and SHA.fullmatch(str(scenario.get('script_sha256', '')))):
                    raise ValueError(f'{code}/{sid} source hashes missing')
                candidate_member = run_dir + '/scenarios/' + sid + '.candidate.txt'
                stdout_member = run_dir + '/scenarios/' + sid + '.stdout.txt'
                stderr_member = run_dir + '/scenarios/' + sid + '.stderr.txt'
                if any(n not in names for n in (candidate_member, stdout_member, stderr_member)):
                    raise ValueError(f'Missing raw evidence: {code}/{sid}')
                raw_content = _member(z, candidate_member).decode('utf-8')
                if raw_content.rstrip('\r\n') != raw:
                    raise ValueError(f'Candidate text differs from evidence: {code}/{sid}')
                stdout = _member(z, stdout_member).decode('utf-8', errors='replace')
                stderr = _member(z, stderr_member).decode('utf-8', errors='replace')
                if not (f'GF_WORDBENCH_BEGIN linearize' in stdout and 'GF_WORDBENCH_END linearize' in stdout):
                    raise ValueError(f'GF evidence markers missing: {code}/{sid}')
                flags = []
                if '&+' in raw:
                    flags.append('Marque de concaténation GF « &+ » visible dans la sortie.')
                if '\ufffd' in raw:
                    flags.append('Caractère de remplacement Unicode dans la sortie.')
                if any(ord(c) < 32 for c in raw):
                    flags.append('Caractère de contrôle inattendu dans la sortie.')
                known = hint_index.get((code, sid, raw))
                if known:
                    flags.append(known)
                lock = _current_sources(code, scenario)
                if lock == 'different':
                    flags.append('Les sources locales ne correspondent plus aux empreintes du rapport (version différente).')
                source_locks.append(lock)
                candidates.append({
                    'language': code, 'scenario': sid, 'meaning_en': scenario.get('meaning_en', ''),
                    'candidate': raw, 'candidate_sha256': digest(raw.encode('utf-8')),
                    'source_sha256': scenario['source_sha256'], 'script_sha256': scenario['script_sha256'],
                    'run_id': run['run_id'], 'stdout_sha256': digest(stdout.encode('utf-8')),
                    'stderr_sha256': digest(stderr.encode('utf-8')),
                    'evidence_zip_member': candidate_member, 'sources_lock': lock,
                    'flags': flags, 'technical_status': 'candidate_for_review', 'linguistic_status': 'unverified',
                })
            language_info.append({'language': code, 'technical_candidates': 15,
                                  'sources_matching': sum(s == 'matching' for s in source_locks),
                                  'sources_different': sum(s == 'different' for s in source_locks)})
    index = {(r['language'], r['scenario']): r for r in candidates}
    for code in FOCUS14:
        for sid1, sid2, note in (
            ('instruction', 'conditional-instruction', 'Aucune condition discernable : sortie identique à l’instruction simple.'),
            ('factual-present', 'factual-negation', 'Négation non exprimée : sortie identique au présent affirmatif.'),
            ('instruction', 'prohibition', 'Interdiction non exprimée : sortie identique à l’impératif affirmatif.'),
            ('possibility', 'obligation', 'Possibilité et obligation indiscernables.'),
            ('past-event', 'future-reference', 'Passé et futur indiscernables.'),
        ):
            a = index[(code, sid1)]; b = index[(code, sid2)]
            if a['candidate'].casefold() == b['candidate'].casefold():
                b['flags'].append(note)
    for info in language_info:
        rows = [r for r in candidates if r['language'] == info['language']]
        info['flagged_scenarios'] = sum(bool(r['flags']) for r in rows)
        info['unflagged_scenarios'] = 15 - info['flagged_scenarios']
    return {
        'schema_id': 'defluens.review14-audit', 'schema_version': '1.0',
        'batch_id': summary['batch_id'], 'batch_sha256': digest(batch.read_bytes()),
        'source_archive_name': batch.name, 'languages': list(FOCUS14),
        'status': 'technical_candidates_unverified',
        'semantic_coverage_verified': False, 'gold_approved': False,
        'note': ('210 generation candidates pass raw-evidence consistency checks. '
                 'Hints are non-exhaustive linguistic review aids, not automatic verdicts. '
                 'No candidate is approved by this process.'),
        'totals': {'languages': 14, 'technical_candidates': len(candidates),
                   'flagged_scenarios': sum(bool(c['flags']) for c in candidates),
                   'unflagged_unreviewed': sum(not c['flags'] for c in candidates),
                   'linguistically_approved': 0},
        'language_details': language_info, 'candidates': candidates,
    }


def _csv(audit: dict) -> str:
    b = io.StringIO(newline='')
    writer = csv.writer(b)
    writer.writerow(('language', 'scenario', 'meaning_en', 'candidate', 'technical_status', 'linguistic_status',
                     'sources_lock', 'flags', 'candidate_sha256', 'run_id', 'evidence_zip_member'))
    for c in audit['candidates']:
        writer.writerow((c[k] if k != 'flags' else ' | '.join(c['flags']) for k in (
            'language', 'scenario', 'meaning_en', 'candidate', 'technical_status', 'linguistic_status',
            'sources_lock', 'flags', 'candidate_sha256', 'run_id', 'evidence_zip_member')))
    return '\ufeff' + b.getvalue()


def _page(audit: dict) -> str:
    data = json.dumps({'batch_id': audit['batch_id'], 'batch_sha256': audit['batch_sha256'],
                       'rows': audit['candidates'], 'totals': audit['totals'], 'languages': audit['languages']},
                      ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    page = r'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ars Magna Defluens — Revue des 14 langues</title><style>
:root{--paper:#F3EFE4;--ink:#1B1C1A;--blue:#24455B;--red:#D95B38;--sage:#91A18C;--ochre:#C4A25A;--edge:#DED7C9}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Segoe UI,Arial,sans-serif}
header{background:var(--blue);color:#fff;padding:30px max(24px,calc((100vw - 1260px)/2))}header small{color:#C9D8DD;letter-spacing:2px;text-transform:uppercase}
header h1{margin:8px 0 5px;font-size:32px}header p{color:#e2e8eb;max-width:900px;line-height:1.6;margin:6px 0}
main{max-width:1260px;margin:0 auto;padding:25px 22px 70px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}
.stat,.toolbar,.card,.help{background:#fffdf8;border:1px solid var(--edge);border-radius:12px;padding:18px}
.stat b{display:block;font-size:28px;color:var(--blue)}.stat small{color:#66706d}.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;position:sticky;top:0;z-index:2;box-shadow:0 4px 16px #24455B10}
input,select,textarea,button{font:inherit;border:1px solid #C9C8C1;border-radius:7px;padding:9px;background:white;color:var(--ink)}
input[type=search]{min-width:220px;flex:1}button{cursor:pointer}button.primary{background:var(--red);color:white;border-color:var(--red);font-weight:650}button.secondary{border-color:var(--blue);color:var(--blue)}
.help{margin:16px 0;color:#4a5655;line-height:1.5}.row-title{display:flex;justify-content:space-between;gap:14px;align-items:center}.lang{font-size:13px;letter-spacing:.08em;color:var(--blue);font-weight:750}.card{margin-top:11px;display:grid;grid-template-columns:2fr 1fr;gap:18px}
.sentence{font-size:19px;line-height:1.4;margin:10px 0;color:var(--blue);font-weight:600}.intent{font-size:13px;color:#64706e}.flag{background:#fff1e8;border-left:3px solid var(--red);padding:8px 10px;margin:6px 0;font-size:13px;line-height:1.4}.ok{background:#edf2eb;border-left:3px solid var(--sage);padding:8px 10px;font-size:13px}
.field{display:grid;gap:4px;margin-bottom:9px}.field label{font-size:12px;color:#4d5c60}.field input,.field select,.field textarea{width:100%}textarea{min-height:55px;resize:vertical}.meta{font:11px Consolas,monospace;color:#7d837e;margin-top:12px;word-break:break-all}
#rows:empty:before{content:'Aucun scénario pour ce filtre';display:block;padding:30px;text-align:center}footer{font-size:12px;color:#717773;padding-top:20px}
@media(max-width:900px){.stats{grid-template-columns:repeat(2,1fr)}.card{grid-template-columns:1fr}.toolbar{position:static}}
</style></head><body>
<header><small>MÉCANISMES ABSTRAITS · GF WORDBENCH</small><h1>Ars Magna Defluens</h1><p>Revue linguistique des 14 langues — 15 capacités par langue. Les 210 sorties ont été produites par GF, mais aucune n'est encore certifiée. Tu peux approuver explicitement une phrase, la rejeter ou la laisser en attente, puis exporter les décisions.</p></header>
<main><section class="stats"><div class="stat"><b>14</b><small>Langues ciblées</small></div><div class="stat"><b>210</b><small>Sorties GF présentes</small></div><div class="stat"><b id="flag-stat">—</b><small>À examiner en priorité (alertes)</small></div><div class="stat"><b id="done-stat">0</b><small>Décisions enregistrées dans cette page</small></div></section>
<div class="toolbar"><select id="language"><option value="">Toutes les langues</option></select><select id="filter"><option value="all">Tous les scénarios</option><option value="flag">Avec alertes</option><option value="clean">Sans alerte (non approuvés)</option><option value="pending">Décisions en attente</option><option value="decided">Décisions prises</option></select><input id="search" type="search" placeholder="Rechercher une phrase, capacité, alerte…"><input id="reviewer" placeholder="Nom ou initiales du réviseur" aria-label="Réviseur"><button id="export" class="primary">Exporter mes décisions JSON</button><button id="import" class="secondary">Importer décisions</button><input id="file" type="file" accept=".json,application/json" hidden></div>
<div class="help"><b>Mode d'emploi :</b> lis la phrase et son sens attendu, examine les alertes puis choisis <i>Approuver</i>, <i>À corriger</i> ou <i>En attente</i>. Une absence d'alerte ne veut PAS dire que la phrase est correcte. Pour approuver, indique ton identité et laisse la référence exactement identique à la sortie GF. Les décisions sont conservées dans ce navigateur lorsque son mode de sécurité le permet ; <b>exporte-les</b> impérativement pour conserver une preuve partageable. Les corrections proposées ne modifient pas la RGL.</div>
<div id="rows"></div><footer>Audit local et hors-ligne. La revue linguistique ne prouve pas à elle seule la généralisation des 15 capacités à tous les contextes. Batch : <span id="batch"></span></footer></main>
<script>const DATA=__DATA__;
const $=id=>document.getElementById(id);const lsKey='defluens-review14-'+DATA.batch_sha256;
let decisions={};try{decisions=JSON.parse(localStorage.getItem(lsKey)||'{}')}catch(e){decisions={}}
const k=r=>r.language+'/'+r.scenario;const text=(tag,content,cls)=>{let el=document.createElement(tag);if(cls)el.className=cls;el.textContent=content;return el};
for(const code of DATA.languages){const o=document.createElement('option');o.value=code;o.textContent=code;$('language').append(o)}
$('flag-stat').textContent=DATA.totals.flagged_scenarios;$('batch').textContent=DATA.batch_id;
function save(){try{localStorage.setItem(lsKey,JSON.stringify(decisions))}catch(e){}$('done-stat').textContent=Object.values(decisions).filter(v=>v.decision&&v.decision!=='pending').length}
function render(){const box=$('rows');box.replaceChildren();const lang=$('language').value,filter=$('filter').value,q=$('search').value.toLocaleLowerCase();
for(const r of DATA.rows){const d=decisions[k(r)]||{},decision=d.decision||'pending';if(lang&&r.language!==lang)continue;
if(filter==='flag'&&!r.flags.length||filter==='clean'&&r.flags.length||filter==='pending'&&decision!=='pending'||filter==='decided'&&decision==='pending')continue;
if(q&&!(`${r.language} ${r.scenario} ${r.candidate} ${r.meaning_en} ${r.flags.join(' ')}`.toLocaleLowerCase().includes(q)))continue;
const card=text('article','','card'),left=text('div',''),right=text('div','');const row=text('div','','row-title');row.append(text('span',r.language,'lang'),text('span',r.scenario,'intent'));left.append(row,text('div',r.candidate,'sentence'),text('div','Sens attendu : '+r.meaning_en,'intent'));
if(r.flags.length){for(const f of r.flags)left.append(text('div',f,'flag'))}else left.append(text('div','Aucune anomalie automatiquement signalée. Revue humaine toujours requise.','ok'));
left.append(text('div','Empreinte : '+r.candidate_sha256+' · Verrou source : '+r.sources_lock,'meta'));
const fld=(title,el)=>{let w=text('div','','field');w.append(text('label',title));w.append(el);right.append(w)};
const sel=document.createElement('select');for(const [v,label] of [['pending','En attente'],['approve','Approuver'],['reject','À corriger / rejeter']]){let o=document.createElement('option');o.value=v;o.textContent=label;sel.append(o)}sel.value=decision;
const note=document.createElement('textarea');note.value=d.notes||'';note.placeholder='Justification ou problème constaté…';
const ref=document.createElement('input');ref.value=d.reference_text===undefined?r.candidate:d.reference_text;ref.placeholder='Référence/forme attendue';
sel.onchange=()=>{decisions[k(r)]={...decisions[k(r)],decision:sel.value,notes:note.value,reference_text:ref.value};save()};
note.onchange=()=>{decisions[k(r)]={...decisions[k(r)],decision:sel.value,notes:note.value,reference_text:ref.value};save()};
ref.onchange=()=>{decisions[k(r)]={...decisions[k(r)],decision:sel.value,notes:note.value,reference_text:ref.value};save()};
fld('Décision linguistique',sel);fld('Référence examinée / correction proposée',ref);fld('Notes du réviseur',note);card.append(left,right);box.append(card)}save()}
$('language').onchange=render;$('filter').onchange=render;$('search').oninput=render;
$('export').onclick=()=>{const reviewer=$('reviewer').value.trim();const payload={schema_id:'defluens.review14-decisions',schema_version:'1.0',batch_id:DATA.batch_id,batch_sha256:DATA.batch_sha256,reviewer,decisions:DATA.rows.map(r=>({language:r.language,scenario:r.scenario,run_id:r.run_id,candidate_sha256:r.candidate_sha256,decision:(decisions[k(r)]||{}).decision||'pending',reference_text:(decisions[k(r)]||{}).reference_text??r.candidate,notes:(decisions[k(r)]||{}).notes||''}))};
const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='defluens-review14-decisions-'+DATA.batch_id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
$('import').onclick=()=>$('file').click();$('file').onchange=async e=>{const f=e.target.files[0];if(!f)return;try{const data=JSON.parse(await f.text());if(data.schema_id!=='defluens.review14-decisions'||data.batch_sha256!==DATA.batch_sha256)throw Error('Archive de source différente');$('reviewer').value=data.reviewer||'';decisions={};for(const d of data.decisions||[]){const r=DATA.rows.find(r=>r.language===d.language&&r.scenario===d.scenario);if(!r||r.candidate_sha256!==d.candidate_sha256)throw Error('Décision non liée à la sortie initiale');decisions[k(r)]={decision:d.decision,reference_text:d.reference_text,notes:d.notes}}render()}catch(e){alert('Import refusé : '+e.message)}};render();
</script></body></html>'''
    return page.replace('__DATA__', data)


def _write_atomic(path: Path, value: str) -> None:
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(value, encoding='utf-8')
    tmp.replace(path)


def generate_audit(batch: Path, out_dir: Path) -> tuple[dict, Path]:
    audit = load_audit(batch)
    base = out_dir.expanduser().resolve() / ('defluens-review14-' + audit['batch_id'])
    base.mkdir(parents=True, exist_ok=True)
    _write_atomic(base / 'review14_summary.json', json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    _write_atomic(base / 'review14_candidates.csv', _csv(audit))
    _write_atomic(base / 'Revue_14_langues.html', _page(audit))
    _write_atomic(base / 'README.txt',
        'ARS MAGNA DEFLUENS — REVUE DES 14 LANGUES\n\n'
        '1) Ouvrir Revue_14_langues.html dans Edge/Chrome/Firefox.\n'
        '2) Comparer chaque phrase au sens attendu. L’absence de signalement ne vaut pas approbation.\n'
        '3) Indiquer le réviseur, approuver ou rejeter explicitement et EXPORTER les décisions JSON.\n'
        '4) Exécuter Lancer_Revue_14_Langues.bat finalize "CHEMIN\\vers\\decisions.json"\n'
        '5) La finalisation vérifie les empreintes et produit un rapport de décisions, PAS une certification RGL.\n'
        'Aucun gold, aucune preuve native-speaker, aucune modification de source n’est créée automatiquement.\n')
    archive = base.with_suffix('.zip')
    with ZipFile(archive, 'w', ZIP_DEFLATED, compresslevel=6) as z:
        for file in sorted(base.iterdir()):
            if file.is_file():
                z.write(file, arcname=base.name + '/' + file.name)
    return audit, archive


def finalize_review(batch: Path, decisions_file: Path, out_dir: Path) -> dict:
    audit = load_audit(batch)
    decisions = json.loads(decisions_file.read_text(encoding='utf-8'))
    if not isinstance(decisions, dict) or decisions.get('schema_id') != 'defluens.review14-decisions' or \
            decisions.get('batch_sha256') != audit['batch_sha256'] or decisions.get('batch_id') != audit['batch_id']:
        raise ValueError('Review is not bound to this exact batch archive')
    reviewer = str(decisions.get('reviewer', '')).strip()
    rows = decisions.get('decisions')
    if not isinstance(rows, list) or len(rows) != 210:
        raise ValueError('Expected exactly 210 review decisions, one per source sentence')
    originals = {(r['language'], r['scenario']): r for r in audit['candidates']}
    seen = set(); finished = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid review decision')
        key = row.get('language'), row.get('scenario')
        if key in seen or key not in originals:
            raise ValueError(f'Unknown or duplicated review item: {key}')
        seen.add(key); source = originals[key]
        if row.get('run_id') != source['run_id'] or row.get('candidate_sha256') != source['candidate_sha256']:
            raise ValueError(f'Decision does not match candidate evidence: {key}')
        choice = row.get('decision', 'pending')
        if choice not in ('pending', 'approve', 'reject'):
            raise ValueError(f'Invalid decision: {key}')
        notes = str(row.get('notes') or '').strip()
        ref = row.get('reference_text', source['candidate'])
        if not isinstance(ref, str) or len(ref) > 20_000:
            raise ValueError(f'Invalid reference: {key}')
        if choice != 'pending' and not reviewer:
            raise ValueError('A named human reviewer is required before approval or rejection')
        if choice == 'approve' and ref != source['candidate']:
            raise ValueError(f'Cannot approve text that differs from actual GF output: {key}')
        if choice == 'reject' and not notes:
            raise ValueError(f'Rejection requires an explanatory note: {key}')
        finished.append({'language': source['language'], 'scenario': source['scenario'],
                         'run_id': source['run_id'], 'candidate_sha256': source['candidate_sha256'],
                         'candidate': source['candidate'], 'reference_text': ref, 'notes': notes,
                         'reviewer': reviewer if choice != 'pending' else '',
                         'review_status': {'approve': 'human_approved_candidate', 'reject': 'requires_correction',
                                           'pending': 'unverified'}[choice]})
    totals = {name:sum(i['review_status'] == name for i in finished) for name in
              ('human_approved_candidate', 'requires_correction', 'unverified')}
    report = {'schema_id': 'defluens.review14-results', 'schema_version': '1.0',
              'batch_id': audit['batch_id'], 'batch_sha256': audit['batch_sha256'],
              'reviewer': reviewer, 'decisions_sha256': digest(decisions_file.read_bytes()),
              'generated_at': datetime.now(timezone.utc).isoformat(),
              'semantic_coverage_verified': False,
              'note': 'Human-reviewed candidates only. Not canonical WordBench gold matches or general coverage certification.',
              'totals': totals, 'decisions': finished}
    folder = out_dir.expanduser().resolve() / ('defluens-review14-' + audit['batch_id'])
    folder.mkdir(parents=True, exist_ok=True)
    _write_atomic(folder / 'review14_results.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


def compare_runs(baseline: Path, current: Path, out_dir: Path) -> dict:
    """Reproducibility check only: compare the same 210 GF probes across runs."""
    earlier, later = load_audit(baseline), load_audit(current)
    prior = {(x['language'], x['scenario']): x for x in earlier['candidates']}
    differences = []
    same_output = 0
    same_source = 0
    for now in later['candidates']:
        old = prior[(now['language'], now['scenario'])]
        output_equal = old['candidate_sha256'] == now['candidate_sha256']
        source_equal = old['source_sha256'] == now['source_sha256'] and old['script_sha256'] == now['script_sha256']
        same_output += int(output_equal)
        same_source += int(source_equal)
        if not output_equal or not source_equal:
            differences.append({'language':now['language'],'scenario':now['scenario'],
                'baseline_candidate':old['candidate'],'current_candidate':now['candidate'],
                'output_same':output_equal,'source_same':source_equal})
    report = {'schema_id':'defluens.review14-repeatability', 'schema_version':'1.0',
              'baseline_batch_sha256':earlier['batch_sha256'], 'current_batch_sha256':later['batch_sha256'],
              'baseline_batch_id':earlier['batch_id'], 'current_batch_id':later['batch_id'],
              'semantic_coverage_verified':False,
              'note':'Repeatability of one fixed sentence per scenario is not general semantic correctness.',
              'totals':{'scenarios':210,'identical_outputs':same_output,
                        'identical_source_locks':same_source,'differences':len(differences)},
              'differences':differences}
    target = out_dir.expanduser().resolve() / ('defluens-review14-' + later['batch_id'])
    target.mkdir(parents=True,exist_ok=True)
    _write_atomic(target/'repeatability.json', json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


def _batch_arg(path: Path | None, batch_dir: Path) -> Path:
    if path:
        return path
    matches = sorted(batch_dir.glob('defluens-batch-full-*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise ValueError(f'No defluens-batch-full-*.zip in {batch_dir}')
    return matches[0]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('audit', 'finalize', 'compare'))
    p.add_argument('--batch', type=Path, help='FULL Defluens batch ZIP (otherwise newest in Downloads)')
    p.add_argument('--batch-dir', type=Path, default=DEFAULT_DOWNLOADS)
    p.add_argument('--out-dir', type=Path, default=DEFAULT_DOWNLOADS)
    p.add_argument('--decisions', type=Path, help='Export JSON from Revue_14_langues.html')
    p.add_argument('--baseline', type=Path, help='Previous FULL batch ZIP (compare only)')
    args = p.parse_args(argv)
    try:
        batch_hint = args.batch
        # Reviews are pinned to the original batch, not whichever run becomes newest.
        if args.action == 'finalize' and batch_hint is None and args.decisions is not None:
            original = json.loads(args.decisions.read_text(encoding='utf-8'))
            wanted = original.get('batch_sha256') if isinstance(original, dict) else None
            if not isinstance(wanted, str) or not SHA.fullmatch(wanted):
                raise ValueError('Decision file has no valid source archive digest')
            batch_hint = next((p for p in args.batch_dir.glob('defluens-batch-full-*.zip')
                               if digest(p.read_bytes()) == wanted), None)
            if batch_hint is None:
                raise ValueError('Original source batch ZIP is missing from Downloads; restore it or use --batch')
        batch = _batch_arg(batch_hint, args.batch_dir)
        if args.action == 'audit':
            audit, archive = generate_audit(batch, args.out_dir)
            print(json.dumps({'batch': str(batch), 'report_zip': str(archive),
                              'review_html': str(archive.with_suffix('') / 'Revue_14_langues.html'),
                              'totals': audit['totals'], 'languages': audit['languages'],
                              'semantic_coverage_verified': False}, ensure_ascii=False, indent=2))
        elif args.action == 'finalize':
            if args.decisions is None:
                raise ValueError('finalize needs --decisions <exported JSON>')
            result = finalize_review(batch, args.decisions, args.out_dir)
            print(json.dumps({'totals': result['totals'], 'semantic_coverage_verified': False},
                             ensure_ascii=False, indent=2))
        else:
            baseline = args.baseline
            if baseline is None:
                archives = sorted(args.batch_dir.glob('defluens-batch-full-*.zip'),
                                  key=lambda x:x.stat().st_mtime,reverse=True)
                baseline = next((x for x in archives if x.resolve() != batch.resolve()),None)
            if baseline is None:
                raise ValueError('Compare requires two FULL batches (supply --baseline)')
            result = compare_runs(baseline,batch,args.out_dir)
            print(json.dumps({'totals':result['totals'], 'semantic_coverage_verified':False},
                             ensure_ascii=False,indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as ex:
        print('Revue 14 error: ' + str(ex), file=__import__('sys').stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
