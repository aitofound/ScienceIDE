# @NAME@: Gkeyll module agent image; only sourcebuild sees the pristine archive.
FROM @DIGEST@ AS sourcebuild
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

FROM sourcebuild AS prep
COPY defect/ /opt/defect/
COPY strip-tree.py /opt/strip-tree.py
RUN python3 /opt/defect/apply_defect.py /opt/defect/defect.json /app/builds/@PROFILE@/source \
 && python3 /opt/rowtool.py rebuild /app/builds/@PROFILE@/source @PROFILE@ 2 \
 && python3 /opt/strip-tree.py /app/builds/@PROFILE@/source "@STRIP_PATHS@"

FROM @DIGEST@
ENV DEBIAN_FRONTEND=noninteractive
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates build-essential clang python3 python3-numpy \
        libopenblas-dev liblapacke-dev libsuperlu-dev \
        time procps tmux curl nodejs npm ripgrep \
 && rm -rf /var/lib/apt/lists/*
RUN npm install -g @openai/codex@0.151.0 && codex --version
COPY --from=prep /app/builds/@PROFILE@/source /app/gkeyll
COPY cases/ /app/cases/
COPY checks/ /app/checks/
COPY rowtool.py /app/rowtool.py
RUN mkdir -p @AGENT_RUN_DIRECTORY@/logs/artifacts
WORKDIR /app
@METADATA_NORMALIZATION@