"""
Logging utilities for the paper-to-slides system.

Provides structured logging with file and console output using loguru.
"""

import sys
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from loguru import logger as _logger

from src.utils.config_loader import load_config

if TYPE_CHECKING:
    from loguru import Logger


def setup_logger(
    name: Optional[str] = None,
    log_level: Optional[str] = None,
    log_dir: Optional[Path] = None
) -> "Logger":
    """
    Set up the application logger with console and file handlers.
    
    Args:
        name: Logger name (used for filtering)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logger("pdf_processor", "DEBUG")
        >>> logger.info("Processing started")
    """
    # Load configuration
    config = load_config()
    log_config = config.get("logging", {})
    
    # Use provided values or fall back to config
    log_level = log_level or log_config.get("level", "INFO")
    log_dir = log_dir or Path(log_config.get("log_dir", "logs"))
    log_format = log_config.get(
        "format",
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Remove default handler
    _logger.remove()
    
    # Add console handler
    _logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler for all logs
    _logger.add(
        log_dir / "paper_to_slides.log",
        format=log_format,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Add separate error log
    _logger.add(
        log_dir / "errors.log",
        format=log_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Add context filter if name provided
    result_logger = _logger
    if name:
        result_logger = _logger.bind(name=name)
    
    result_logger.info(f"Logger initialized with level: {log_level}")
    return result_logger


def get_logger(name: str) -> "Logger":
    """
    Get a logger instance with a specific name.
    
    Args:
        name: Logger name for identification
    
    Returns:
        Logger instance bound to the given name
    
    Example:
        >>> logger = get_logger("image_generator")
        >>> logger.debug("Starting image generation")
    """
    return _logger.bind(name=name)