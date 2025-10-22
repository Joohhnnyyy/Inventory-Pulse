"""
Logger Utility Module

Provides consistent logging configuration and utilities for the application.
"""

import logging
import sys
from typing import Optional
from loguru import logger
import os
from datetime import datetime

def setup_logger(
    name: Optional[str] = None,
    level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "1 day",
    retention: str = "30 days"
) -> logging.Logger:
    """
    Set up a logger with consistent formatting and configuration.
    
    Args:
        name: Logger name (defaults to calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        rotation: Log rotation policy
        retention: Log retention policy
        
    Returns:
        Configured logger instance
    """
    # Remove default loguru handler
    logger.remove()
    
    # Console handler with colored output
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # File handler if specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logger.add(
            log_file,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
    
    # Create standard library logger that forwards to loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
    
    # Set up standard library logger
    stdlib_logger = logging.getLogger(name)
    stdlib_logger.handlers = [InterceptHandler()]
    stdlib_logger.setLevel(getattr(logging, level.upper()))
    
    return stdlib_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_function_call(func):
    """
    Decorator to log function calls with parameters and execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        func_logger = get_logger(func.__module__)
        start_time = datetime.now()
        
        # Log function entry
        func_logger.debug(f"Entering {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            func_logger.debug(f"Exiting {func.__name__} successfully (took {execution_time:.3f}s)")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            func_logger.error(f"Error in {func.__name__} after {execution_time:.3f}s: {str(e)}")
            raise
    
    return wrapper

def log_async_function_call(func):
    """
    Decorator to log async function calls with parameters and execution time.
    
    Args:
        func: Async function to decorate
        
    Returns:
        Decorated async function
    """
    async def wrapper(*args, **kwargs):
        func_logger = get_logger(func.__module__)
        start_time = datetime.now()
        
        # Log function entry
        func_logger.debug(f"Entering async {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            func_logger.debug(f"Exiting async {func.__name__} successfully (took {execution_time:.3f}s)")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            func_logger.error(f"Error in async {func.__name__} after {execution_time:.3f}s: {str(e)}")
            raise
    
    return wrapper

class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__module__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def log_critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)

def configure_third_party_loggers(level: str = "WARNING"):
    """
    Configure third-party library loggers to reduce noise.
    
    Args:
        level: Logging level for third-party loggers
    """
    # List of noisy third-party loggers
    noisy_loggers = [
        'urllib3.connectionpool',
        'requests.packages.urllib3.connectionpool',
        'googleapiclient.discovery',
        'googleapiclient.discovery_cache',
        'google.auth.transport.requests',
        'notion_client.client'
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(getattr(logging, level.upper()))

# Configure third-party loggers by default
configure_third_party_loggers()