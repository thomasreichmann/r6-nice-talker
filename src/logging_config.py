"""
Structured logging configuration with support for verbose/debug modes.
"""
import logging
import sys
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Any, Dict

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON for machine parsing.
    Used in verbose mode for structured analytics and debugging.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra
            
        return json.dumps(log_data)


class SanitizingFormatter(logging.Formatter):
    """
    Formatter that sanitizes sensitive information from log messages.
    Replaces API keys and tokens with masked versions.
    """
    SENSITIVE_KEYS = ["api_key", "token", "password", "secret", "authorization"]
    
    def format(self, record: logging.LogRecord) -> str:
        # First, let parent formatter handle the formatting
        try:
            result = super().format(record)
        except (TypeError, ValueError):
            # If formatting fails, return a safe default
            result = f"{record.levelname}: {record.msg}"
        
        # Then sanitize the formatted message
        for key in self.SENSITIVE_KEYS:
            if key in result.lower():
                # Simple masking - replace anything that looks like a key
                import re
                result = re.sub(
                    r'(api[_-]?key|token|password|secret)["\s:=]+[\w\-]{8,}',
                    r'\1=***REDACTED***',
                    result,
                    flags=re.IGNORECASE
                )
        
        return result


def setup_logging(verbose: bool = False, log_file: str = "bot.log") -> None:
    """
    Configure logging with console and file handlers.
    
    Args:
        verbose: Enable DEBUG level and JSON formatting
        log_file: Path to log file (rotating, 10MB max, 5 backups)
    """
    # Determine log level
    from src.config import Config
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console Handler (colored if available, otherwise standard)
    if HAS_COLORLOG and not verbose:
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
    else:
        # Standard or JSON formatting
        if verbose:
            console_formatter = JSONFormatter()
        else:
            console_formatter = SanitizingFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
    
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # File Handler (Rotating, always uses standard format with sanitization)
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        if verbose:
            file_formatter = JSONFormatter()
        else:
            file_formatter = SanitizingFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}", file=sys.stderr)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    if verbose:
        logger.debug("Verbose logging enabled (DEBUG level, JSON format)")
    logger.info(f"Logging configured: Level={logging.getLevelName(log_level)}, File={log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger with the given name.
    """
    return logging.getLogger(name)

