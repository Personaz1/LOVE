import os
import time
import logging
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime
import json

import google.generativeai as genai
from openai import OpenAI

from prompts.psychologist_prompt import PSYCHOLOGIST_SYSTEM_PROMPT
from memory.user_profiles import UserProfile
from memory.conversation_history import ConversationHistory
from shared_context import SharedContext
from profile_updater import profile_updater

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Initialize OpenAI as fallback
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Initialize profile and memory systems
        self.profile_manager = profile_updater  # Use the global profile_updater
        self.conversation_history = ConversationHistory()
        self.shared_context = SharedContext()
    
    async def generate_streaming_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using the best available AI model"""
        try:
            return await self._generate_gemini_streaming_response(
                system_prompt, user_message, context, user_profile
            )
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            logger.info("🔄 Falling back to OpenAI streaming...")
            return await self._generate_openai_streaming_response(
                system_prompt, user_message, context, user_profile
            )
    
    async def _generate_gemini_streaming_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ):
        """Generate streaming response using Gemini 2.0 Flash"""
        api_start_time = time.time()
        
        # Build comprehensive prompt
        full_prompt = self._build_prompt(system_prompt, user_message, context, user_profile)
        
        try:
            logger.info("🌐 Making Gemini streaming API call...")
            
            # Use generate_content with stream=True for streaming
            response_stream = self.gemini_model.generate_content(
                full_prompt,
                stream=True
            )
            
            chunk_count = 0
            full_response = ""
            function_calls_made = []
            
            for chunk in response_stream:
                chunk_count += 1
                if chunk and hasattr(chunk, 'text') and chunk.text:
                    chunk_text = chunk.text
                    full_response += chunk_text
                    
                    # Check for function calls in the chunk
                    function_calls = self._extract_function_calls(chunk_text)
                    for func_call in function_calls:
                        if func_call not in function_calls_made:
                            self._execute_function_call(func_call)
                            function_calls_made.append(func_call)
                    
                    logger.debug(f"📄 Received chunk {chunk_count}: {len(chunk_text)} chars")
                    yield chunk_text
                elif chunk and hasattr(chunk, 'parts') and chunk.parts:
                    for part in chunk.parts:
                        if hasattr(part, 'text') and part.text:
                            part_text = part.text
                            full_response += part_text
                            
                            # Check for function calls in the part
                            function_calls = self._extract_function_calls(part_text)
                            for func_call in function_calls:
                                if func_call not in function_calls_made:
                                    self._execute_function_call(func_call)
                                    function_calls_made.append(func_call)
                            
                            logger.debug(f"📄 Received part {chunk_count}: {len(part_text)} chars")
                            yield part_text
            
            # Check for function calls in the complete response
            function_calls = self._extract_function_calls(full_response)
            for func_call in function_calls:
                if func_call not in function_calls_made:
                    self._execute_function_call(func_call)
                    function_calls_made.append(func_call)
            
            api_time = time.time() - api_start_time
            logger.info(f"🌐 Gemini streaming API call completed in {api_time:.2f}s")
            logger.info(f"📊 Total chunks received: {chunk_count}")
            logger.info(f"🔧 Function calls made: {len(function_calls_made)}")
            
            if chunk_count == 0:
                logger.warning("⚠️ No chunks received from Gemini streaming")
                yield "I'm here to help you with your relationship questions. Could you please tell me more about what's on your mind?"
                
        except Exception as e:
            logger.error(f"🌐 Gemini streaming error: {e}")
            # Fallback to non-streaming
            try:
                logger.info("🔄 Falling back to non-streaming Gemini...")
                response = await self._generate_gemini_response(
                    system_prompt, user_message, context, user_profile
                )
                yield response
            except Exception as fallback_error:
                logger.error(f"🌐 Gemini fallback also failed: {fallback_error}")
                yield "I'm experiencing some technical difficulties. Please try again in a moment."
    
    async def _generate_openai_streaming_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ):
        """Generate streaming response using OpenAI"""
        api_start_time = time.time()
        
        # Build comprehensive prompt
        full_prompt = self._build_prompt(system_prompt, user_message, context, user_profile)
        
        try:
            logger.info("🤖 Making OpenAI streaming API call...")
            
            response_stream = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                stream=True,
                max_tokens=1000,
                temperature=0.7
            )
            
            chunk_count = 0
            for chunk in response_stream:
                chunk_count += 1
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    logger.debug(f"🤖 Received chunk {chunk_count}: {len(content)} chars")
                    yield content
            
            api_time = time.time() - api_start_time
            logger.info(f"🤖 OpenAI streaming API call completed in {api_time:.2f}s")
            logger.info(f"📊 Total chunks received: {chunk_count}")
            
        except Exception as e:
            logger.error(f"🤖 OpenAI streaming error: {e}")
            yield "I'm experiencing some technical difficulties. Please try again in a moment."
    
    async def _generate_gemini_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate non-streaming response using Gemini (fallback)"""
        full_prompt = self._build_prompt(system_prompt, user_message, context, user_profile)
        
        try:
            response = self.gemini_model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"🌐 Gemini non-streaming error: {e}")
            return "I'm experiencing some technical difficulties. Please try again in a moment."
    
    def _build_prompt(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build comprehensive prompt with context and profile"""
        prompt_parts = []
        
        # Add system prompt
        prompt_parts.append(system_prompt)
        
        # Add user profile information
        if user_profile:
            profile_info = f"""
## USER PROFILE
- Current Feeling: {user_profile.get('current_feeling', 'Not specified')}
- Relationship Status: {user_profile.get('relationship_status', 'Not specified')}
- Profile: {user_profile.get('profile', 'Not specified')}
"""
            prompt_parts.append(profile_info)
        
        # Add conversation context
        if context:
            prompt_parts.append(f"## CONVERSATION CONTEXT\n{context}")
        
        # Add emotional history and trends
        try:
            emotional_history = self.profile_manager.get_emotional_history(limit=5)
            if emotional_history:
                history_text = "## RECENT EMOTIONAL HISTORY\n"
                for entry in emotional_history:
                    history_text += f"- {entry.get('date', 'Unknown')} {entry.get('time', '')}: {entry.get('feeling', 'Unknown')} (was: {entry.get('previous_feeling', 'Unknown')})\n"
                prompt_parts.append(history_text)
            
            trends = self.profile_manager.get_emotional_trends()
            if trends and trends.get('trend') != 'No data':
                trends_text = f"## EMOTIONAL TRENDS\n- Overall Trend: {trends.get('trend', 'Unknown')}\n- Most Common Feeling: {trends.get('most_common', 'Unknown')}\n"
                prompt_parts.append(trends_text)
        except Exception as e:
            logger.error(f"Error getting emotional history: {e}")
        
        # Add user message
        prompt_parts.append(f"\n## USER MESSAGE\n{user_message}")
        
        # Add instructions for emotion detection and function calls
        prompt_parts.append("""
## IMPORTANT INSTRUCTIONS
1. If the user expresses any emotional state (explicitly or implicitly), immediately update their current feeling using the update_current_feeling() function
2. Provide empathetic, supportive response
3. Consider emotional trends and patterns in your advice
4. Be natural and conversational in your response

## AVAILABLE FUNCTIONS
You can call these functions to update user data:

def update_current_feeling(username, feeling, context=""):
    \"\"\"Update user's emotional state\"\"\"
    return profile_updater.update_current_feeling(feeling, context)

def update_relationship_status(username, status):
    \"\"\"Update relationship status\"\"\"
    return profile_updater.update_relationship_status(status)

def update_user_profile(username, profile_data):
    \"\"\"Update user profile\"\"\"
    return profile_updater.update_user_profile(username, profile_data)

def add_diary_entry(username, entry):
    \"\"\"Add diary entry\"\"\"
    return profile_updater.add_diary_entry(username, entry)

def add_relationship_insight(insight):
    \"\"\"Add relationship insight\"\"\"
    return profile_updater.add_relationship_insight(insight)

## FUNCTION CALL EXAMPLES
When you detect emotions, call functions like this:
- update_current_feeling("meranda", "Happy", "User expressed joy")
- update_current_feeling("meranda", "Sad", "User shared feeling down")
- update_relationship_status("meranda", "Feeling connected")

IMPORTANT: Call these functions when you detect emotional content, then provide your natural response.
""")
        
        return "\n".join(prompt_parts)
    
    # Function wrappers for the model to call
    def update_current_feeling(self, username: str, feeling: str, context: str = "") -> bool:
        """Update user's emotional state - called by model"""
        try:
            result = self.profile_manager.update_current_feeling(feeling, context)
            logger.info(f"💭 Model updated feeling: {username} -> {feeling} (context: {context})")
            return result
        except Exception as e:
            logger.error(f"Error in update_current_feeling: {e}")
            return False
    
    def update_relationship_status(self, username: str, status: str) -> bool:
        """Update relationship status - called by model"""
        try:
            result = self.profile_manager.update_relationship_status(status)
            logger.info(f"💕 Model updated relationship status: {username} -> {status}")
            return result
        except Exception as e:
            logger.error(f"Error in update_relationship_status: {e}")
            return False
    
    def update_user_profile(self, username: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile - called by model"""
        try:
            result = self.profile_manager.update_user_profile(username, profile_data)
            logger.info(f"🔄 Model updated profile: {username}")
            return result
        except Exception as e:
            logger.error(f"Error in update_user_profile: {e}")
            return False
    
    def add_diary_entry(self, username: str, entry: Dict[str, Any]) -> bool:
        """Add diary entry - called by model"""
        try:
            result = self.profile_manager.add_diary_entry(username, entry)
            logger.info(f"📖 Model added diary entry: {username}")
            return result
        except Exception as e:
            logger.error(f"Error in add_diary_entry: {e}")
            return False
    
    def add_relationship_insight(self, insight: str) -> bool:
        """Add relationship insight - called by model"""
        try:
            result = self.profile_manager.add_relationship_insight(insight)
            logger.info(f"💡 Model added insight: {insight[:50]}...")
            return result
        except Exception as e:
            logger.error(f"Error in add_relationship_insight: {e}")
            return False
    
    # File system functions for multi-step agency
    def read_user_profile(self, username: str) -> str:
        """Read user's profile file - called by model"""
        try:
            profile = self.profile_manager.get_profile()
            return f"Profile for {username}: {json.dumps(profile, indent=2, ensure_ascii=False)}"
        except Exception as e:
            logger.error(f"Error reading profile for {username}: {e}")
            return f"Error reading profile for {username}: {str(e)}"
    
    def read_emotional_history(self, username: str) -> str:
        """Read emotional history file - called by model"""
        try:
            history = self.profile_manager.get_emotional_history(limit=20)
            return f"Emotional history for {username}: {json.dumps(history, indent=2, ensure_ascii=False)}"
        except Exception as e:
            logger.error(f"Error reading emotional history for {username}: {e}")
            return f"Error reading emotional history for {username}: {str(e)}"
    
    def read_diary_entries(self, username: str) -> str:
        """Read user's diary entries - called by model"""
        try:
            # This would need to be implemented in profile_updater
            return f"Diary entries for {username}: Not implemented yet"
        except Exception as e:
            logger.error(f"Error reading diary for {username}: {e}")
            return f"Error reading diary for {username}: {str(e)}"
    
    def write_insight_to_file(self, username: str, insight: str) -> bool:
        """Save insight to file - called by model"""
        try:
            result = self.profile_manager.add_relationship_insight(insight)
            logger.info(f"💾 Model wrote insight to file for {username}: {insight[:50]}...")
            return result
        except Exception as e:
            logger.error(f"Error writing insight for {username}: {e}")
            return False
    
    def search_user_data(self, username: str, query: str) -> str:
        """Search user's data files - called by model"""
        try:
            # Search in profile
            profile = self.profile_manager.get_profile()
            profile_text = json.dumps(profile, ensure_ascii=False)
            
            # Search in emotional history
            history = self.profile_manager.get_emotional_history(limit=50)
            history_text = json.dumps(history, ensure_ascii=False)
            
            # Simple text search
            results = []
            if query.lower() in profile_text.lower():
                results.append("Found in profile")
            if query.lower() in history_text.lower():
                results.append("Found in emotional history")
            
            return f"Search results for '{query}' in {username}'s data: {', '.join(results) if results else 'No matches found'}"
        except Exception as e:
            logger.error(f"Error searching data for {username}: {e}")
            return f"Error searching data for {username}: {str(e)}"
    
    def read_file(self, path: str) -> str:
        """Read any file in the system - called by model"""
        try:
            import os
            if not os.path.exists(path):
                return f"File not found: {path}"
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"File {path} content:\n{content}"
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return f"Error reading file {path}: {str(e)}"
    
    def write_file(self, path: str, content: str) -> bool:
        """Write content to file - called by model"""
        try:
            import os
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"💾 Model wrote to file: {path}")
            return True
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            return False
    
    def list_directory(self, path: str) -> str:
        """List files in directory - called by model"""
        try:
            import os
            if not os.path.exists(path):
                return f"Directory not found: {path}"
            
            files = os.listdir(path)
            return f"Files in {path}:\n" + "\n".join(files)
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            return f"Error listing directory {path}: {str(e)}"
    
    def search_files(self, query: str) -> str:
        """Search across all files - called by model"""
        try:
            import os
            import glob
            
            # Search in memory directory
            memory_files = glob.glob("memory/**/*.json", recursive=True)
            results = []
            
            for file_path in memory_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if query.lower() in content.lower():
                            results.append(file_path)
                except:
                    continue
            
            return f"Files containing '{query}':\n" + "\n".join(results) if results else f"No files found containing '{query}'"
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return f"Error searching files: {str(e)}"
    
    def get_file_info(self, path: str) -> str:
        """Get file metadata - called by model"""
        try:
            import os
            if not os.path.exists(path):
                return f"File not found: {path}"
            
            stat = os.stat(path)
            return f"File info for {path}:\nSize: {stat.st_size} bytes\nModified: {datetime.fromtimestamp(stat.st_mtime)}"
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return f"Error getting file info for {path}: {str(e)}"
    
    def _extract_function_calls(self, text: str) -> List[str]:
        """Extract function calls from text"""
        import re
        
        # Look for function call patterns
        patterns = [
            r'update_current_feeling\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']*)["\'])?\s*\)',
            r'update_relationship_status\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)',
            r'update_user_profile\s*\(\s*["\']([^"\']+)["\']\s*,\s*\{([^}]+)\}\s*\)',
            r'add_diary_entry\s*\(\s*["\']([^"\']+)["\']\s*,\s*\{([^}]+)\}\s*\)',
            r'add_relationship_insight\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'read_user_profile\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'read_emotional_history\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'read_diary_entries\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'write_insight_to_file\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)',
            r'search_user_data\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)',
            r'read_file\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'write_file\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)',
            r'list_directory\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'search_files\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'get_file_info\s*\(\s*["\']([^"\']+)["\']\s*\)'
        ]
        
        function_calls = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if pattern == patterns[0]:  # update_current_feeling
                    username, feeling, context = match[0], match[1], match[2] if len(match) > 2 else ""
                    function_calls.append(f"update_current_feeling({username}, {feeling}, {context})")
                elif pattern == patterns[1]:  # update_relationship_status
                    username, status = match[0], match[1]
                    function_calls.append(f"update_relationship_status({username}, {status})")
                elif pattern == patterns[2]:  # update_user_profile
                    username, profile_data = match[0], match[1]
                    function_calls.append(f"update_user_profile({username}, {profile_data})")
                elif pattern == patterns[3]:  # add_diary_entry
                    username, entry = match[0], match[1]
                    function_calls.append(f"add_diary_entry({username}, {entry})")
                elif pattern == patterns[4]:  # add_relationship_insight
                    insight = match[0]
                    function_calls.append(f"add_relationship_insight({insight})")
                elif pattern == patterns[5]:  # read_user_profile
                    username = match[0]
                    function_calls.append(f"read_user_profile({username})")
                elif pattern == patterns[6]:  # read_emotional_history
                    username = match[0]
                    function_calls.append(f"read_emotional_history({username})")
                elif pattern == patterns[7]:  # read_diary_entries
                    username = match[0]
                    function_calls.append(f"read_diary_entries({username})")
                elif pattern == patterns[8]:  # write_insight_to_file
                    username, insight = match[0], match[1]
                    function_calls.append(f"write_insight_to_file({username}, {insight})")
                elif pattern == patterns[9]:  # search_user_data
                    username, query = match[0], match[1]
                    function_calls.append(f"search_user_data({username}, {query})")
                elif pattern == patterns[10]:  # read_file
                    path = match[0]
                    function_calls.append(f"read_file({path})")
                elif pattern == patterns[11]:  # write_file
                    path, content = match[0], match[1]
                    function_calls.append(f"write_file({path}, {content})")
                elif pattern == patterns[12]:  # list_directory
                    path = match[0]
                    function_calls.append(f"list_directory({path})")
                elif pattern == patterns[13]:  # search_files
                    query = match[0]
                    function_calls.append(f"search_files({query})")
                elif pattern == patterns[14]:  # get_file_info
                    path = match[0]
                    function_calls.append(f"get_file_info({path})")
        
        return function_calls
    
    def _execute_function_call(self, func_call: str):
        """Execute a function call extracted from model response"""
        try:
            logger.info(f"🔧 Executing function call: {func_call}")
            
            if func_call.startswith("update_current_feeling("):
                # Extract parameters
                import re
                match = re.search(r'update_current_feeling\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']*)["\'])?\s*\)', func_call)
                if match:
                    username = match.group(1)
                    feeling = match.group(2)
                    context = match.group(3) if match.group(3) else ""
                    self.update_current_feeling(username, feeling, context)
            
            elif func_call.startswith("update_relationship_status("):
                match = re.search(r'update_relationship_status\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    username = match.group(1)
                    status = match.group(2)
                    self.update_relationship_status(username, status)
            
            elif func_call.startswith("add_diary_entry("):
                match = re.search(r'add_diary_entry\s*\(\s*["\']([^"\']+)["\']\s*,\s*\{([^}]+)\}\s*\)', func_call)
                if match:
                    username = match.group(1)
                    entry_str = match.group(2)
                    # Parse entry as dict
                    try:
                        entry = eval(f"{{{entry_str}}}")
                        self.add_diary_entry(username, entry)
                    except:
                        logger.error(f"Failed to parse diary entry: {entry_str}")
            
            elif func_call.startswith("add_relationship_insight("):
                match = re.search(r'add_relationship_insight\s*\(\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    insight = match.group(1)
                    self.add_relationship_insight(insight)
            
            elif func_call.startswith("read_user_profile("):
                match = re.search(r'read_user_profile\s*\(\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    username = match.group(1)
                    result = self.read_user_profile(username)
                    logger.info(f"📖 Model read profile for {username}")
            
            elif func_call.startswith("read_emotional_history("):
                match = re.search(r'read_emotional_history\s*\(\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    username = match.group(1)
                    result = self.read_emotional_history(username)
                    logger.info(f"📊 Model read emotional history for {username}")
            
            elif func_call.startswith("read_diary_entries("):
                match = re.search(r'read_diary_entries\s*\(\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    username = match.group(1)
                    result = self.read_diary_entries(username)
                    logger.info(f"📖 Model read diary for {username}")
            
            elif func_call.startswith("write_insight_to_file("):
                match = re.search(r'write_insight_to_file\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    username = match.group(1)
                    insight = match.group(2)
                    self.write_insight_to_file(username, insight)
            
            elif func_call.startswith("search_user_data("):
                match = re.search(r'search_user_data\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    username = match.group(1)
                    query = match.group(2)
                    result = self.search_user_data(username, query)
                    logger.info(f"🔍 Model searched data for {username}: {query}")
            
            elif func_call.startswith("read_file("):
                match = re.search(r'read_file\s*\(\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    path = match.group(1)
                    result = self.read_file(path)
                    logger.info(f"📄 Model read file: {path}")
            
            elif func_call.startswith("write_file("):
                match = re.search(r'write_file\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    path = match.group(1)
                    content = match.group(2)
                    self.write_file(path, content)
            
            elif func_call.startswith("list_directory("):
                match = re.search(r'list_directory\s*\(\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    path = match.group(1)
                    result = self.list_directory(path)
                    logger.info(f"📁 Model listed directory: {path}")
            
            elif func_call.startswith("search_files("):
                match = re.search(r'search_files\s*\(\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    query = match.group(1)
                    result = self.search_files(query)
                    logger.info(f"🔍 Model searched files: {query}")
            
            elif func_call.startswith("get_file_info("):
                match = re.search(r'get_file_info\s*\(\s*["\']([^"\']+)["\']\s*\)', func_call)
                if match:
                    path = match.group(1)
                    result = self.get_file_info(path)
                    logger.info(f"ℹ️ Model got file info: {path}")
                    
        except Exception as e:
            logger.error(f"Error executing function call {func_call}: {e}") 