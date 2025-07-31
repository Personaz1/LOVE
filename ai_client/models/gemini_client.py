"""
Gemini Client for ΔΣ Guardian AI
Handles all interactions with Google Gemini models
"""

import os
import time
import logging
import re
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime
import json

import google.generativeai as genai

from ..utils.config import Config
from ..utils.error_handler import error_handler
from ..utils.logger import ai_logger

logger = logging.getLogger(__name__)

class GeminiClient:
    """Gemini model client with quota management and error handling"""
    
    def __init__(self):
        # Initialize Gemini
        self.config = Config()
        genai.configure(api_key=self.config.GEMINI_API_KEY)
        
        # Model management
        self.current_model_index = 0
        self.model_errors = {}
        
        # Initialize models
        self.models = {}
        for model_config in self.config.MODELS:
            try:
                model = genai.GenerativeModel(model_config['name'])
                self.models[model_config['name']] = model
            except Exception as e:
                logger.error(f"Failed to initialize model {model_config['name']}: {e}")
        
        logger.info("✅ Gemini client initialized")
    
    def _get_current_model(self):
        """Get current model"""
        model_config = self.config.MODELS[self.current_model_index]
        model_name = model_config['name']
        return self.models.get(model_name)
    
    def _switch_to_next_model(self):
        """Switch to next available model"""
        self.current_model_index = (self.current_model_index + 1) % len(self.config.MODELS)
        new_model_config = self.config.MODELS[self.current_model_index]
        
        ai_logger.log_model_switch(
            self.config.MODELS[self.current_model_index - 1]['name'],
            new_model_config['name'],
            "quota exceeded"
        )
        
        return self.models.get(new_model_config['name'])
    
    def _handle_quota_error(self, error: Exception, model_name: str):
        """Handle quota exceeded errors"""
        # Record error
        self.model_errors[model_name] = time.time()
        
        # Switch to next model
        new_model = self._switch_to_next_model()
        
        if new_model:
            return new_model
        else:
            raise Exception("No available models")
    
    def generate_response(self, message: str, user_profile: Optional[Dict[str, Any]] = None,
                         context: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Generate response using current model"""
        max_retries = len(self.config.MODELS)
        
        for attempt in range(max_retries):
            try:
                model = self._get_current_model()
                if not model:
                    raise Exception("No model available")
                
                # Build prompt
                prompt = self._build_prompt(message, user_profile, context, system_prompt)
                
                # Generate response
                response = model.generate_content(prompt)
                
                if response.text:
                    return response.text
                else:
                    return "No response generated"
                    
            except Exception as e:
                error_msg = str(e)
                
                if "429" in error_msg or "quota" in error_msg.lower():
                    # Quota exceeded, try next model
                    try:
                        self._handle_quota_error(e, self.config.MODELS[self.current_model_index]['name'])
                        continue
                    except Exception as switch_error:
                        return f"All models exhausted: {str(switch_error)}"
                else:
                    # Other error
                    return f"Model error: {error_msg}"
        
        return "All models failed"
    
    async def generate_streaming_response(self, system_prompt: str, user_message: str,
                                        context: Optional[str] = None,
                                        user_profile: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        max_retries = len(self.config.MODELS)
        
        for attempt in range(max_retries):
            try:
                model = self._get_current_model()
                if not model:
                    raise Exception("No model available")
                
                # Build prompt
                prompt = self._build_prompt(user_message, user_profile, context, system_prompt)
                
                # Generate streaming response
                response = model.generate_content(prompt, stream=True)
                
                total_chunks = 0
                tool_calls = []
                
                async for chunk in response:
                    if chunk.text:
                        total_chunks += 1
                        yield chunk.text
                    
                    # Check for tool calls
                    if hasattr(chunk, 'candidates') and chunk.candidates:
                        for candidate in chunk.candidates:
                            if hasattr(candidate, 'content') and candidate.content:
                                for part in candidate.content.parts:
                                    if hasattr(part, 'function_call'):
                                        tool_calls.append(part.function_call)
                
                # Log completion
                ai_logger.log_info(f"🌐 Multi-step streaming completed in {time.time():.2f}s")
                ai_logger.log_info(f"📊 Total chunks received: {total_chunks}")
                
                return
                
            except Exception as e:
                error_msg = str(e)
                
                if "429" in error_msg or "quota" in error_msg.lower():
                    # Quota exceeded, try next model
                    try:
                        self._handle_quota_error(e, self.config.MODELS[self.current_model_index]['name'])
                        continue
                    except Exception as switch_error:
                        yield f"All models exhausted: {str(switch_error)}"
                        return
                else:
                    # Other error
                    yield f"Model error: {error_msg}"
                    return
        
        yield "All models failed"
    
    def _build_prompt(self, message: str, user_profile: Optional[Dict[str, Any]] = None,
                      context: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Build complete prompt for model"""
        # Use provided system prompt or default
        if not system_prompt:
            from prompts.guardian_prompt import AI_GUARDIAN_SYSTEM_PROMPT
            system_prompt = AI_GUARDIAN_SYSTEM_PROMPT
        
        # Build context
        context_parts = []
        
        if context:
            context_parts.append(f"CONTEXT:\n{context}")
        
        if user_profile:
            profile_text = json.dumps(user_profile, indent=2)
            context_parts.append(f"USER PROFILE:\n{profile_text}")
        
        # Combine all parts
        full_prompt = f"{system_prompt}\n\n"
        
        if context_parts:
            full_prompt += "\n\n".join(context_parts) + "\n\n"
        
        full_prompt += f"USER MESSAGE:\n{message}\n\nRESPONSE:"
        
        return full_prompt
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        current_model_config = self.config.MODELS[self.current_model_index]
        
        return {
            "current_model": current_model_config['name'],
            "model_errors": self.model_errors,
            "available_models": [m['name'] for m in self.config.MODELS],
            "current_model_index": self.current_model_index
        } 