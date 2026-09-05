#!/usr/bin/env bash
# Install the Book Genesis runtime from this checkout on macOS or Linux.
set -euo pipefail

REPO_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$REPO_DIR"

if [ ! -f "$REPO_DIR/pyproject.toml" ]; then
  echo "Error: pyproject.toml was not found beside this script." >&2
  exit 1
fi

PYTHON=""

# An activated virtual environment is an explicit author choice. Use its interpreter
# directly before searching PATH, while retaining the usual macOS/Linux commands as
# portable fallbacks.
if [ -n "${VIRTUAL_ENV:-}" ]; then
  for candidate in "$VIRTUAL_ENV/bin/python" "$VIRTUAL_ENV/Scripts/python.exe"; do
    if [ -x "$candidate" ] && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
      PYTHON="$candidate"
      break
    fi
  done
fi

for candidate in python3 python; do
  if [ -n "$PYTHON" ]; then
    break
  fi
  if ! command -v "$candidate" >/dev/null 2>&1; then
    continue
  fi
  if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done

if [ -z "$PYTHON" ]; then
  echo "Error: Book Genesis requires Python 3.10 or newer (tried an active virtual environment, python3, and python)." >&2
  exit 1
fi

PYTHON_VERSION="$("$PYTHON" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
echo "Installing Book Genesis with $PYTHON ($PYTHON_VERSION)..."
"$PYTHON" -m pip install .

echo
echo "Book Genesis is installed. Next:"
echo "  book-genesis setup"
echo "  book-genesis new --idea \"Your idea\" --language en --path books/my-book"
echo
echo "The installer did not connect a provider or run a model."
