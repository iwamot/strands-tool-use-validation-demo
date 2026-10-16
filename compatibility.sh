#!/bin/bash
set -euo pipefail

# mise (uv only — a full `mise install` would put the pinned Python ahead of
# the version under test)
eval "$(mise activate bash)"
mise install aqua:astral-sh/uv

# CI (compatibility.yml) runs this once per supported Python version — the
# requires-python floor upward — by setting UV_PYTHON.
# Locally: UV_PYTHON=3.11 ./compatibility.sh
export UV_PROJECT_ENVIRONMENT="$PWD/.venv-compat/${UV_PYTHON:-default}"

uv sync --locked
# The tests import every example, so they also catch syntax incompatibilities.
(cd en && uv run --no-sync python -m unittest discover -s tests)
(cd ja && uv run --no-sync python -m unittest discover -s tests)
