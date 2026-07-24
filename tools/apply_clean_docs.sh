#!/usr/bin/env bash
set -euo pipefail
repo="${1:?Usage: apply_clean_docs.sh <repository-root>}"
source="$(cd "$(dirname "$0")/.." && pwd)"
backup="$repo/documentation_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup/project" "$backup/templates/project"
for rel in docs project/docs templates/project/docs; do
  if [ -e "$repo/$rel" ]; then
    mkdir -p "$backup/$(dirname "$rel")"
    mv "$repo/$rel" "$backup/$rel"
  fi
done
for rel in README.md CONTRIBUTING.md SECURITY.md; do
  [ ! -e "$repo/$rel" ] || mv "$repo/$rel" "$backup/$rel"
done
cp -R "$source/docs" "$repo/docs"
mkdir -p "$repo/project" "$repo/templates/project"
cp -R "$source/project/docs" "$repo/project/docs"
cp -R "$source/templates/project/docs" "$repo/templates/project/docs"
for rel in README.md CONTRIBUTING.md SECURITY.md; do cp "$source/$rel" "$repo/$rel"; done
echo "Documentation replaced. Backup: $backup"
