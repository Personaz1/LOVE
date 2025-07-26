import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime

from config import settings


class MCPClient:
    def __init__(self):
        self.base_url = settings.MCP_SERVER_URL
        self.token = settings.MCP_SERVER_TOKEN
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated request to MCP server"""
        if not self.base_url:
            return {"error": "MCP server not configured"}
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}" if self.token else ""
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/{endpoint}",
                json=data,
                headers=headers
            ) as response:
                return await response.json()
        except Exception as e:
            return {"error": f"MCP request failed: {str(e)}"}
    
    async def create_memory_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create memory entities for relationship context"""
        return await self._make_request("memory/create_entities", {"entities": entities})
    
    async def create_memory_relations(self, relations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create memory relations between entities"""
        return await self._make_request("memory/create_relations", {"relations": relations})
    
    async def add_memory_observations(self, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add observations to existing memory entities"""
        return await self._make_request("memory/add_observations", {"observations": observations})
    
    async def search_memory(self, query: str) -> Dict[str, Any]:
        """Search memory for relevant context"""
        return await self._make_request("memory/search", {"query": query})
    
    async def get_memory_context(self, entity_names: List[str]) -> Dict[str, Any]:
        """Get memory context for specific entities"""
        return await self._make_request("memory/open_nodes", {"names": entity_names})
    
    async def fetch_external_data(self, url: str, **kwargs) -> Dict[str, Any]:
        """Fetch external data through MCP server"""
        return await self._make_request("fetch", {"url": url, **kwargs})
    
    async def store_relationship_insight(self, couple_id: str, insight: str, context: Dict[str, Any]):
        """Store relationship insight in MCP memory"""
        entities = [
            {
                "name": f"couple_{couple_id}",
                "entityType": "relationship",
                "observations": [f"Insight: {insight}", f"Context: {json.dumps(context)}"]
            }
        ]
        
        return await self.create_memory_entities(entities)
    
    async def get_relationship_history(self, couple_id: str) -> Dict[str, Any]:
        """Get relationship history from MCP memory"""
        return await self.search_memory(f"couple_{couple_id} relationship history")
    
    async def store_conflict_resolution(self, couple_id: str, conflict_data: Dict[str, Any]):
        """Store conflict resolution data"""
        entities = [
            {
                "name": f"conflict_{couple_id}_{datetime.now().isoformat()}",
                "entityType": "conflict_resolution",
                "observations": [
                    f"Conflict type: {conflict_data.get('type')}",
                    f"Resolution approach: {conflict_data.get('approach')}",
                    f"Outcome: {conflict_data.get('outcome')}",
                    f"Lessons learned: {conflict_data.get('lessons')}"
                ]
            }
        ]
        
        relations = [
            {
                "from": f"couple_{couple_id}",
                "to": f"conflict_{couple_id}_{datetime.now().isoformat()}",
                "relationType": "experienced"
            }
        ]
        
        await self.create_memory_entities(entities)
        await self.create_memory_relations(relations)
    
    # New methods for user profiles and personalized insights
    async def store_user_profile(self, user_id: int, profile_data: Dict[str, Any]):
        """Store user profile in MCP memory"""
        entities = [
            {
                "name": f"user_{user_id}",
                "entityType": "person",
                "observations": [
                    f"Full name: {profile_data.get('full_name')}",
                    f"Personality: {', '.join(profile_data.get('personality_traits', []))}",
                    f"Communication style: {profile_data.get('communication_style')}",
                    f"Love language: {profile_data.get('love_language')}",
                    f"Relationship goals: {', '.join(profile_data.get('relationship_goals', []))}",
                    f"Current status: {profile_data.get('current_relationship_status')}",
                    f"Strengths: {', '.join(profile_data.get('strengths_in_relationship', []))}",
                    f"Growth areas: {', '.join(profile_data.get('areas_for_improvement', []))}"
                ]
            }
        ]
        
        return await self.create_memory_entities(entities)
    
    async def store_personalized_insight(self, user_id: int, couple_id: str, insight_data: Dict[str, Any]):
        """Store personalized insight for a user"""
        entities = [
            {
                "name": f"insight_{user_id}_{datetime.now().isoformat()}",
                "entityType": "personalized_insight",
                "observations": [
                    f"Title: {insight_data.get('title')}",
                    f"Description: {insight_data.get('description')}",
                    f"Recommendations: {', '.join(insight_data.get('recommendations', []))}",
                    f"Generated for: {insight_data.get('generated_for')}",
                    f"Context: {json.dumps(insight_data.get('context_data', {}))}"
                ]
            }
        ]
        
        relations = [
            {
                "from": f"user_{user_id}",
                "to": f"insight_{user_id}_{datetime.now().isoformat()}",
                "relationType": "receives"
            },
            {
                "from": f"couple_{couple_id}",
                "to": f"insight_{user_id}_{datetime.now().isoformat()}",
                "relationType": "generates"
            }
        ]
        
        await self.create_memory_entities(entities)
        await self.create_memory_relations(relations)
    
    async def get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user context from MCP memory"""
        return await self.get_memory_context([f"user_{user_id}"])
    
    async def search_personalized_patterns(self, user_id: int, query: str) -> Dict[str, Any]:
        """Search for personalized patterns and insights"""
        return await self.search_memory(f"user_{user_id} {query}")
    
    async def store_diary_entry(self, user_id: int, diary_data: Dict[str, Any]):
        """Store diary entry in MCP memory"""
        entities = [
            {
                "name": f"diary_{user_id}_{diary_data.get('entry_date')}",
                "entityType": "diary_entry",
                "observations": [
                    f"Mood: {diary_data.get('mood')}",
                    f"Relationship thoughts: {diary_data.get('relationship_thoughts')}",
                    f"Personal growth: {diary_data.get('personal_growth')}",
                    f"Gratitude: {diary_data.get('gratitude_notes')}",
                    f"Challenges: {diary_data.get('challenges')}",
                    f"Goals: {diary_data.get('goals_for_tomorrow')}"
                ]
            }
        ]
        
        relations = [
            {
                "from": f"user_{user_id}",
                "to": f"diary_{user_id}_{diary_data.get('entry_date')}",
                "relationType": "writes"
            }
        ]
        
        await self.create_memory_entities(entities)
        await self.create_memory_relations(relations)
    
    async def get_relationship_dynamics(self, couple_id: str) -> Dict[str, Any]:
        """Get relationship dynamics analysis from MCP memory"""
        return await self.search_memory(f"couple_{couple_id} dynamics patterns communication")
    
    async def store_relationship_milestone(self, couple_id: str, milestone_data: Dict[str, Any]):
        """Store relationship milestone in MCP memory"""
        entities = [
            {
                "name": f"milestone_{couple_id}_{datetime.now().isoformat()}",
                "entityType": "relationship_milestone",
                "observations": [
                    f"Type: {milestone_data.get('type')}",
                    f"Description: {milestone_data.get('description')}",
                    f"Impact: {milestone_data.get('impact')}",
                    f"Emotional significance: {milestone_data.get('emotional_significance')}"
                ]
            }
        ]
        
        relations = [
            {
                "from": f"couple_{couple_id}",
                "to": f"milestone_{couple_id}_{datetime.now().isoformat()}",
                "relationType": "achieves"
            }
        ]
        
        await self.create_memory_entities(entities)
        await self.create_memory_relations(relations)


class MCPTools:
    """Wrapper for MCP tool functions that can be used in prompts"""
    
    def __init__(self):
        self.client = MCPClient()
    
    async def store_insight(self, couple_id: str, insight: str, context: Dict[str, Any]):
        """Store psychological insight about the relationship"""
        return await self.client.store_relationship_insight(couple_id, insight, context)
    
    async def get_history(self, couple_id: str):
        """Get relationship history and patterns"""
        return await self.client.get_relationship_history(couple_id)
    
    async def store_conflict(self, couple_id: str, conflict_data: Dict[str, Any]):
        """Store conflict resolution data for learning"""
        return await self.client.store_conflict_resolution(couple_id, conflict_data)
    
    async def search_patterns(self, query: str):
        """Search for patterns in relationship data"""
        return await self.client.search_memory(query)
    
    async def fetch_relationship_advice(self, topic: str):
        """Fetch relationship advice from external sources"""
        # This would integrate with relationship psychology resources
        return await self.client.fetch_external_data(
            f"https://api.relationship-advice.com/search?topic={topic}"
        )
    
    # New methods for user profiles and personalized insights
    async def store_user_profile(self, user_id: int, profile_data: Dict[str, Any]):
        """Store user profile for personalized insights"""
        return await self.client.store_user_profile(user_id, profile_data)
    
    async def generate_personalized_insight(self, user_id: int, couple_id: str, context: str):
        """Generate personalized insight for a specific user"""
        # Get user context from MCP
        user_context = await self.client.get_user_context(user_id)
        
        # Get relationship dynamics
        dynamics = await self.client.get_relationship_dynamics(couple_id)
        
        # Generate personalized insight
        insight_data = {
            "title": f"Personalized Insight for {profile_data.get('full_name', 'Partner')}",
            "description": f"Based on your communication style and relationship patterns, here's what I've learned...",
            "recommendations": [
                "Practice active listening during emotional conversations",
                "Express your feelings more openly",
                "Set aside quality time for deep connection"
            ],
            "generated_for": "individual",
            "context_data": {
                "user_context": user_context,
                "relationship_dynamics": dynamics,
                "current_context": context
            }
        }
        
        return await self.client.store_personalized_insight(user_id, couple_id, insight_data)
    
    async def get_user_personalized_advice(self, user_id: int, couple_id: str):
        """Get personalized advice for a specific user"""
        return await self.client.search_personalized_patterns(user_id, "advice recommendations")
    
    async def store_diary_entry(self, user_id: int, diary_data: Dict[str, Any]):
        """Store personal diary entry"""
        return await self.client.store_diary_entry(user_id, diary_data)
    
    async def get_user_diary_insights(self, user_id: int):
        """Get insights from user's diary entries"""
        return await self.client.search_personalized_patterns(user_id, "diary patterns mood trends")
    
    async def store_relationship_milestone(self, couple_id: str, milestone_data: Dict[str, Any]):
        """Store relationship milestone for celebration and learning"""
        return await self.client.store_relationship_milestone(couple_id, milestone_data)
    
    async def get_couple_insights(self, couple_id: str):
        """Get comprehensive insights for the couple"""
        return await self.client.get_relationship_dynamics(couple_id)


# Global MCP tools instance
mcp_tools = MCPTools() 