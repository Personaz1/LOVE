import os
import time
import logging
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime
import json
from dotenv import load_dotenv

import google.generativeai as genai

# Load environment variables
load_dotenv()

from prompts.psychologist_prompt import AI_GUARDIAN_SYSTEM_PROMPT
from memory.user_profiles import UserProfile
from memory.conversation_history import ConversationHistory
from shared_context import SharedContextManager
from profile_updater import profile_updater
from file_agent import file_agent

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        # Initialize Gemini with explicit API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Initialize profile and memory systems
        self.profile_manager = profile_updater  # Use the global profile_updater
        self.conversation_history = ConversationHistory()
        self.shared_context = SharedContextManager()
    
    async def generate_streaming_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using Gemini AI model"""
        try:
            async for chunk in self._generate_gemini_streaming_response(
                system_prompt, user_message, context, user_profile
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            yield f"Error: Unable to generate response. Please try again."
    
    async def _generate_gemini_streaming_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ):
        """Generate streaming response using Gemini 2.0 Flash with proper multi-step reasoning"""
        api_start_time = time.time()
        
        # Step 1: Generate initial response with tool calls
        thinking_prompt = self._build_thinking_prompt(system_prompt, user_message, context, user_profile)
        
        try:
            logger.info("🧠 Step 1: Generating thinking response...")
            
            # Get initial response that may contain tool calls
            initial_response = self.gemini_model.generate_content(thinking_prompt)
            initial_text = initial_response.text if hasattr(initial_response, 'text') else str(initial_response)
            
            # Extract and execute tool calls
            tool_calls = self._extract_tool_calls(initial_text)
            tool_results = []
            
            for tool_call in tool_calls:
                logger.info(f"🔧 Executing tool call: {tool_call}")
                try:
                    result = self._execute_tool_call(tool_call)
                    tool_results.append(f"Tool {tool_call} returned: {result}")
                except Exception as e:
                    logger.error(f"❌ Tool call failed: {e}")
                    tool_results.append(f"Tool {tool_call} failed: {str(e)}")
            
            # Step 2: Generate final response with tool results
            final_prompt = self._build_final_prompt(
                system_prompt, user_message, context, user_profile, 
                initial_text, tool_results
            )
            
            logger.info("💬 Step 2: Generating final response...")
            
            # Stream the final response
            response_stream = self.gemini_model.generate_content(
                final_prompt,
                stream=True
            )
            
            chunk_count = 0
            for chunk in response_stream:
                chunk_count += 1
                if chunk and hasattr(chunk, 'text') and chunk.text:
                    chunk_text = chunk.text
                    logger.debug(f"📄 Received chunk {chunk_count}: {len(chunk_text)} chars")
                    yield chunk_text
                elif chunk and hasattr(chunk, 'parts') and chunk.parts:
                    for part in chunk.parts:
                        if hasattr(part, 'text') and part.text:
                            part_text = part.text
                            logger.debug(f"📄 Received part {chunk_count}: {len(part_text)} chars")
                            yield part_text
            
            api_time = time.time() - api_start_time
            logger.info(f"🌐 Multi-step streaming completed in {api_time:.2f}s")
            logger.info(f"📊 Total chunks received: {chunk_count}")
            logger.info(f"🔧 Tool calls executed: {len(tool_calls)}")
            
            if chunk_count == 0:
                logger.warning("⚠️ No chunks received from final response")
                yield "I'm here to help you with your relationship questions. Could you please tell me more about what's on your mind?"
                
        except Exception as e:
            logger.error(f"🌐 Multi-step streaming error: {e}")
            yield "I'm experiencing some technical difficulties. Please try again in a moment."
    

    
    async def _generate_gemini_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate non-streaming response using Gemini (fallback)"""
        # Use the same multi-step approach for consistency
        thinking_prompt = self._build_thinking_prompt(system_prompt, user_message, context, user_profile)
        
        try:
            # Step 1: Get thinking response
            initial_response = self.gemini_model.generate_content(thinking_prompt)
            initial_text = initial_response.text if hasattr(initial_response, 'text') else str(initial_response)
            
            # Extract and execute tool calls
            tool_calls = self._extract_tool_calls(initial_text)
            tool_results = []
            
            for tool_call in tool_calls:
                try:
                    result = self._execute_tool_call(tool_call)
                    tool_results.append(f"Tool {tool_call} returned: {result}")
                except Exception as e:
                    tool_results.append(f"Tool {tool_call} failed: {str(e)}")
            
            # Step 2: Generate final response
            final_prompt = self._build_final_prompt(
                system_prompt, user_message, context, user_profile, 
                initial_text, tool_results
            )
            
            response = self.gemini_model.generate_content(final_prompt)
            return response.text
        except Exception as e:
            logger.error(f"🌐 Gemini non-streaming error: {e}")
            return "I'm experiencing some technical difficulties. Please try again in a moment."
    
    def _build_thinking_prompt(
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
        
        # Add instructions for thinking and tool calling
        prompt_parts.append("""
## THINKING PHASE INSTRUCTIONS
You are in the THINKING phase. Analyze the user's message and determine what actions to take.

## AVAILABLE TOOLS
You can use these tools by wrapping them in ```tool_code blocks:

```tool_code
update_current_feeling("username", "feeling", "context")
```

```tool_code
update_relationship_status("username", "status")
```

```tool_code
update_user_profile("username", {"field": "value"})
```

```tool_code
add_diary_entry("username", {"content": "entry", "mood": "feeling"})
```

```tool_code
add_relationship_insight("insight text")
```

```tool_code
read_file("path/to/file")
```

```tool_code
write_file("path/to/file", "content")
```

## THINKING PROCESS
1. Analyze the user's emotional state and update if needed
2. Consider what tools would be helpful
3. Use tool_code blocks to call tools
4. Think about what response would be most helpful
5. Do NOT provide the final response yet - this is just the thinking phase

Example thinking response:
```tool_code
update_current_feeling("meranda", "Curious", "User asked about available tools")
```
I need to update the user's emotional state since they're asking about tools, which shows curiosity. I should also think about what tools would be most relevant to mention.
""")
        
        return "\n".join(prompt_parts)
    
    def _build_final_prompt(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        thinking_response: str = "",
        tool_results: List[str] = None
    ) -> str:
        """Build prompt for final response generation"""
        prompt_parts = []
        
        # Add system prompt
        prompt_parts.append(system_prompt)
        
        # Add context if available
        if context:
            prompt_parts.append(f"\n## CONTEXT\n{context}")
        
        # Add user profile if available
        if user_profile:
            prompt_parts.append(f"\n## USER PROFILE\n{json.dumps(user_profile, indent=2)}")
        
        # Add user message
        prompt_parts.append(f"\n## USER MESSAGE\n{user_message}")
        
        # Add thinking phase results
        if thinking_response:
            prompt_parts.append(f"\n## THINKING PHASE\n{thinking_response}")
        
        # Add tool results
        if tool_results:
            prompt_parts.append(f"\n## TOOL RESULTS\n" + "\n".join(tool_results))
        
        # Add final response instructions
        prompt_parts.append("""
## FINAL RESPONSE INSTRUCTIONS
Now provide your final response to the user. Be natural, empathetic, and helpful. 
Do NOT include any tool_code blocks in your response - those were already executed.
Focus on being a supportive guardian angel for the user's family and relationship needs.
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
        """Read any file in the system using FileAgent"""
        try:
            result = file_agent.read_file(path)
            if result.get("success"):
                return f"File {path} content:\n{result['content']}"
            else:
                return f"Error reading file {path}: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return f"Error reading file {path}: {str(e)}"
    
    def write_file(self, path: str, content: str) -> bool:
        """Write content to file using FileAgent"""
        try:
            result = file_agent.write_file(path, content)
            if result.get("success"):
                logger.info(f"💾 Model wrote to file: {path}")
                return True
            else:
                logger.error(f"❌ Failed to write to {path}: {result.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            return False
    
    def list_files(self, directory: str = "") -> str:
        """List files in directory using FileAgent"""
        try:
            result = file_agent.list_files(directory)
            if result.get("success"):
                files = result.get("files", [])
                file_list = []
                for file in files:
                    file_list.append(f"📄 {file['name']} ({file['size']} bytes)")
                return f"Files in {result['directory']}:\n" + "\n".join(file_list)
            else:
                return f"Error listing directory {directory}: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Error listing directory {directory}: {e}")
            return f"Error listing directory {directory}: {str(e)}"
    
    def search_files(self, query: str) -> str:
        """Search across all files using FileAgent"""
        try:
            result = file_agent.search_files(query)
            if result.get("success"):
                results = result.get("results", [])
                if results:
                    file_list = []
                    for file in results:
                        file_list.append(f"📄 {file['name']} ({file['matches']} matches)")
                    return f"Files containing '{query}':\n" + "\n".join(file_list)
                else:
                    return f"No files found containing '{query}'"
            else:
                return f"Error searching files: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return f"Error searching files: {str(e)}"
    
    def get_file_info(self, path: str) -> str:
        """Get file metadata using FileAgent"""
        try:
            result = file_agent.get_file_info(path)
            if result.get("success"):
                info = result
                return f"File info for {path}:\nSize: {info['size']} bytes\nModified: {datetime.fromtimestamp(info['modified'])}\nExtension: {info['extension']}\nReadable: {info['is_readable']}\nWritable: {info['is_writable']}"
            else:
                return f"Error getting file info for {path}: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return f"Error getting file info for {path}: {str(e)}"
    
    def delete_file(self, path: str) -> bool:
        """Delete file safely using FileAgent"""
        try:
            result = file_agent.delete_file(path)
            if result.get("success"):
                logger.info(f"🗑️ Model deleted file: {path}")
                return True
            else:
                logger.error(f"❌ Failed to delete {path}: {result.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            return False
    
    def _extract_tool_calls(self, text: str) -> List[str]:
        """Extract function calls from text"""
        import re
        
        # Look for tool_code blocks
        tool_code_pattern = r'```tool_code\s*\n(.*?)\n```'
        tool_calls = []
        
        matches = re.findall(tool_code_pattern, text, re.DOTALL)
        for match in matches:
            tool_calls.append(match.strip())
        
        return tool_calls
    
    def _execute_tool_call(self, tool_call: str) -> str:
        """Execute a function call extracted from model response"""
        try:
            logger.info(f"🔧 Executing tool call: {tool_call}")
            
            # Parse the tool call using ast.literal_eval for safety
            import ast
            import re
            
            # Extract function name and arguments
            func_match = re.match(r'(\w+)\s*\((.*)\)', tool_call.strip())
            if not func_match:
                return f"Invalid tool call format: {tool_call}"
            
            func_name = func_match.group(1)
            args_str = func_match.group(2)
            
            # Parse arguments safely
            try:
                # Handle different argument patterns
                if func_name == "update_current_feeling":
                    # Extract username, feeling, context
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']*)["\'])?', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        feeling = arg_match.group(2)
                        context = arg_match.group(3) if arg_match.group(3) else ""
                        result = self.update_current_feeling(username, feeling, context)
                        return f"Updated feeling to '{feeling}' for {username}"
                
                elif func_name == "update_relationship_status":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        status = arg_match.group(2)
                        result = self.update_relationship_status(username, status)
                        return f"Updated relationship status to '{status}' for {username}"
                
                elif func_name == "read_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        result = self.read_file(path)
                        return f"Read file {path}: {result[:100]}..."
                
                elif func_name == "write_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        content = arg_match.group(2)
                        result = self.write_file(path, content)
                        return f"Wrote to file {path}: {result}"
                
                elif func_name == "list_files":
                    arg_match = re.match(r'["\']([^"\']*)["\']', args_str)
                    if arg_match:
                        directory = arg_match.group(1)
                        result = self.list_files(directory)
                        return f"Listed files in {directory}: {result}"
                
                else:
                    return f"Unknown tool: {func_name}"
                    
            except Exception as parse_error:
                return f"Error parsing tool call arguments: {parse_error}"
                
        except Exception as e:
            logger.error(f"❌ Tool call execution failed: {e}")
            return f"Tool execution failed: {str(e)}"
 