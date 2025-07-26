"""
Shared Context System for Dr. Harmony
Provides unified context management for both Telegram bot and web interface
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class SharedContext:
    """Shared context data structure"""
    couple_id: str
    last_updated: str
    relationship_phase: str
    communication_patterns: Dict[str, Any]
    shared_memories: List[Dict[str, Any]]
    relationship_insights: List[Dict[str, Any]]
    conflict_history: List[Dict[str, Any]]
    milestone_history: List[Dict[str, Any]]
    current_topics: List[str]
    emotional_tone: str
    trust_level: int  # 1-10
    intimacy_level: int  # 1-10
    communication_quality: int  # 1-10

class SharedContextManager:
    """Manages shared context between bot and web interface"""
    
    def __init__(self, context_file: str = "./memory/shared_context.json"):
        self.context_file = context_file
        self.ensure_directory()
        self.context = self.load_context()
    
    def ensure_directory(self):
        """Ensure the memory directory exists"""
        Path(self.context_file).parent.mkdir(parents=True, exist_ok=True)
    
    def load_context(self) -> SharedContext:
        """Load shared context from file"""
        try:
            if os.path.exists(self.context_file):
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return SharedContext(**data)
        except Exception as e:
            print(f"Error loading shared context: {e}")
        
        # Return default context
        return SharedContext(
            couple_id="couple_1_2",
            last_updated=datetime.now().isoformat(),
            relationship_phase="growing",
            communication_patterns={},
            shared_memories=[],
            relationship_insights=[],
            conflict_history=[],
            milestone_history=[],
            current_topics=[],
            emotional_tone="neutral",
            trust_level=7,
            intimacy_level=6,
            communication_quality=7
        )
    
    def save_context(self):
        """Save shared context to file"""
        try:
            self.context.last_updated = datetime.now().isoformat()
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.context), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving shared context: {e}")
    
    def update_communication_pattern(self, pattern: str, frequency: int = 1):
        """Update communication patterns"""
        if pattern not in self.context.communication_patterns:
            self.context.communication_patterns[pattern] = 0
        self.context.communication_patterns[pattern] += frequency
        self.save_context()
    
    def add_shared_memory(self, memory: Dict[str, Any]):
        """Add a shared memory"""
        memory['timestamp'] = datetime.now().isoformat()
        self.context.shared_memories.append(memory)
        
        # Keep only last 50 memories
        if len(self.context.shared_memories) > 50:
            self.context.shared_memories = self.context.shared_memories[-50:]
        
        self.save_context()
    
    def add_relationship_insight(self, insight: Dict[str, Any]):
        """Add a relationship insight"""
        insight['timestamp'] = datetime.now().isoformat()
        self.context.relationship_insights.append(insight)
        
        # Keep only last 20 insights
        if len(self.context.relationship_insights) > 20:
            self.context.relationship_insights = self.context.relationship_insights[-20:]
        
        self.save_context()
    
    def add_conflict_record(self, conflict: Dict[str, Any]):
        """Add a conflict record"""
        conflict['timestamp'] = datetime.now().isoformat()
        self.context.conflict_history.append(conflict)
        
        # Keep only last 10 conflicts
        if len(self.context.conflict_history) > 10:
            self.context.conflict_history = self.context.conflict_history[-10:]
        
        self.save_context()
    
    def add_milestone(self, milestone: Dict[str, Any]):
        """Add a relationship milestone"""
        milestone['timestamp'] = datetime.now().isoformat()
        self.context.milestone_history.append(milestone)
        self.save_context()
    
    def update_current_topics(self, topics: List[str]):
        """Update current conversation topics"""
        self.context.current_topics = topics[:5]  # Keep only 5 topics
        self.save_context()
    
    def update_emotional_tone(self, tone: str):
        """Update emotional tone"""
        self.context.emotional_tone = tone
        self.save_context()
    
    def update_relationship_metrics(self, trust: Optional[int] = None, 
                                  intimacy: Optional[int] = None, 
                                  communication: Optional[int] = None):
        """Update relationship metrics"""
        if trust is not None:
            self.context.trust_level = max(1, min(10, trust))
        if intimacy is not None:
            self.context.intimacy_level = max(1, min(10, intimacy))
        if communication is not None:
            self.context.communication_quality = max(1, min(10, communication))
        self.save_context()
    
    def get_context_summary(self) -> str:
        """Get a summary of the shared context"""
        summary = f"Relationship: {self.context.relationship_phase} phase, Trust: {self.context.trust_level}/10, Topics: {', '.join(self.context.current_topics[:3])}"
        return summary
    
    def get_recent_insights(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent relationship insights"""
        return self.context.relationship_insights[-limit:]
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent shared memories"""
        return self.context.shared_memories[-limit:]
    
    def get_communication_patterns(self) -> Dict[str, Any]:
        """Get communication patterns"""
        return self.context.communication_patterns
    
    def get_conflict_history(self) -> List[Dict[str, Any]]:
        """Get conflict history"""
        return self.context.conflict_history
    
    def get_milestone_history(self) -> List[Dict[str, Any]]:
        """Get milestone history"""
        return self.context.milestone_history

# Global shared context manager instance
shared_context = SharedContextManager() 