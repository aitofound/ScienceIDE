#!/bin/bash
# @NAME@ oracle: restore the exact source and produce every graded final state.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$HERE/apply_defect.py" "$HERE/defect_fix.json" /app/MITgcm
mkdir -p /app/builds /logs/artifacts
@BUILD_LINES@
for check in @CHECKS_SH@; do
  python3 /app/rowtool.py run /app/builds "/app/cases/$check" \
    "/logs/artifacts/$check" --timeout @ROW_TIMEOUT@ --strict
done
python3 - <<'PY'
import glob, json, os
rows = {}
for path in glob.glob('/logs/artifacts/*/_run_status.json'):
    status = json.load(open(path))
    rows[status['check']] = status['wall']
json.dump(rows, open('/logs/artifacts/timing.json', 'w'), indent=1, sort_keys=True)
PY
echo "oracle: source restored; final-state rows delivered"
