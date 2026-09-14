# @NAME@: fail-hard clean reference, crash-tolerant straw, minimal grader.
FROM @DIGEST@ AS reference

ENV DEBIAN_FRONTEND=noninteractive
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3 python3-numpy ca-certificates make gfortran \
    && rm -rf /var/lib/apt/lists/*

COPY source/@MITGCM_ARCHIVE@ /tmp/mitgcm.tar.gz
RUN echo "@MITGCM_SHA256@  /tmp/mitgcm.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/mitgcm.tar.gz -C /opt \
 && mv /opt/mitgcm-@MITGCM_COMMIT@ /opt/MITgcm \
 && rm /tmp/mitgcm.tar.gz \
 && test ! -e /opt/MITgcm/.git

COPY cases/ /opt/cases/
COPY rowtool.py runtime_lib.py /opt/
RUN set -e; \
    mkdir -p /opt/builds /ref; \
    for profile in @BUILD_PROFILES_SH@; do \
      python3 /opt/rowtool.py build /opt/MITgcm /opt/cases "$profile" "/opt/builds/$profile" --jobs 4 --strict; \
    done; \
    for check in @CHECKS_SH@; do \
      python3 /opt/rowtool.py run /opt/builds "/opt/cases/$check" "/ref/$check" --timeout @ROW_TIMEOUT@ --strict; \
    done; \
    python3 -c "import json,os; rows={c:json.load(open('/ref/'+c+'/_run_status.json'))['wall'] for c in '@CHECKS_SH@'.split()}; json.dump(rows,open('/ref/walltimes.json','w'),indent=1,sort_keys=True)"

# Defective builds/runs are diagnostic. Any build failure, crash, timeout, or
# missing output is retained as a legitimate floor-zero symptom.
FROM reference AS straw

COPY defect/ /opt/defect/
COPY grade.py grade_floor.py /opt/
COPY checks/ /opt/checks/
RUN set -e; \
    cp -a /opt/MITgcm /opt/MITgcm-straw; \
    python3 /opt/defect/apply_defect.py /opt/defect/defect.json /opt/MITgcm-straw; \
    straw_build=ok; mkdir -p /opt/straw-builds /straw; \
    for profile in @BUILD_PROFILES_SH@; do \
      if ! python3 /opt/rowtool.py build /opt/MITgcm-straw /opt/cases "$profile" "/opt/straw-builds/$profile" --jobs 4 --strict; then \
        straw_build=build_failed; break; \
      fi; \
    done; \
    for check in @CHECKS_SH@; do \
      if [ "$straw_build" = ok ]; then \
        python3 /opt/rowtool.py run /opt/straw-builds "/opt/cases/$check" "/straw/$check" --timeout @STRAW_TIMEOUT@ || true; \
      else \
        mkdir -p "/straw/$check"; \
        printf '{"check":"%s","status":"build_failed","exit":"build_failed"}\n' "$check" > "/straw/$check/_run_status.json"; \
      fi; \
    done; \
    if ! python3 /opt/grade_floor.py --grade /opt/grade.py --candidate /straw \
      --reference /ref --checks-dir /opt/checks --out /floor.json; then \
      printf '%s\n' '{"floor":0.0,"floor_reason":"straw_grader_failure"}' > /floor.json; \
    fi; \
    test -s /floor.json; \
    rm -rf /straw /opt/MITgcm-straw /opt/straw-builds

FROM @DIGEST@

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3 python3-numpy ca-certificates make gfortran \
    && rm -rf /var/lib/apt/lists/*
COPY --from=reference /ref/ /tests/reference/
COPY --from=straw /floor.json /tests/floor.json
COPY checks/ /tests/checks/
COPY grade.py /tests/grade.py
COPY test.sh /tests/test.sh
RUN chmod +x /tests/test.sh && mkdir -p /logs/verifier /logs/artifacts
