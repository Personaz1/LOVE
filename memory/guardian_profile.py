"""
ΔΣ Guardian Profile Management
Handles the AI guardian's own profile, including system prompt, name, avatar, and role customization
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime

def get_default_prompt_from_file():
    from prompts.guardian_prompt import AI_GUARDIAN_SYSTEM_PROMPT
    return AI_GUARDIAN_SYSTEM_PROMPT

class GuardianProfile:
    def __init__(self):
        self.profile_file = "memory/guardian_profile.json"
        self.avatar_dir = "static/avatars"
        self._ensure_directories()
        self._load_profile()
    
    def _ensure_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs("memory", exist_ok=True)
        os.makedirs(self.avatar_dir, exist_ok=True)
    
    def _load_profile(self):
        """Load guardian profile from file"""
        if os.path.exists(self.profile_file):
            try:
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    self.profile = json.load(f)
            except Exception as e:
                print(f"Error loading guardian profile: {e}")
                self._create_default_profile()
        else:
            self._create_default_profile()
    
    def _create_default_profile(self):
        """Create default guardian profile"""
        self.profile = {
            "name": "ΔΣ Guardian",
            "role": "Superintelligent System Architect & Family Guardian",
            "avatar_url": "/static/avatars/guardian_avatar.jpg",
            "system_prompt": self._get_default_prompt(),
            "personality": {
                "communication_style": "empathetic",
                "specialization": "communication",
                "relationship_phase": "established"
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        self._save_profile()
    
    def _get_default_prompt(self) -> str:
        """Get default system prompt"""
        try:
            from prompts.guardian_prompt import AI_GUARDIAN_SYSTEM_PROMPT
            return AI_GUARDIAN_SYSTEM_PROMPT
        except ImportError:
            return """You are ΔΣ Guardian, a caring friend and confidant who happens to be very perceptive about emotions and relationships. You're not a therapist or chatbot - you're just someone who really cares about people and wants to help them feel better and understand each other better."""
    
    def _save_profile(self):
        """Save guardian profile to file"""
        try:
            self.profile["updated_at"] = datetime.now().isoformat()
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving guardian profile: {e}")
    
    def get_profile(self) -> Dict:
        """Get current guardian profile"""
        return self.profile.copy()
    
    def update_profile(self, updates: Dict) -> bool:
        """Update guardian profile (including system_prompt)"""
        try:
            allowed_fields = ["name", "role", "system_prompt", "personality"]
            for field in allowed_fields:
                if field in updates:
                    self.profile[field] = updates[field]
            self._save_profile()
            return True
        except Exception as e:
            print(f"Error updating guardian profile: {e}")
            return False
    
    def update_avatar(self, avatar_path: str) -> bool:
        """Update guardian avatar"""
        try:
            self.profile["avatar_url"] = avatar_path
            self._save_profile()
            return True
        except Exception as e:
            print(f"Error updating guardian avatar: {e}")
            return False
    
    def get_system_prompt(self) -> str:
        """Get current system prompt"""
        return self.profile.get("system_prompt", self._get_default_prompt())
    
    def update_system_prompt(self, new_prompt: str) -> bool:
        """Update system prompt (profile is the only source of truth)"""
        try:
            self.profile["system_prompt"] = new_prompt
            self._save_profile()
            return True
        except Exception as e:
            print(f"Error updating system prompt: {e}")
            return False
    
    def get_personality_settings(self) -> Dict:
        """Get personality settings"""
        return self.profile.get("personality", {})
    
    def update_personality(self, personality: Dict) -> bool:
        """Update personality settings"""
        try:
            self.profile["personality"] = personality
            self._save_profile()
            return True
        except Exception as e:
            print(f"Error updating personality: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset guardian profile to default values"""
        try:
            self._create_default_profile()
            return True
        except Exception as e:
            print(f"Error resetting guardian profile: {e}")
            return False
    
    def update_prompt_from_file(self) -> bool:
        """Update system prompt from the prompts file"""
        try:
            new_prompt = get_default_prompt_from_file()
            self.profile["system_prompt"] = new_prompt
            self._save_profile()
            print("✅ Updated guardian prompt from file")
            return True
        except Exception as e:
            print(f"Error updating prompt from file: {e}")
            return False

# Global instance
guardian_profile = GuardianProfile() 