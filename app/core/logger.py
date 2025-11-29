"""
Structured logging configuration.
"""
import logging
import sys
from typing import Optional
from pathlib import Path
from app.core.config import settings


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a structured logger with console and optional file output.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        settings.log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def log_operation(
    logger: logging.Logger,
    operation: str,
    doc_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log an operation with structured data.
    
    Args:
        logger: Logger instance
        operation: Operation name
        doc_id: Document ID (if applicable)
        **kwargs: Additional data to log
    """
    log_data = {
        "operation": operation,
        "doc_id": doc_id,
        **kwargs
    }
    
    log_message = f"Operation: {operation}"
    if doc_id:
        log_message += f" | Doc ID: {doc_id}"
    
    # Add additional data
    if kwargs:
        extras = " | ".join(f"{k}: {v}" for k, v in kwargs.items())
        log_message += f" | {extras}"
    
    logger.info(log_message)


def log_error(
    logger: logging.Logger,
    error: Exception,
    operation: Optional[str] = None,
    doc_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log an error with structured data.
    
    Args:
        logger: Logger instance
        error: Exception instance
        operation: Operation name where error occurred
        doc_id: Document ID (if applicable)
        **kwargs: Additional context data
    """
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "operation": operation,
        "doc_id": doc_id,
        **kwargs
    }
    
    log_message = f"Error: {type(error).__name__} - {str(error)}"
    if operation:
        log_message += f" | Operation: {operation}"
    if doc_id:
        log_message += f" | Doc ID: {doc_id}"
    
    # Add additional context
    if kwargs:
        extras = " | ".join(f"{k}: {v}" for k, v in kwargs.items())
        log_message += f" | {extras}"
    
    logger.error(log_message, exc_info=True)


# Create main application logger
app_logger = setup_logger("pdf_rag_system", log_file="logs/app.log")

# Create component-specific loggers
upload_logger = setup_logger("pdf_rag_system.upload")
rag_logger = setup_logger("pdf_rag_system.rag")
api_logger = setup_logger("pdf_rag_system.api")