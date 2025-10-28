import logging
import os
from logging.handlers import RotatingFileHandler

# PUBLIC_INTERFACE
def configure_logging() -> logging.Logger:
    """Configure application-wide logging with console and rotating file handlers.
    Returns the configured root logger."""
    logger = logging.getLogger()
    if logger.handlers:
        return logger  # already configured

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Optional rotating file handler
    log_file = os.getenv("LOG_FILE", "").strip()
    if log_file:
        fh = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    logger.debug("Logging configured", extra={"level": level, "log_file": log_file})
    return logger
