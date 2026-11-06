"""Independent practical application-coverage CLI over the canonical WordBench engine.

Does not modify WordBench's frozen ValidationMode or command vocabulary.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tomllib

from gf_wordbench.practical.coverage import assess, load_profile, selected_scenario_ids, write_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='gf-wordbench-practical', description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    check = actions.add_parser('check', help='assess an existing canonical WordBench summary')
    check.add_argument('--summary', type=Path, required=True)
    check.add_argument('--practical-profile', type=Path, required=True)
    check.add_argument('--language-key')
    check.add_argument('--output', type=Path)
    run = actions.add_parser('run', help='execute targeted GF scenarios in the normal WordBench engine')
    run.add_argument('--language-path', type=Path, required=True)
    run.add_argument('--validation-profile', type=Path, required=True)
    run.add_argument('--practical-profile', type=Path, required=True)
    run.add_argument('--language-key')
    run.add_argument('--include-optional', action='store_true')
    run.add_argument('--gf-executable', type=Path)
    run.add_argument('--rgl-root', type=Path)
    run.add_argument('--output-root', type=Path)
    run.add_argument('--output', type=Path)
    return parser


def validate_profile_scenario_scope(validation_profile: Path, scenario_ids: tuple[str, ...]) -> None:
    """Guard WordBench's rule: every registered required scenario runs in checkpoint mode."""
    with validation_profile.open('rb') as handle:
        data = tomllib.load(handle)
    policy = data.get('validation', {})
    modules = data.get('modules', {})
    if not isinstance(policy, dict) or not isinstance(modules, dict):
        raise ValueError('malformed WordBench validation profile')
    required = policy.get('required_scenarios', [])
    optional = policy.get('optional_scenarios', [])
    checkpoints = modules.get('checkpoints', [])
    if not all(isinstance(item, list) for item in (required, optional, checkpoints)):
        raise ValueError('malformed scenario/checkpoint registry')
    if not checkpoints:
        raise ValueError('checkpoint mode requires a registered compilation checkpoint')
    if not set(required).issubset(scenario_ids):
        raise ValueError('validation profile requires unrelated scenarios: supply a dedicated practical profile')
    if not set(scenario_ids).issubset(set(required) | set(optional)):
        raise ValueError('practical scenarios are missing from the WordBench validation profile')


def execute(argv: list[str] | None = None) -> dict:
    args = build_parser().parse_args(argv)
    profile = load_profile(args.practical_profile)
    if args.action == 'check':
        summary_path = args.summary
    else:
        from gf_wordbench.entrypoints.cli.audit_commands import execute_validate_cli_command
        from gf_wordbench.entrypoints.cli.parser import CliCommand, CliRequest
        scenario_ids = selected_scenario_ids(profile, include_optional=args.include_optional)
        if not scenario_ids:
            raise ValueError('profile did not select any scenario')
        validate_profile_scenario_scope(args.validation_profile, scenario_ids)
        options = {
            'mode': 'checkpoint',
            'language_path': args.language_path,
            'validation_profile': args.validation_profile,
            'scenario_ids': scenario_ids,
            'strict': True,
        }
        for key in ('gf_executable', 'rgl_root', 'output_root'):
            value = getattr(args, key)
            if value is not None:
                options[key] = value
        # Reuse exactly one canonical WordBench run. No new GF executor.
        run = execute_validate_cli_command(CliRequest(command=CliCommand.VALIDATE, arguments=options))
        summary_path = Path(run.run_paths.run_dir) / 'summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    result = assess(profile, summary, language_key=args.language_key)
    result_path = args.output or summary_path.parent / 'practical_coverage.json'
    if result_path.resolve() == summary_path.resolve():
        raise ValueError('refusing to overwrite canonical WordBench summary')
    write_result(result, result_path)
    result['result_path'] = str(result_path)
    return result


def main(argv: list[str] | None = None) -> int:
    try:
        result = execute(argv)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f'Practical coverage error: {exc}', file=sys.stderr)
        return 2
    except Exception as exc:
        print(f'WordBench validation failed: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 3
    print(json.dumps({'status':result['status'], 'language_key': result['language_key'], 'result_path': result['result_path']}, ensure_ascii=False))
    return 0 if result['status'] == 'ready' else 1


if __name__ == '__main__':
    raise SystemExit(main())
