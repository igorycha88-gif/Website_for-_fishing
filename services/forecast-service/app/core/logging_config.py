import logging
import sys
from datetime import datetime

import structlog
from app.core.config import settings


def get_logger(name: str):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger(name)


def log_to_dict(message: str, **kwargs):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.SERVICE_NAME,
        "level": kwargs.get("level", "info"),
        "message": message,
    }
    log_entry.update(kwargs)
    return log_entry
