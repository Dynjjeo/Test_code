from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import orjson
import structlog


if TYPE_CHECKING:
    from structlog.typing import Processor


def setup_logger(*, json_logs: bool) -> None:
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.StackInfoRenderer(),
    ]

    processors.extend(
        [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(serializer=orjson.dumps),
        ]
        if json_logs
        else [
            structlog.dev.ConsoleRenderer(),
        ]
    )

    logger_factory = (
        structlog.BytesLoggerFactory() if json_logs else structlog.PrintLoggerFactory()
    )

    structlog.configure(
        processors=processors,
        logger_factory=logger_factory,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        cache_logger_on_first_use=False,
    )
