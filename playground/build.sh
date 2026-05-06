#!/usr/bin/env bash
# Rebuild the Pyodide-loadable wheel that ships next to playground/index.html.
# Run this after every version bump in pyproject.toml.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -d .venv ]]; then
  echo "no .venv/ — run 'python -m venv .venv && .venv/bin/pip install -e \".[dev]\" build' first" >&2
  exit 1
fi

rm -f playground/floras-*.whl
.venv/bin/python -m build --wheel --outdir playground/

# Hatchling drops the wheel as floras-<version>-py3-none-any.whl inside
# playground/. Update the reference in index.html so the browser fetches it.
WHEEL_NAME=$(ls playground/floras-*-py3-none-any.whl | xargs -n1 basename)
echo "built ${WHEEL_NAME}"

if grep -q 'floras-[0-9]\+\.[0-9]\+\.[0-9]\+-py3-none-any\.whl' playground/index.html; then
  sed -i.bak -E "s/floras-[0-9]+\.[0-9]+\.[0-9]+-py3-none-any\.whl/${WHEEL_NAME}/" playground/index.html
  rm -f playground/index.html.bak
  echo "updated playground/index.html wheel reference"
fi
