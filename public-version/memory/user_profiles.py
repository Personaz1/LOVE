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
    

    

    
    def get_emotional_trends(self) -> Dict[str, Any]:
        """Analyze emotional trends and detect patterns"""
        try:
            emotional_history = self.get_emotional_history(limit=50)  # Last 50 entries
            
            if not emotional_history:
                return {"trend": "No data", "most_common": "No data", "recent_changes": [], "patterns": {}, "alerts": []}
            
            # Count feelings
            feeling_counts = {}
            for entry in emotional_history:
                feeling = entry.get("feeling", "Unknown")
                feeling_counts[feeling] = feeling_counts.get(feeling, 0) + 1
            
            # Find most common feeling
            most_common = max(feeling_counts.items(), key=lambda x: x[1])[0] if feeling_counts else "No data"
            
            # Get recent changes (last 10)
            recent_changes = emotional_history[-10:] if len(emotional_history) >= 10 else emotional_history
            
            # Determine trend
            if len(emotional_history) >= 2:
                recent_feeling = emotional_history[-1].get("feeling", "")
                previous_feeling = emotional_history[-2].get("feeling", "")
                
                positive_feelings = ["Happy", "Energetic", "Excited", "Optimistic", "Calm"]
                negative_feelings = ["Sad", "Anxious", "Stressed", "Pessimistic", "Angry"]
                extreme_feelings = ["Energetic", "Excited", "Stressed", "Anxious", "Angry"]
                
                if recent_feeling in positive_feelings and previous_feeling in negative_feelings:
                    trend = "Improving"
                elif recent_feeling in negative_feelings and previous_feeling in positive_feelings:
                    trend = "Declining"
                else:
                    trend = "Stable"
            else:
                trend = "New user"
            
            # Analyze patterns for mental health indicators
            patterns = self._analyze_mental_health_patterns(emotional_history)
            alerts = self._generate_mental_health_alerts(emotional_history, patterns)
            
            return {
                "trend": trend,
                "most_common": most_common,
                "recent_changes": recent_changes,
                "total_entries": len(emotional_history),
                "patterns": patterns,
                "alerts": alerts
            }
            
        except Exception as e:
            logger.error(f"Error analyzing emotional trends for {self.username}: {e}")
            return {"trend": "Error", "most_common": "Error", "recent_changes": [], "patterns": {}, "alerts": []}
    
    def _analyze_mental_health_patterns(self, emotional_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns that might indicate mental health issues"""
        try:
            if len(emotional_history) < 10:
                return {"bipolar_risk": "Insufficient data", "depression_risk": "Insufficient data", "anxiety_risk": "Insufficient data"}
            
            # Define feeling categories
            elevated_feelings = ["Energetic", "Excited", "Optimistic"]
            depressed_feelings = ["Sad", "Pessimistic", "Tired"]
            anxious_feelings = ["Anxious", "Stressed", "Confused"]
            stable_feelings = ["Happy", "Calm", "Neutral"]
            
            # Analyze mood swings (potential bipolar indicators)
            mood_swings = 0
            rapid_changes = 0
            
            for i in range(1, len(emotional_history)):
                prev_feeling = emotional_history[i-1].get("feeling", "")
                curr_feeling = emotional_history[i].get("feeling", "")
                
                # Count extreme mood changes
                if (prev_feeling in elevated_feelings and curr_feeling in depressed_feelings) or \
                   (prev_feeling in depressed_feelings and curr_feeling in elevated_feelings):
                    mood_swings += 1
                
                # Count rapid changes (within short time periods)
                prev_time = emotional_history[i-1].get("timestamp", "")
                curr_time = emotional_history[i].get("timestamp", "")
                if self._is_rapid_change(prev_time, curr_time):
                    rapid_changes += 1
            
            # Calculate risks
            total_entries = len(emotional_history)
            bipolar_risk = "Low"
            if mood_swings > total_entries * 0.3:  # More than 30% are mood swings
                bipolar_risk = "High"
            elif mood_swings > total_entries * 0.15:  # More than 15% are mood swings
                bipolar_risk = "Medium"
            
            # Analyze depression patterns
            depressed_count = sum(1 for entry in emotional_history if entry.get("feeling", "") in depressed_feelings)
            depression_ratio = depressed_count / total_entries
            depression_risk = "Low"
            if depression_ratio > 0.6:  # More than 60% depressed feelings
                depression_risk = "High"
            elif depression_ratio > 0.4:  # More than 40% depressed feelings
                depression_risk = "Medium"
            
            # Analyze anxiety patterns
            anxious_count = sum(1 for entry in emotional_history if entry.get("feeling", "") in anxious_feelings)
            anxiety_ratio = anxious_count / total_entries
            anxiety_risk = "Low"
            if anxiety_ratio > 0.5:  # More than 50% anxious feelings
                anxiety_risk = "High"
            elif anxiety_ratio > 0.3:  # More than 30% anxious feelings
                anxiety_risk = "Medium"
            
            return {
                "bipolar_risk": bipolar_risk,
                "depression_risk": depression_risk,
                "anxiety_risk": anxiety_risk,
                "mood_swings_count": mood_swings,
                "rapid_changes_count": rapid_changes,
                "depression_ratio": round(depression_ratio, 2),
                "anxiety_ratio": round(anxiety_ratio, 2)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing mental health patterns for {self.username}: {e}")
            return {"bipolar_risk": "Error", "depression_risk": "Error", "anxiety_risk": "Error"}
    
    def _is_rapid_change(self, prev_time: str, curr_time: str) -> bool:
        """Check if mood change happened within a short time period (e.g., 2 hours)"""
        try:
            from datetime import datetime, timedelta
            
            prev_dt = datetime.fromisoformat(prev_time.replace('Z', '+00:00'))
            curr_dt = datetime.fromisoformat(curr_time.replace('Z', '+00:00'))
            
            time_diff = abs((curr_dt - prev_dt).total_seconds() / 3600)  # hours
            return time_diff <= 2  # Rapid change if within 2 hours
        except:
            return False
    
    def _generate_mental_health_alerts(self, emotional_history: List[Dict[str, Any]], patterns: Dict[str, Any]) -> List[str]:
        """Generate alerts based on mental health patterns"""
        alerts = []
        
        try:
            # High risk alerts
            if patterns.get("bipolar_risk") == "High":
                alerts.append("⚠️ High risk of bipolar disorder: frequent mood swings")
            
            if patterns.get("depression_risk") == "High":
                alerts.append("⚠️ High risk of depression: predominance of negative emotions")
            
            if patterns.get("anxiety_risk") == "High":
                alerts.append("⚠️ High risk of anxiety: frequent stress and anxiety states")
            
            # Medium risk alerts
            if patterns.get("bipolar_risk") == "Medium":
                alerts.append("⚠️ Medium risk of bipolar disorder: mood swings observed")
            
            if patterns.get("depression_risk") == "Medium":
                alerts.append("⚠️ Medium risk of depression: signs of depression noticeable")
            
            if patterns.get("anxiety_risk") == "Medium":
                alerts.append("⚠️ Medium risk of anxiety: periodic stress states")
            
            # Pattern alerts
            if patterns.get("rapid_changes_count", 0) > 5:
                alerts.append("⚠️ Frequent rapid mood changes")
            
            # Positive patterns
            if patterns.get("depression_risk") == "Low" and patterns.get("anxiety_risk") == "Low":
                alerts.append("✅ Stable emotional state")
            
        except Exception as e:
            logger.error(f"Error generating mental health alerts for {self.username}: {e}")
        
        return alerts
    
    def delete_diary_entry(self, index: int) -> bool:
        """Delete a diary entry by index"""
        try:
            file_path = f"memory/user_profiles/{self.username}_diary.json"
            
            if not os.path.exists(file_path):
                return False
            
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
                if (not profile_file.name.endswith(("_emotions.json", "_insights.json", "relationship_insights.json")) and 
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
    




# Global instance
profile_manager = UserProfileManager() 