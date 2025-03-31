"""Logger configuration for the DAG system."""

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance.

    If the logger is for the main entry point, return the root logger.
    Otherwise, return a named logger.
    """
    if name in {"__main__", "dag.main"}:
        return logging.getLogger()
    return logging.getLogger(name)
