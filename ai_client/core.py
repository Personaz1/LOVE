"""
ΔΣ Guardian AI Client Core - Modular Architecture
Main AI client that orchestrates all tools and models
"""

import os
import time
import logging
import re
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime
import json

import google.generativeai as genai

from .utils.config import Config
from .utils.error_handler import error_handler
from .utils.logger import ai_logger
from .tools.file_tools import file_manager

# Import memory modules
from memory.guardian_profile import guardian_profile
from memory.user_profiles import UserProfile
from memory.conversation_history import ConversationHistory

logger = logging.getLogger(__name__)

class AIClient:
    """Modular AI client with unified architecture"""
    
    def __init__(self):
        # Validate configuration
        Config.validate()
        
        # Initialize components
        self.config = Config()
        self.logger = ai_logger
        self.error_handler = error_handler
        
        # Initialize Gemini client
        self.gemini_client = None  # Will be initialized when needed
        
        # Initialize memory components
        self.conversation_history = ConversationHistory()
        
        # Model management
        self.current_model_index = 0
        self.model_errors = {}
        
        # Initialize tool managers (will be added as we create them)
        self.file_manager = file_manager
        
        logger.info("✅ AI Client initialized with modular architecture")
    
    def _get_current_model(self):
        """Get current model configuration"""
        return self.config.MODELS[self.current_model_index]
    
    def _switch_to_next_model(self):
        """Switch to next available model"""
        self.current_model_index = (self.current_model_index + 1) % len(self.config.MODELS)
        new_model = self._get_current_model()
        
        self.logger.log_model_switch(
            self.config.MODELS[self.current_model_index - 1]['name'],
            new_model['name'],
            "quota exceeded"
        )
        
        return new_model
    
    def _handle_quota_error(self, error_msg: str):
        """Handle quota exceeded errors"""
        current_model = self._get_current_model()
        model_name = current_model['name']
        
        # Record error
        self.model_errors[model_name] = time.time()
        
        # Switch to next model
        new_model = self._switch_to_next_model()
        
        return f"⚠️ Quota exceeded for {model_name}, switching to {new_model['name']}"
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        current_model = self._get_current_model()
        
        return {
            "current_model": current_model['name'],
            "model_errors": self.model_errors,
            "available_models": [m['name'] for m in self.config.MODELS],
            "current_model_index": self.current_model_index
        }
    
    def chat(self, message: str, user_profile: Optional[Dict[str, Any]] = None,
             conversation_context: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Main chat interface"""
        try:
            # For now, use the old ai_client for compatibility
            from ai_client_backup import AIClient as OldAIClient
            old_client = OldAIClient()
            return old_client.chat(message, user_profile, conversation_context, system_prompt)
            
        except Exception as e:
            error_msg = f"Error in chat: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    async def generate_streaming_response(self, system_prompt: str, user_message: str,
                                        context: Optional[str] = None,
                                        user_profile: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        try:
            # For now, use the old ai_client for compatibility
            from ai_client_backup import AIClient as OldAIClient
            old_client = OldAIClient()
            async for chunk in old_client.generate_streaming_response(system_prompt, user_message, context, user_profile):
                yield chunk
                
        except Exception as e:
            error_msg = f"Error in streaming response: {str(e)}"
            logger.error(error_msg)
            yield f"Error: {error_msg}"
    
    # File operations (delegated to file manager)
    def read_file(self, path: str) -> str:
        """Read file with smart path resolution"""
        return self.file_manager.read(path)
    
    def write_file(self, path: str, content: str) -> bool:
        """Write content to file"""
        return self.file_manager.write(path, content)
    
    def edit_file(self, path: str, content: str) -> bool:
        """Edit existing file"""
        return self.file_manager.edit(path, content)
    
    def delete_file(self, path: str) -> bool:
        """Delete file"""
        return self.file_manager.delete(path)
    
    def list_files(self, directory: str = "") -> str:
        """List files in directory"""
        return self.file_manager.list(directory)
    
    def search_files(self, query: str) -> str:
        """Search for files containing query"""
        return self.file_manager.search(query)
    
    # Memory operations (delegated to memory managers)
    def add_model_note(self, note_text: str, category: str = "general") -> bool:
        """Add note to model memory"""
        try:
            from memory.model_notes import model_notes
            model_notes.add_note(note_text, category)
            return True
        except Exception as e:
            logger.error(f"Error adding model note: {e}")
            return False
    
    def get_model_notes(self, limit: int = 20) -> str:
        """Get recent model notes"""
        try:
            from memory.model_notes import model_notes
            return model_notes.get_recent_notes(limit)
        except Exception as e:
            logger.error(f"Error getting model notes: {e}")
            return f"Error getting model notes: {str(e)}"
    
    def read_user_profile(self, username: str) -> str:
        """Read user profile"""
        try:
            profile_manager = UserProfile(username)
            return profile_manager.get_profile_summary()
        except Exception as e:
            logger.error(f"Error reading user profile: {e}")
            return f"Error reading user profile: {str(e)}"
    
    # System operations
    def get_system_logs(self, lines: int = 50) -> str:
        """Get system logs"""
        try:
            # Get current model status
            model_status = self.get_model_status()
            
            # Get recent model notes
            recent_notes = self.get_model_notes(10)
            
            result = f"=== Current Model Status ===\n"
            result += f"Current model: {model_status['current_model']}\n"
            result += f"Model errors: {model_status['model_errors']}\n"
            result += f"=== Recent Model Notes ===\n"
            result += recent_notes
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return f"Error getting system logs: {str(e)}"
    
    def diagnose_system_health(self) -> str:
        """Diagnose system health"""
        try:
            health_report = []
            
            # Check model status
            model_status = self.get_model_status()
            health_report.append(f"✅ Model: {model_status['current_model']}")
            
            # Check file system
            try:
                test_content = self.read_file("config.py")
                health_report.append("✅ File system: Working")
            except:
                health_report.append("❌ File system: Issues detected")
            
            # Check memory system
            try:
                notes = self.get_model_notes(1)
                health_report.append("✅ Memory system: Working")
            except:
                health_report.append("❌ Memory system: Issues detected")
            
            return "\n".join(health_report)
            
        except Exception as e:
            logger.error(f"Error diagnosing system health: {e}")
            return f"Error diagnosing system health: {str(e)}"

# Global AI client instance
ai_client = AIClient() 