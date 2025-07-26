import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

class SimpleUserProfile:
    """Simple user profile - one file per user"""
    
    def __init__(self, username: str, profile_dir: Path = None):
        self.username = username
        self.profile_dir = profile_dir or Path("memory/user_profiles")
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.profile_file = self.profile_dir / f"{username}.json"
        
        # Initialize profile if doesn't exist
        if not self.profile_file.exists():
            self._create_default_profile()
    
    def _create_default_profile(self):
        """Create default profile"""
        default_profile = {
            "username": self.username,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "profile": "Tell me about yourself...",
            "hidden_profile": "Model's private notes about this user...",
            "relationship_status": "In a relationship",
            "current_feeling": "Happy and connected"
        }
        self._save_profile(default_profile)
    
    def _load_profile(self) -> Dict[str, Any]:
        """Load profile from file"""
        try:
            with open(self.profile_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading profile for {self.username}: {e}")
            return {}
    
    def _save_profile(self, profile_data: Dict[str, Any]):
        """Save profile to file"""
        try:
            profile_data["last_updated"] = datetime.now().isoformat()
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving profile for {self.username}: {e}")
    
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile (visible to user)"""
        return self._load_profile()
    
    def get_hidden_profile(self) -> Dict[str, Any]:
        """Get hidden profile (model's private notes)"""
        profile = self._load_profile()
        return {
            "username": profile.get("username", self.username),
            "hidden_profile": profile.get("hidden_profile", ""),
            "last_updated": profile.get("last_updated", "")
        }
    
    def update_profile(self, new_profile: str) -> bool:
        """Update user profile"""
        try:
            profile = self._load_profile()
            profile["profile"] = new_profile
            self._save_profile(profile)
            return True
        except Exception as e:
            print(f"Error updating profile for {self.username}: {e}")
            return False
    
    def update_hidden_profile(self, new_hidden_profile: str) -> bool:
        """Update hidden profile (model's private notes)"""
        try:
            profile = self._load_profile()
            profile["hidden_profile"] = new_hidden_profile
            self._save_profile(profile)
            return True
        except Exception as e:
            print(f"Error updating hidden profile for {self.username}: {e}")
            return False
    
    def update_relationship_status(self, status: str) -> bool:
        """Update relationship status"""
        try:
            profile = self._load_profile()
            profile["relationship_status"] = status
            self._save_profile(profile)
            return True
        except Exception as e:
            print(f"Error updating relationship status for {self.username}: {e}")
            return False
    
    def update_current_feeling(self, feeling: str) -> bool:
        """Update current feeling"""
        try:
            profile = self._load_profile()
            profile["current_feeling"] = feeling
            self._save_profile(profile)
            return True
        except Exception as e:
            print(f"Error updating current feeling for {self.username}: {e}")
            return False

class UserProfileManager:
    """Manager for all user profiles"""
    
    def __init__(self, profile_dir: Path = None):
        self.profile_dir = profile_dir or Path("memory/user_profiles")
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize default users
        self.initialize_default_users()
    
    def initialize_default_users(self):
        """Initialize default user profiles"""
        # Create Stepan profile
        stepan_profile = SimpleUserProfile("stepan", self.profile_dir)
        if not stepan_profile.profile_file.exists():
            stepan_profile.update_profile("Stepan Egoshin - passionate about technology and innovation. Love building things and exploring new ideas with Meranda.")
            stepan_profile.update_hidden_profile("Stepan is analytical and solution-oriented. He values deep conversations and intellectual connection. Sometimes needs help with emotional expression.")
        
        # Create Meranda profile
        meranda_profile = SimpleUserProfile("meranda", self.profile_dir)
        if not meranda_profile.profile_file.exists():
            meranda_profile.update_profile("Meranda Musser - creative and emotional soul. Love expressing feelings and creating beautiful moments with Stepan.")
            meranda_profile.update_hidden_profile("Meranda is deeply emotional and intuitive. She values emotional connection and creative expression. Sometimes needs reassurance and emotional support.")
    
    def get_user_profile(self, username: str) -> Optional[SimpleUserProfile]:
        """Get user profile by username"""
        try:
            return SimpleUserProfile(username, self.profile_dir)
        except Exception as e:
            print(f"Error getting profile for {username}: {e}")
            return None
    
    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all user profiles"""
        profiles = {}
        try:
            for profile_file in self.profile_dir.glob("*.json"):
                username = profile_file.stem
                profile = self.get_user_profile(username)
                if profile:
                    profiles[username] = profile.get_profile()
        except Exception as e:
            print(f"Error getting all profiles: {e}")
        return profiles
    
    def get_all_hidden_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all hidden profiles (model's private notes)"""
        hidden_profiles = {}
        try:
            for profile_file in self.profile_dir.glob("*.json"):
                username = profile_file.stem
                profile = self.get_user_profile(username)
                if profile:
                    hidden_profiles[username] = profile.get_hidden_profile()
        except Exception as e:
            print(f"Error getting all hidden profiles: {e}")
        return hidden_profiles
    
    def create_user(self, username: str, initial_profile: str = "") -> bool:
        """Create new user profile"""
        try:
            profile = SimpleUserProfile(username, self.profile_dir)
            if initial_profile:
                profile.update_profile(initial_profile)
            return True
        except Exception as e:
            print(f"Error creating user {username}: {e}")
            return False
    
    def delete_user(self, username: str) -> bool:
        """Delete user profile"""
        try:
            profile_file = self.profile_dir / f"{username}.json"
            if profile_file.exists():
                profile_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting user {username}: {e}")
            return False
    
    def list_users(self) -> List[str]:
        """List all users"""
        try:
            return [profile_file.stem for profile_file in self.profile_dir.glob("*.json")]
        except Exception as e:
            print(f"Error listing users: {e}")
            return []
    
    # Diary methods (keeping existing functionality)
    def get_diary_entries(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent diary entries for a user"""
        try:
            file_path = self.profile_dir / f"{username}_diary.json"
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    entries = json.load(f)
                    return entries[:limit]
            else:
                # Return default entry if file doesn't exist
                return [{
                    "content": "Hi Diary",
                    "timestamp": datetime.now().isoformat(),
                    "mood": "Reflective"
                }]
        except Exception as e:
            print(f"Error loading diary entries: {e}")
            return [{
                "content": "Hi Diary",
                "timestamp": datetime.now().isoformat(),
                "mood": "Reflective"
            }]
    
    def add_diary_entry(self, username: str, entry_data: Dict[str, Any]):
        """Add diary entry for user"""
        try:
            file_path = self.profile_dir / f"{username}_diary.json"
            
            # Load existing entries
            entries = []
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    entries = json.load(f)
            
            # Add new entry
            new_entry = {
                "content": entry_data.get("content", ""),
                "timestamp": entry_data.get("timestamp", datetime.now().isoformat()),
                "mood": entry_data.get("mood", "Reflective")
            }
            entries.append(new_entry)
            
            # Save back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error adding diary entry: {e}")
            return False
    
    def update_diary_entry(self, username: str, index: int, new_content: str):
        """Update diary entry at specific index"""
        try:
            file_path = self.profile_dir / f"{username}_diary.json"
            
            if not file_path.exists():
                return False
            
            # Load existing entries
            with open(file_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)
            
            # Check if index is valid
            if index < 0 or index >= len(entries):
                return False
            
            # Update the entry
            entries[index]["content"] = new_content
            entries[index]["timestamp"] = datetime.now().isoformat()
            
            # Save back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error updating diary entry: {e}")
            return False
    
    def delete_diary_entry(self, username: str, index: int):
        """Delete diary entry at specific index"""
        try:
            file_path = self.profile_dir / f"{username}_diary.json"
            
            if not file_path.exists():
                return False
            
            # Load existing entries
            with open(file_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)
            
            # Check if index is valid
            if index < 0 or index >= len(entries):
                return False
            
            # Remove the entry
            entries.pop(index)
            
            # Save back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error deleting diary entry: {e}")
            return False

# Global instance
profile_manager = UserProfileManager() 