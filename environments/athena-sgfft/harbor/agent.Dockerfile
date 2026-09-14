# @NAME@: Athena++ self-gravity agent image. Only the prep stage sees the
# reused pristine archive and exact defect record.
FROM @DIGEST@ AS prep

ENV DEBIAN_FRONTEND=noninteractive
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates python3 \
 && rm -rf /var/lib/apt/lists/*

COPY source/@ATHENA_ARCHIVE@ /tmp/athena.tar.gz
RUN echo "@ATHENA_SHA256@  /tmp/athena.tar.gz" | sha256sum -c - \
 && mkdir -p /app \
 && tar -xzf /tmp/athena.tar.gz -C /tmp \
 && mv /tmp/athena-@ATHENA_COMMIT@ /app/athena \
 && rm /tmp/athena.tar.gz \
 && test ! -e /app/athena/.git

COPY defect/ /opt/defect/
COPY strip-tree.py /opt/strip-tree.py
RUN python3 /opt/defect/apply_defect.py /opt/defect/defect.json /app/athena \
 && python3 /opt/strip-tree.py /app/athena "@STRIP_PATHS@"

FROM @DIGEST@

ENV DEBIAN_FRONTEND=noninteractive
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates build-essential python3 \
        libfftw3-dev libopenmpi-dev openmpi-bin \
        time procps tmux curl nodejs npm ripgrep \
 && rm -rf /var/lib/apt/lists/*
RUN npm install -g @openai/codex@0.151.0 && codex --version

COPY --from=prep /app/athena /app/athena
COPY cases/ /app/cases/
COPY checks/ /app/checks/
COPY sg_format.py /app/sg_format.py
RUN mkdir -p /app/run /logs/artifacts
WORKDIR /app
