import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from config import settings


@dataclass
class MemoryEntry:
    timestamp: str
    user_id: int
    username: str
    message: str
    context_type: str  # 'conversation', 'conflict', 'milestone', 'insight'
    emotional_tone: Optional[str] = None
    relationship_dynamics: Optional[str] = None
    action_items: Optional[List[str]] = None
    ai_insights: Optional[str] = None


@dataclass
class RelationshipContext:
    couple_id: str
    partner1_id: int
    partner1_name: str
    partner2_id: int
    partner2_name: str
    relationship_start_date: str
    current_phase: str
    communication_patterns: List[str]
    conflict_resolution_style: str
    shared_goals: List[str]
    challenges: List[str]
    strengths: List[str]
    last_session_date: str
    total_sessions: int


class RelationshipMemory:
    def __init__(self):
        self.memory_file = Path(settings.MEMORY_FILE_PATH)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memories: List[MemoryEntry] = []
        self.relationships: Dict[str, RelationshipContext] = {}
        self.load_memory()
    
    def load_memory(self):
        """Load existing memory from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memories = [MemoryEntry(**entry) for entry in data.get('memories', [])]
                    self.relationships = {
                        k: RelationshipContext(**v) for k, v in data.get('relationships', {}).items()
                    }
            except Exception as e:
                print(f"Error loading memory: {e}")
                self.memories = []
                self.relationships = {}
    
    def save_memory(self):
        """Save memory to disk"""
        try:
            data = {
                'memories': [asdict(memory) for memory in self.memories],
                'relationships': {k: asdict(v) for k, v in self.relationships.items()},
                'last_updated': datetime.now().isoformat()
            }
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def add_memory(self, entry: MemoryEntry):
        """Add a new memory entry"""
        self.memories.append(entry)
        if len(self.memories) > settings.MAX_MEMORY_ENTRIES:
            # Remove oldest entries
            self.memories = self.memories[-settings.MAX_MEMORY_ENTRIES:]
        self.save_memory()
    
    def get_recent_memories(self, user_id: int, limit: int = 10) -> List[MemoryEntry]:
        """Get recent memories for a specific user"""
        user_memories = [m for m in self.memories if m.user_id == user_id]
        return user_memories[-limit:]
    
    def get_relationship_context(self, couple_id: str) -> Optional[RelationshipContext]:
        """Get relationship context for a couple"""
        return self.relationships.get(couple_id)
    
    def update_relationship_context(self, context: RelationshipContext):
        """Update relationship context"""
        self.relationships[context.couple_id] = context
        self.save_memory()
    
    def get_shared_memories(self, couple_id: str, limit: int = 20) -> List[MemoryEntry]:
        """Get memories shared between partners"""
        context = self.get_relationship_context(couple_id)
        if not context:
            return []
        
        couple_memories = [
            m for m in self.memories 
            if m.user_id in [context.partner1_id, context.partner2_id]
        ]
        return couple_memories[-limit:]
    
    def analyze_communication_patterns(self, couple_id: str) -> Dict[str, Any]:
        """Analyze communication patterns for insights"""
        context = self.get_relationship_context(couple_id)
        if not context:
            return {}
        
        shared_memories = self.get_shared_memories(couple_id, limit=100)
        
        # Analyze patterns
        partner1_messages = [m for m in shared_memories if m.user_id == context.partner1_id]
        partner2_messages = [m for m in shared_memories if m.user_id == context.partner2_id]
        
        analysis = {
            'total_interactions': len(shared_memories),
            'partner1_contribution': len(partner1_messages),
            'partner2_contribution': len(partner2_messages),
            'communication_balance': len(partner1_messages) / max(len(partner2_messages), 1),
            'recent_emotional_tone': self._analyze_emotional_tone(shared_memories[-10:]),
            'conflict_frequency': len([m for m in shared_memories if m.context_type == 'conflict']),
            'positive_moments': len([m for m in shared_memories if m.context_type == 'milestone'])
        }
        
        return analysis
    
    def _analyze_emotional_tone(self, memories: List[MemoryEntry]) -> Dict[str, int]:
        """Analyze emotional tone from recent memories"""
        tone_counts = {}
        for memory in memories:
            if memory.emotional_tone:
                tone_counts[memory.emotional_tone] = tone_counts.get(memory.emotional_tone, 0) + 1
        return tone_counts
    
    def get_insights_for_session(self, couple_id: str) -> str:
        """Generate insights for the current session"""
        context = self.get_relationship_context(couple_id)
        if not context:
            return "No relationship context found."
        
        analysis = self.analyze_communication_patterns(couple_id)
        recent_memories = self.get_shared_memories(couple_id, limit=5)
        
        insights = f"""
Relationship Context for {context.partner1_name} & {context.partner2_name}:
- Relationship Phase: {context.current_phase}
- Total Sessions: {context.total_sessions}
- Communication Balance: {analysis.get('communication_balance', 0):.2f}
- Recent Emotional Tone: {analysis.get('recent_emotional_tone', {})}
- Shared Goals: {', '.join(context.shared_goals)}
- Current Challenges: {', '.join(context.challenges)}
- Relationship Strengths: {', '.join(context.strengths)}
        """
        
        return insights.strip()


# Global memory instance
relationship_memory = RelationshipMemory() 