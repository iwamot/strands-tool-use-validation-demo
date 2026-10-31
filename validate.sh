#!/bin/bash
set -e

# mise
eval "$(mise activate bash)"
mise fmt
mise install

# Python
uv sync
mise run licenses python
uv audit
uv-override-prune --fix
ruff check --fix
ruff format
# en/ and ja/ use the same module names, so each runs as its own test suite.
(cd en && uv run python -m unittest discover -s tests)
(cd ja && uv run python -m unittest discover -s tests)

# Shared lint tasks
mise run gha-lint
mise run shell-lint

# Check for uncommitted changes
git diff --exit-code
