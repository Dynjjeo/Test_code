FROM ${DOCKER_HUB}/python:3.10-slim

ENV PATH="/app/bin:$PATH" \
    WORKFLOWS_CACHE_DIR=/app/.cache/downloaded_models

RUN groupadd -r app && \
    useradd -l -r -d /app -g app -N app && \
    mkdir -p $WORKFLOWS_CACHE_DIR && \
    chown -R app:app /app

COPY --from=workflows-build --chown=app:app /app /app

USER app
WORKDIR /app
