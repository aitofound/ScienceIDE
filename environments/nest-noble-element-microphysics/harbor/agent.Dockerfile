FROM @DIGEST@ AS prep
RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY source/nest-sab-1d0c74983.tar.gz /tmp/nest.tar.gz
RUN echo '@SOURCE_SHA@  /tmp/nest.tar.gz' | sha256sum -c - && mkdir -p /app/nest && tar -xzf /tmp/nest.tar.gz --strip-components=2 -C /app/nest
COPY defect/ /opt/defect/
RUN python3 /opt/defect/apply_defect.py /opt/defect/defect.json /app/nest && rm -rf /app/nest/.git /app/nest/G4integration /app/nest/GarfieldppIntegration

FROM @DIGEST@
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake git python3 python3-numpy ca-certificates procps curl time && rm -rf /var/lib/apt/lists/*
COPY source/gcem-a20b0fc0.tar.gz /tmp/gcem.tar.gz
RUN echo '@GCEM_SHA@  /tmp/gcem.tar.gz' | sha256sum -c - && mkdir -p /opt/nest-fetch/gcem-src && tar -xzf /tmp/gcem.tar.gz -C /opt/nest-fetch/gcem-src && rm /tmp/gcem.tar.gz
COPY --from=prep /app/nest /app/nest
COPY checks/ /app/checks/
COPY rowtool.py /app/rowtool.py
ENV CXXFLAGS=-ffp-contract=off OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
RUN mkdir -p /logs/artifacts
WORKDIR /app
@METADATA_NORMALIZATION@