# @NAME@: fail-hard clean reference, crash-tolerant straw, minimal grader.
FROM @DIGEST@ AS reference
ENV DEBIAN_FRONTEND=noninteractive
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 ca-certificates build-essential \
        libopenblas-dev liblapacke-dev libsuperlu-dev \
 && rm -rf /var/lib/apt/lists/*
COPY source/@GKEYLL_ARCHIVE@ /tmp/gkeyll.tar.gz
RUN echo "@GKEYLL_SHA256@  /tmp/gkeyll.tar.gz" | sha256sum -c - \
 && mkdir -p /app \
 && tar -xzf /tmp/gkeyll.tar.gz -C /app \
 && rm /tmp/gkeyll.tar.gz \
 && test ! -e /app/gkeyll/.git
COPY rowtool.py /opt/rowtool.py
RUN mkdir -p /app/builds \
 && python3 /opt/rowtool.py build /app/gkeyll @PROFILE@ /app/builds/@PROFILE@ @BUILD_JOBS@ \
 && test -s /app/builds/@PROFILE@/source/build/@APP@/libg0@APP@.so
COPY cases/ /opt/cases/
COPY checks/ /opt/checks/
RUN set -e; \
    mkdir -p /ref; \
    : > /ref/walltimes.txt; \
    for check in @CHECKS_SH@; do \
      t0=$(date +%s%N); \
      python3 /opt/rowtool.py run /app/builds "/opt/cases/$check" "/opt/checks/$check" "/ref/$check" @ROW_TIMEOUT@; \
      test -s "/ref/$check/run.ok"; \
      t1=$(date +%s%N); \
      echo "$check $t0 $t1" >> /ref/walltimes.txt; \
    done; \
    python3 -c "import json; rows={}; [rows.__setitem__(x.split()[0],round((int(x.split()[2])-int(x.split()[1]))/1e9,4)) for x in open('/ref/walltimes.txt')]; json.dump(rows,open('/ref/walltimes.json','w'),indent=1,sort_keys=True)"

FROM reference AS straw
COPY defect/ /opt/defect/
COPY grade.py grade_floor.py /opt/
RUN set -e; \
    mkdir -p /opt/straw-builds/@PROFILE@; \
    cp -a /app/builds/@PROFILE@/source /opt/straw-builds/@PROFILE@/source; \
    straw_status=ok; \
    if ! python3 /opt/defect/apply_defect.py /opt/defect/defect.json /opt/straw-builds/@PROFILE@/source; then straw_status="crashed: apply"; fi; \
    mkdir -p /straw; \
    if [ "$straw_status" = ok ] && ! python3 /opt/rowtool.py rebuild /opt/straw-builds/@PROFILE@/source @PROFILE@ 2; then straw_status="crashed: build"; fi; \
    if [ "$straw_status" = ok ]; then \
      for check in @CHECKS_SH@; do \
        if timeout @STRAW_TIMEOUT@ python3 /opt/rowtool.py run /opt/straw-builds "/opt/cases/$check" "/opt/checks/$check" "/straw/$check" @ROW_TIMEOUT@; then :; \
        else rc=$?; if [ "$rc" -eq 124 ]; then straw_status="measurement_failed: timeout"; else straw_status="crashed: run (rc=$rc)"; fi; break; fi; \
      done; \
    fi; \
    if [ "$straw_status" = "measurement_failed: timeout" ]; then echo "straw measurement timed out; refusing to bake an unmeasured floor" >&2; exit 1; fi; \
    if ! python3 /opt/grade_floor.py --grade /opt/grade.py --candidate /straw --reference /ref --checks-dir /opt/checks --out /floor.json --straw-status "$straw_status" --timeout @STRAW_TIMEOUT@; then \
      printf '%s\n' '{"floor": 0.0, "straw_status": "crashed: grade"}' > /floor.json; \
    fi; \
    rm -rf /straw /opt/straw-builds

FROM @DIGEST@
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-numpy \
 && rm -rf /var/lib/apt/lists/*
COPY --from=reference /ref/ /tests/reference/
COPY --from=straw /floor.json /tests/floor.json
COPY checks/ /tests/checks/
COPY grade.py /tests/grade.py
COPY test.sh /tests/test.sh
RUN chmod +x /tests/test.sh && mkdir -p /logs/verifier /logs/artifacts
