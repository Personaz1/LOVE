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
            print(f"Error updating feeling for {self.username}: {e}")
            return False

class UserProfile:
    """Advanced user profile with emotional history and diary"""
    
    def __init__(self, username: str):
        self.username = username
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Ensure all necessary files exist"""
        # Create directory if it doesn't exist
        os.makedirs("memory/user_profiles", exist_ok=True)
        
        # Initialize profile file
        profile_file = f"memory/user_profiles/{self.username}.json"
        if not os.path.exists(profile_file):
            default_profile = {
                "username": self.username,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "profile": "Tell me about yourself...",
                "hidden_profile": "Model's private notes about this user...",
                "relationship_status": "In a relationship",
                "current_feeling": "Not specified"
            }
            self._save_profile(default_profile)
        
        # Initialize emotional history file
        history_file = f"memory/user_profiles/{self.username}_emotions.json"
        if not os.path.exists(history_file):
            default_history = {
                "username": self.username,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "emotional_history": []
            }
            self._save_emotional_history(default_history)
        
        # Initialize diary file with test entry
        diary_file = f"memory/user_profiles/{self.username}_diary.json"
        if not os.path.exists(diary_file):
            test_entries = [
                {
                    "content": "Привет, дневник! Это моя первая запись.",
                    "timestamp": datetime.now().isoformat(),
                    "mood": "Curious"
                },
                {
                    "content": "Сегодня я чувствую себя хорошо. Хочу записать свои мысли.",
                    "timestamp": datetime.now().isoformat(),
                    "mood": "Happy"
                }
            ]
            with open(diary_file, 'w', encoding='utf-8') as f:
                json.dump(test_entries, f, indent=2, ensure_ascii=False)
        
        # Initialize relationship insights file
        insights_file = f"memory/user_profiles/relationship_insights.json"
        if not os.path.exists(insights_file):
            default_insights = {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "insights": []
            }
            with open(insights_file, 'w', encoding='utf-8') as f:
                json.dump(default_insights, f, indent=2, ensure_ascii=False)
    
    def _save_profile(self, profile_data: Dict[str, Any]):
        """Save profile to file"""
        try:
            profile_data["last_updated"] = datetime.now().isoformat()
            with open(f"memory/user_profiles/{self.username}.json", 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving profile for {self.username}: {e}")
    
    def _save_emotional_history(self, history_data: Dict[str, Any]):
        """Save emotional history to file"""
        try:
            history_data["last_updated"] = datetime.now().isoformat()
            with open(f"memory/user_profiles/{self.username}_emotions.json", 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving emotional history for {self.username}: {e}")
    
    def _load_profile(self) -> Dict[str, Any]:
        """Load profile from file"""
        try:
            with open(f"memory/user_profiles/{self.username}.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading profile for {self.username}: {e}")
            return {}
    
    def _load_emotional_history(self) -> Dict[str, Any]:
        """Load emotional history from file"""
        try:
            with open(f"memory/user_profiles/{self.username}_emotions.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading emotional history for {self.username}: {e}")
            return {"emotional_history": []}
    
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile"""
        return self._load_profile()
    
    def get_emotional_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent emotional history"""
        try:
            history_data = self._load_emotional_history()
            emotional_history = history_data.get("emotional_history", [])
            
            # Ensure it's a list
            if not isinstance(emotional_history, list):
                emotional_history = []
            
            # Return last N entries
            if limit > 0 and len(emotional_history) > limit:
                return emotional_history[-limit:]
            return emotional_history
        except Exception as e:
            logger.error(f"Error getting emotional history for {self.username}: {e}")
            return []
    
    def update_current_feeling(self, feeling: str, context: str = "") -> bool:
        """Update user's current emotional state"""
        try:
            # Update profile
            profile = self._load_profile()
            old_feeling = profile.get("current_feeling", "Not specified")
            profile["current_feeling"] = feeling
            self._save_profile(profile)
            
            # Add to emotional history
            history_data = self._load_emotional_history()
            emotional_history = history_data.get("emotional_history", [])
            
            # Ensure it's a list
            if not isinstance(emotional_history, list):
                emotional_history = []
            
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
    
    def update_relationship_status(self, status: str) -> bool:
        """Update relationship status"""
        try:
            profile = self._load_profile()
            profile["relationship_status"] = status
            self._save_profile(profile)
            logger.info(f"💕 Updated relationship status for {self.username}: {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating relationship status for {self.username}: {e}")
            return False
    
    def update_user_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Update user profile with new data"""
        try:
            profile = self._load_profile()
            profile.update(profile_data)
            self._save_profile(profile)
            logger.info(f"👤 Updated profile for {self.username}")
            return True
        except Exception as e:
            logger.error(f"Error updating profile for {self.username}: {e}")
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
    

            
            # Load existing entries
            with open(file_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)
                
                # Ensure entries is a list
                if not isinstance(entries, list):
                    return False
            
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
    
    def add_relationship_insight(self, insight: str) -> bool:
        """Add relationship insight"""
        try:
            file_path = f"memory/user_profiles/relationship_insights.json"
            
            # Load existing insights
            insights_data = {}
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    insights_data = json.load(f)
            
            # Ensure insights is a list
            insights = insights_data.get("insights", [])
            if not isinstance(insights, list):
                insights = []
            
            # Add new insight
            new_insight = {
                "insight": insight,
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M")
            }
            insights.append(new_insight)
            
            # Update data
            insights_data["insights"] = insights
            insights_data["last_updated"] = datetime.now().isoformat()
            
            # Save back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(insights_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💡 Added relationship insight: {insight[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error adding relationship insight: {e}")
            return False
    
    def read_user_profile(self, username: str) -> str:
        """Read user's profile information"""
        try:
            profile = self.get_profile()
            return json.dumps(profile, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error reading profile for {username}: {e}")
            return f"Error reading profile: {str(e)}"
    
    def read_emotional_history(self, username: str) -> str:
        """Read user's emotional history"""
        try:
            history = self.get_emotional_history(limit=20)
            return json.dumps(history, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error getting emotional history: {e}")
            return f"Error reading emotional history: {str(e)}"
    


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
            stepan_profile.update_profile("Stepan Egoshin - passionate about technology, AI, and innovation. Loves deep conversations and building meaningful connections.")
            stepan_profile.update_hidden_profile("Stepan shows strong analytical thinking and prefers direct communication. He values intellectual growth and meaningful relationships.")
        
        # Create Meranda profile
        meranda_profile = SimpleUserProfile("meranda", self.profile_dir)
        if not meranda_profile.profile_file.exists():
            meranda_profile.update_profile("Meranda - creative and empathetic soul who loves art, music, and deep emotional connections. Values authenticity and open communication.")
            meranda_profile.update_hidden_profile("Meranda is highly intuitive and emotionally intelligent. She needs reassurance and values quality time in relationships.")
    
    def get_user_profile(self, username: str) -> Optional[SimpleUserProfile]:
        """Get user profile by username"""
        try:
            profile_file = self.profile_dir / f"{username}.json"
            if profile_file.exists():
                return SimpleUserProfile(username, self.profile_dir)
            return None
        except Exception as e:
            print(f"Error getting user profile for {username}: {e}")
            return None
    
    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all user profiles"""
        profiles = {}
        try:
            for profile_file in self.profile_dir.glob("*.json"):
                if not profile_file.name.endswith(("_emotions.json", "_insights.json")):
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
                if not profile_file.name.endswith(("_emotions.json", "_insights.json")):
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
        """Delete user profile and all associated files"""
        try:
            # Delete main profile
            profile_file = self.profile_dir / f"{username}.json"
            if profile_file.exists():
                profile_file.unlink()
            
            # Delete emotional history
            emotions_file = self.profile_dir / f"{username}_emotions.json"
            if emotions_file.exists():
                emotions_file.unlink()
            

            
            return True
        except Exception as e:
            print(f"Error deleting user {username}: {e}")
            return False
    
    def list_users(self) -> List[str]:
        """List all usernames"""
        try:
            users = []
            for profile_file in self.profile_dir.glob("*.json"):
                if not profile_file.name.endswith(("_emotions.json", "_insights.json")):
                    users.append(profile_file.stem)
            return users
        except Exception as e:
            print(f"Error listing users: {e}")
            return []
    


    def update_hidden_profile(self, username: str, hidden_profile_data: Dict[str, Any]) -> bool:
        """Update user's hidden profile (model's private notes)"""
        try:
            profile = self.get_user_profile(username)
            if profile:
                return profile.update_hidden_profile(hidden_profile_data)
            return False
        except Exception as e:
            logger.error(f"Error updating hidden profile for {username}: {e}")
            return False
    
    def read_hidden_profile(self, username: str) -> str:
        """Read user's hidden profile"""
        try:
            profile = self.get_user_profile(username)
            if profile:
                return json.dumps(profile.get_hidden_profile(), indent=2, ensure_ascii=False)
            return "Profile not found"
        except Exception as e:
            logger.error(f"Error reading hidden profile for {username}: {e}")
            return f"Error reading hidden profile: {str(e)}"

# Global instance
profile_manager = UserProfileManager() 