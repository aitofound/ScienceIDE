#!/usr/bin/env bash
set -uo pipefail
mkdir -p /logs/verifier
if ! python3 /tests/grade.py --candidate /logs/artifacts --reference /tests/reference \
  --checks-dir /tests/checks --out /logs/verifier/reward.json --report /logs/verifier/grading_report.json; then
  echo '{"grader_error":1}' > /logs/verifier/reward.json
  exit 1
fi
