"""Logging utilities for structured logging."""

import logging
import logging.config
import json
import time
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'patient_id'):
            log_data["patient_id"] = record.patient_id
        
        if hasattr(record, 'step'):
            log_data["step"] = record.step
        
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        
        if hasattr(record, 'grievance_count'):
            log_data["grievance_count"] = record.grievance_count
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class Logger:
    """Enhanced logger with structured logging capabilities."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with configuration."""
        logger = logging.getLogger(self.name)
        
        # Set log level
        level = getattr(logging, self.config.get("level", "INFO"))
        logger.setLevel(level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create formatter
        if self.config.get("format") == "structured":
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = self.config.get("file")
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured fields."""
        self.logger.info(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured fields."""
        self.logger.debug(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured fields."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured fields."""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional structured fields."""
        self.logger.critical(message, extra=kwargs)
    
    def log_patient_processing(self, patient_id: str, step: str, duration_ms: int):
        """Log patient processing with structured data."""
        self.info(
            f"Processing patient record",
            patient_id=patient_id,
            step=step,
            duration_ms=duration_ms
        )
    
    def log_grievance_found(self, patient_id: str, grievance_count: int, details: str):
        """Log grievance discovery with structured data."""
        self.info(
            f"Grievances found for patient",
            patient_id=patient_id,
            grievance_count=grievance_count,
            details=details[:100] + "..." if len(details) > 100 else details
        )
    
    def log_verification_sent(self, patient_id: str, method: str, status: str):
        """Log verification message sending."""
        self.info(
            f"Verification message sent",
            patient_id=patient_id,
            method=method,
            status=status
        )
    
    def log_pipeline_start(self, total_records: int):
        """Log pipeline start."""
        self.info(
            f"Starting EHR audit pipeline",
            total_records=total_records
        )
    
    def log_pipeline_complete(self, total_records: int, processing_time_ms: int):
        """Log pipeline completion."""
        self.info(
            f"EHR audit pipeline completed",
            total_records=total_records,
            duration_ms=processing_time_ms
        )


# Global logger factory
_loggers = {}


def get_logger(name: str, config: Dict[str, Any] = None) -> Logger:
    """Get or create a logger instance."""
    if name not in _loggers:
        if config is None:
            config = {"level": "INFO", "format": "structured"}
        _loggers[name] = Logger(name, config)
    
    return _loggers[name]


def setup_logging(config: Dict[str, Any]):
    """Setup global logging configuration."""
    # Create logs directory
    log_file = config.get("file")
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": "self_critique_author.utils.logger.StructuredFormatter"
            },
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "structured" if config.get("format") == "structured" else "standard",
                "level": config.get("level", "INFO")
            }
        },
        "root": {
            "level": config.get("level", "INFO"),
            "handlers": ["console"]
        }
    })
