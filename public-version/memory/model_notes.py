"""
MODEL NOTES System
AI's private notes and thoughts about users, itself, and observations
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ModelNotes:
    """AI's private notes system - for model's personal thoughts and observations"""
    
    def __init__(self, notes_file: str = "memory/model_notes.json"):
        self.notes_file = notes_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure notes file exists with default structure"""
        if not os.path.exists(self.notes_file):
            default_notes = {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "notes": [],
                "user_observations": {},
                "personal_thoughts": [],
                "system_insights": []
            }
            self._save_notes(default_notes)
    
    def _load_notes(self) -> Dict[str, Any]:
        """Load notes from file"""
        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading model notes: {e}")
            return {
                "notes": [],
                "user_observations": {},
                "personal_thoughts": [],
                "system_insights": []
            }
    
    def _save_notes(self, notes_data: Dict[str, Any]):
        """Save notes to file"""
        try:
            notes_data["last_updated"] = datetime.now().isoformat()
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(notes_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving model notes: {e}")
    
    def add_note(self, note_text: str, category: str = "general") -> bool:
        """Add a new note"""
        try:
            notes_data = self._load_notes()
            
            new_note = {
                "id": f"note_{len(notes_data.get('notes', []))}_{datetime.now().timestamp()}",
                "text": note_text,
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M")
            }
            
            notes_data.setdefault("notes", []).append(new_note)
            self._save_notes(notes_data)
            
            logger.info(f"📝 Model added note: {note_text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error adding model note: {e}")
            return False
    
    def add_user_observation(self, username: str, observation: str) -> bool:
        """Add observation about specific user"""
        try:
            notes_data = self._load_notes()
            
            if username not in notes_data.get("user_observations", {}):
                notes_data["user_observations"][username] = []
            
            new_observation = {
                "id": f"obs_{len(notes_data['user_observations'][username])}_{datetime.now().timestamp()}",
                "observation": observation,
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M")
            }
            
            notes_data["user_observations"][username].append(new_observation)
            self._save_notes(notes_data)
            
            logger.info(f"👁️ Model observed {username}: {observation[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user observation: {e}")
            return False
    
    def add_personal_thought(self, thought: str) -> bool:
        """Add personal thought or reflection"""
        try:
            notes_data = self._load_notes()
            
            new_thought = {
                "id": f"thought_{len(notes_data.get('personal_thoughts', []))}_{datetime.now().timestamp()}",
                "thought": thought,
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M")
            }
            
            notes_data.setdefault("personal_thoughts", []).append(new_thought)
            self._save_notes(notes_data)
            
            logger.info(f"🧠 Model thought: {thought[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error adding personal thought: {e}")
            return False
    
    def add_system_insight(self, insight: str) -> bool:
        """Add system-level insight or pattern recognition"""
        try:
            notes_data = self._load_notes()
            
            new_insight = {
                "id": f"insight_{len(notes_data.get('system_insights', []))}_{datetime.now().timestamp()}",
                "insight": insight,
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M")
            }
            
            notes_data.setdefault("system_insights", []).append(new_insight)
            self._save_notes(notes_data)
            
            logger.info(f"💡 Model insight: {insight[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error adding system insight: {e}")
            return False
    
    def get_all_notes(self, limit: int = 50) -> Dict[str, Any]:
        """Get all notes organized by category"""
        try:
            notes_data = self._load_notes()
            
            # Limit recent entries
            result = {
                "general_notes": notes_data.get("notes", [])[-limit:],
                "user_observations": {},
                "personal_thoughts": notes_data.get("personal_thoughts", [])[-limit:],
                "system_insights": notes_data.get("system_insights", [])[-limit:]
            }
            
            # Limit user observations per user
            for username, observations in notes_data.get("user_observations", {}).items():
                result["user_observations"][username] = observations[-limit:]
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all notes: {e}")
            return {}
    
    def get_user_observations(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get observations about specific user"""
        try:
            notes_data = self._load_notes()
            observations = notes_data.get("user_observations", {}).get(username, [])
            return observations[-limit:] if limit > 0 else observations
            
        except Exception as e:
            logger.error(f"Error getting user observations: {e}")
            return []
    
    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """Search through all notes"""
        try:
            notes_data = self._load_notes()
            results = []
            
            # Search in general notes
            for note in notes_data.get("notes", []):
                if query.lower() in note.get("text", "").lower():
                    results.append({"type": "note", "data": note})
            
            # Search in user observations
            for username, observations in notes_data.get("user_observations", {}).items():
                for obs in observations:
                    if query.lower() in obs.get("observation", "").lower():
                        results.append({"type": "user_observation", "user": username, "data": obs})
            
            # Search in personal thoughts
            for thought in notes_data.get("personal_thoughts", []):
                if query.lower() in thought.get("thought", "").lower():
                    results.append({"type": "personal_thought", "data": thought})
            
            # Search in system insights
            for insight in notes_data.get("system_insights", []):
                if query.lower() in insight.get("insight", "").lower():
                    results.append({"type": "system_insight", "data": insight})
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            return []
    
    def clear_old_notes(self, days_old: int = 30) -> bool:
        """Clear notes older than specified days"""
        try:
            notes_data = self._load_notes()
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            # Filter general notes
            notes_data["notes"] = [
                note for note in notes_data.get("notes", [])
                if datetime.fromisoformat(note.get("timestamp", "2020-01-01")).timestamp() > cutoff_date
            ]
            
            # Filter personal thoughts
            notes_data["personal_thoughts"] = [
                thought for thought in notes_data.get("personal_thoughts", [])
                if datetime.fromisoformat(thought.get("timestamp", "2020-01-01")).timestamp() > cutoff_date
            ]
            
            # Filter system insights
            notes_data["system_insights"] = [
                insight for insight in notes_data.get("system_insights", [])
                if datetime.fromisoformat(insight.get("timestamp", "2020-01-01")).timestamp() > cutoff_date
            ]
            
            # Filter user observations
            for username in notes_data.get("user_observations", {}):
                notes_data["user_observations"][username] = [
                    obs for obs in notes_data["user_observations"][username]
                    if datetime.fromisoformat(obs.get("timestamp", "2020-01-01")).timestamp() > cutoff_date
                ]
            
            self._save_notes(notes_data)
            logger.info(f"🧹 Cleared notes older than {days_old} days")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing old notes: {e}")
            return False

# Global instance
model_notes = ModelNotes() 