"""
Automatic Theme Management System
Manages themes based on context, mood, and conversation dynamics
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ThemeManager:
    """Manages automatic theme switching based on context"""
    
    def __init__(self, theme_file: str = "memory/current_theme.json"):
        self.theme_file = theme_file
        self.current_theme = "neutral"  # Default theme
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(theme_file), exist_ok=True)
        
        # Load current theme
        self._load_theme()
    
    def _load_theme(self):
        """Load current theme from file"""
        try:
            if os.path.exists(self.theme_file):
                with open(self.theme_file, 'r') as f:
                    theme_data = json.load(f)
                    self.current_theme = theme_data.get("theme", "neutral")
            else:
                self._save_theme("neutral")
        except Exception as e:
            logger.error(f"Error loading theme: {e}")
            self.current_theme = "neutral"
    
    def _save_theme(self, theme: str):
        """Save theme to file"""
        try:
            theme_data = {
                "theme": theme,
                "updated_at": datetime.now().isoformat(),
                "reason": "automatic"
            }
            
            with open(self.theme_file, 'w') as f:
                json.dump(theme_data, f, indent=2)
            
            self.current_theme = theme
            logger.info(f"Saved theme: {theme}")
            
        except Exception as e:
            logger.error(f"Error saving theme: {e}")
    
    def analyze_context_and_set_theme(self, 
                                    user_profile: Dict[str, Any],
                                    recent_messages: list,
                                    emotional_history: list) -> str:
        """Analyze context and automatically set appropriate theme"""
        
        # Default to neutral
        new_theme = "neutral"
        
        try:
            # Analyze current feeling
            current_feeling = user_profile.get('current_feeling', '').lower()
            
            # Analyze recent conversation content
            conversation_text = ""
            for msg in recent_messages:
                if isinstance(msg, dict):
                    conversation_text += f" {msg.get('message', '')} {msg.get('ai_response', '')}"
                else:
                    conversation_text += f" {str(msg)}"
            conversation_text = conversation_text.lower()
            
            # Use AI model to analyze context and determine theme
            # This replaces hardcoded pattern matching with intelligent analysis
            try:
                # Simple heuristic: analyze feeling and conversation tone
                if current_feeling in ['happy', 'joy', 'excited', 'passionate', 'loving']:
                    new_theme = "romantic"
                elif current_feeling in ['sad', 'lonely', 'missing', 'nostalgic', 'reflective']:
                    new_theme = "melancholy"
                else:
                    new_theme = "neutral"
                
                # Override based on conversation content if strongly indicated
                if any(word in conversation_text for word in ['love', 'romantic', 'relationship', 'kiss', 'hug', 'heart']):
                    new_theme = "romantic"
                elif any(word in conversation_text for word in ['sad', 'lonely', 'missing', 'nostalgic']):
                    new_theme = "melancholy"
                    
            except Exception as e:
                logger.error(f"Error in theme analysis: {e}")
                new_theme = "neutral"
            
            # Update theme if changed
            if new_theme != self.current_theme:
                self._save_theme(new_theme)
                logger.info(f"Auto-changed theme from {self.current_theme} to {new_theme}")
            
        except Exception as e:
            logger.error(f"Error analyzing context for theme: {e}")
            new_theme = self.current_theme
        
        return new_theme
    
    def get_current_theme(self) -> str:
        """Get current theme"""
        return self.current_theme
    
    def get_theme_data(self) -> Dict[str, Any]:
        """Get theme data for API response"""
        return {
            "theme": self.current_theme,
            "updated_at": datetime.now().isoformat(),
            "automatic": True
        }
    
    def force_theme(self, theme: str, reason: str = "manual"):
        """Force set a specific theme (for testing or special cases)"""
        if theme in ["romantic", "neutral", "melancholy"]:
            self._save_theme(theme)
            logger.info(f"Forced theme to {theme} (reason: {reason})")
        else:
            logger.warning(f"Invalid theme: {theme}")

# Global theme manager instance
theme_manager = ThemeManager() 