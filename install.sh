#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")" && pwd)"
target="${1:-claude}"

case "$target" in
  claude|codex|kimi|shared) ;;
  *)
    echo "Usage: ./install.sh [claude|codex|kimi|shared] [--dry-run] [--force] [--include-legacy]" >&2
    exit 2
    ;;
esac

if [ "$#" -gt 0 ]; then
  shift
fi

if command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
elif command -v python >/dev/null 2>&1; then
  python_bin="python"
else
  echo "Python 3 was not found in PATH." >&2
  exit 1
fi

exec "$python_bin" "$repo_dir/runner/cli.py" install "$target" "$@"
