"""
Chat Summary Tools - Mini model for generating chat titles
"""

import logging
from typing import List, Dict, Any
from ..models.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class ChatSummaryTools:
    """Tools for generating chat summaries and titles"""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.summary_prompt = """
You are a chat title generator. Your job is to create short, descriptive titles for conversations.

**RULES:**
- Keep titles under 50 characters
- Be specific and descriptive
- Focus on the main topic or purpose
- Use clear, simple language
- Avoid generic titles like "Chat" or "Conversation"

**EXAMPLES:**
- "Planning weekend trip"
- "Debugging vision system"
- "Discussing AI architecture"
- "Family dinner plans"
- "Code review session"

**INPUT:** Conversation messages
**OUTPUT:** Short, descriptive title

Generate a title for this conversation:
"""
    
    def generate_chat_title(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a title for a chat based on its messages"""
        try:
            if not messages or len(messages) < 2:
                return "New Conversation"
            
            # Format messages for analysis
            conversation_text = ""
            for msg in messages[-10:]:  # Last 10 messages for context
                sender = msg.get('sender', 'user')
                content = msg.get('content', '')
                if content:
                    conversation_text += f"{sender}: {content}\n"
            
            if not conversation_text.strip():
                return "New Conversation"
            
            # Use a lightweight model for title generation
            self.gemini_client.switch_to_model('gemini-2.0-flash-lite')
            
            response = self.gemini_client.chat(
                message=f"{self.summary_prompt}\n\n{conversation_text}",
                system_prompt="You are a chat title generator. Create short, descriptive titles."
            )
            
            # Clean up response
            title = response.strip()
            if len(title) > 50:
                title = title[:47] + "..."
            
            logger.info(f"📝 Generated chat title: {title}")
            return title
            
        except Exception as e:
            logger.error(f"❌ Error generating chat title: {e}")
            return "New Conversation"
    
    def should_rename_chat(self, messages: List[Dict[str, Any]], current_title: str) -> bool:
        """Determine if chat should be renamed based on content"""
        if not messages or len(messages) < 3:
            return False
        
        # Don't rename if title is already descriptive
        if current_title != "New Conversation" and len(current_title) > 10:
            return False
        
        # Rename if we have enough conversation content
        return len(messages) >= 3 