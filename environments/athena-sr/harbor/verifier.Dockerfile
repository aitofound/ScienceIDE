# @NAME@: hard-failing reference, crash-tolerant straw floor, minimal grader.
FROM @DIGEST@ AS reference

ENV DEBIAN_FRONTEND=noninteractive
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates build-essential python3 time procps \
 && rm -rf /var/lib/apt/lists/*

COPY source/@ATHENA_ARCHIVE@ /tmp/athena.tar.gz
RUN echo "@ATHENA_SHA256@  /tmp/athena.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/athena.tar.gz -C /opt \
 && mv /opt/athena-@ATHENA_COMMIT@ /opt/athena \
 && rm /tmp/athena.tar.gz \
 && test ! -e /opt/athena/.git

COPY cases/ /opt/cases/
COPY rowtool.py /opt/rowtool.py
# Reference failure is fatal: no guards or fallbacks are permitted in this leg.
RUN set -e; \
    mkdir -p /opt/builds /ref; \
    for variant in @BUILD_VARIANTS_SH@; do \
      python3 /opt/rowtool.py build /opt/athena "$variant" "/opt/builds/$variant" 4; \
    done; \
    : > /ref/walltimes.txt; \
    for check in @CHECKS_SH@; do \
      t0=$(date +%s%N); \
      python3 /opt/rowtool.py run /opt/builds "/opt/cases/$check" "/ref/$check" @ROW_TIMEOUT@; \
      t1=$(date +%s%N); \
      echo "$check $t0 $t1" >> /ref/walltimes.txt; \
    done; \
    python3 -c "import json; rows={}; \
[rows.__setitem__(line.split()[0],round((int(line.split()[2])-int(line.split()[1]))/1e9,4)) for line in open('/ref/walltimes.txt')]; \
json.dump(rows,open('/ref/walltimes.json','w'),indent=1,sort_keys=True)"

# The defective straw is only a floor symptom. Build crashes, run crashes, and
# hangs all produce a valid floor=0 record; they must never abort image build.
FROM reference AS straw

COPY defect/ /opt/defect/
COPY grade.py sr_format.py grade_floor.py /opt/
COPY checks/ /opt/checks/
RUN set -eu; \
    cp -a /opt/athena /opt/athena-straw; \
    straw_status="ok"; \
    if ! python3 /opt/defect/apply_defect.py /opt/defect/defect.json /opt/athena-straw; then \
      straw_status="crashed: apply"; \
    fi; \
    mkdir -p /opt/straw-builds /straw; \
    if [ "$straw_status" = ok ]; then \
      for variant in @BUILD_VARIANTS_SH@; do \
        if ! timeout @STRAW_TIMEOUT@ python3 /opt/rowtool.py build /opt/athena-straw "$variant" "/opt/straw-builds/$variant" 4; then \
          straw_status="crashed: build"; break; \
        fi; \
      done; \
    fi; \
    if [ "$straw_status" = ok ]; then \
      for check in @CHECKS_SH@; do \
        if ! timeout @STRAW_TIMEOUT@ python3 /opt/rowtool.py run /opt/straw-builds "/opt/cases/$check" "/straw/$check" @ROW_TIMEOUT@; then \
          straw_status="crashed: run"; break; \
        fi; \
      done; \
    fi; \
    python3 /opt/grade_floor.py --grade /opt/grade.py --candidate /straw \
      --reference /ref --checks-dir /opt/checks --out /floor.json \
      --straw-status "$straw_status"; \
    test -s /floor.json; \
    rm -rf /straw /opt/athena-straw /opt/straw-builds

FROM python:3.13-slim

COPY --from=reference /ref/ /tests/reference/
COPY --from=straw /floor.json /tests/floor.json
COPY checks/ /tests/checks/
COPY grade.py sr_format.py /tests/
COPY test.sh /tests/test.sh
RUN chmod +x /tests/test.sh \
 && mkdir -p /logs/verifier /logs/artifacts
