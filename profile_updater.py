"""
Profile Updater - Functions for AI to update user profiles and shared context
"""

from memory.user_profiles import profile_manager
from shared_context import shared_context
from datetime import datetime

class ProfileUpdater:
    """Profile updater for AI to modify user profiles and context"""
    
    def update_user_profile(self, username: str, new_profile: str) -> bool:
        """Update user profile"""
        try:
            profile = profile_manager.get_user_profile(username)
            if profile:
                return profile.update_profile(new_profile)
            return False
        except Exception as e:
            print(f"Error updating user profile for {username}: {e}")
            return False
    
    def update_hidden_profile(self, username: str, new_hidden_profile: str) -> bool:
        """Update hidden profile (model's private notes)"""
        try:
            profile = profile_manager.get_user_profile(username)
            if profile:
                return profile.update_hidden_profile(new_hidden_profile)
            return False
        except Exception as e:
            print(f"Error updating hidden profile for {username}: {e}")
            return False
    
    def update_relationship_status(self, username: str, status: str) -> bool:
        """Update relationship status"""
        try:
            profile = profile_manager.get_user_profile(username)
            if profile:
                return profile.update_relationship_status(status)
            return False
        except Exception as e:
            print(f"Error updating relationship status for {username}: {e}")
            return False
    
    def update_current_feeling(self, username: str, feeling: str) -> bool:
        """Update current feeling"""
        try:
            profile = profile_manager.get_user_profile(username)
            if profile:
                return profile.update_current_feeling(feeling)
            return False
        except Exception as e:
            print(f"Error updating current feeling for {username}: {e}")
            return False
    
    def add_relationship_insight(self, insight: str) -> bool:
        """Add insight to shared context"""
        try:
            shared_context.add_relationship_insight(insight)
            return True
        except Exception as e:
            print(f"Error adding relationship insight: {e}")
            return False
    
    def update_relationship_phase(self, phase: str) -> bool:
        """Update relationship phase in shared context"""
        try:
            shared_context.update_relationship_phase(phase)
            return True
        except Exception as e:
            print(f"Error updating relationship phase: {e}")
            return False
    
    def add_diary_entry(self, username: str, entry_data: dict) -> bool:
        """Add diary entry for user"""
        try:
            return profile_manager.add_diary_entry(username, entry_data)
        except Exception as e:
            print(f"Error adding diary entry for {username}: {e}")
            return False

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

def add_diary_entry(username: str, entry_data: dict) -> bool:
    """Add diary entry"""
    return profile_updater.add_diary_entry(username, entry_data) 