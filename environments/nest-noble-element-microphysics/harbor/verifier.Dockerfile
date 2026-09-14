FROM @DIGEST@ AS reference
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake git python3 python3-numpy ca-certificates && rm -rf /var/lib/apt/lists/*
COPY source/ /tmp/source/
RUN echo '@SOURCE_SHA@  /tmp/source/nest-sab-1d0c74983.tar.gz' | sha256sum -c - && echo '@GCEM_SHA@  /tmp/source/gcem-a20b0fc0.tar.gz' | sha256sum -c - && mkdir -p /reference/nest /opt/nest-fetch/gcem-src && tar -xzf /tmp/source/nest-sab-1d0c74983.tar.gz --strip-components=2 -C /reference/nest && tar -xzf /tmp/source/gcem-a20b0fc0.tar.gz -C /opt/nest-fetch/gcem-src
COPY checks/ /tests/checks/
COPY rowtool.py /tests/rowtool.py
COPY grade.py /tests/grade.py
ENV CXXFLAGS=-ffp-contract=off OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
RUN set -eu; for check in @CHECKS_SH@; do python3 /tests/rowtool.py /reference/nest /tests/checks/$check /ref/$check @ROW_TIMEOUT@; test -f /ref/$check/run.ok; done

FROM reference AS straw
COPY defect/ /opt/defect/
COPY grade_floor.py /opt/grade_floor.py
RUN cp -a /reference/nest /straw-source && python3 /opt/defect/apply_defect.py /opt/defect/defect.json /straw-source
RUN set -eu; for check in @CHECKS_SH@; do python3 /tests/rowtool.py /straw-source /tests/checks/$check /tests/straw/$check @STRAW_TIMEOUT@; done
RUN python3 /opt/grade_floor.py --grade /tests/grade.py --candidate /tests/straw --reference /ref --checks-dir /tests/checks --out /tests/floor.json --straw-status ok --check @CHECK_FLAGS@

FROM @DIGEST@
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-numpy && rm -rf /var/lib/apt/lists/*
COPY --from=straw /ref /tests/reference
COPY --from=straw /tests/floor.json /tests/floor.json
COPY checks/ /tests/checks/
COPY grade.py test.sh /tests/
RUN chmod +x /tests/test.sh
WORKDIR /tests
