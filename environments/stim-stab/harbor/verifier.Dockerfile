# @NAME@: fail-hard reference, crash-tolerant straw, minimal grader.
FROM @DIGEST@ AS reference
ENV DEBIAN_FRONTEND=noninteractive
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build python3 python3-dev python3-pip python3-numpy ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --break-system-packages pybind11==2.11.1
COPY source/@STIM_ARCHIVE@ /tmp/stim.tar.gz
RUN echo "@STIM_SHA256@  /tmp/stim.tar.gz" | sha256sum -c - \
 && mkdir -p /opt \
 && tar -xzf /tmp/stim.tar.gz -C /opt \
 && mv /opt/stim-@STIM_COMMIT@ /opt/stim \
 && rm /tmp/stim.tar.gz && test -f /opt/stim/CMakeLists.txt && test ! -e /opt/stim/.git
COPY rowtool.py /opt/rowtool.py
RUN python3 /opt/rowtool.py build /opt/stim /opt/build 2 @BUILD_KIND@
COPY checks/ /opt/checks/
RUN set -e; mkdir -p /ref; : > /ref/walltimes.txt; \
    for check in @CHECKS_SH@; do \
      t0=$(date +%s%N); \
      python3 /opt/rowtool.py run /opt/stim /opt/build "/opt/checks/$check" "/ref/$check" @ROW_TIMEOUT@; \
      test -s "/ref/$check/run.ok"; \
      t1=$(date +%s%N); echo "$check $t0 $t1" >> /ref/walltimes.txt; \
    done; \
    python3 -c "import json; rows={}; [rows.__setitem__(x.split()[0],round((int(x.split()[2])-int(x.split()[1]))/1e9,4)) for x in open('/ref/walltimes.txt')]; json.dump(rows,open('/ref/walltimes.json','w'),indent=1,sort_keys=True)"

FROM reference AS straw
COPY defect/ /opt/defect/
COPY grade.py grade_floor.py /opt/
RUN set -e; cp -a /opt/stim /opt/stim-straw; straw_status=ok; \
    if ! python3 /opt/defect/apply_defect.py /opt/defect/defect.json /opt/stim-straw; then straw_status="crashed: apply"; fi; \
    if [ "$straw_status" = ok ]; then rm -rf /opt/stim; mv /opt/stim-straw /opt/stim; fi; \
    if [ "$straw_status" = ok ] && ! python3 /opt/rowtool.py rebuild /opt/stim /opt/build 2 @BUILD_KIND@; then straw_status="crashed: build"; fi; \
    mkdir -p /straw; \
    if [ "$straw_status" = ok ]; then for check in @CHECKS_SH@; do \
      set +e; timeout @STRAW_TIMEOUT@ python3 /opt/rowtool.py run /opt/stim /opt/build "/opt/checks/$check" "/straw/$check" @ROW_TIMEOUT@; rc=$?; set -e; \
      if [ "$rc" -eq 124 ]; then straw_status="measurement_failed: timeout"; break; elif [ "$rc" -ne 0 ]; then straw_status="crashed: run"; break; fi; \
    done; fi; \
    python3 /opt/grade_floor.py --grade /opt/grade.py --candidate /straw --reference /ref \
      --checks-dir /opt/checks --out /floor.json --straw-status "$straw_status" --timeout @STRAW_TIMEOUT@; \
    case "$straw_status" in measurement_failed:*) echo "$straw_status" >&2; exit 1;; esac; \
    rm -rf /straw /opt/stim-straw /opt/build

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
