"""
Test suite for Family Psychologist Bot
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from bot.family_psychologist_bot import FamilyPsychologistBot
from memory.relationship_memory import RelationshipMemory, MemoryEntry, RelationshipContext
from prompts.psychologist_prompt import get_context_aware_prompt, PSYCHOLOGIST_SYSTEM_PROMPT


class TestRelationshipMemory:
    """Test the relationship memory system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.memory = RelationshipMemory()
        self.memory.memory_file = "test_memory.json"
    
    def test_add_memory(self):
        """Test adding memory entries"""
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            user_id=123,
            username="test_user",
            message="test message",
            context_type="conversation"
        )
        
        self.memory.add_memory(entry)
        assert len(self.memory.memories) == 1
        assert self.memory.memories[0].message == "test message"
    
    def test_get_recent_memories(self):
        """Test retrieving recent memories"""
        # Add multiple memories
        for i in range(5):
            entry = MemoryEntry(
                timestamp=datetime.now().isoformat(),
                user_id=123,
                username="test_user",
                message=f"message {i}",
                context_type="conversation"
            )
            self.memory.add_memory(entry)
        
        recent = self.memory.get_recent_memories(123, limit=3)
        assert len(recent) == 3
        assert recent[-1].message == "message 4"
    
    def test_relationship_context(self):
        """Test relationship context management"""
        context = RelationshipContext(
            couple_id="test_couple",
            partner1_id=123,
            partner1_name="Partner1",
            partner2_id=456,
            partner2_name="Partner2",
            relationship_start_date="2023-01-01",
            current_phase="established",
            communication_patterns=[],
            conflict_resolution_style="collaborative",
            shared_goals=["better communication"],
            challenges=["time management"],
            strengths=["strong connection"],
            last_session_date=datetime.now().isoformat(),
            total_sessions=1
        )
        
        self.memory.update_relationship_context(context)
        retrieved = self.memory.get_relationship_context("test_couple")
        
        assert retrieved is not None
        assert retrieved.partner1_name == "Partner1"
        assert retrieved.partner2_name == "Partner2"


class TestPromptSystem:
    """Test the prompt system"""
    
    def test_basic_prompt(self):
        """Test basic prompt generation"""
        prompt = PSYCHOLOGIST_SYSTEM_PROMPT
        assert "Dr. Harmony" in prompt
        assert "family psychologist" in prompt.lower()
    
    def test_context_aware_prompt(self):
        """Test context-aware prompt generation"""
        couple_context = {
            "total_sessions": 10,
            "conflict_frequency": 2,
            "communication_balance": 1.0,
            "challenges": ["communication issues"]
        }
        
        prompt = get_context_aware_prompt(couple_context)
        assert "established" in prompt.lower()
        assert "empathetic" in prompt.lower()
        assert "communication" in prompt.lower()


class TestBotCommands:
    """Test bot command handlers"""
    
    @pytest.fixture
    def bot(self):
        """Create bot instance for testing"""
        with patch('config.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
            mock_settings.OPENAI_API_KEY = "test_key"
            return FamilyPsychologistBot()
    
    @pytest.fixture
    def mock_update(self):
        """Create mock update object"""
        update = Mock()
        update.effective_user.id = 123
        update.effective_user.first_name = "TestUser"
        update.message.reply_text = AsyncMock()
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context object"""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_start_command(self, bot, mock_update, mock_context):
        """Test start command"""
        await bot.start_command(mock_update, mock_context)
        
        # Verify reply was called
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Dr. Harmony" in call_args
        assert "family psychologist" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_help_command(self, bot, mock_update, mock_context):
        """Test help command"""
        await bot.help_command(mock_update, mock_context)
        
        # Verify reply was called
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Available Commands" in call_args


class TestMCPIntegration:
    """Test MCP tools integration"""
    
    @pytest.mark.asyncio
    async def test_mcp_client_creation(self):
        """Test MCP client creation"""
        from mcp_tools.mcp_client import MCPClient
        
        client = MCPClient()
        assert client.base_url is None  # Default when not configured
        
        # Test async context manager
        async with client:
            assert client.session is not None
    
    @pytest.mark.asyncio
    async def test_mcp_tools_wrapper(self):
        """Test MCP tools wrapper"""
        from mcp_tools.mcp_client import MCPTools
        
        tools = MCPTools()
        
        # Test that methods exist
        assert hasattr(tools, 'store_insight')
        assert hasattr(tools, 'get_history')
        assert hasattr(tools, 'store_conflict')
        assert hasattr(tools, 'search_patterns')


class TestConfiguration:
    """Test configuration management"""
    
    def test_settings_loading(self):
        """Test settings loading"""
        from config import settings
        
        # Test that settings object exists
        assert hasattr(settings, 'TELEGRAM_BOT_TOKEN')
        assert hasattr(settings, 'OPENAI_API_KEY')
        assert hasattr(settings, 'OPENAI_MODEL')
        assert hasattr(settings, 'MEMORY_FILE_PATH')


# Integration tests
class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.asyncio
    async def test_memory_persistence(self):
        """Test that memory persists across instances"""
        # Create first memory instance
        memory1 = RelationshipMemory()
        memory1.memory_file = "test_integration.json"
        
        # Add some data
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            user_id=999,
            username="integration_test",
            message="integration test message",
            context_type="conversation"
        )
        memory1.add_memory(entry)
        
        # Create second memory instance (should load same data)
        memory2 = RelationshipMemory()
        memory2.memory_file = "test_integration.json"
        
        # Check that data was loaded
        recent = memory2.get_recent_memories(999)
        assert len(recent) == 1
        assert recent[0].message == "integration test message"
    
    @pytest.mark.asyncio
    async def test_bot_memory_integration(self):
        """Test bot integration with memory system"""
        with patch('config.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
            mock_settings.OPENAI_API_KEY = "test_key"
            
            bot = FamilyPsychologistBot()
            
            # Test that bot has access to memory
            assert hasattr(bot, 'active_sessions')
            assert isinstance(bot.active_sessions, dict)


if __name__ == "__main__":
    pytest.main([__file__]) 