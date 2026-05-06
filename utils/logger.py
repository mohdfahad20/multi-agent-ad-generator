"""
utils/logger.py
Centralized rich logger — writes to console (coloured) and to logs/cwt_agent.log
"""

import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

_console = Console(stderr=True)
_loggers: dict[str, logging.Logger] = {}

LOG_FILE = Path(__file__).parent.parent / "logs" / "cwt_agent.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(f"cwt.{name}")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # ── Rich console handler ─────────────────────────────────────────────
        console_handler = RichHandler(
            console=_console,
            show_time=True,
            show_level=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
        console_handler.setLevel(logging.INFO)

        # ── File handler ─────────────────────────────────────────────────────
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.propagate = False

    _loggers[name] = logger
    return logger