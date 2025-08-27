ARG DOCKER_HUB=docker.io

# -------------------------------------------------------------

FROM ${DOCKER_HUB}/ticket-base AS ticket-build

WORKDIR /src

# TODO: temporarily, should be after `uv sync`
COPY libs ./libs
COPY packages ./packages
COPY src ./src
COPY README.md ./README.md

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
    --package ticket \
    --locked \
    --no-dev \
    --no-editable