"""
Centralized error handling for ΔΣ Guardian AI Client
Unified error management and recovery strategies
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling for AI client operations"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, datetime] = {}
    
    def handle_quota_error(self, error: Exception, model_name: str) -> str:
        """Handle API quota exceeded errors"""
        self._log_error('quota', model_name, str(error))
        
        error_msg = f"⚠️ Quota exceeded for {model_name}, switching model..."
        logger.warning(error_msg)
        
        return "QUOTA_EXCEEDED"
    
    def handle_tool_error(self, error: Exception, tool_name: str) -> str:
        """Handle tool execution errors"""
        self._log_error('tool', tool_name, str(error))
        
        if "does not exist" in str(error):
            return f"Tool '{tool_name}' does not exist. Use only the tools listed in the prompt."
        elif "Invalid arguments" in str(error):
            return f"Invalid arguments for {tool_name}. Check the tool usage examples."
        else:
            return f"Error executing {tool_name}: {str(error)}"
    
    def handle_file_error(self, error: Exception, operation: str, path: str) -> str:
        """Handle file operation errors"""
        self._log_error('file', operation, str(error))
        
        if "No such file or directory" in str(error):
            return f"File not found: {path}. Use smart path resolution or check the path."
        elif "Permission denied" in str(error):
            return f"Permission denied for {path}. Check file permissions."
        else:
            return f"File operation error ({operation}): {str(error)}"
    
    def handle_model_error(self, error: Exception, model_name: str) -> str:
        """Handle model-specific errors"""
        self._log_error('model', model_name, str(error))
        
        if "429" in str(error):
            return self.handle_quota_error(error, model_name)
        elif "timeout" in str(error).lower():
            return f"Model {model_name} timed out. Retrying with different model..."
        else:
            return f"Model error ({model_name}): {str(error)}"
    
    def handle_network_error(self, error: Exception, operation: str) -> str:
        """Handle network-related errors"""
        self._log_error('network', operation, str(error))
        
        if "timeout" in str(error).lower():
            return f"Network timeout during {operation}. Please try again."
        elif "connection" in str(error).lower():
            return f"Network connection error during {operation}. Check your internet connection."
        else:
            return f"Network error during {operation}: {str(error)}"
    
    def _log_error(self, error_type: str, context: str, message: str):
        """Log error with context"""
        key = f"{error_type}:{context}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        self.last_errors[key] = datetime.now()
        
        logger.error(f"❌ {error_type.upper()} ERROR in {context}: {message}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            'error_counts': self.error_counts,
            'last_errors': {k: v.isoformat() for k, v in self.last_errors.items()}
        }
    
    def reset_errors(self):
        """Reset error tracking"""
        self.error_counts.clear()
        self.last_errors.clear()

# Global error handler instance
error_handler = ErrorHandler() 