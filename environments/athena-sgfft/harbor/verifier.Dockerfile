# @NAME@: fail-hard clean reference, crash-tolerant defective straw, grader.
FROM @DIGEST@ AS reference

ENV DEBIAN_FRONTEND=noninteractive
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates build-essential python3 \
        libfftw3-dev libopenmpi-dev openmpi-bin time procps \
 && rm -rf /var/lib/apt/lists/*

COPY source/@ATHENA_ARCHIVE@ /tmp/athena.tar.gz
RUN echo "@ATHENA_SHA256@  /tmp/athena.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/athena.tar.gz -C /opt \
 && mv /opt/athena-@ATHENA_COMMIT@ /opt/athena \
 && rm /tmp/athena.tar.gz \
 && test ! -e /opt/athena/.git

COPY cases/ /opt/cases/
COPY rowtool.py /opt/rowtool.py
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

# A defective compile, crash, or hang is itself a valid floor=0 symptom.
FROM reference AS straw

COPY defect/ /opt/defect/
COPY grade.py sg_format.py grade_floor.py /opt/
COPY checks/ /opt/checks/
RUN set -e; \
    cp -a /opt/athena /opt/athena-straw; \
    python3 /opt/defect/apply_defect.py /opt/defect/defect.json /opt/athena-straw; \
    mkdir -p /opt/straw-builds /straw; \
    for variant in @BUILD_VARIANTS_SH@; do \
      ( timeout @STRAW_BUILD_TIMEOUT@ python3 /opt/rowtool.py build /opt/athena-straw "$variant" "/opt/straw-builds/$variant" 4 ) || true; \
    done; \
    for check in @CHECKS_SH@; do \
      ( timeout @STRAW_TIMEOUT@ python3 /opt/rowtool.py run /opt/straw-builds "/opt/cases/$check" "/straw/$check" @ROW_TIMEOUT@ ) || true; \
    done; \
    python3 /opt/grade_floor.py --grade /opt/grade.py --candidate /straw \
      --reference /ref --checks-dir /opt/checks --out /floor.json; \
    rm -rf /straw /opt/athena-straw /opt/straw-builds

FROM python:3.13-slim

COPY --from=reference /ref/ /tests/reference/
COPY --from=straw /floor.json /tests/floor.json
COPY checks/ /tests/checks/
COPY grade.py sg_format.py /tests/
COPY test.sh /tests/test.sh
RUN chmod +x /tests/test.sh \
 && mkdir -p /logs/verifier /logs/artifacts
