#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
(cd e2e && npx playwright test --reporter=list)
