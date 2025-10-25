"""
Logger setup utility for the Evernote to Notion migration tool.

Provides consistent logging configuration across all modules.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Setup logger with file and console handlers.

    Args:
        name: Logger name (default: root logger)
        level: Logging level (default: INFO)
        log_file: Path to log file (default: logs/migration_{timestamp}.log)
        console: Enable console output (default: True)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger('migration', level=logging.DEBUG)
        >>> logger.info("Processing started")
        >>> logger.error("Something failed")
    """
    # Get logger
    logger = logging.getLogger(name) if name else logging.getLogger()
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"migration_{timestamp}.log"

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    logger.debug(f"Logger initialized: {name or 'root'}")

    return logger


def setup_migration_logger(verbose: bool = False) -> logging.Logger:
    """
    Setup logger specifically for migration script.

    Args:
        verbose: Enable DEBUG level logging

    Returns:
        Configured logger for migration
    """
    level = logging.DEBUG if verbose else logging.INFO

    logger = setup_logger(
        name='migration',
        level=level,
        console=True
    )

    return logger


# Example usage
if __name__ == "__main__":
    # Basic logger
    logger = setup_logger()
    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error")

    # Verbose migration logger
    migration_logger = setup_migration_logger(verbose=True)
    migration_logger.debug("Debug message")
    migration_logger.info("Processing file...")
    migration_logger.error("Failed to process")
