# syntax=docker/dockerfile:1.7

FROM python:3.11-slim-bookworm AS runtime

ARG APP_VERSION=2.6.0

LABEL org.opencontainers.image.title="Linux Recon Horde" \
      org.opencontainers.image.description="Local-first reconnaissance orchestration engine" \
      org.opencontainers.image.version="${APP_VERSION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HORDE_HOST=0.0.0.0 \
    HORDE_PORT=8787

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        dnsutils \
        iputils-ping \
        netcat-openbsd \
        nmap \
        tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY horde ./horde

RUN python -m pip install --upgrade "pip>=24,<26" \
    && python -m pip install .

RUN groupadd --system horde \
    && useradd --system --gid horde --home-dir /app --shell /usr/sbin/nologin horde \
    && mkdir -p /app/logs /app/modules \
    && chown -R horde:horde /app

USER horde

EXPOSE 8787

VOLUME ["/app/logs", "/app/modules"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import json,urllib.request; d=json.load(urllib.request.urlopen('http://127.0.0.1:8787/api/health', timeout=3)); raise SystemExit(0 if d.get('status') == 'online' else 1)"

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["horde-server"]
