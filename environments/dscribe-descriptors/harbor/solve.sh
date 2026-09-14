#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$HERE/apply_defect.py" "$HERE/defect_fix.json" /app/dscribe
python3 /app/rowtool.py rebuild /app/dscribe /app/site 2
: > /tmp/walltimes.txt
for check in @CHECKS_SH@; do
  t0=$(date +%s%N)
  python3 /app/rowtool.py run /app/dscribe /app/site "/app/checks/$check" "/logs/artifacts/$check" @ROW_TIMEOUT@
  t1=$(date +%s%N); echo "$check $t0 $t1" >> /tmp/walltimes.txt
done
python3 -c "import json; rows={}; [rows.__setitem__(x.split()[0],round((int(x.split()[2])-int(x.split()[1]))/1e9,4)) for x in open('/tmp/walltimes.txt')]; json.dump(rows,open('/logs/artifacts/timing.json','w'),indent=1,sort_keys=True)"
echo "oracle: repaired, rebuilt, and delivered"

