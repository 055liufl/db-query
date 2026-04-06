FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Docker Toolbox / small VMs: pip 24+ Rich progress bar spawns threads; low nproc hits RuntimeError: can't start new thread
ENV PIP_PROGRESS_BAR=off
# Slow / cross-border networks: avoid ReadTimeoutError on files.pythonhosted.org (large wheels e.g. asyncpg)
ENV PIP_DEFAULT_TIMEOUT=600
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
# pip 25+ / 镜像源：若出现 "THESE PACKAGES DO NOT MATCH THE HASHES"，勿强制校验哈希（或 wheel 与锁不一致）
ENV PIP_REQUIRE_HASHES=0
ENV PIP_CONSTRAINT=

# 构建时可通过 --build-arg 覆盖，例如国内镜像：
#   docker build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
#                --build-arg PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn ./backend
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=

COPY pyproject.toml .
COPY app ./app

# Use pip only (not `uv pip`): `uv` can panic with Tokio PermissionDenied on Docker Toolbox / restricted seccomp.
# Do not run "pip install -U pip": it pulls from files.pythonhosted.org and often times out on slow links.
RUN set -e; \
    EXTRA=""; \
    if [ -n "$PIP_TRUSTED_HOST" ]; then EXTRA="--trusted-host $PIP_TRUSTED_HOST"; fi; \
    pip install --no-cache-dir --progress-bar off --default-timeout 600 --retries 20 \
        -i "${PIP_INDEX_URL}" $EXTRA .

# Dev deps + tests: CI parity (ruff/mypy/pytest) and docker-compose profile `test`.
# Build: docker build --target test ./backend
FROM base AS test
# ARG does not carry across FROM; empty PIP_INDEX_URL breaks pip -i and hatchling fetch.
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=
COPY tests ./tests
RUN set -e; \
    EXTRA=""; \
    if [ -n "$PIP_TRUSTED_HOST" ]; then EXTRA="--trusted-host $PIP_TRUSTED_HOST"; fi; \
    pip install --no-cache-dir --progress-bar off --default-timeout 600 --retries 20 \
        -i "${PIP_INDEX_URL}" $EXTRA ".[dev]"
CMD ["python", "-m", "pytest", "-q"]

# Default image: production API only (last stage = default `docker build` target).
FROM base AS runtime
EXPOSE 8000

# Use asyncio+h11 so Docker Toolbox / small VMs avoid uvloop/httptools issues (uvicorn[standard] defaults).
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio", "--http", "h11"]
