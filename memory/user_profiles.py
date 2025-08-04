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
            "notes": "User notes...",
            
            
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
    

    

    


class UserProfile:
    """Advanced user profile"""
    
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


            }
            self._save_profile(default_profile)
        

    
    def _save_profile(self, profile_data: Dict[str, Any]):
        """Save profile to file"""
        try:
            profile_data["last_updated"] = datetime.now().isoformat()
            with open(f"memory/user_profiles/{self.username}.json", 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving profile for {self.username}: {e}")
    

    
    def _load_profile(self) -> Dict[str, Any]:
        """Load profile from file"""
        try:
            with open(f"memory/user_profiles/{self.username}.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading profile for {self.username}: {e}")
            return {}
    

    
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile"""
        return self._load_profile()
    

    

    

    
    def update_profile(self, new_profile_text: str) -> bool:
        """Update user profile text - treat as simple text field"""
        try:
            profile = self._load_profile()
            profile["profile"] = new_profile_text
            self._save_profile(profile)
            logger.info(f"👤 Updated profile text for {self.username}")
            return True
        except Exception as e:
            logger.error(f"Error updating profile for {self.username}: {e}")
            return False
    

    

    

    

    

    

    

    

    
    def read_user_profile(self, username: str) -> str:
        """Read user's profile information"""
        try:
            profile = self.get_profile()
            return json.dumps(profile, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error reading profile for {username}: {e}")
            return f"Error reading profile: {str(e)}"
    

    


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

        
        # Create Meranda profile
        meranda_profile = SimpleUserProfile("meranda", self.profile_dir)
        if not meranda_profile.profile_file.exists():
            meranda_profile.update_profile("Meranda - creative and empathetic soul who loves art, music, and deep emotional connections. Values authenticity and open communication.")

    
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
                # Only process main profile files, skip emotions, insights, etc.
                if (not profile_file.name.endswith(("_insights.json")) and 
                    not profile_file.name.startswith("relationship_")):
                    username = profile_file.stem
                    profile = self.get_user_profile(username)
                    if profile:
                        profiles[username] = profile.get_profile()
        except Exception as e:
            print(f"Error getting all profiles: {e}")
        return profiles
    

    
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
            

            

            
            return True
        except Exception as e:
            print(f"Error deleting user {username}: {e}")
            return False
    
    def list_users(self) -> List[str]:
        """List all usernames"""
        try:
            users = []
            for profile_file in self.profile_dir.glob("*.json"):
                if not profile_file.name.endswith(("_insights.json")):
                    users.append(profile_file.stem)
            return users
        except Exception as e:
            print(f"Error listing users: {e}")
            return []
    




# Global instance
profile_manager = UserProfileManager() 