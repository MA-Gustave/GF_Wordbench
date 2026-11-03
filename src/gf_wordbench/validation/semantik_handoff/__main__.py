from __future__ import annotations
import argparse
import json
from pathlib import Path
from .service import inspect_semantik_handoff, materialize_verified_handoff


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a SemantiK Phrase Ops candidate handoff.")
    parser.add_argument("source")
    parser.add_argument("--materialize")
    args = parser.parse_args()
    inspection = inspect_semantik_handoff(args.source)
    print(json.dumps(inspection.to_dict(), ensure_ascii=False, indent=2))
    if inspection.valid and args.materialize:
        materialize_verified_handoff(args.source, args.materialize)
    return 0 if inspection.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
