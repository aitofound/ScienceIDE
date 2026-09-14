#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$HERE/apply_defect.py" "$HERE/defect_fix.json" /app/nest
for check in @CHECKS_SH@; do
  python3 /app/rowtool.py /app/nest "/app/checks/$check" "/logs/artifacts/$check" @ROW_TIMEOUT@
done
