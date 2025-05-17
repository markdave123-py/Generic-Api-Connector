"""Structured logger with sensitive data redaction."""

import logging
from typing import Dict

_sensitive_headers = {
    "authorization",
    "api-key",
    "cookie",
    "set-cookie",
}


def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    return {
        k: ("***" if k.lower() in _sensitive_headers else v) for k, v in headers.items()
    }


def configure(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("connector")
    if logger.handlers:
        return logger  # already configured
    handler = logging.StreamHandler()
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


logger = configure()
