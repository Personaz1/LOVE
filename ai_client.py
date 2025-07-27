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

from file_agent import file_agent

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        # Initialize Gemini with explicit API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        # Changed to gemini-2.0-flash-lite for higher rate limits (1000 RPD vs 50)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        # Initialize memory systems
        self.conversation_history = ConversationHistory()
        # Don't initialize profile_manager here - it needs username
        # Will create per-user instances when needed

    def _get_profile_manager(self, username: str) -> UserProfile:
        """Get or create profile manager for specific user"""
        return UserProfile(username)

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
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.error(f"🌐 API quota exceeded: {e}")
                yield "I've reached my daily conversation limit. Please try again tomorrow or consider upgrading to a paid plan for unlimited conversations."
            else:
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
            emotional_history = self._get_profile_manager(user_profile.get('username', 'meranda')).get_emotional_history(limit=5)
            if emotional_history:
                history_text = "## RECENT EMOTIONAL HISTORY\n"
                for entry in emotional_history:
                    history_text += f"- {entry.get('date', 'Unknown')} {entry.get('time', '')}: {entry.get('feeling', 'Unknown')} (was: {entry.get('previous_feeling', 'Unknown')})\n"
                prompt_parts.append(history_text)
            
            trends = self._get_profile_manager(user_profile.get('username', 'meranda')).get_emotional_trends()
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
        """Update user's current emotional state"""
        try:
            profile_manager = self._get_profile_manager(username)
            return profile_manager.update_current_feeling(feeling, context)
        except Exception as e:
            logger.error(f"Error updating feeling: {e}")
            return False

    def update_relationship_status(self, username: str, status: str) -> bool:
        """Update user's relationship status"""
        try:
            profile_manager = self._get_profile_manager(username)
            return profile_manager.update_relationship_status(status)
        except Exception as e:
            logger.error(f"Error updating relationship status: {e}")
            return False

    def update_user_profile(self, username: str, profile_data: Dict[str, Any]) -> bool:
        """Update user's profile information"""
        try:
            profile_manager = self._get_profile_manager(username)
            return profile_manager.update_profile(profile_data)
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return False



    def add_relationship_insight(self, username: str, insight: str) -> bool:
        """Add relationship insight for the user"""
        try:
            profile_manager = self._get_profile_manager(username)
            return profile_manager.add_relationship_insight(insight)
        except Exception as e:
            logger.error(f"Error adding relationship insight: {e}")
            return False

    def update_hidden_profile(self, username: str, hidden_profile_data: Dict[str, Any]) -> bool:
        """Update user's hidden profile (AI's private notes)"""
        try:
            profile_manager = self._get_profile_manager(username)
            return profile_manager.update_hidden_profile(hidden_profile_data)
        except Exception as e:
            logger.error(f"Error updating hidden profile: {e}")
            return False

    def read_hidden_profile(self, username: str) -> str:
        """Read user's hidden profile"""
        try:
            profile_manager = self._get_profile_manager(username)
            return profile_manager.get_hidden_profile()
        except Exception as e:
            logger.error(f"Error reading hidden profile: {e}")
            return "No hidden profile available"

    def read_user_profile(self, username: str) -> str:
        """Read user's profile information"""
        try:
            profile_manager = self._get_profile_manager(username)
            return profile_manager.get_profile()
        except Exception as e:
            logger.error(f"Error reading profile: {e}")
            return "No profile available"

    def read_emotional_history(self, username: str) -> str:
        """Read user's emotional history"""
        try:
            profile_manager = self._get_profile_manager(username)
            return profile_manager.get_emotional_history()
        except Exception as e:
            logger.error(f"Error getting emotional history: {e}")
            return "No emotional history available"


    
    def write_insight_to_file(self, username: str, insight: str) -> bool:
        """Save insight to file - called by model"""
        try:
            user_profile = self._get_profile_manager(username)
            # Add insight as relationship insight
            result = user_profile.add_relationship_insight(insight)
            logger.info(f"💾 Model wrote insight to file for {username}: {insight[:50]}...")
            return result
        except Exception as e:
            logger.error(f"Error writing insight for {username}: {e}")
            return False
    
    def search_user_data(self, username: str, query: str) -> str:
        """Search user's data files - called by model"""
        try:
            user_profile = self._get_profile_manager(username)
            
            # Search in profile
            profile = user_profile.get_profile()
            profile_text = json.dumps(profile, ensure_ascii=False)
            
            # Search in emotional history
            history = user_profile.get_emotional_history(limit=50)
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
            # Clean up the tool call
            cleaned_call = match.strip()
            if cleaned_call:
                tool_calls.append(cleaned_call)
        
        # Also look for direct function calls without tool_code blocks
        direct_pattern = r'(\w+)\s*\([^)]*\)'
        direct_matches = re.findall(direct_pattern, text)
        for match in direct_matches:
            if match not in ['print', 'len', 'str', 'int', 'float', 'bool']:  # Skip common Python functions
                # Find the full function call
                full_match = re.search(rf'{match}\s*\([^)]*\)', text)
                if full_match:
                    tool_calls.append(full_match.group(0))
        
        return tool_calls
    
    def _execute_tool_call(self, tool_call: str) -> str:
        """Execute a function call extracted from model response"""
        try:
            logger.info(f"🔧 Executing tool call: {tool_call}")
            
            # Parse the tool call using regex for safety
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
                    else:
                        return f"Invalid arguments for update_current_feeling: {args_str}"
                
                elif func_name == "update_relationship_status":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        status = arg_match.group(2)
                        result = self.update_relationship_status(username, status)
                        return f"Updated relationship status to '{status}' for {username}"
                    else:
                        return f"Invalid arguments for update_relationship_status: {args_str}"
                
                elif func_name == "update_user_profile":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*({[^}]+})', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        profile_data_str = arg_match.group(2)
                        try:
                            import json
                            profile_data = json.loads(profile_data_str)
                            result = self.update_user_profile(username, profile_data)
                            return f"Updated profile for {username}"
                        except json.JSONDecodeError:
                            return f"Invalid JSON in profile data: {profile_data_str}"
                    else:
                        return f"Invalid arguments for update_user_profile: {args_str}"
                

                
                elif func_name == "add_relationship_insight":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        insight = arg_match.group(1)
                        result = self.add_relationship_insight(username, insight)
                        return f"Added relationship insight: {insight[:50]}..."
                    else:
                        return f"Invalid arguments for add_relationship_insight: {args_str}"
                
                elif func_name == "read_user_profile":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        result = self.read_user_profile(username)
                        return f"Read profile for {username}: {result[:100]}..."
                    else:
                        return f"Invalid arguments for read_user_profile: {args_str}"
                
                elif func_name == "read_emotional_history":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        result = self.read_emotional_history(username)
                        return f"Read emotional history for {username}: {result[:100]}..."
                    else:
                        return f"Invalid arguments for read_emotional_history: {args_str}"
                
                elif func_name == "read_diary_entries":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        result = self.read_diary_entries(username)
                        return f"Read diary entries for {username}: {result[:100]}..."
                    else:
                        return f"Invalid arguments for read_diary_entries: {args_str}"
                
                elif func_name == "search_user_data":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        query = arg_match.group(2)
                        result = self.search_user_data(username, query)
                        return f"Searched data for {username}: {result[:100]}..."
                    else:
                        return f"Invalid arguments for search_user_data: {args_str}"
                
                elif func_name == "read_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        result = self.read_file(path)
                        return f"Read file {path}: {result[:100]}..."
                    else:
                        return f"Invalid arguments for read_file: {args_str}"
                
                elif func_name == "write_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        content = arg_match.group(2)
                        result = self.write_file(path, content)
                        return f"Wrote to file {path}: {result}"
                    else:
                        return f"Invalid arguments for write_file: {args_str}"
                
                elif func_name == "list_files":
                    arg_match = re.match(r'["\']([^"\']*)["\']', args_str)
                    if arg_match:
                        directory = arg_match.group(1)
                        result = self.list_files(directory)
                        return f"Listed files in {directory}: {result}"
                    else:
                        return f"Invalid arguments for list_files: {args_str}"
                
                elif func_name == "search_files":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        query = arg_match.group(1)
                        result = self.search_files(query)
                        return f"Searched files for '{query}': {result}"
                    else:
                        return f"Invalid arguments for search_files: {args_str}"
                
                elif func_name == "get_file_info":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        result = self.get_file_info(path)
                        return f"File info for {path}: {result}"
                    else:
                        return f"Invalid arguments for get_file_info: {args_str}"
                
                elif func_name == "delete_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        result = self.delete_file(path)
                        return f"Deleted file {path}: {result}"
                    else:
                        return f"Invalid arguments for delete_file: {args_str}"
                
                else:
                    return f"Unknown tool: {func_name}"
                    
            except Exception as parse_error:
                return f"Error parsing tool call arguments: {parse_error}"
                
        except Exception as e:
            logger.error(f"❌ Tool call execution failed: {e}")
            return f"Tool execution failed: {str(e)}"
 