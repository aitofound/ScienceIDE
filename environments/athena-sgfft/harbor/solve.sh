#!/bin/bash
# @NAME@ oracle: inverse the defect, rebuild, and deliver native evolution.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$HERE/apply_defect.py" "$HERE/defect_fix.json" /app/athena

mkdir -p /app/run/builds
for variant in @BUILD_VARIANTS_SH@; do
  python3 "$HERE/rowtool.py" build /app/athena "$variant" "/app/run/builds/$variant" 4
done

: > /tmp/walltimes.txt
for check in @CHECKS_SH@; do
  t0=$(date +%s%N)
  python3 "$HERE/rowtool.py" run /app/run/builds "/app/cases/$check" "/logs/artifacts/$check" @ROW_TIMEOUT@
  t1=$(date +%s%N)
  echo "$check $t0 $t1" >> /tmp/walltimes.txt
done

python3 -c "import json; rows={}; \
[rows.__setitem__(line.split()[0],round((int(line.split()[2])-int(line.split()[1]))/1e9,4)) for line in open('/tmp/walltimes.txt')]; \
json.dump(rows,open('/logs/artifacts/timing.json','w'),indent=1,sort_keys=True)"
echo "oracle: fixed, rebuilt, and delivered"
