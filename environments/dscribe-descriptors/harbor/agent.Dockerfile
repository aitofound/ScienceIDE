# @NAME@: source-only defective agent; reference archive restricted to prep.
FROM @DIGEST@ AS prep
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
COPY source/@DSCRIBE_ARCHIVE@ /tmp/source.tar.gz
RUN echo '@DSCRIBE_SHA256@  /tmp/source.tar.gz' | sha256sum -c - && mkdir -p /app/dscribe && tar -xzf /tmp/source.tar.gz -C /app/dscribe --strip-components=2
COPY defect/ /opt/defect/
COPY strip-tree.py /opt/strip-tree.py
RUN python3 /opt/defect/apply_defect.py /opt/defect/defect.json /app/dscribe && python3 /opt/strip-tree.py /app/dscribe '@STRIP_PATHS@'
FROM @DIGEST@
RUN apt-get update && apt-get install -y --no-install-recommends build-essential python3 python3-dev python3-setuptools python3-pybind11 python3-numpy python3-scipy python3-sklearn python3-joblib python3-sparse python3-ase ca-certificates curl procps tmux ripgrep && rm -rf /var/lib/apt/lists/*
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 NPY_NUM_BUILD_JOBS=2 JOBLIB_MULTIPROCESSING=0 CFLAGS=-ffp-contract=off CXXFLAGS=-ffp-contract=off
COPY --from=prep /app/dscribe /app/dscribe
COPY checks/ /app/checks/
COPY cases/ /app/cases/
COPY rowtool.py /app/rowtool.py
RUN mkdir -p /app/site /logs/artifacts
WORKDIR /app
