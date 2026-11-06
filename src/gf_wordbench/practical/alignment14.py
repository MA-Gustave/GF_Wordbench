"""Conservative RGL-backed lexical alignment for the fourteen Defluens pilot languages.

No raw RGL edits, linguistic certification, gold creation, or GF execution.
Every proposal is linked to the *actual local* RGL lexical implementation.
Use `apply` only after confirming the selected WordBench source snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from gf_wordbench.practical.pilot import _validate_pilot

WORKSPACE = Path(__file__).resolve().parents[3]
PILOTS = WORKSPACE / 'pilots' / 'practical_generation_v1'
POLICY_FILE = PILOTS / 'alignment_focus14_v2.json'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_policy(path: Path = POLICY_FILE) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding='utf-8'))
    if policy.get('schema_id') != 'defluens.rgl-backed-alignment-policy':
        raise ValueError('Unexpected alignment policy')
    if len(policy['languages']) != 14 or len(set(policy['languages'])) != 14:
        raise ValueError('Alignment must list fourteen unique languages')
    return policy


def _source_root(rgl_root: Path) -> Path:
    p = rgl_root / 'src' if (rgl_root / 'src').is_dir() else rgl_root
    if not p.is_dir():
        raise ValueError(f'RGL source folder missing: {p}')
    return p.resolve(strict=True)


def _rgl_provenance(src: Path, lang: str, directory: str, *, ready: bool) -> dict[str, str]:
    """Check RGL source availability, never merely assume a lexical symbol exists."""
    paths = [src / directory / f'Lexicon{lang}.gf',
             src / directory / f'Paradigms{lang}.gf']
    provenance = {}
    if not all(p.is_file() and not p.is_symlink() for p in paths):
        raise ValueError(f'{lang}: Lexicon and Paradigms RGL sources required')
    lex = paths[0].read_text(encoding='utf-8', errors='replace')
    for symbol in ['book_N', 'house_N', 'say_VS'] + (['ready_A'] if ready else []):
        if not re.search(r'(?m)^\s*(?:lin\s+)?' + symbol + r'\s*=\s*', lex):
            raise ValueError(f'{lang}: RGL Lexicon lacks a concrete implementation of {symbol}')
        # A literal nonExist implementation cannot be reused as demonstrated coverage.
        match = re.search(r'(?m)^\s*(?:lin\s+)?' + symbol + r'\s*=\s*([^;]{0,300})', lex)
        if match and match.group(1).lstrip().startswith('nonExist'):
            raise ValueError(f'{lang}: {symbol} is nonExist in RGL Lexicon')
    for path in paths:
        provenance[path.relative_to(src).as_posix()] = sha256(path.read_bytes())
    return provenance


def _replace(src: str, old: str, new: str) -> tuple[str, bool]:
    """Replace an exact generated expression; already-aligned files are unchanged."""
    if old not in src:
        return src, False
    return src.replace(old, new), True


def _aligned_source(source: str, lang: str, seed: dict[str, str], policy: dict[str, Any], sid: str) -> tuple[str, list[str]]:
    if not (source.startswith('-- Ars Magna Defluens:') or source.startswith('-- Defluens RGL alignment v0.2.0:') or source.startswith('-- Defluens lexical stabilization v0.2.1:') or source.startswith('-- Defluens stabilization v0.2.2:') or source.startswith('-- Defluens stabilization v0.2.3:')):
        raise ValueError(f'{lang}/{sid}: unexpected GF input header; refusing unreviewed rewrite')
    changes: list[str] = []
    def update(old: str, new: str, label: str) -> None:
        nonlocal source
        source, did = _replace(source, old, new)
        if did:
            changes.append(label)

    # Lexicon<RGL> is the existing lexical authority, e.g. irregular say_VS,
    # noun gender/declension, and copula-sensitive ready_A in Spa/Por.
    update(f'(mkN "{seed["book"]}")', 'L.book_N', 'rgl_lexicon_book')
    update(f'(mkN "{seed["house"]}")', 'L.house_N', 'rgl_lexicon_house')
    update(f'(mkVS (mkV "{seed["say"]}"))', 'L.say_VS', 'rgl_lexicon_say')
    if lang in policy['ready_from_lexicon']:
        update(f'(mkAP (mkA "{seed["ready"]}"))', '(mkAP L.ready_A)', 'rgl_lexicon_ready')

    # A named individual with explicit feminine gender, where the RGL API
    # offers mkPN : Str -> Gender -> PN. This is test persona metadata, not a
    # universal inference from the string "Mira".
    if lang in policy['feminine_test_persona']:
        update(f'(mkPN "{seed["name"]}")', f'(mkPN "{seed["name"]}" feminine)', 'test_persona_gender')
    if lang in policy['meeting_feminine']:
        update(f'(mkN "{seed["meeting"]}")', f'(mkN "{seed["meeting"]}" feminine)', 'meeting_noun_gender')
    if lang == 'Ger':
        update(f'(mkN "{seed["device"]}")', f'(mkN "{seed["device"]}" neuter)', 'device_noun_gender')
    if lang in policy['return_lemma_override']:
        update(f'(mkV "{seed["return"]}")', f'(mkV "{policy["return_lemma_override"][lang]}")', 'return_lexical_meaning')
    # In Fre/Spa/Ita, simple pastTense in GF RGL often expresses the
    # imperfect; a present anterior gives a completed event without forcing
    # exhaustive language-specific tense support. This is a *proposal*.
    if sid == 'past-event' and lang in policy['past_event_anterior']:
        update('mkS pastTense (mkCl ', 'mkS anteriorAnt (mkCl ', 'completed_event_as_anterior')
    if changes and 'L.' in source:
        update(f'open Syntax{lang}, Paradigms{lang} in {{',
               f'open Syntax{lang}, Paradigms{lang}, (L = Lexicon{lang}) in {{', 'import_rgl_lexicon')
        if f'(L = Lexicon{lang})' not in source:
            raise ValueError(f'{lang}/{sid}: could not add required Lexicon alias')
    if changes:
        source = source.replace('-- Ars Magna Defluens:',
                                '-- Defluens RGL alignment v0.2.0: PROPOSED, GF AND LINGUISTIC REVIEW REQUIRED\n-- Ars Magna Defluens:',1)
    return source, changes


def prepare_alignment(*, pilots_root: Path = PILOTS, rgl_root: Path,
                      languages: tuple[str, ...] | None = None,
                      policy_path: Path = POLICY_FILE) -> tuple[dict[str, Any], dict[Path, bytes]]:
    """Prepare all edits and metadata in memory; no filesystem writes."""
    policy = read_policy(policy_path)
    requested = tuple(languages or policy['languages'])
    if not requested or any(x not in policy['languages'] for x in requested) or len(set(requested)) != len(requested):
        raise ValueError('Only unique selected languages from the fourteen-language focus are permitted')
    src = _source_root(rgl_root)
    root = pilots_root.resolve(strict=True)
    catalog = json.loads((root / 'language_catalog.json').read_text(encoding='utf-8'))['languages']
    edits: dict[Path, bytes] = {}
    audit: dict[str, Any] = {
        'schema_id': 'defluens.rgl-backed-alignment', 'schema_version': '2.0',
        'policy_sha256': sha256(policy_path.read_bytes()),
        'source_root': str(src), 'pilots_root': str(root),
        'real_gf_executed': False, 'linguistic_gold_approved': False,
        'validation_status': 'pending_windows_gf_and_semantic_review',
        'languages': {}, 'totals': {'languages': len(requested), 'scenarios_examined': 0,
                                     'scenarios_modified': 0, 'gf_files_modified': 0},
    }
    for lang in requested:
        _validate_pilot(lang, pilots_root=root)
        item = catalog[lang]
        directory, seed = item['rgl_directory'], item['lexical_seeds']
        prov = _rgl_provenance(src, lang, directory, ready=lang in policy['ready_from_lexicon'])
        lang_root = root / lang
        manifest_path = lang_root / 'pilot_manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        laudit = {'rgl_directory': directory, 'rgl_sources_sha256': prov,
                  'modified': [], 'unchanged': [], 'status': 'proposal_not_gf_validated'}
        for entry in manifest['scenarios']:
            audit['totals']['scenarios_examined'] += 1
            sid = entry['id']
            gf_file = lang_root / 'validation' / 'inputs' / entry['module']
            script_file = lang_root / entry['script']
            old = gf_file.read_text(encoding='utf-8')
            updated, reasons = _aligned_source(old, lang, seed, policy, sid)
            if not reasons:
                laudit['unchanged'].append(sid)
                continue
            b = updated.encode('utf-8')
            edits[gf_file] = b
            oldhash = entry['source_sha256']
            newhash = sha256(b)
            entry['source_sha256'] = newhash
            # One source-lock directive for the concrete module, leaving the
            # separately locked abstract source untouched.
            old_script = script_file.read_text(encoding='utf-8')
            pattern = r'(?m)^(-- GF_WORDBENCH_INPUT_SHA256 )' + re.escape(oldhash) + r'( validation/inputs/' + re.escape(entry['module']) + r')$'
            new_script, count = re.subn(pattern, lambda m: m.group(1) + newhash + m.group(2), old_script)
            if count != 1:
                raise ValueError(f'{lang}/{sid}: expected exactly one matching source SHA lock; got {count}')
            edits[script_file] = new_script.encode('utf-8')
            entry['script_sha256'] = sha256(edits[script_file])
            laudit['modified'].append({'scenario': sid, 'changes': reasons,
                                       'previous_sha256': oldhash, 'new_sha256': newhash})
            audit['totals']['scenarios_modified'] += 1
            audit['totals']['gf_files_modified'] += 1
        if laudit['modified']:
            manifest['alignment'] = {
                'policy': 'alignment_focus14_v2.json',
                'status': 'proposed_not_gf_validated',
                'rgl_source_sha256': prov,
                'gold_approved': False,
            }
            edits[manifest_path] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        audit['languages'][lang] = laudit
    return audit, edits


def apply_alignment(*, pilots_root: Path = PILOTS, rgl_root: Path,
                    languages: tuple[str, ...] | None = None,
                    policy_path: Path = POLICY_FILE, dry_run: bool = False) -> dict[str, Any]:
    audit, changes = prepare_alignment(pilots_root=pilots_root, rgl_root=rgl_root,
                                       languages=languages, policy_path=policy_path)
    if not dry_run:
        # Validate all changes before writing anything. No RGL file is ever modified.
        for path in changes:
            if not path.resolve().is_relative_to(pilots_root.resolve()) or path.is_symlink():
                raise ValueError(f'unsafe write target: {path}')
        backups = {path: path.read_bytes() for path in changes}
        try:
            for path, data in changes.items():
                staged = path.with_name(path.name + '.defluens-stage')
                staged.write_bytes(data)
                staged.replace(path)
            for lang in audit['languages']:
                _validate_pilot(lang, pilots_root=pilots_root)
        except Exception:
            # Roll back the complete write-set if a source lock fails after
            # editing; do not strand a pilot half-upgraded.
            for path, content in backups.items():
                path.write_bytes(content)
            raise
        finally:
            for path in changes:
                path.with_name(path.name + '.defluens-stage').unlink(missing_ok=True)
    audit['applied'] = not dry_run
    audit['files_written'] = len(changes) if not dry_run else 0
    return audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'apply', 'verify', 'compare'))
    parser.add_argument('--rgl-root', required=True, type=Path)
    parser.add_argument('--pilots-root', type=Path, default=PILOTS)
    parser.add_argument('--language', action='append', default=[])
    parser.add_argument('--report', type=Path)
    parser.add_argument('--batch-dir', type=Path)
    parser.add_argument('--batch-zip', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == 'compare':
            from gf_wordbench.practical.alignment_compare import compare_archive, locate_latest_matching_batch
            if args.batch_zip:
                archive = args.batch_zip
            elif args.batch_dir:
                archive = locate_latest_matching_batch(args.batch_dir, pilots_root=args.pilots_root)
            else:
                raise ValueError('compare requires --batch-zip or --batch-dir')
            result = compare_archive(archive, pilots_root=args.pilots_root)
        elif args.action == 'verify':
            langs = tuple(args.language or read_policy()['languages'])
            statuses = {l: _validate_pilot(l, pilots_root=args.pilots_root) for l in langs}
            result = {'status': 'preflight_ok', 'languages': list(statuses),
                      'scenarios': sum(r['scenario_count'] for r in statuses.values()),
                      'gf_executed': False, 'gold_approved': False}
        else:
            result = apply_alignment(rgl_root=args.rgl_root, pilots_root=args.pilots_root,
                                     languages=tuple(args.language) or None,
                                     dry_run=args.action == 'plan')
        serialized = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(serialized, encoding='utf-8')
        print(serialized)
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f'Alignment error: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
