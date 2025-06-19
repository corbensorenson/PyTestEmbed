"""
PyTestEmbed Error Handler

Provides robust error handling and recovery mechanisms for all
PyTestEmbed operations including graceful degradation and fallbacks.
"""

import logging
import traceback
import time
import os
from typing import Any, Optional, Callable, Dict, List, Union
from functools import wraps
from pathlib import Path
import json

from .config_manager import get_config_manager


class PyTestEmbedError(Exception):
    """Base exception for PyTestEmbed errors."""
    pass


class ParseError(PyTestEmbedError):
    """Error during parsing operations."""
    pass


class AIError(PyTestEmbedError):
    """Error during AI operations."""
    pass


class CacheError(PyTestEmbedError):
    """Error during cache operations."""
    pass


class ConfigError(PyTestEmbedError):
    """Error during configuration operations."""
    pass


class NetworkError(PyTestEmbedError):
    """Error during network operations."""
    pass


class ErrorHandler:
    """Centralized error handling and recovery system."""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.logger = self._setup_logging()
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, float] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Setup default recovery strategies
        self._setup_recovery_strategies()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for error handling."""
        logger = logging.getLogger('pytestembed')
        
        if not logger.handlers:
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            
            # Create file handler if possible
            try:
                log_dir = Path.home() / ".pytestembed" / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = log_dir / "pytestembed.log"
                
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                
                # Create formatter
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                console_handler.setFormatter(formatter)
                file_handler.setFormatter(formatter)
                
                logger.addHandler(console_handler)
                logger.addHandler(file_handler)
                
            except Exception:
                # Fallback to console only
                logger.addHandler(console_handler)
        
        logger.setLevel(logging.DEBUG if self.config_manager.config.verbose else logging.WARNING)
        return logger
    
    def _setup_recovery_strategies(self):
        """Setup default recovery strategies for different error types."""
        self.recovery_strategies.update({
            'ai_unavailable': self._recover_ai_unavailable,
            'network_timeout': self._recover_network_timeout,
            'parse_error': self._recover_parse_error,
            'cache_corrupted': self._recover_cache_corrupted,
            'config_invalid': self._recover_config_invalid,
            'file_not_found': self._recover_file_not_found,
            'permission_denied': self._recover_permission_denied
        })
    
    def handle_error(self, error: Exception, context: str = "", 
                    recovery_strategy: Optional[str] = None) -> Optional[Any]:
        """Handle an error with appropriate recovery strategy."""
        error_type = type(error).__name__
        error_key = f"{error_type}_{context}"
        
        # Log the error
        self.logger.error(f"Error in {context}: {error_type}: {str(error)}")
        if self.config_manager.config.verbose:
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Track error frequency
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = time.time()
        
        # Attempt recovery
        if recovery_strategy and recovery_strategy in self.recovery_strategies:
            try:
                return self.recovery_strategies[recovery_strategy](error, context)
            except Exception as recovery_error:
                self.logger.error(f"Recovery strategy '{recovery_strategy}' failed: {recovery_error}")
        
        # Auto-detect recovery strategy
        auto_strategy = self._detect_recovery_strategy(error, context)
        if auto_strategy and auto_strategy in self.recovery_strategies:
            try:
                return self.recovery_strategies[auto_strategy](error, context)
            except Exception as recovery_error:
                self.logger.error(f"Auto recovery strategy '{auto_strategy}' failed: {recovery_error}")
        
        return None
    
    def _detect_recovery_strategy(self, error: Exception, context: str) -> Optional[str]:
        """Auto-detect appropriate recovery strategy."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        if 'ai' in context.lower() or 'generation' in context.lower():
            if 'timeout' in error_message or 'connection' in error_message:
                return 'network_timeout'
            else:
                return 'ai_unavailable'
        
        elif 'parse' in context.lower():
            return 'parse_error'
        
        elif 'cache' in context.lower():
            return 'cache_corrupted'
        
        elif 'config' in context.lower():
            return 'config_invalid'
        
        elif 'file not found' in error_message or 'no such file' in error_message:
            return 'file_not_found'
        
        elif 'permission denied' in error_message:
            return 'permission_denied'
        
        elif 'timeout' in error_message or 'connection' in error_message:
            return 'network_timeout'
        
        return None
    
    def _recover_ai_unavailable(self, error: Exception, context: str) -> Optional[Any]:
        """Recovery strategy for AI unavailability."""
        self.logger.warning("AI service unavailable, falling back to template generation")
        
        # Return a fallback result indicating template generation should be used
        return {
            'fallback': True,
            'strategy': 'template',
            'reason': 'ai_unavailable',
            'error': str(error)
        }
    
    def _recover_network_timeout(self, error: Exception, context: str) -> Optional[Any]:
        """Recovery strategy for network timeouts."""
        error_key = f"network_timeout_{context}"
        retry_count = self.error_counts.get(error_key, 0)
        
        if retry_count < self.max_retries:
            self.logger.warning(f"Network timeout, retrying in {self.retry_delay} seconds (attempt {retry_count + 1})")
            time.sleep(self.retry_delay)
            return {'retry': True, 'attempt': retry_count + 1}
        else:
            self.logger.error("Max retries exceeded for network timeout, falling back")
            return {'fallback': True, 'strategy': 'offline', 'reason': 'network_timeout'}
    
    def _recover_parse_error(self, error: Exception, context: str) -> Optional[Any]:
        """Recovery strategy for parse errors."""
        self.logger.warning("Parse error encountered, attempting partial parsing")
        
        return {
            'fallback': True,
            'strategy': 'partial_parse',
            'reason': 'syntax_error',
            'error': str(error)
        }
    
    def _recover_cache_corrupted(self, error: Exception, context: str) -> Optional[Any]:
        """Recovery strategy for corrupted cache."""
        self.logger.warning("Cache corrupted, clearing and rebuilding")
        
        try:
            from .cache_manager import get_cache_manager
            cache_manager = get_cache_manager()
            cache_manager.clear_cache()
            return {'cache_cleared': True, 'retry': True}
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return {'fallback': True, 'strategy': 'no_cache'}
    
    def _recover_config_invalid(self, error: Exception, context: str) -> Optional[Any]:
        """Recovery strategy for invalid configuration."""
        self.logger.warning("Invalid configuration, resetting to defaults")
        
        try:
            self.config_manager.reset_to_defaults()
            return {'config_reset': True, 'retry': True}
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return {'fallback': True, 'strategy': 'default_config'}
    
    def _recover_file_not_found(self, error: Exception, context: str) -> Optional[Any]:
        """Recovery strategy for file not found errors."""
        self.logger.warning(f"File not found: {error}")
        
        return {
            'fallback': True,
            'strategy': 'skip_file',
            'reason': 'file_not_found',
            'error': str(error)
        }
    
    def _recover_permission_denied(self, error: Exception, context: str) -> Optional[Any]:
        """Recovery strategy for permission denied errors."""
        self.logger.warning(f"Permission denied: {error}")
        
        return {
            'fallback': True,
            'strategy': 'read_only',
            'reason': 'permission_denied',
            'error': str(error)
        }
    
    def with_error_handling(self, func: Callable, context: str = "", 
                           recovery_strategy: Optional[str] = None,
                           default_return: Any = None) -> Callable:
        """Decorator to add error handling to any function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                recovery_result = self.handle_error(e, context, recovery_strategy)
                
                if recovery_result and recovery_result.get('retry'):
                    # Retry the operation
                    try:
                        return func(*args, **kwargs)
                    except Exception as retry_error:
                        self.logger.error(f"Retry failed: {retry_error}")
                        return default_return
                
                return default_return
        
        return wrapper
    
    def safe_execute(self, func: Callable, *args, context: str = "", 
                    default_return: Any = None, **kwargs) -> Any:
        """Safely execute a function with error handling."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            recovery_result = self.handle_error(e, context)
            
            if recovery_result and recovery_result.get('retry'):
                try:
                    return func(*args, **kwargs)
                except Exception as retry_error:
                    self.logger.error(f"Retry failed: {retry_error}")
                    return default_return
            
            return default_return
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            'error_counts': self.error_counts.copy(),
            'last_errors': self.last_errors.copy(),
            'total_errors': sum(self.error_counts.values()),
            'unique_error_types': len(self.error_counts)
        }
    
    def clear_error_stats(self):
        """Clear error statistics."""
        self.error_counts.clear()
        self.last_errors.clear()


def with_error_recovery(context: str = "", recovery_strategy: Optional[str] = None, 
                       default_return: Any = None):
    """Decorator for adding error recovery to functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            return error_handler.safe_execute(
                func, *args, 
                context=context or func.__name__,
                default_return=default_return,
                **kwargs
            )
        return wrapper
    return decorator


def safe_import(module_name: str, fallback_value: Any = None) -> Any:
    """Safely import a module with fallback."""
    try:
        import importlib
        return importlib.import_module(module_name)
    except ImportError as e:
        error_handler = get_error_handler()
        error_handler.logger.warning(f"Failed to import {module_name}: {e}")
        return fallback_value


def safe_file_operation(operation: Callable, file_path: str, 
                       default_return: Any = None) -> Any:
    """Safely perform file operations with error handling."""
    error_handler = get_error_handler()
    
    try:
        return operation(file_path)
    except FileNotFoundError:
        error_handler.logger.warning(f"File not found: {file_path}")
        return default_return
    except PermissionError:
        error_handler.logger.warning(f"Permission denied: {file_path}")
        return default_return
    except Exception as e:
        error_handler.handle_error(e, f"file_operation_{file_path}")
        return default_return


def validate_and_recover_json(json_str: str, default_value: Any = None) -> Any:
    """Validate JSON and recover from corruption."""
    error_handler = get_error_handler()
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        error_handler.logger.warning(f"Invalid JSON, attempting recovery: {e}")
        
        # Try to fix common JSON issues
        try:
            # Remove trailing commas
            fixed_json = json_str.replace(',}', '}').replace(',]', ']')
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            # Try to extract partial data
            try:
                # Find the first complete object/array
                for i in range(len(json_str)):
                    try:
                        partial = json_str[:i+1]
                        return json.loads(partial)
                    except json.JSONDecodeError:
                        continue
            except:
                pass
        
        error_handler.logger.error("JSON recovery failed, using default value")
        return default_value


# Global error handler instance
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler
