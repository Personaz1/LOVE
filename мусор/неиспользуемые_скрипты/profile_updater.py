"""
Profile Updater - Functions for AI to update user profiles and shared context
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ProfileUpdater:
    """Profile updater with emotional history tracking"""
    
    def __init__(self, username: str = "meranda"):
        self.username = username
        self.profile_file = f"memory/user_profiles/{username}_profile.json"
        self.emotional_history_file = f"memory/user_profiles/{username}_emotions.json"

        self.insights_file = f"memory/user_profiles/relationship_insights.json"
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Ensure all necessary files exist"""
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
        

        
        # Create insights file if it doesn't exist
        if not os.path.exists(self.insights_file):
            default_insights = {
                "insights": [],
                "created_at": datetime.now().isoformat()
            }
            self._save_insights(default_insights)
    
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
    

    
    def _save_insights(self, insights_data: Dict[str, Any]):
        """Save insights data to file"""
        try:
            with open(self.insights_file, 'w', encoding='utf-8') as f:
                json.dump(insights_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving insights: {e}")
    
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
    

    
    def _load_insights(self) -> Dict[str, Any]:
        """Load insights data from file"""
        try:
            with open(self.insights_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading insights: {e}")
            return {"insights": []}
    
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
    
    def update_relationship_status(self, status: str) -> bool:
        """Update relationship status"""
        try:
            profile = self._load_profile()
            profile["relationship_status"] = status
            profile["last_updated"] = datetime.now().isoformat()
            self._save_profile(profile)
            
            logger.info(f"💕 Updated relationship status for {self.username}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating relationship status for {self.username}: {e}")
            return False
    
    def update_user_profile(self, username: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile"""
        try:
            profile = self._load_profile()
            profile.update(profile_data)
            profile["last_updated"] = datetime.now().isoformat()
            self._save_profile(profile)
            
            logger.info(f"🔄 Updated profile for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating profile for {username}: {e}")
            return False
    

    
    def add_relationship_insight(self, insight: str) -> bool:
        """Add relationship insight"""
        try:
            insights_data = self._load_insights()
            insights = insights_data.get("insights", [])
            
            insight_entry = {
                "content": insight,
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M")
            }
            
            insights.append(insight_entry)
            insights_data["insights"] = insights
            insights_data["last_updated"] = datetime.now().isoformat()
            
            self._save_insights(insights_data)
            
            logger.info(f"💡 Added relationship insight: {insight[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error adding relationship insight: {e}")
            return False
    
    def get_profile(self) -> Dict[str, Any]:
        """Get current profile"""
        return self._load_profile()
    
    def get_emotional_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent emotional history"""
        history_data = self._load_emotional_history()
        emotional_history = history_data.get("emotional_history", [])
        return emotional_history[-limit:] if limit > 0 else emotional_history
    
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

# Global instance
profile_updater = ProfileUpdater()

# Helper functions for AI to call
def update_stepan_profile(new_profile: str) -> bool:
    """Update Stepan's profile"""
    return profile_updater.update_user_profile("stepan", new_profile)

def update_meranda_profile(new_profile: str) -> bool:
    """Update Meranda's profile"""
    return profile_updater.update_user_profile("meranda", new_profile)

def update_stepan_hidden_profile(new_hidden_profile: str) -> bool:
    """Update Stepan's hidden profile"""
    return profile_updater.update_hidden_profile("stepan", new_hidden_profile)

def update_meranda_hidden_profile(new_hidden_profile: str) -> bool:
    """Update Meranda's hidden profile"""
    return profile_updater.update_hidden_profile("meranda", new_hidden_profile)

def update_stepan_relationship_status(status: str) -> bool:
    """Update Stepan's relationship status"""
    return profile_updater.update_relationship_status("stepan", status)

def update_meranda_relationship_status(status: str) -> bool:
    """Update Meranda's relationship status"""
    return profile_updater.update_relationship_status("meranda", status)

def update_stepan_current_feeling(feeling: str) -> bool:
    """Update Stepan's current feeling"""
    return profile_updater.update_current_feeling("stepan", feeling)

def update_meranda_current_feeling(feeling: str) -> bool:
    """Update Meranda's current feeling"""
    return profile_updater.update_current_feeling("meranda", feeling)

def add_relationship_insight(insight: str) -> bool:
    """Add relationship insight"""
    return profile_updater.add_relationship_insight(insight)

def update_relationship_phase(phase: str) -> bool:
    """Update relationship phase"""
    return profile_updater.update_relationship_phase(phase)

 