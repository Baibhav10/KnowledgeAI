"""
Centralized logging configuration.
Set up once here; every module does `from app.core.logging import logger`.
Using logging (not print) means output can be redirected to files,
log aggregators, or structured JSON in production.
"""
import logging
import sys


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("knowledge_base_ai")


logger = setup_logging()