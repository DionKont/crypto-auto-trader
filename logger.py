# logger.py

import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Union, List


class Logger:
    _loggers: Dict[str, logging.Logger] = {}
    _lock = threading.Lock()
    _default_log_dir = "logs"
    _default_log_file = "trader.log"
    _default_formatter = None

    @classmethod
    def _get_default_formatter(cls) -> logging.Formatter:
        """Get or create the default formatter (singleton pattern)."""
        if cls._default_formatter is None:
            cls._default_formatter = logging.Formatter(
                fmt="%(asctime)s [%(module)s::%(name)s] %(levelname)-8s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z"  # ISO 8601 format
            )
        return cls._default_formatter

    def __new__(
        cls,
        name: str,
        *,
        level: int = logging.INFO,
        log_to_console: bool = True,
        log_to_file: Optional[Union[str, bool]] = None,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5
    ) -> logging.Logger:
        """
        Create or retrieve a logger instance.
        
        Args:
            name: Logger name
            level: Logging level
            log_to_console: Whether to log to console
            log_to_file: File path to log to, or True to use default path, or None/False to disable
            max_bytes: Max bytes per log file before rotation
            backup_count: Number of backup files to keep
            
        Returns:
            Logger instance
        """
        with cls._lock:  # Thread-safe singleton
            if name in cls._loggers:
                return cls._loggers[name]

            logger = logging.getLogger(name)
            logger.setLevel(level)
            logger.propagate = False  # Prevent duplicate logs from root logger

            formatter = cls._get_default_formatter()

            if log_to_console:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(level)
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)

            # Handle file logging with improved logic
            if log_to_file:
                if isinstance(log_to_file, bool):
                    # Use default path if log_to_file is True
                    file_path = os.path.join(cls._default_log_dir, cls._default_log_file)
                else:
                    # Use provided path
                    file_path = log_to_file
                
                cls._ensure_log_path_exists(file_path)
                file_handler = RotatingFileHandler(
                    file_path, 
                    maxBytes=max_bytes, 
                    backupCount=backup_count, 
                    encoding="utf-8"
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

            cls._loggers[name] = logger
            return logger

    @staticmethod
    def _ensure_log_path_exists(file_path: str):
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    @classmethod
    def get_logger(cls, name: str) -> Optional[logging.Logger]:
        """Get an existing logger by name."""
        return cls._loggers.get(name)

    @classmethod
    def remove_logger(cls, name: str) -> bool:
        """
        Remove a logger and clean up its handlers.
        
        Args:
            name: Logger name to remove
            
        Returns:
            True if logger was removed, False if it didn't exist
        """
        with cls._lock:
            if name in cls._loggers:
                logger = cls._loggers[name]
                # Clean up handlers
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
                del cls._loggers[name]
                return True
            return False

    @classmethod
    def list_loggers(cls) -> List[str]:
        """Get a list of all active logger names."""
        return list(cls._loggers.keys())

    @classmethod
    def cleanup_all(cls) -> None:
        """Clean up all loggers and their handlers."""
        with cls._lock:
            for name in list(cls._loggers.keys()):
                cls.remove_logger(name)
