FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Docker Toolbox / small VMs: pip 24+ Rich progress bar spawns threads; low nproc hits RuntimeError: can't start new thread
ENV PIP_PROGRESS_BAR=off
# Slow / cross-border networks: avoid ReadTimeoutError on files.pythonhosted.org (large wheels e.g. asyncpg)
ENV PIP_DEFAULT_TIMEOUT=600
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 构建时可通过 --build-arg 覆盖，例如国内镜像：
#   docker build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
#                --build-arg PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn ./backend
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=

COPY pyproject.toml .
COPY app ./app

# Do not run "pip install -U pip": it pulls from files.pythonhosted.org and often times out on slow links.
RUN set -e; \
    TH=""; \
    if [ -n "$PIP_TRUSTED_HOST" ]; then TH="--trusted-host $PIP_TRUSTED_HOST"; fi; \
    pip install --no-cache-dir --progress-bar off --default-timeout 600 --retries 20 \
    . -i "${PIP_INDEX_URL}" $TH

EXPOSE 8000

# Use asyncio+h11 so Docker Toolbox / small VMs avoid uvloop/httptools issues (uvicorn[standard] defaults).
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio", "--http", "h11"]
