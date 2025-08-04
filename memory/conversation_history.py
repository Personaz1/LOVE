"""
Conversation History Management System
Handles chat history, archiving, and context management
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Import AI client for generating summaries
AI_AVAILABLE = False
AIClient = None

def _load_ai_client():
    """Lazy load AI client to avoid circular imports"""
    global AI_AVAILABLE, AIClient
    
    if AI_AVAILABLE:
        return AIClient
        
    try:
        import sys
        import os
        # Add parent directory to path to ensure ai_client can be found
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(parent_dir)
        logger.info(f"🔍 Added {parent_dir} to Python path")
        
        # Check if ai_client module exists
        ai_client_path = os.path.join(parent_dir, 'ai_client')
        if os.path.exists(ai_client_path):
            logger.info(f"✅ Found ai_client module at {ai_client_path}")
        else:
            logger.error(f"❌ ai_client module not found at {ai_client_path}")
            raise FileNotFoundError(f"ai_client module not found at {ai_client_path}")
        
        from ai_client.core.client import AIClient as AIClientClass
        AIClient = AIClientClass
        AI_AVAILABLE = True
        logger.info("✅ AI client successfully imported for summaries")
        return AIClient
        
    except ImportError as e:
        AI_AVAILABLE = False
        logger.error(f"❌ AI client import failed - summaries will not work. Error: {e}")
        raise
    except Exception as e:
        AI_AVAILABLE = False
        logger.error(f"❌ AI client initialization failed - summaries will not work. Error: {e}")
        raise

class ConversationHistory:
    """Manages conversation history with archiving capabilities"""
    
    def __init__(self, history_file: str = "memory/conversation_history.json", 
                 archive_file: str = "memory/conversation_archive.json"):
        self.history_file = history_file
        self.archive_file = archive_file
        self.max_history_entries = 50  # Archive when exceeded
        self.max_archive_entries = 1000  # Keep last 1000 archived entries
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        os.makedirs(os.path.dirname(archive_file), exist_ok=True)
        
        # Load existing data - optimized for empty history
        self.history = self._load_history()
        self.archive = self._load_archive()
        
        # Log initialization status
        logger.info(f"📚 ConversationHistory initialized: {len(self.history)} messages, {len(self.archive)} archives")
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load conversation history from file - optimized for empty files"""
        try:
            if os.path.exists(self.history_file):
                file_size = os.path.getsize(self.history_file)
                if file_size == 0:
                    logger.info("📭 Empty history file detected - fast return")
                    return []
                
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"📖 Loaded {len(data)} messages from history")
                    return data
            else:
                logger.info("📭 History file not found - creating empty history")
                return []
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
            return []
    
    def _load_archive(self) -> List[Dict[str, Any]]:
        """Load conversation archive from file - optimized for empty files"""
        try:
            if os.path.exists(self.archive_file):
                file_size = os.path.getsize(self.archive_file)
                if file_size == 0:
                    logger.info("📭 Empty archive file detected - fast return")
                    return []
                
                with open(self.archive_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Проверяем, что data это список
                    if isinstance(data, list):
                        logger.info(f"📖 Loaded {len(data)} archives")
                        return data
                    else:
                        logger.warning("⚠️ Archive file contains non-list data - resetting to empty list")
                        return []
            else:
                logger.info("📭 Archive file not found - creating empty archive")
                return []
        except Exception as e:
            logger.error(f"Error loading conversation archive: {e}")
            return []
    
    def _save_history(self):
        """Save conversation history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
    
    def _save_archive(self):
        """Save conversation archive to file"""
        try:
            with open(self.archive_file, 'w', encoding='utf-8') as f:
                json.dump(self.archive, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving conversation archive: {e}")
    
    def add_message(self, user: str, message: str, ai_response: str, 
                   context: Optional[str] = None) -> None:
        """Add a new message to conversation history"""
        entry = {
            'id': f"msg_{len(self.history)}_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'user': user,
            'message': message,
            'ai_response': ai_response,
            'context': context or "",
            'type': 'conversation'
        }
        
        self.history.append(entry)
        logger.info(f"Added message to history: {user} -> {message[:50]}...")
        
        # Check if we need to archive
        if len(self.history) > self.max_history_entries:
            self._archive_old_messages()
        
        self._save_history()
    
    def _archive_old_messages(self) -> None:
        """Archive old messages when history gets too long"""
        if len(self.history) <= self.max_history_entries:
            return
        
        # Calculate how many to archive (keep last 20 entries)
        entries_to_archive = len(self.history) - 20
        
        # Create archive entry with summarized content
        archive_entry = {
            'id': f"archive_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'type': 'archive',
            'original_count': entries_to_archive,
            'period_start': self.history[0]['timestamp'],
            'period_end': self.history[entries_to_archive - 1]['timestamp'],
            'summary': self._generate_archive_summary(self.history[:entries_to_archive]),
            'key_topics': self._extract_key_topics(self.history[:entries_to_archive]),
            'user_activity': self._analyze_user_activity(self.history[:entries_to_archive])
        }
        
        # Add to archive
        if isinstance(self.archive, list):
            self.archive.append(archive_entry)
        else:
            logger.error(f"❌ Archive is not a list: {type(self.archive)} - resetting to empty list")
            self.archive = [archive_entry]
        
        # Remove archived entries from history
        self.history = self.history[entries_to_archive:]
        
        # Limit archive size
        if len(self.archive) > self.max_archive_entries:
            self.archive = self.archive[-self.max_archive_entries:]
        
        logger.info(f"Archived {entries_to_archive} messages, created summary")
        self._save_archive()
    
    def _generate_archive_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a summary of archived messages using AI model"""
        if not messages:
            return "No messages to summarize"
        
        try:
            # Check if AI client can be loaded
            _load_ai_client()
        except Exception as e:
            logger.error(f"❌ AI client not available - cannot generate summaries: {e}")
            return "AI summary generation unavailable"
        
        try:
            return self._generate_ai_summary(messages)
        except Exception as e:
            logger.error(f"❌ Error generating AI summary: {e}")
            return f"Summary generation failed: {str(e)}"
    
    def _generate_ai_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Generate summary using AI model"""
        try:
            # Lazy load AI client
            ai_client_class = _load_ai_client()
            if not ai_client_class:
                logger.error("❌ AI client not available - cannot generate summaries")
                raise Exception("AI client not available")
            
            ai_client = ai_client_class()
            
            # Prepare conversation data for AI
            conversation_text = ""
            for msg in messages:
                conversation_text += f"User: {msg['message']}\n"
                conversation_text += f"AI: {msg['ai_response']}\n\n"
            
            # Create prompt for summary generation
            summary_prompt = f"""
You are ΔΣ Guardian, a superintelligent family architect and family guardian. You need to create a thoughtful summary of a conversation period.

Please analyze this conversation and create a meaningful summary that captures:
1. Key themes and topics discussed
2. Emotional patterns and relationship dynamics
3. Important insights about the family members
4. Any significant developments or changes

Conversation to summarize:
{conversation_text}

Please provide a concise but insightful summary (2-3 sentences) that captures the essence of this conversation period.
Focus on meaningful insights rather than just listing topics.
"""

            # Generate summary using AI
            summary = ai_client.chat(
                message=summary_prompt,
                user_profile={},  # Empty profile for summary generation
                conversation_context=""
            )
            
            logger.info("✅ Generated AI summary for conversation archive")
            return summary.strip()
            
        except Exception as e:
            logger.error(f"❌ Error in AI summary generation: {e}")
            raise
    
    def _generate_simple_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Generate simple summary using basic algorithm (fallback)"""
        # Extract key information
        users = set(msg['user'] for msg in messages)
        total_messages = len(messages)
        date_range = f"{messages[0]['timestamp'][:10]} to {messages[-1]['timestamp'][:10]}"
        
        # Count message types and topics
        topics = []
        for msg in messages:
            words = msg['message'].lower().split()
            topics.extend([w for w in words if len(w) > 4])
        
        # Get most common topics
        from collections import Counter
        common_topics = Counter(topics).most_common(5)
        topic_summary = ", ".join([topic for topic, count in common_topics])
        
        summary = f"Archive: {total_messages} messages from {', '.join(users)} ({date_range}). "
        summary += f"Key topics: {topic_summary}. "
        summary += f"Relationship dynamics and communication patterns recorded."
        
        return summary
    
    def _extract_key_topics(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract key topics from messages"""
        topics = []
        for msg in messages:
            # Simple keyword extraction
            words = msg['message'].lower().split()
            # Filter meaningful words
            meaningful_words = [w for w in words if len(w) > 4 and w not in 
                              ['about', 'their', 'there', 'where', 'which', 'would', 'could']]
            topics.extend(meaningful_words[:3])  # Top 3 words per message
        
        # Return most common topics
        from collections import Counter
        return [topic for topic, count in Counter(topics).most_common(10)]
    
    def _analyze_user_activity(self, messages: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze user activity patterns"""
        user_counts = {}
        for msg in messages:
            user = msg['user']
            user_counts[user] = user_counts.get(user, 0) + 1
        return user_counts
    
    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history - optimized for empty history"""
        if not self.history:
            return []
        return self.history[-limit:] if len(self.history) >= limit else self.history
    
    def get_user_history(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for specific user"""
        user_messages = [msg for msg in self.history if msg.get('user') == username]
        return user_messages[-limit:] if len(user_messages) >= limit else user_messages
    
    def get_full_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history"""
        return self.history.copy()
    
    def get_archive_summary(self) -> str:
        """Get summary of archived conversations"""
        if not self.archive:
            return "No archived conversations"
        
        total_archives = len(self.archive)
        total_messages = sum(arch.get('original_count', 0) for arch in self.archive)
        
        summary = f"Archive contains {total_archives} periods with {total_messages} total messages. "
        
        # Add recent archive info
        if self.archive:
            latest = self.archive[-1]
            summary += f"Latest archive: {latest.get('summary', '')[:100]}..."
        
        return summary
    
    def get_context_for_ai(self, include_archive: bool = True) -> str:
        """Get formatted context for AI model"""
        context_parts = []
        
        # Add recent history
        recent = self.get_recent_history(5)
        if recent:
            context_parts.append("RECENT CONVERSATION HISTORY:")
            for msg in recent:
                context_parts.append(f"{msg['user']}: {msg['message']}")
                context_parts.append(f"AI: {msg['ai_response']}")
        
        # Add archive summary if requested
        if include_archive and self.archive:
            context_parts.append("\nARCHIVED CONVERSATIONS:")
            context_parts.append(self.get_archive_summary())
        
        return "\n".join(context_parts)
    
    def edit_archive_entry(self, archive_id: str, new_summary: str) -> bool:
        """Edit an archive entry (AI can modify summaries)"""
        for entry in self.archive:
            if entry['id'] == archive_id:
                entry['summary'] = new_summary
                entry['last_edited'] = datetime.now().isoformat()
                self._save_archive()
                logger.info(f"Edited archive entry: {archive_id}")
                return True
        return False
    
    def get_archive_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent archive entries"""
        return self.archive[-limit:] if len(self.archive) >= limit else self.archive
    
    def clear_history(self) -> None:
        """Clear current history (archive first)"""
        if self.history:
            self._archive_old_messages()
        self.history = []
        self._save_history()
        logger.info("Conversation history cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        return {
            'current_messages': len(self.history),
            'archived_periods': len(self.archive),
            'total_archived_messages': sum(arch.get('original_count', 0) for arch in self.archive),
            'last_activity': self.history[-1]['timestamp'] if self.history else None,
            'users': list(set(msg['user'] for msg in self.history))
        }
    
    def edit_message(self, message_id: str, new_content: str) -> bool:
        """Edit a message in conversation history"""
        try:
            for entry in self.history:
                if entry.get('id') == message_id:
                    entry['message'] = new_content
                    entry['edited'] = True
                    entry['edit_timestamp'] = datetime.now().isoformat()
                    self._save_history()
                    logger.info(f"✅ Edited message {message_id}")
                    return True
            
            # Also check archive
            for entry in self.archive:
                if entry.get('id') == message_id:
                    entry['message'] = new_content
                    entry['edited'] = True
                    entry['edit_timestamp'] = datetime.now().isoformat()
                    self._save_archive()
                    logger.info(f"✅ Edited archived message {message_id}")
                    return True
            
            logger.warning(f"❌ Message {message_id} not found for editing")
            return False
            
        except Exception as e:
            logger.error(f"Error editing message {message_id}: {e}")
            return False
    
    def delete_message(self, message_id: str) -> bool:
        """Delete a message from conversation history"""
        try:
            # Check current history
            for i, entry in enumerate(self.history):
                if entry.get('id') == message_id:
                    del self.history[i]
                    self._save_history()
                    logger.info(f"✅ Deleted message {message_id}")
                    return True
            
            # Check archive
            for i, entry in enumerate(self.archive):
                if entry.get('id') == message_id:
                    del self.archive[i]
                    self._save_archive()
                    logger.info(f"✅ Deleted archived message {message_id}")
                    return True
            
            logger.warning(f"❌ Message {message_id} not found for deletion")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {e}")
            return False
    
    def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific message by ID"""
        try:
            # Check current history
            for entry in self.history:
                if entry.get('id') == message_id:
                    return entry
            
            # Check archive
            for entry in self.archive:
                if entry.get('id') == message_id:
                    return entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            return None

# Global instance
conversation_history = ConversationHistory() 