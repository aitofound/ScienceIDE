# @NAME@: clean chemistry reference, crash-tolerant straw, then grader.
FROM @DIGEST@ AS reference

ENV DEBIAN_FRONTEND=noninteractive
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates build-essential python3 libopenmpi-dev openmpi-bin time procps \
 && rm -rf /var/lib/apt/lists/*
# SUNDIALS 6.4.1 full prefix (headers+libs, BSD-3) matching native calibration;
# the pinned base image is actually trixie whose sundials is 7.x (ABI-incompatible)
COPY sundials-641.tgz /tmp/sundials-641.tgz
RUN tar xzf /tmp/sundials-641.tgz -C /usr && rm /tmp/sundials-641.tgz && ldconfig

COPY source/@ATHENA_ARCHIVE@ /tmp/athena.tar.gz
RUN echo "@ATHENA_SHA256@  /tmp/athena.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/athena.tar.gz -C /opt \
 && mv /opt/athena-@ATHENA_COMMIT@ /opt/athena \
 && rm /tmp/athena.tar.gz \
 && test ! -e /opt/athena/.git

COPY cases/ /opt/cases/
COPY rowtool.py build_profiles.json /opt/
RUN set -e; \
    mkdir -p /opt/builds /ref; \
    for profile in @BUILD_PROFILES_SH@; do \
      python3 /opt/rowtool.py build /opt/athena "$profile" "/opt/builds/$profile" 4 /usr; \
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

# The unfixed straw may crash, hang, or fail to build. Those are legitimate
# defect symptoms and freeze floor=0; only the clean reference is fail-hard.
FROM reference AS straw

COPY defect/ /opt/defect/
COPY grade.py chem_format.py grade_floor.py /opt/
COPY checks/ /opt/checks/
RUN set -e; \
    cp -a /opt/athena /opt/athena-straw; \
    python3 /opt/defect/apply_defect.py /opt/defect/defect.json /opt/athena-straw; \
    straw_status=ok; \
    mkdir -p /opt/straw-builds /straw; \
    for profile in @BUILD_PROFILES_SH@; do \
      if ! python3 /opt/rowtool.py build /opt/athena-straw "$profile" "/opt/straw-builds/$profile" 4 /usr; then \
        straw_status="crashed: build"; break; \
      fi; \
    done; \
    if [ "$straw_status" = ok ]; then \
      for check in @CHECKS_SH@; do \
        if ! timeout @STRAW_TIMEOUT@ python3 /opt/rowtool.py run /opt/straw-builds "/opt/cases/$check" "/straw/$check" @ROW_TIMEOUT@; then \
          straw_status="crashed-or-timeout: run"; break; \
        fi; \
      done; \
    fi; \
    if ! python3 /opt/grade_floor.py --grade /opt/grade.py \
      --candidate /straw --reference /ref --checks-dir /opt/checks \
      --out /floor.json --straw-status "$straw_status" --timeout @STRAW_TIMEOUT@; then \
      printf '%s\n' '{"floor": 0.0, "straw_status": "crashed: grade"}' > /floor.json; \
    fi; \
    rm -rf /straw /opt/athena-straw /opt/straw-builds; \
    test -s /floor.json

FROM python:3.13-slim

COPY --from=reference /ref/ /tests/reference/
COPY --from=straw /floor.json /tests/floor.json
COPY checks/ /tests/checks/
COPY grade.py chem_format.py /tests/
COPY test.sh /tests/test.sh
RUN chmod +x /tests/test.sh \
 && mkdir -p /logs/verifier /logs/artifacts
