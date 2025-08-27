FROM ${DOCKER_HUB}/python:3.10-slim AS ticket-base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl=7.88.* && \
    curl --proto '=https' --tlsv1.2 -LsSf https://github.com/astral-sh/uv/releases/download/0.5.26/uv-installer.sh | sh && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH" \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_HTTP_TIMEOUT=10000 \
    UV_PYTHON=python3.10 \
    UV_PROJECT_ENVIRONMENT=/app
