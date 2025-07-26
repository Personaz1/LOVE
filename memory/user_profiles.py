import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

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

class UserProfile:
    """User profile with emotional history tracking"""
    
    def __init__(self, username: str):
        self.username = username
        self.profile_file = f"memory/user_profiles/{username}_profile.json"
        self.emotional_history_file = f"memory/user_profiles/{username}_emotions.json"
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Ensure profile and emotional history files exist"""
        os.makedirs("memory/user_profiles", exist_ok=True)
        
        # Create profile file if it doesn't exist
        if not os.path.exists(self.profile_file):
            default_profile = {
                "username": self.username,
                "profile": "",
                "relationship_status": "Not specified",
                "current_feeling": "Not specified",
                "last_updated": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            self._save_profile(default_profile)
        
        # Create emotional history file if it doesn't exist
        if not os.path.exists(self.emotional_history_file):
            default_history = {
                "username": self.username,
                "emotional_history": [],
                "created_at": datetime.now().isoformat()
            }
            self._save_emotional_history(default_history)
    
    def _save_profile(self, profile_data: Dict[str, Any]):
        """Save profile data to file"""
        try:
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving profile for {self.username}: {e}")
    
    def _save_emotional_history(self, history_data: Dict[str, Any]):
        """Save emotional history to file"""
        try:
            with open(self.emotional_history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving emotional history for {self.username}: {e}")
    
    def _load_profile(self) -> Dict[str, Any]:
        """Load profile data from file"""
        try:
            with open(self.profile_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading profile for {self.username}: {e}")
            return {}
    
    def _load_emotional_history(self) -> Dict[str, Any]:
        """Load emotional history from file"""
        try:
            with open(self.emotional_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading emotional history for {self.username}: {e}")
            return {"emotional_history": []}
    
    def get_profile(self) -> Dict[str, Any]:
        """Get current profile"""
        return self._load_profile()
    
    def get_emotional_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent emotional history"""
        history_data = self._load_emotional_history()
        emotional_history = history_data.get("emotional_history", [])
        return emotional_history[-limit:] if limit > 0 else emotional_history
    
    def update_current_feeling(self, feeling: str, context: str = "") -> bool:
        """Update current feeling and add to emotional history"""
        try:
            # Load current profile
            profile = self._load_profile()
            old_feeling = profile.get("current_feeling", "Not specified")
            
            # Update profile
            profile["current_feeling"] = feeling
            profile["last_updated"] = datetime.now().isoformat()
            self._save_profile(profile)
            
            # Add to emotional history
            history_data = self._load_emotional_history()
            emotional_history = history_data.get("emotional_history", [])
            
            emotion_entry = {
                "feeling": feeling,
                "previous_feeling": old_feeling,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M")
            }
            
            emotional_history.append(emotion_entry)
            history_data["emotional_history"] = emotional_history
            history_data["last_updated"] = datetime.now().isoformat()
            
            self._save_emotional_history(history_data)
            
            logger.info(f"💭 Updated feeling for {self.username}: {old_feeling} -> {feeling}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating feeling for {self.username}: {e}")
            return False
    
    def get_emotional_trends(self) -> Dict[str, Any]:
        """Analyze emotional trends"""
        try:
            emotional_history = self.get_emotional_history(limit=30)  # Last 30 entries
            
            if not emotional_history:
                return {"trend": "No data", "most_common": "No data", "recent_changes": []}
            
            # Count feelings
            feeling_counts = {}
            for entry in emotional_history:
                feeling = entry.get("feeling", "Unknown")
                feeling_counts[feeling] = feeling_counts.get(feeling, 0) + 1
            
            # Find most common feeling
            most_common = max(feeling_counts.items(), key=lambda x: x[1])[0] if feeling_counts else "No data"
            
            # Get recent changes (last 5)
            recent_changes = emotional_history[-5:] if len(emotional_history) >= 5 else emotional_history
            
            # Determine trend
            if len(emotional_history) >= 2:
                recent_feeling = emotional_history[-1].get("feeling", "")
                previous_feeling = emotional_history[-2].get("feeling", "")
                
                positive_feelings = ["Happy", "Joyful", "Feeling great", "Content", "Calm"]
                negative_feelings = ["Sad", "Feeling bad", "Angry", "Anxious", "Nervous"]
                
                if recent_feeling in positive_feelings and previous_feeling in negative_feelings:
                    trend = "Improving"
                elif recent_feeling in negative_feelings and previous_feeling in positive_feelings:
                    trend = "Declining"
                else:
                    trend = "Stable"
            else:
                trend = "New user"
            
            return {
                "trend": trend,
                "most_common": most_common,
                "recent_changes": recent_changes,
                "total_entries": len(emotional_history)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing emotional trends for {self.username}: {e}")
            return {"trend": "Error", "most_common": "Error", "recent_changes": []}
    
    # Diary methods
    def get_diary_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent diary entries for the user"""
        try:
            file_path = f"memory/user_profiles/{self.username}_diary.json"
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    entries = json.load(f)
                    return entries[-limit:] if limit > 0 else entries
            else:
                # Return default entry if file doesn't exist
                return [{
                    "content": "Hi Diary",
                    "timestamp": datetime.now().isoformat(),
                    "mood": "Reflective"
                }]
        except Exception as e:
            logger.error(f"Error loading diary entries for {self.username}: {e}")
            return [{
                "content": "Hi Diary",
                "timestamp": datetime.now().isoformat(),
                "mood": "Reflective"
            }]
    
    def add_diary_entry(self, entry_data: Dict[str, Any]):
        """Add diary entry for the user"""
        try:
            file_path = f"memory/user_profiles/{self.username}_diary.json"
            
            # Load existing entries
            entries = []
            if os.path.exists(file_path):
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
            logger.error(f"Error adding diary entry for {self.username}: {e}")
            return False
    
    def update_diary_entry(self, index: int, new_content: str):
        """Update diary entry at specific index"""
        try:
            file_path = f"memory/user_profiles/{self.username}_diary.json"
            
            if not os.path.exists(file_path):
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
            logger.error(f"Error updating diary entry for {self.username}: {e}")
            return False
    
    def delete_diary_entry(self, index: int):
        """Delete diary entry at specific index"""
        try:
            file_path = f"memory/user_profiles/{self.username}_diary.json"
            
            if not os.path.exists(file_path):
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
            logger.error(f"Error deleting diary entry for {self.username}: {e}")
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