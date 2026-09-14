#!/bin/bash
# Harbor verifier entry point for Athena chemistry repair tasks. A grader crash must
# still leave reward.json so a scientific zero is distinct from infra failure.
set -uo pipefail

mkdir -p /logs/verifier
python3 /tests/grade.py \
  --candidate /logs/artifacts \
  --reference /tests/reference \
  --checks-dir /tests/checks \
  --out /logs/verifier/reward.json \
  --report /logs/verifier/grading_report.json

if [ ! -f /logs/verifier/reward.json ]; then
  echo '{"reward": 0.0, "reward_repair": 0.0, "equivalence_pass": 0, "speedup": 0.0, "grader_error": 1}' \
    > /logs/verifier/reward.json
fi
