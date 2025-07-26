"""
Logging configuration for System Companion.

This module provides centralized logging setup with proper formatting,
file handling, and performance considerations.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup logging configuration for System Companion.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Path to log file (default: ~/.local/share/system-companion/logs/app.log)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("system_companion")
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    simple_formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s"
    )
    
    # Console handler (simple format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (detailed format)
    if log_file is None:
        log_dir = Path.home() / ".local" / "share" / "system-companion" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler (errors only)
    error_log_file = log_file.parent / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Performance logging
    perf_logger = logging.getLogger("system_companion.performance")
    perf_logger.setLevel(logging.DEBUG)
    
    perf_log_file = log_file.parent / "performance.log"
    perf_handler = logging.handlers.RotatingFileHandler(
        perf_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    perf_handler.setLevel(logging.DEBUG)
    perf_handler.setFormatter(detailed_formatter)
    perf_logger.addHandler(perf_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    perf_logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (will be prefixed with 'system_companion')
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"system_companion.{name}")


def get_performance_logger() -> logging.Logger:
    """
    Get the performance logger for timing and profiling.
    
    Returns:
        Performance logger instance
    """
    return logging.getLogger("system_companion.performance")


def update_log_level(level: str) -> None:
    """
    Update the log level for all system_companion loggers.
    
    Args:
        level: Log level string ('DEBUG', 'INFO', 'WARNING', 'ERROR')
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    
    log_level = level_map.get(level.upper(), logging.INFO)
    
    # Update main logger
    main_logger = logging.getLogger("system_companion")
    main_logger.setLevel(log_level)
    
    # Update console handler to show debug messages when debug mode is enabled
    for handler in main_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            handler.setLevel(log_level)
            break
    
    # Update performance logger
    perf_logger = logging.getLogger("system_companion.performance")
    perf_logger.setLevel(log_level)
    
    # Log the change
    main_logger.info(f"Log level updated to: {level}")


def get_log_file_path() -> Path:
    """
    Get the path to the main log file.
    
    Returns:
        Path to the log file
    """
    log_dir = Path.home() / ".local" / "share" / "system-companion" / "logs"
    return log_dir / "app.log"


class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, operation: str, logger: Optional[logging.Logger] = None) -> None:
        self.operation = operation
        self.logger = logger or get_performance_logger()
        self.start_time: Optional[float] = None
        
    def __enter__(self) -> "PerformanceTimer":
        import time
        self.start_time = time.time()
        self.logger.debug(f"Starting operation: {self.operation}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        import time
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.logger.debug(f"Completed operation: {self.operation} in {duration:.3f}s")
            
            if exc_type is not None:
                self.logger.error(f"Operation failed: {self.operation} after {duration:.3f}s") 