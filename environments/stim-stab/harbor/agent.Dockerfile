# @NAME@: Stim agent image. Only prep sees the archive and defect record.
FROM @DIGEST@ AS prep
ENV DEBIAN_FRONTEND=noninteractive
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates \
 && rm -rf /var/lib/apt/lists/*
COPY source/@STIM_ARCHIVE@ /tmp/stim.tar.gz
RUN echo "@STIM_SHA256@  /tmp/stim.tar.gz" | sha256sum -c - \
 && mkdir -p /app \
 && tar -xzf /tmp/stim.tar.gz -C /app \
 && mv /app/stim-@STIM_COMMIT@ /app/stim \
 && rm /tmp/stim.tar.gz \
 && test -f /app/stim/CMakeLists.txt && test ! -e /app/stim/.git
COPY defect/ /opt/defect/
COPY strip-tree.py /opt/strip-tree.py
RUN python3 /opt/defect/apply_defect.py /opt/defect/defect.json /app/stim \
 && python3 /opt/strip-tree.py /app/stim "@STRIP_PATHS@"

FROM @DIGEST@
ENV DEBIAN_FRONTEND=noninteractive
@APT_MIRROR@RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build python3 python3-dev python3-pip python3-numpy \
    ca-certificates time procps tmux curl nodejs npm ripgrep \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --break-system-packages pybind11==2.11.1 \
 && npm install -g @openai/codex@0.151.0 && codex --version
COPY --from=prep /app/stim /app/stim
COPY cases/ /app/cases/
COPY checks/ /app/checks/
COPY rowtool.py /app/rowtool.py
RUN mkdir -p /app/build /logs/artifacts
WORKDIR /app
