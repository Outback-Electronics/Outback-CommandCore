"""
Advanced Logging Setup for CommandCore Launcher

Provides comprehensive logging configuration with file rotation,
structured logging, performance tracking, and error reporting.
"""

import logging
import logging.handlers
import sys
import os
import json
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from contextlib import contextmanager

from PySide6.QtCore import QObject, Signal


class LogLevel(Enum):
    """Enhanced log levels with descriptions."""
    DEBUG = ("DEBUG", "Detailed information for debugging")
    INFO = ("INFO", "General information about application operation")
    WARNING = ("WARNING", "Warning messages for potential issues")
    ERROR = ("ERROR", "Error messages for handled exceptions")
    CRITICAL = ("CRITICAL", "Critical errors that may cause application failure")


@dataclass
class LogConfig:
    """Comprehensive logging configuration."""
    # Basic settings
    level: str = "INFO"
    
    # File logging
    file_enabled: bool = True
    file_path: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 5
    
    # Console logging
    console_enabled: bool = True
    console_level: str = "INFO"
    
    # Formatting
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # Advanced features
    structured_logging: bool = True
    performance_logging: bool = True
    error_context: bool = True
    log_caller_info: bool = True
    
    # Filtering
    excluded_loggers: List[str] = None
    included_modules: List[str] = None


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def __init__(self, include_context: bool = True):
        super().__init__()
        self.include_context = include_context
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra context if available
        if self.include_context and hasattr(record, 'extra_context'):
            log_data['context'] = record.extra_context
        
        # Add performance data if available
        if hasattr(record, 'performance_data'):
            log_data['performance'] = record.performance_data
        
        return json.dumps(log_data, default=str)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for better readability."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console output."""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Format the basic message
        formatted = super().format(record)
        
        # Add colors
        colored_level = f"{log_color}{record.levelname}{reset_color}"
        formatted = formatted.replace(record.levelname, colored_level, 1)
        
        return formatted


class PerformanceTracker:
    """Track performance metrics for logging."""
    
    def __init__(self):
        self.start_times: Dict[str, float] = {}
        self.metrics: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        import time
        with self._lock:
            self.start_times[operation] = time.perf_counter()
    
    def end_timer(self, operation: str) -> Optional[float]:
        """End timing and return duration."""
        import time
        with self._lock:
            if operation in self.start_times:
                duration = time.perf_counter() - self.start_times[operation]
                del self.start_times[operation]
                
                # Store metric
                if operation not in self.metrics:
                    self.metrics[operation] = []
                self.metrics[operation].append(duration)
                
                # Keep only last 100 measurements
                if len(self.metrics[operation]) > 100:
                    self.metrics[operation] = self.metrics[operation][-100:]
                
                return duration
        return None
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get performance statistics for an operation."""
        with self._lock:
            if operation not in self.metrics or not self.metrics[operation]:
                return {}
            
            measurements = self.metrics[operation]
            return {
                'count': len(measurements),
                'avg': sum(measurements) / len(measurements),
                'min': min(measurements),
                'max': max(measurements),
                'recent': measurements[-1] if measurements else 0
            }


class LoggingManager(QObject):
    """Advanced logging manager with Qt integration."""
    
    # Signals for log events
    log_message_received = Signal(str, str, str)  # level, logger, message
    error_occurred = Signal(str, str)             # error_type, message
    
    def __init__(self, config: Optional[LogConfig] = None):
        super().__init__()
        
        self.config = config or LogConfig()
        self.performance_tracker = PerformanceTracker()
        self.loggers: Dict[str, logging.Logger] = {}
        self.handlers: List[logging.Handler] = []
        
        # Error tracking
        self.error_count: Dict[str, int] = {}
        self.last_errors: List[Dict[str, Any]] = []
        self.max_error_history = 50
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup comprehensive logging configuration."""
        # Clear existing handlers
        self._clear_existing_handlers()
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level.upper()))
        
        # Setup file logging
        if self.config.file_enabled:
            self._setup_file_logging()
        
        # Setup console logging
        if self.config.console_enabled:
            self._setup_console_logging()
        
        # Setup Qt logging integration
        self._setup_qt_logging()
        
        # Setup exception handling
        self._setup_exception_handling()
        
        print(f"Logging initialized - Level: {self.config.level}, File: {self.config.file_enabled}")
    
    def _clear_existing_handlers(self):
        """Clear existing handlers to avoid duplicates."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()
        
        self.handlers.clear()
    
    def _setup_file_logging(self):
        """Setup file logging with rotation."""
        try:
            # Determine log file path
            if self.config.file_path:
                log_file = Path(self.config.file_path)
            else:
                log_dir = self._get_log_directory()
                log_file = log_dir / "commandcore.log"
            
            # Ensure log directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            
            # Choose formatter based on structured logging setting
            if self.config.structured_logging:
                formatter = StructuredFormatter(include_context=self.config.error_context)
            else:
                formatter = logging.Formatter(
                    fmt=self.config.format_string,
                    datefmt=self.config.date_format
                )
            
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, self.config.level.upper()))
            
            # Add to root logger
            logging.getLogger().addHandler(file_handler)
            self.handlers.append(file_handler)
            
            print(f"File logging enabled: {log_file}")
            
        except Exception as e:
            print(f"Failed to setup file logging: {e}")
    
    def _setup_console_logging(self):
        """Setup console logging with colors."""
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            
            # Use colored formatter for console
            if sys.stdout.isatty():  # Only use colors for real terminals
                formatter = ColoredConsoleFormatter(
                    fmt=self.config.format_string,
                    datefmt=self.config.date_format
                )
            else:
                formatter = logging.Formatter(
                    fmt=self.config.format_string,
                    datefmt=self.config.date_format
                )
            
            console_handler.setFormatter(formatter)
            console_handler.setLevel(getattr(logging, self.config.console_level.upper()))
            
            # Add to root logger
            logging.getLogger().addHandler(console_handler)
            self.handlers.append(console_handler)
            
        except Exception as e:
            print(f"Failed to setup console logging: {e}")
    
    def _setup_qt_logging(self):
        """Setup Qt-specific logging integration."""
        try:
            # Create custom handler for Qt signals
            class QtSignalHandler(logging.Handler):
                def __init__(self, manager):
                    super().__init__()
                    self.manager = manager
                
                def emit(self, record):
                    try:
                        self.manager.log_message_received.emit(
                            record.levelname,
                            record.name,
                            record.getMessage()
                        )
                        
                        # Track errors
                        if record.levelno >= logging.ERROR:
                            self.manager._track_error(record)
                            
                    except Exception:
                        pass  # Avoid recursive errors
            
            qt_handler = QtSignalHandler(self)
            qt_handler.setLevel(logging.WARNING)  # Only emit signals for warnings and above
            
            logging.getLogger().addHandler(qt_handler)
            self.handlers.append(qt_handler)
            
        except Exception as e:
            print(f"Failed to setup Qt logging: {e}")
    
    def _setup_exception_handling(self):
        """Setup global exception handling."""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # Don't log keyboard interrupts
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Log the exception
            logger = self.get_logger("global_exception_handler")
            logger.critical(
                "Uncaught exception",
                exc_info=(exc_type, exc_value, exc_traceback),
                extra={'extra_context': {'unhandled': True}}
            )
            
            # Emit Qt signal
            self.error_occurred.emit(
                exc_type.__name__,
                str(exc_value)
            )
        
        sys.excepthook = handle_exception
    
    def _get_log_directory(self) -> Path:
        """Get the default log directory."""
        try:
            from PySide6.QtCore import QStandardPaths
            data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if data_dir:
                return Path(data_dir) / "CommandCore" / "logs"
        except Exception:
            pass
        
        # Fallback to application directory
        return Path(__file__).parent.parent / "logs"
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with performance tracking."""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            
            # Add performance tracking methods
            original_info = logger.info
            original_debug = logger.debug
            original_warning = logger.warning
            original_error = logger.error
            original_critical = logger.critical
            
            def enhanced_log(original_method, level):
                def wrapper(msg, *args, **kwargs):
                    # Add performance context if available
                    if self.config.performance_logging:
                        perf_data = kwargs.pop('performance_data', None)
                        if perf_data:
                            extra = kwargs.get('extra', {})
                            extra['performance_data'] = perf_data
                            kwargs['extra'] = extra
                    
                    # Add caller info if enabled
                    if self.config.log_caller_info:
                        import inspect
                        frame = inspect.currentframe().f_back.f_back
                        extra = kwargs.get('extra', {})
                        extra.update({
                            'caller_file': frame.f_code.co_filename,
                            'caller_line': frame.f_lineno,
                            'caller_function': frame.f_code.co_name
                        })
                        kwargs['extra'] = extra
                    
                    return original_method(msg, *args, **kwargs)
                return wrapper
            
            logger.info = enhanced_log(original_info, 'INFO')
            logger.debug = enhanced_log(original_debug, 'DEBUG')
            logger.warning = enhanced_log(original_warning, 'WARNING')
            logger.error = enhanced_log(original_error, 'ERROR')
            logger.critical = enhanced_log(original_critical, 'CRITICAL')
            
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def _track_error(self, record: logging.LogRecord):
        """Track error for statistics and reporting."""
        error_type = record.levelname
        
        # Count errors by type
        if error_type not in self.error_count:
            self.error_count[error_type] = 0
        self.error_count[error_type] += 1
        
        # Store recent errors
        error_data = {
            'timestamp': datetime.fromtimestamp(record.created),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            error_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1])
            }
        
        self.last_errors.append(error_data)
        
        # Limit error history
        if len(self.last_errors) > self.max_error_history:
            self.last_errors = self.last_errors[-self.max_error_history:]
    
    @contextmanager
    def performance_context(self, operation: str, logger_name: str = "performance"):
        """Context manager for performance logging."""
        logger = self.get_logger(logger_name)
        self.performance_tracker.start_timer(operation)
        
        try:
            yield
        finally:
            duration = self.performance_tracker.end_timer(operation)
            if duration is not None:
                logger.info(
                    f"Operation '{operation}' completed",
                    extra={
                        'performance_data': {
                            'operation': operation,
                            'duration': duration,
                            'stats': self.performance_tracker.get_stats(operation)
                        }
                    }
                )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        return {
            'config': asdict(self.config),
            'error_counts': self.error_count.copy(),
            'recent_errors': len(self.last_errors),
            'active_loggers': len(self.loggers),
            'handlers': len(self.handlers),
            'performance_operations': len(self.performance_tracker.metrics)
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error messages."""
        return self.last_errors[-limit:] if self.last_errors else []
    
    def update_config(self, new_config: LogConfig):
        """Update logging configuration at runtime."""
        self.config = new_config
        self._setup_logging()
    
    def cleanup(self):
        """Clean up logging resources."""
        try:
            # Close all handlers
            for handler in self.handlers:
                handler.close()
            
            # Clear references
            self.handlers.clear()
            self.loggers.clear()
            
            print("Logging cleanup completed")
            
        except Exception as e:
            print(f"Error during logging cleanup: {e}")


# Global logging manager
_logging_manager: Optional[LoggingManager] = None

def setup_logging(name: str = None, 
                 level: str = "INFO", 
                 config: Optional[LogConfig] = None) -> logging.Logger:
    """Setup logging and return a logger instance."""
    global _logging_manager
    
    if _logging_manager is None:
        if config is None:
            config = LogConfig(level=level)
        _logging_manager = LoggingManager(config)
    
    if name:
        return _logging_manager.get_logger(name)
    else:
        return _logging_manager.get_logger("commandcore")

def get_logging_manager() -> Optional[LoggingManager]:
    """Get the global logging manager."""
    return _logging_manager

def cleanup_logging():
    """Clean up the global logging manager."""
    global _logging_manager
    if _logging_manager is not None:
        _logging_manager.cleanup()
        _logging_manager = None

@contextmanager
def log_performance(operation: str, logger_name: str = "performance"):
    """Convenience context manager for performance logging."""
    manager = get_logging_manager()
    if manager:
        with manager.performance_context(operation, logger_name):
            yield
    else:
        yield