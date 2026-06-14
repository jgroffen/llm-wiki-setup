#!/usr/bin/env bash
# Install the LLM Wiki git hooks by pointing core.hooksPath at .githooks/.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

chmod +x .githooks/pre-commit 2>/dev/null || true
git config core.hooksPath .githooks
echo "Installed: core.hooksPath -> .githooks"
echo "The pre-commit hook will run: build, lint, source-lint, audit_public."
