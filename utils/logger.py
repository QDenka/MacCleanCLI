"""
Logging configuration for macOS Cleaner
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(name: str, log_file: Optional[Path] = None,
                 level: int = logging.INFO,
                 console_level: int = logging.WARNING) -> logging.Logger:
    """
    Set up a logger with console and optional file output.

    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with simple format for user-friendly output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler with detailed format
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger by name."""
    return logging.getLogger(name)


def configure_logging(verbose: bool = False) -> None:
    """Configure logging behavior for CLI runtime."""
    target_level = logging.DEBUG if verbose else logging.INFO
    console_level = logging.INFO if verbose else logging.WARNING

    # Root logger
    root = logging.getLogger()
    root.setLevel(target_level)
    for handler in root.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(console_level)

    # Already-instantiated named loggers
    for logger_obj in logging.Logger.manager.loggerDict.values():
        if not isinstance(logger_obj, logging.Logger):
            continue
        logger_obj.setLevel(target_level)
        for handler in logger_obj.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(console_level)


# Default log directory
LOG_DIR = Path.home() / ".macos-cleaner" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Default log file
DEFAULT_LOG_FILE = LOG_DIR / f"cleaner_{datetime.now().strftime('%Y%m%d')}.log"

# Configure root logger
root_logger = setup_logger("macos_cleaner", DEFAULT_LOG_FILE)