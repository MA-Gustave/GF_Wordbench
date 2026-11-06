"""Inspect retained GF candidate compilation failures; no GF execution or mutation.

Example (Windows):
  python tools/inspect_semantik_gf_failure.py --root "%USERPROFILE%\\Downloads\\Ars_Magna_Defluens\\semantik_candidates" --profile defluens-core-fr-1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def _tail(path: Path, max_bytes: int = 32_768, max_lines: int = 100) -> str:
    try:
        with path.open('rb') as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - max_bytes))
            raw = handle.read(max_bytes)
    except OSError:
        return '(aucun journal disponible)'
    if not raw:
        return '(journal vide)'
    text = raw.decode('utf-8-sig', errors='replace')
    return '\n'.join(text.splitlines()[-max_lines:])


def choose_failure(root: Path, profile: str | None = None) -> tuple[Path, dict]:
    if (root/'build-report.json').is_file():
        files = [root/'build-report.json']
    else:
        files = list(root.glob('semantik-pgf-build-*/build-report.json'))
    found: list[tuple[Path, dict]] = []
    for file in files:
        try:
            report = json.loads(file.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if (not profile or report.get('profile_id') == profile) and report.get('status') != 'PGF_BUILT_CANDIDATE_ONLY':
            found.append((file, report))
    if not found:
        raise FileNotFoundError('Aucun rapport de compilation echouee dans ' + str(root))
    return max(found, key=lambda entry: entry[0].stat().st_mtime)


def inspect(root: Path, profile: str | None = None) -> str:
    file, report = choose_failure(root, profile)
    directory = file.parent
    lines = [
        'DIAGNOSTIC GF - aucune modification des candidats',
        'Profil : ' + str(report.get('profile_id', '?')),
        'Statut : ' + str(report.get('status', '?')),
        'Code GF : ' + str(report.get('exit_code', '?')),
        'Dossier : ' + str(directory),
        'Rapport : ' + str(file),
    ]
    if report.get('failure_reason'):
        lines.append('Raison : ' + str(report['failure_reason']))
    for name in ('gf-stderr.log', 'gf-stdout.log'):
        lines.extend(('', '--- ' + name + ' (100 dernieres lignes) ---', _tail(directory/name)))
    lines.append('')
    lines.append('Archives des journaux conservees; PGF/RuntimeSet ni publies ni actives.')
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path.home()/'Downloads'/'Ars_Magna_Defluens'/'semantik_candidates'
    parser.add_argument('--root', type=Path, default=default_root, help='Dossier semantik_candidates ou semantik-pgf-build-*')
    parser.add_argument('--profile', choices=('defluens-core-fr-1', 'defluens-core-en-1', 'defluens-attribute-fr-1', 'konstellation-explorer-3'))
    args = parser.parse_args(argv)
    try:
        print(inspect(args.root.expanduser().resolve(), args.profile))
    except (OSError, ValueError) as exc:
        print('Diagnostic introuvable : ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
