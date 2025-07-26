"""
Tests for user profile management system
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from memory.user_profiles import (
    UserProfile, PersonalDiary, RelationshipInsight, 
    UserProfileManager, profile_manager
)


class TestUserProfile:
    """Test user profile functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.original_memory_path = profile_manager.memory_file.parent
        profile_manager.memory_file = Path(self.test_dir) / "test_memory.json"
        profile_manager.profiles_dir = Path(self.test_dir) / "user_profiles"
        profile_manager.insights_dir = profile_manager.profiles_dir / "insights"
        profile_manager.diary_dir = profile_manager.profiles_dir / "diaries"
        
        # Create directories
        profile_manager.profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_manager.insights_dir.mkdir(exist_ok=True)
        profile_manager.diary_dir.mkdir(exist_ok=True)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_create_user_profile(self):
        """Test creating a user profile"""
        profile = UserProfile(
            user_id=123,
            username="test_user",
            full_name="Test User",
            birth_date="1990-01-01",
            personality_traits=["Analytical", "Creative"],
            communication_style="Direct and logical",
            love_language="Quality time",
            relationship_goals=["Better communication"],
            current_relationship_status="Committed",
            relationship_concerns=["Time management"],
            personal_growth_areas=["Patience"],
            strengths_in_relationship=["Loyalty"],
            areas_for_improvement=["Active listening"],
            last_updated=datetime.now().isoformat(),
            profile_version=1
        )
        
        assert profile.user_id == 123
        assert profile.full_name == "Test User"
        assert "Analytical" in profile.personality_traits
        assert profile.communication_style == "Direct and logical"
    
    def test_save_and_load_profile(self):
        """Test saving and loading user profile"""
        profile = UserProfile(
            user_id=456,
            username="test_user",
            full_name="Test User",
            birth_date="1990-01-01",
            personality_traits=["Analytical"],
            communication_style="Direct",
            love_language="Quality time",
            relationship_goals=["Communication"],
            current_relationship_status="Committed",
            relationship_concerns=[],
            personal_growth_areas=[],
            strengths_in_relationship=[],
            areas_for_improvement=[],
            last_updated=datetime.now().isoformat(),
            profile_version=1
        )
        
        # Save profile
        profile_manager.save_profile(profile)
        
        # Load profile
        loaded_profile = profile_manager.load_profile(456)
        
        assert loaded_profile is not None
        assert loaded_profile.user_id == 456
        assert loaded_profile.full_name == "Test User"
        assert loaded_profile.personality_traits == ["Analytical"]
    
    def test_update_profile_field(self):
        """Test updating specific profile fields"""
        # Create and save profile
        profile = UserProfile(
            user_id=789,
            username="test_user",
            full_name="Test User",
            birth_date="1990-01-01",
            personality_traits=["Analytical"],
            communication_style="Direct",
            love_language="Quality time",
            relationship_goals=["Communication"],
            current_relationship_status="Committed",
            relationship_concerns=[],
            personal_growth_areas=[],
            strengths_in_relationship=[],
            areas_for_improvement=[],
            last_updated=datetime.now().isoformat(),
            profile_version=1
        )
        profile_manager.save_profile(profile)
        
        # Update field
        success = profile_manager.update_profile_field(789, "full_name", "Updated Name")
        assert success is True
        
        # Load and verify
        updated_profile = profile_manager.load_profile(789)
        assert updated_profile.full_name == "Updated Name"
        assert updated_profile.profile_version == 2
    
    def test_get_profile_summary(self):
        """Test getting profile summary"""
        profile = UserProfile(
            user_id=999,
            username="test_user",
            full_name="Test User",
            birth_date="1990-01-01",
            personality_traits=["Analytical", "Creative"],
            communication_style="Direct and logical",
            love_language="Quality time",
            relationship_goals=["Better communication", "Deeper connection"],
            current_relationship_status="Committed and growing",
            relationship_concerns=[],
            personal_growth_areas=[],
            strengths_in_relationship=["Loyalty", "Empathy"],
            areas_for_improvement=["Active listening"],
            last_updated=datetime.now().isoformat(),
            profile_version=1
        )
        profile_manager.save_profile(profile)
        
        summary = profile_manager.get_profile_summary(999)
        
        assert summary["full_name"] == "Test User"
        assert "Analytical" in summary["personality_traits"]
        assert summary["communication_style"] == "Direct and logical"
        assert "Better communication" in summary["relationship_goals"]
        assert "Loyalty" in summary["strengths"]
    
    def test_create_diary_entry(self):
        """Test creating diary entry"""
        entry = PersonalDiary(
            user_id=123,
            entry_date="2024-01-15",
            mood="Happy",
            relationship_thoughts="Feeling connected today",
            personal_growth="Learned to listen better",
            gratitude_notes="Grateful for my partner's support",
            challenges="Work stress affecting mood",
            goals_for_tomorrow="Practice active listening"
        )
        
        assert entry.user_id == 123
        assert entry.mood == "Happy"
        assert "connected" in entry.relationship_thoughts
    
    def test_save_and_load_diary_entries(self):
        """Test saving and loading diary entries"""
        entry = PersonalDiary(
            user_id=456,
            entry_date="2024-01-15",
            mood="Happy",
            relationship_thoughts="Feeling connected today",
            personal_growth="Learned to listen better",
            gratitude_notes="Grateful for my partner's support",
            challenges="Work stress affecting mood",
            goals_for_tomorrow="Practice active listening"
        )
        
        # Save entry
        profile_manager.save_diary_entry(entry)
        
        # Load entries
        entries = profile_manager.get_diary_entries(456, limit=5)
        
        assert len(entries) == 1
        assert entries[0].user_id == 456
        assert entries[0].mood == "Happy"
        assert "connected" in entries[0].relationship_thoughts
    
    def test_create_relationship_insight(self):
        """Test creating relationship insight"""
        insight = RelationshipInsight(
            insight_id="test_insight_1",
            couple_id="couple_123",
            insight_type="communication",
            title="Communication Pattern",
            description="Noticed improvement in active listening",
            recommendations=["Continue practicing", "Schedule regular check-ins"],
            generated_for="both",
            context_data={"pattern": "improved_listening"},
            created_date=datetime.now().isoformat()
        )
        
        assert insight.insight_id == "test_insight_1"
        assert insight.insight_type == "communication"
        assert "improvement" in insight.description
        assert len(insight.recommendations) == 2
    
    def test_save_and_load_insights(self):
        """Test saving and loading relationship insights"""
        insight = RelationshipInsight(
            insight_id="test_insight_2",
            couple_id="couple_456",
            insight_type="communication",
            title="Communication Pattern",
            description="Noticed improvement in active listening",
            recommendations=["Continue practicing"],
            generated_for="both",
            context_data={"pattern": "improved_listening"},
            created_date=datetime.now().isoformat()
        )
        
        # Save insight
        profile_manager.create_relationship_insight(insight)
        
        # Load insights
        insights = profile_manager.get_insights_for_couple("couple_456")
        
        assert len(insights) == 1
        assert insights[0].insight_id == "test_insight_2"
        assert insights[0].insight_type == "communication"
    
    def test_generate_personalized_advice(self):
        """Test generating personalized advice"""
        # Create profile
        profile = UserProfile(
            user_id=111,
            username="test_user",
            full_name="Test User",
            birth_date="1990-01-01",
            personality_traits=["Analytical"],
            communication_style="Direct",
            love_language="Quality time",
            relationship_goals=["Communication"],
            current_relationship_status="Committed",
            relationship_concerns=[],
            personal_growth_areas=[],
            strengths_in_relationship=[],
            areas_for_improvement=[],
            last_updated=datetime.now().isoformat(),
            profile_version=1
        )
        profile_manager.save_profile(profile)
        
        # Generate advice
        advice_data = profile_manager.generate_personalized_advice(111, "couple_111", "test context")
        
        assert "user_profile" in advice_data
        assert advice_data["user_profile"]["full_name"] == "Test User"
        assert "recent_insights" in advice_data
        assert "recent_diary_entries" in advice_data
        assert advice_data["context"] == "test context"


if __name__ == "__main__":
    pytest.main([__file__]) 