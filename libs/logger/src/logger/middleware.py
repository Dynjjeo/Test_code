from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

import structlog


if TYPE_CHECKING:
    from fastapi import Request, Response
    from starlette.middleware.base import RequestResponseEndpoint


async def logging_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    structlog.contextvars.clear_contextvars()

    structlog.contextvars.bind_contextvars(
        url=str(request.url),
        path=request.url.path,
        scheme=request.url.scheme,
        query_params=str(request.query_params),
        path_params=str(request.path_params),
        http_method=request.method,
        http_version=request.scope["http_version"],
        client_host=request.client.host if request.client is not None else "",
        client_port=request.client.port if request.client is not None else "",
        request_id=str(uuid.uuid4()),
        cookies=request.cookies,
    )

    start_time = time.perf_counter()
    response: Response = await call_next(request)
    process_time = time.perf_counter() - start_time
    structlog.contextvars.bind_contextvars(
        status_code=response.status_code,
        process_time=process_time,
    )

    return response
