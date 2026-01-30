"""
Logging Utility Module

Provides a centralized, professional logging system for the Investor Bot application.
Implements structured logging with configurable levels, formatted output, and
support for both console and file-based logging.

Author: Pepetopia Development Team
"""

import logging
import sys
from datetime import datetime
from typing import Optional


class LoggerFactory:
    """
    Factory class for creating and managing application loggers.
    
    Provides consistent logging configuration across all modules with
    support for different log levels and output formats.
    """
    
    # Class-level cache for logger instances
    _loggers: dict = {}
    
    # Default configuration
    DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_LEVEL = logging.INFO
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        level: Optional[int] = None,
        log_format: Optional[str] = None
    ) -> logging.Logger:
        """
        Retrieves or creates a logger instance with the specified configuration.
        
        Args:
            name: The name identifier for the logger (typically module name)
            level: Optional logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Optional custom format string for log messages
            
        Returns:
            logging.Logger: Configured logger instance
        """
        # Return cached logger if exists
        if name in cls._loggers:
            return cls._loggers[name]
        
        # Create new logger
        logger = logging.getLogger(name)
        logger.setLevel(level or cls.DEFAULT_LEVEL)
        
        # Prevent duplicate handlers
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level or cls.DEFAULT_LEVEL)
            
            # Formatter
            formatter = logging.Formatter(
                fmt=log_format or cls.DEFAULT_FORMAT,
                datefmt=cls.DEFAULT_DATE_FORMAT
            )
            console_handler.setFormatter(formatter)
            
            logger.addHandler(console_handler)
        
        # Cache the logger
        cls._loggers[name] = logger
        
        return logger
    
    @classmethod
    def set_global_level(cls, level: int) -> None:
        """
        Updates the logging level for all cached loggers.
        
        Args:
            level: The new logging level to apply globally
        """
        for logger in cls._loggers.values():
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)


# Convenience function for quick logger access
def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger instance.
    
    Args:
        name: The name identifier for the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return LoggerFactory.get_logger(name)
