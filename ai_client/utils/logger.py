"""
Enhanced logging system for ΔΣ Guardian AI Client
Structured logging with different levels and contexts
"""

import logging
import sys
from typing import Optional
from datetime import datetime

class AIClientLogger:
    """Enhanced logging for AI client operations"""
    
    def __init__(self, name: str = "ai_client"):
        self.logger = logging.getLogger(name)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler('app.log')
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Set level
        self.logger.setLevel(logging.INFO)
    
    def log_model_switch(self, from_model: str, to_model: str, reason: str = ""):
        """Log model switching"""
        msg = f"🔄 Switched from {from_model} to {to_model}"
        if reason:
            msg += f" (reason: {reason})"
        self.logger.info(msg)
    
    def log_tool_call(self, tool_name: str, args: str, result: str = ""):
        """Log tool execution"""
        self.logger.info(f"🔧 Executing tool call: {tool_name}({args})")
        if result:
            self.logger.info(f"✅ {tool_name} result: {result[:100]}...")
    
    def log_error(self, error_type: str, context: str, message: str):
        """Log errors with context"""
        self.logger.error(f"❌ {error_type.upper()} ERROR in {context}: {message}")
    
    def log_warning(self, message: str):
        """Log warnings"""
        self.logger.warning(f"⚠️ {message}")
    
    def log_info(self, message: str):
        """Log info messages"""
        self.logger.info(f"ℹ️ {message}")
    
    def log_success(self, message: str):
        """Log success messages"""
        self.logger.info(f"✅ {message}")
    
    def log_debug(self, message: str):
        """Log debug messages"""
        self.logger.debug(f"🐛 {message}")

# Global logger instance
ai_logger = AIClientLogger() 