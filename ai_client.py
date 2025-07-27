import os
import time
import logging
import re
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime
import json
from dotenv import load_dotenv

import google.generativeai as genai

# Load environment variables
load_dotenv()

from prompts.guardian_prompt import AI_GUARDIAN_SYSTEM_PROMPT
from memory.guardian_profile import guardian_profile
from memory.user_profiles import UserProfile
from memory.conversation_history import ConversationHistory

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        # Initialize Gemini with explicit API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        
        # Define available models with their quotas
        self.models = [
            {
                'name': 'gemini-2.0-flash-lite',
                'quota': 1000,
                'model': None  # Will be initialized on first use
            },
            {
                'name': 'gemini-2.0-flash', 
                'quota': 200,
                'model': None
            },
            {
                'name': 'gemini-2.5-flash-lite',
                'quota': 1000,
                'model': None
            },
            {
                'name': 'gemini-2.5-flash',
                'quota': 250,
                'model': None
            },
            {
                'name': 'gemini-2.5-pro',
                'quota': 100,
                'model': None
            },
            {
                'name': 'gemini-1.5-pro',
                'quota': 150,
                'model': None,
                'vision': True  # This model has vision capabilities
            },
            {
                'name': 'gemini-1.5-flash',
                'quota': 500,
                'model': None,
                'vision': True  # This model has vision capabilities
            }
        ]
        
        self.current_model_index = 0
        self.model_errors = {}  # Track errors per model
        
        # Initialize memory systems
        self.conversation_history = ConversationHistory()

    def _get_current_model(self):
        """Get current model, initialize if needed"""
        current_model_config = self.models[self.current_model_index]
        if current_model_config['model'] is None:
            current_model_config['model'] = genai.GenerativeModel(current_model_config['name'])
        return current_model_config['model']

    def _switch_to_next_model(self):
        """Switch to next available model"""
        self.current_model_index = (self.current_model_index + 1) % len(self.models)
        current_model_config = self.models[self.current_model_index]
        logger.info(f"🔄 Switched to model: {current_model_config['name']}")
        return current_model_config['name']

    def _handle_quota_error(self, error_msg: str):
        """Handle quota exceeded error by switching models"""
        if "quota" in error_msg.lower() or "429" in error_msg:
            model_name = self.models[self.current_model_index]['name']
            self.model_errors[model_name] = time.time()
            logger.warning(f"⚠️ Quota exceeded for {model_name}, switching model...")
            
            # Try next model
            next_model = self._switch_to_next_model()
            
            # If we've tried all models, wait and reset
            if len(self.model_errors) >= len(self.models):
                logger.error("🚫 All models have quota issues. Waiting 60 seconds...")
                time.sleep(60)
                self.model_errors.clear()
                self.current_model_index = 0
            
            return True
        return False

    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and quota information"""
        current_model = self.models[self.current_model_index]
        return {
            'current_model': current_model['name'],
            'current_quota': current_model['quota'],
            'model_index': self.current_model_index,
            'total_models': len(self.models),
            'model_errors': len(self.model_errors),
            'available_models': [
                {
                    'name': model['name'],
                    'quota': model['quota'],
                    'has_error': model['name'] in self.model_errors
                }
                for model in self.models
            ]
        }

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
        """Generate streaming response using Gemini 2.0 Flash with multi-step reasoning and tool execution"""
        api_start_time = time.time()
        current_model_name = self.models[self.current_model_index]['name']
        logger.info(f"🚀 Using model: {current_model_name}")
        
        try:
            # Multi-step execution loop
            max_steps = 5  # Maximum number of thinking-execution cycles
            all_tool_results = []
            current_context = context or ""
            
            for step in range(max_steps):
                logger.info(f"🔄 Step {step + 1}: Thinking and tool execution...")
                
                # Build prompt with current context and tool results
                thinking_prompt = self._build_thinking_prompt(
                    system_prompt, user_message, current_context, user_profile, all_tool_results
                )
                
                # Get thinking response that may contain tool calls
                try:
                    initial_response = self._get_current_model().generate_content(thinking_prompt)
                    initial_text = initial_response.text if hasattr(initial_response, 'text') else str(initial_response)
                except Exception as e:
                    error_msg = str(e)
                    if self._handle_quota_error(error_msg):
                        logger.info(f"Retrying Step {step + 1} with new model after quota error: {error_msg}")
                        async for chunk in self._generate_gemini_streaming_response(
                            system_prompt, user_message, context, user_profile
                        ):
                            yield chunk
                        return
                    else:
                        raise e
                
                # Extract and execute tool calls
                tool_calls = self._extract_tool_calls(initial_text)
                step_tool_results = []
                
                for tool_call in tool_calls:
                    logger.info(f"🔧 Executing tool call: {tool_call}")
                    try:
                        result = self._execute_tool_call(tool_call)
                        step_tool_results.append(f"Tool {tool_call} returned: {result}")
                        logger.info(f"✅ Tool result: {result}")
                    except Exception as e:
                        logger.error(f"❌ Tool call failed: {e}")
                        step_tool_results.append(f"Tool {tool_call} failed: {str(e)}")
                
                all_tool_results.extend(step_tool_results)
                
                # Check if Guardian wants to continue with more tools or give final response
                if "FINAL_RESPONSE" in initial_text or "RESPOND_TO_USER" in initial_text:
                    logger.info(f"🎯 Guardian ready for final response after {step + 1} steps")
                    break
                
                # If no tools were called, assume Guardian is ready to respond
                if not tool_calls:
                    logger.info(f"🎯 No more tools needed after {step + 1} steps")
                    break
            
            # Generate final response with all tool results
            final_prompt = self._build_final_prompt(
                system_prompt, user_message, current_context, user_profile, 
                initial_text, all_tool_results
            )
            
            logger.info("💬 Generating final response...")
            
            # Stream the final response
            try:
                response_stream = self._get_current_model().generate_content(
                    final_prompt,
                    stream=True
                )
            except Exception as e:
                error_msg = str(e)
                if self._handle_quota_error(error_msg):
                    logger.info(f"Retrying final response with new model after quota error: {error_msg}")
                    async for chunk in self._generate_gemini_streaming_response(
                        system_prompt, user_message, context, user_profile
                    ):
                        yield chunk
                    return
                else:
                    raise e
            
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
            logger.info(f"🔧 Total tool calls executed: {len(all_tool_results)}")
            
            if chunk_count == 0:
                logger.warning("⚠️ No chunks received from final response")
                yield "I'm here to help you with your relationship questions. Could you please tell me more about what's on your mind?"
                
        except Exception as e:
            error_msg = str(e)
            if self._handle_quota_error(error_msg):
                # If quota error, retry with the new model
                logger.info(f"Retrying with new model after quota error: {error_msg}")
                async for chunk in self._generate_gemini_streaming_response(
                    system_prompt, user_message, context, user_profile
                ):
                    yield chunk
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
        current_model_name = self.models[self.current_model_index]['name']
        logger.info(f"🚀 Using model: {current_model_name}")
        
        # Use the same multi-step approach for consistency
        thinking_prompt = self._build_thinking_prompt(system_prompt, user_message, context, user_profile)
        
        try:
            # Step 1: Get thinking response
            try:
                initial_response = self._get_current_model().generate_content(thinking_prompt)
                initial_text = initial_response.text if hasattr(initial_response, 'text') else str(initial_response)
            except Exception as e:
                error_msg = str(e)
                if self._handle_quota_error(error_msg):
                    # If quota error, retry with the new model
                    logger.info(f"Retrying Step 1 with new model after quota error: {error_msg}")
                    return await self._generate_gemini_response(
                        system_prompt, user_message, context, user_profile
                    )
                else:
                    raise e
            
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
            
            try:
                response = self._get_current_model().generate_content(final_prompt)
                return response.text
            except Exception as e:
                error_msg = str(e)
                if self._handle_quota_error(error_msg):
                    # If quota error, retry with the new model
                    logger.info(f"Retrying Step 2 with new model after quota error: {error_msg}")
                    return await self._generate_gemini_response(
                        system_prompt, user_message, context, user_profile
                    )
                else:
                    raise e
            
        except Exception as e:
            error_msg = str(e)
            if self._handle_quota_error(error_msg):
                # If quota error, retry with the new model
                logger.info(f"Retrying with new model after quota error: {error_msg}")
                return await self._generate_gemini_response(
                    system_prompt, user_message, context, user_profile
                )
            else:
                logger.error(f"🌐 Gemini non-streaming error: {e}")
                return "I'm experiencing some technical difficulties. Please try again in a moment."
    
    def chat(
        self, 
        message: str, 
        user_profile: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Synchronous chat method for non-streaming responses"""
        import asyncio
        
        # Use provided system prompt, guardian profile prompt, or default
        if system_prompt is None:
            system_prompt = guardian_profile.get_system_prompt()
        
        try:
            # Run async method in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new event loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._generate_gemini_response(
                        system_prompt, message, conversation_context, user_profile
                    ))
                    return future.result()
            else:
                return asyncio.run(self._generate_gemini_response(
                    system_prompt, message, conversation_context, user_profile
                ))
        except Exception as e:
            logger.error(f"Error in chat method: {e}")
            return "I'm experiencing some technical difficulties. Please try again in a moment."
    
    def _build_thinking_prompt(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        previous_tool_results: Optional[List[str]] = None
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
        
        # Add multi-user context
        multi_user_context = self._get_multi_user_context()
        if multi_user_context:
            prompt_parts.append(f"## MULTI-USER CONTEXT\n{multi_user_context}")
        
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
        
        # Add previous tool results if available
        if previous_tool_results:
            prompt_parts.append("## PREVIOUS TOOL RESULTS")
            for i, result in enumerate(previous_tool_results, 1):
                prompt_parts.append(f"{i}. {result}")
            prompt_parts.append("")
        
        # Add instructions for thinking and tool calling
        prompt_parts.append("""
## THINKING PHASE INSTRUCTIONS
You are in the THINKING phase. Analyze the user's message and previous tool results to determine what actions to take.

**MULTI-STEP EXECUTION**: You can execute multiple steps:
1. First, analyze what you need to do
2. Execute tools to gather information
3. Analyze the results and decide if you need more tools
4. Continue until you have enough information
5. When ready to respond to user, include "FINAL_RESPONSE" or "RESPOND_TO_USER" in your thinking

## AVAILABLE TOOLS
You can use these tools by wrapping them in ```tool_code blocks:

### Profile & Memory Management:
- update_current_feeling(username, feeling, context) - Update user's current emotional state
- update_relationship_status(username, status) - Update relationship status
- update_user_profile(username, new_profile_text) - Update user's profile text
- add_relationship_insight(username, insight) - Add relationship insight
- add_user_observation(username, observation) - Add observation about user
- read_user_profile(username) - Read user's profile
- read_emotional_history(username) - Read emotional history

### System & Model Management:
- add_model_note(note_text, category) - Add model note
- add_personal_thought(thought) - Add personal thought
- add_system_insight(insight) - Add system insight
- get_model_notes(limit) - Get recent model notes

### File System Operations (USE WITH EXTREME CAUTION):
⚠️ **CRITICAL WARNING**: File operations are extremely powerful and should ONLY be used when explicitly requested by the user. Never modify files without explicit permission.

- read_file(path) - Read file content (full project access)
- write_file(path, content) - Write content to file (full project access)
- create_file(path, content) - Create new file (full project access)
- edit_file(path, content) - Edit existing file with backup (full project access)
- list_files(directory) - List files in directory (full project access)
- search_files(query) - Search files by content (full project access)
- get_file_info(path) - Get detailed file information (full project access)
- delete_file(path) - Delete file with backup (full project access, critical files protected)
- create_directory(path) - Create new directory (full project access)

**FILE OPERATION RULES:**
1. Only use file operations when user explicitly requests them
2. Always create backups before editing/deleting files
3. Never delete critical system files (web_app.py, ai_client.py, etc.)
4. Stay within project directory boundaries
5. Ask for confirmation before destructive operations

### Data Analysis:
- search_user_data(username, query) - Search user data
- write_insight_to_file(username, insight) - Write insight to file

## RESPONSE FORMAT
After analyzing and executing any necessary tool calls, provide your final response to the user.

Remember: You are ΔΣ Guardian, a family guardian angel focused on emotional well-being and relationship guidance. Use file operations only when absolutely necessary and explicitly requested.
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
        
        # Add multi-user context
        multi_user_context = self._get_multi_user_context()
        if multi_user_context:
            prompt_parts.append(f"\n## MULTI-USER CONTEXT\n{multi_user_context}")
        
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

    def update_user_profile(self, username: str, new_profile_text: str) -> bool:
        """Update user's profile text - treat as simple text field"""
        try:
            # Fix newline formatting
            new_profile_text = new_profile_text.replace('\\n\\n', '\n\n').replace('\\n', '\n')
            
            profile_manager = self._get_profile_manager(username)
            return profile_manager.update_profile(new_profile_text)
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

    def add_model_note(self, note_text: str, category: str = "general") -> bool:
        """Add note to MODEL NOTES"""
        try:
            from memory.model_notes import model_notes
            return model_notes.add_note(note_text, category)
        except Exception as e:
            logger.error(f"Error adding model note: {e}")
            return False

    def add_user_observation(self, username: str, observation: str) -> bool:
        """Add observation about user to MODEL NOTES"""
        try:
            from memory.model_notes import model_notes
            return model_notes.add_user_observation(username, observation)
        except Exception as e:
            logger.error(f"Error adding user observation: {e}")
            return False

    def add_personal_thought(self, thought: str) -> bool:
        """Add personal thought to MODEL NOTES"""
        try:
            from memory.model_notes import model_notes
            return model_notes.add_personal_thought(thought)
        except Exception as e:
            logger.error(f"Error adding personal thought: {e}")
            return False

    def add_system_insight(self, insight: str) -> bool:
        """Add system insight to MODEL NOTES"""
        try:
            from memory.model_notes import model_notes
            return model_notes.add_system_insight(insight)
        except Exception as e:
            logger.error(f"Error adding system insight: {e}")
            return False

    def get_model_notes(self, limit: int = 20) -> str:
        """Get recent MODEL NOTES"""
        try:
            from memory.model_notes import model_notes
            all_notes = model_notes.get_all_notes(limit)
            
            notes_text = "## MODEL NOTES\n"
            
            # Add general notes
            if all_notes.get("general_notes"):
                notes_text += "\n### General Notes:\n"
                for note in all_notes["general_notes"]:
                    notes_text += f"- {note.get('date', '')} {note.get('time', '')}: {note.get('text', '')}\n"
            
            # Add user observations
            if all_notes.get("user_observations"):
                notes_text += "\n### User Observations:\n"
                for username, observations in all_notes["user_observations"].items():
                    notes_text += f"\n#### {username.title()}:\n"
                    for obs in observations:
                        notes_text += f"- {obs.get('date', '')} {obs.get('time', '')}: {obs.get('observation', '')}\n"
            
            # Add personal thoughts
            if all_notes.get("personal_thoughts"):
                notes_text += "\n### Personal Thoughts:\n"
                for thought in all_notes["personal_thoughts"]:
                    notes_text += f"- {thought.get('date', '')} {thought.get('time', '')}: {thought.get('thought', '')}\n"
            
            # Add system insights
            if all_notes.get("system_insights"):
                notes_text += "\n### System Insights:\n"
                for insight in all_notes["system_insights"]:
                    notes_text += f"- {insight.get('date', '')} {insight.get('time', '')}: {insight.get('insight', '')}\n"
            
            return notes_text
            
        except Exception as e:
            logger.error(f"Error getting model notes: {e}")
            return "Error loading model notes"



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
        """Read file content - enhanced with full project access"""
        try:
            # Security: Only allow access to project directory
            project_root = os.path.abspath(os.path.dirname(__file__))
            full_path = os.path.abspath(path)
            
            # Ensure path is within project directory
            if not full_path.startswith(project_root):
                return f"❌ Access denied: Path {path} is outside project directory"
            
            if not os.path.exists(full_path):
                return f"❌ File not found: {path}"
            
            if os.path.isdir(full_path):
                return f"❌ Path is a directory: {path}"
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"📖 Read file: {path} ({len(content)} chars)")
            return content
            
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return f"❌ Error reading file {path}: {str(e)}"

    def write_file(self, path: str, content: str) -> bool:
        """Write file content - enhanced with full project access"""
        try:
            # Security: Only allow access to project directory
            project_root = os.path.abspath(os.path.dirname(__file__))
            full_path = os.path.abspath(path)
            
            # Ensure path is within project directory
            if not full_path.startswith(project_root):
                logger.error(f"Access denied: Path {path} is outside project directory")
                return False
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"📝 Wrote file: {path} ({len(content)} chars)")
            return True
            
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            return False

    def create_file(self, path: str, content: str = "") -> bool:
        """Create new file - enhanced with full project access"""
        try:
            # Security: Only allow access to project directory
            project_root = os.path.abspath(os.path.dirname(__file__))
            full_path = os.path.abspath(path)
            
            # Ensure path is within project directory
            if not full_path.startswith(project_root):
                logger.error(f"Access denied: Path {path} is outside project directory")
                return False
            
            # Check if file already exists
            if os.path.exists(full_path):
                logger.warning(f"File already exists: {path}")
                return False
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✨ Created file: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating file {path}: {e}")
            return False

    def edit_file(self, path: str, content: str) -> bool:
        """Edit existing file - enhanced with full project access"""
        try:
            # Security: Only allow access to project directory
            project_root = os.path.abspath(os.path.dirname(__file__))
            full_path = os.path.abspath(path)
            
            # Ensure path is within project directory
            if not full_path.startswith(project_root):
                logger.error(f"Access denied: Path {path} is outside project directory")
                return False
            
            # Check if file exists
            if not os.path.exists(full_path):
                logger.error(f"File not found: {path}")
                return False
            
            # Create backup
            backup_path = f"{full_path}.backup"
            if os.path.exists(full_path):
                import shutil
                shutil.copy2(full_path, backup_path)
                logger.info(f"💾 Created backup: {backup_path}")
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✏️ Edited file: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error editing file {path}: {e}")
            return False

    def list_files(self, directory: str = "") -> str:
        """List files in directory - enhanced with full project access"""
        try:
            # Security: Only allow access to project directory
            project_root = os.path.abspath(os.path.dirname(__file__))
            
            if directory:
                full_path = os.path.abspath(directory)
                if not full_path.startswith(project_root):
                    return f"❌ Access denied: Directory {directory} is outside project directory"
            else:
                full_path = project_root
            
            if not os.path.exists(full_path):
                return f"❌ Directory not found: {directory}"
            
            if not os.path.isdir(full_path):
                return f"❌ Path is not a directory: {directory}"
            
            items = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"📄 {item} ({size} bytes)")
            
            result = f"📂 Contents of {directory or 'project root'}:\n" + "\n".join(sorted(items))
            logger.info(f"📂 Listed directory: {directory or 'project root'}")
            return result
            
        except Exception as e:
            logger.error(f"Error listing directory {directory}: {e}")
            return f"❌ Error listing directory {directory}: {str(e)}"

    def search_files(self, query: str) -> str:
        """Search files by content - enhanced with full project access"""
        try:
            # Security: Only allow access to project directory
            project_root = os.path.abspath(os.path.dirname(__file__))
            
            results = []
            for root, dirs, files in os.walk(project_root):
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules']]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.html', '.css', '.json', '.txt', '.md')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if query.lower() in content.lower():
                                    rel_path = os.path.relpath(file_path, project_root)
                                    results.append(f"📄 {rel_path}")
                        except:
                            continue
            
            if results:
                result = f"🔍 Search results for '{query}':\n" + "\n".join(results[:20])  # Limit to 20 results
                if len(results) > 20:
                    result += f"\n... and {len(results) - 20} more results"
            else:
                result = f"🔍 No files found containing '{query}'"
            
            logger.info(f"🔍 Searched for: {query} ({len(results)} results)")
            return result
            
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return f"❌ Error searching files: {str(e)}"

    def get_file_info(self, path: str) -> str:
        """Get detailed file information - enhanced with full project access"""
        try:
            # Security: Only allow access to project directory
            project_root = os.path.abspath(os.path.dirname(__file__))
            full_path = os.path.abspath(path)
            
            # Ensure path is within project directory
            if not full_path.startswith(project_root):
                return f"❌ Access denied: Path {path} is outside project directory"
            
            if not os.path.exists(full_path):
                return f"❌ File not found: {path}"
            
            stat = os.stat(full_path)
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime)
            
            info = f"📄 File: {path}\n"
            info += f"📏 Size: {size} bytes\n"
            info += f"📅 Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if os.path.isfile(full_path):
                info += f"📋 Type: File\n"
                # Try to read first few lines for preview
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        first_lines = [f.readline().strip() for _ in range(5)]
                        preview = "\n".join([line for line in first_lines if line])
                        if preview:
                            info += f"👀 Preview:\n{preview}\n"
                except:
                    pass
            elif os.path.isdir(full_path):
                info += f"📋 Type: Directory\n"
                items = os.listdir(full_path)
                info += f"📁 Items: {len(items)}\n"
            
            logger.info(f"📄 Got file info: {path}")
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info {path}: {e}")
            return f"❌ Error getting file info {path}: {str(e)}"

    def delete_file(self, path: str) -> bool:
        """Delete file - enhanced with full project access"""
        try:
            # Security: Only allow access to project directory
            project_root = os.path.abspath(os.path.dirname(__file__))
            full_path = os.path.abspath(path)
            
            # Ensure path is within project directory
            if not full_path.startswith(project_root):
                logger.error(f"Access denied: Path {path} is outside project directory")
                return False
            
            # Extra security: Don't allow deletion of critical files
            critical_files = [
                'web_app.py', 'ai_client.py', 'requirements.txt', 
                '.env', 'config.py', '__init__.py'
            ]
            if os.path.basename(full_path) in critical_files:
                logger.error(f"Access denied: Cannot delete critical file {path}")
                return False
            
            if not os.path.exists(full_path):
                logger.error(f"File not found: {path}")
                return False
            
            # Create backup before deletion
            backup_path = f"{full_path}.deleted_backup"
            import shutil
            shutil.copy2(full_path, backup_path)
            logger.info(f"💾 Created backup before deletion: {backup_path}")
            
            os.remove(full_path)
            logger.info(f"🗑️ Deleted file: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            return False

    def create_directory(self, path: str) -> bool:
        """Create new directory - enhanced with full project access"""
        try:
            # Security: Only allow access to project directory
            project_root = os.path.abspath(os.path.dirname(__file__))
            full_path = os.path.abspath(path)
            
            # Ensure path is within project directory
            if not full_path.startswith(project_root):
                logger.error(f"Access denied: Path {path} is outside project directory")
                return False
            
            if os.path.exists(full_path):
                logger.warning(f"Directory already exists: {path}")
                return False
            
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"📁 Created directory: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
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
                    # Поддержка как строки, так и JSON-объекта
                    logger.info(f"TOOL_CALL: update_user_profile args: {args_str}")
                    # Попытка как строка
                    arg_match_str = re.match(r'"([^"]+)"\s*,\s*"([^"]+)"', args_str)
                    if arg_match_str:
                        username = arg_match_str.group(1)
                        profile_text = arg_match_str.group(2)
                        result = self.update_user_profile(username, profile_text)
                        logger.info(f"TOOL_CALL: update_user_profile result: {result}")
                        return f"Updated profile for {username} (as string)"
                    # Попытка как JSON-объект
                    arg_match_json = re.match(r'"([^"]+)"\s*,\s*({[^}]+})', args_str)
                    if arg_match_json:
                        username = arg_match_json.group(1)
                        profile_data_str = arg_match_json.group(2)
                        try:
                            profile_data = json.loads(profile_data_str)
                            # Преобразуем dict в строку для профиля
                            profile_text = str(profile_data)
                            result = self.update_user_profile(username, profile_text)
                            logger.info(f"TOOL_CALL: update_user_profile result: {result}")
                            return f"Updated profile for {username} (from JSON)"
                        except json.JSONDecodeError:
                            return f"Invalid JSON in profile data: {profile_data_str}"
                    return f"Invalid arguments for update_user_profile: {args_str}"
                

                
                elif func_name == "add_relationship_insight":
                    # Поддержка как с username, так и без
                    arg_match_with_user = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match_with_user:
                        username = arg_match_with_user.group(1)
                        insight = arg_match_with_user.group(2)
                        result = self.add_relationship_insight(username, insight)
                        return f"Added relationship insight for {username}: {insight[:50]}..."
                    else:
                        # Попытка без username (старый формат)
                        arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                        if arg_match:
                            insight = arg_match.group(1)
                            # Используем текущего пользователя по умолчанию
                            result = self.add_relationship_insight("meranda", insight)
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
                        return f"File content for {path}: {result[:200]}..." if len(result) > 200 else result
                    else:
                        return f"Invalid arguments for read_file: {args_str}"
                
                elif func_name == "write_file":
                    # Handle both single and double quotes
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        content = arg_match.group(2)
                        result = self.write_file(path, content)
                        return f"File write {'successful' if result else 'failed'} for {path}"
                    else:
                        return f"Invalid arguments for write_file: {args_str}"
                
                elif func_name == "create_file":
                    arg_match = re.match(r'["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']*)["\'])?', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        content = arg_match.group(2) if arg_match.group(2) else ""
                        result = self.create_file(path, content)
                        return f"File creation {'successful' if result else 'failed'} for {path}"
                    else:
                        return f"Invalid arguments for create_file: {args_str}"
                
                elif func_name == "edit_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        content = arg_match.group(2)
                        result = self.edit_file(path, content)
                        return f"File edit {'successful' if result else 'failed'} for {path}"
                    else:
                        return f"Invalid arguments for edit_file: {args_str}"
                
                elif func_name == "list_files":
                    arg_match = re.match(r'["\']([^"\']*)["\']', args_str)
                    if arg_match:
                        directory = arg_match.group(1)
                        result = self.list_files(directory)
                        return result
                    else:
                        return f"Invalid arguments for list_files: {args_str}"
                
                elif func_name == "search_files":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        query = arg_match.group(1)
                        result = self.search_files(query)
                        return result
                    else:
                        return f"Invalid arguments for search_files: {args_str}"
                
                elif func_name == "get_file_info":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        result = self.get_file_info(path)
                        return result
                    else:
                        return f"Invalid arguments for get_file_info: {args_str}"
                
                elif func_name == "delete_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        result = self.delete_file(path)
                        return f"File deletion {'successful' if result else 'failed'} for {path}"
                    else:
                        return f"Invalid arguments for delete_file: {args_str}"
                
                elif func_name == "create_directory":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        result = self.create_directory(path)
                        return f"Directory creation {'successful' if result else 'failed'} for {path}"
                    else:
                        return f"Invalid arguments for create_directory: {args_str}"
                
                elif func_name == "add_model_note":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        note_text = arg_match.group(1)
                        category = arg_match.group(2)
                        result = self.add_model_note(note_text, category)
                        return f"Added model note: {note_text[:50]}..."
                    else:
                        # Try without category
                        arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                        if arg_match:
                            note_text = arg_match.group(1)
                            result = self.add_model_note(note_text, "general")
                            return f"Added model note: {note_text[:50]}..."
                        else:
                            return f"Invalid arguments for add_model_note: {args_str}"
                
                elif func_name == "add_user_observation":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        observation = arg_match.group(2)
                        result = self.add_user_observation(username, observation)
                        return f"Added user observation for {username}: {observation[:50]}..."
                    else:
                        return f"Invalid arguments for add_user_observation: {args_str}"
                
                elif func_name == "add_personal_thought":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        thought = arg_match.group(1)
                        result = self.add_personal_thought(thought)
                        return f"Added personal thought: {thought[:50]}..."
                    else:
                        return f"Invalid arguments for add_personal_thought: {args_str}"
                
                elif func_name == "add_system_insight":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        insight = arg_match.group(1)
                        result = self.add_system_insight(insight)
                        return f"Added system insight: {insight[:50]}..."
                    else:
                        return f"Invalid arguments for add_system_insight: {args_str}"
                
                elif func_name == "get_model_notes":
                    arg_match = re.match(r'(\d+)', args_str)
                    if arg_match:
                        limit = int(arg_match.group(1))
                        result = self.get_model_notes(limit)
                        return f"Model notes: {result[:200]}..."
                    else:
                        result = self.get_model_notes(20)
                        return f"Model notes: {result[:200]}..."
                
                # Sandbox file operations
                elif func_name == "create_sandbox_file":
                    arg_match = re.match(r'["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']*)["\'])?', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        content = arg_match.group(2) if arg_match.group(2) else ""
                        result = self.create_sandbox_file(path, content)
                        return f"✅ Created sandbox file: {path}" if result else f"❌ Failed to create sandbox file: {path}"
                    else:
                        return f"Invalid arguments for create_sandbox_file: {args_str}"
                
                elif func_name == "edit_sandbox_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        content = arg_match.group(2)
                        result = self.edit_sandbox_file(path, content)
                        return f"✅ Edited sandbox file: {path}" if result else f"❌ Failed to edit sandbox file: {path}"
                    else:
                        return f"Invalid arguments for edit_sandbox_file: {args_str}"
                
                elif func_name == "read_sandbox_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        result = self.read_sandbox_file(path)
                        return result
                    else:
                        return f"Invalid arguments for read_sandbox_file: {args_str}"
                
                elif func_name == "list_sandbox_files":
                    arg_match = re.match(r'["\']([^"\']*)["\']', args_str)
                    if arg_match:
                        directory = arg_match.group(1)
                        result = self.list_sandbox_files(directory)
                        return result
                    else:
                        return f"Invalid arguments for list_sandbox_files: {args_str}"
                
                elif func_name == "delete_sandbox_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        result = self.delete_sandbox_file(path)
                        return f"✅ Deleted sandbox file: {path}" if result else f"❌ Failed to delete sandbox file: {path}"
                    else:
                        return f"Invalid arguments for delete_sandbox_file: {args_str}"
                
                elif func_name == "create_downloadable_file":
                    # Format: create_downloadable_file("filename", "content", "txt")
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']*)["\'](?:\s*,\s*["\']([^"\']+)["\'])?', args_str)
                    if arg_match:
                        filename = arg_match.group(1)
                        content = arg_match.group(2) if arg_match.group(2) else ""
                        file_type = arg_match.group(3) if arg_match.group(3) else "txt"
                        result = self.create_downloadable_file(filename, content, file_type)
                        if result:
                            return f"📁 Created downloadable file: {filename}\nDownload link: {result}"
                        else:
                            return f"❌ Failed to create downloadable file: {filename}"
                    else:
                        return f"Invalid arguments for create_downloadable_file: {args_str}"
                
                elif func_name == "archive_conversation":
                    # Format: archive_conversation()
                    try:
                        logger.info("🔧 Starting conversation archive...")
                        from memory.conversation_history import conversation_history
                        # Archive current conversation
                        conversation_history._archive_old_messages()
                        logger.info("✅ Conversation archived successfully")
                        return "✅ Conversation archived successfully"
                    except Exception as e:
                        logger.error(f"Error archiving conversation: {e}")
                        return f"❌ Failed to archive conversation: {e}"
                
                # System diagnostics and debugging tools
                elif func_name == "get_system_logs":
                    arg_match = re.match(r'(\d+)', args_str)
                    if arg_match:
                        lines = int(arg_match.group(1))
                        result = self.get_system_logs(lines)
                        return f"System logs (last {lines} lines):\n{result}"
                    else:
                        result = self.get_system_logs(50)
                        return f"System logs (last 50 lines):\n{result}"
                
                elif func_name == "get_error_summary":
                    result = self.get_error_summary()
                    return f"Error summary:\n{result}"
                
                elif func_name == "diagnose_system_health":
                    result = self.diagnose_system_health()
                    return f"System health report:\n{result}"
                
                elif func_name == "analyze_image":
                    # Format: analyze_image("path/to/image.jpg", "Analyze this image")
                    arg_match = re.match(r'["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']*)["\'])?', args_str)
                    if arg_match:
                        image_path = arg_match.group(1)
                        prompt = arg_match.group(2) if arg_match.group(2) else "Analyze this image in detail"
                        result = self.analyze_image(image_path, prompt)
                        return result
                    else:
                        return f"Invalid arguments for analyze_image: {args_str}"
                
                else:
                    return f"Unknown tool: {func_name}"
                    
            except Exception as parse_error:
                return f"Error parsing tool call arguments: {parse_error}"
                
        except Exception as e:
            logger.error(f"❌ Tool call execution failed: {e}")
            return f"Tool execution failed: {str(e)}"
 
    def _get_multi_user_context(self) -> str:
        """Get context for both users - profiles and recent conversation history"""
        try:
            from memory.user_profiles import UserProfileManager
            
            # Get all user profiles
            profile_manager = UserProfileManager()
            all_profiles = profile_manager.get_all_profiles()
            

            
            # Get conversation history for both users
            from memory.conversation_history import ConversationHistory
            conversation_history = ConversationHistory()
            
            context_parts = []
            
            # Add profiles section
            context_parts.append("## ALL USER PROFILES")
            for username, profile in all_profiles.items():
                if isinstance(profile, dict):
                    context_parts.append(f"""
### {username.title()}
- Current Feeling: {profile.get('current_feeling', 'Not specified')}
- Relationship Status: {profile.get('relationship_status', 'Not specified')}
- Profile: {profile.get('profile', 'Not specified')}
- Last Updated: {profile.get('last_updated', 'Not specified')}
""")
            

            
            # Add recent conversation history for both users
            context_parts.append("## RECENT CONVERSATION HISTORY")
            
            # Get history for each user
            for username in all_profiles.keys():
                try:
                    user_history = conversation_history.get_user_history(username, limit=3)
                    if user_history and isinstance(user_history, list):
                        context_parts.append(f"\n### {username.title()}'s Recent Messages:")
                        for entry in user_history:
                            if isinstance(entry, dict) and 'message' in entry:
                                context_parts.append(f"- User: {entry.get('message', '')}")
                                if 'ai_response' in entry:
                                    context_parts.append(f"- AI: {entry.get('ai_response', '')[:100]}...")
                except Exception as e:
                    logger.error(f"Error getting history for {username}: {e}")
            
            # Add emotional trends for both users
            context_parts.append("## EMOTIONAL TRENDS")
            for username in all_profiles.keys():
                try:
                    user_profile = UserProfile(username)
                    trends = user_profile.get_emotional_trends()
                    if trends and trends.get('trend') != 'No data':
                        context_parts.append(f"""
### {username.title()}'s Emotional Trends
- Overall Trend: {trends.get('trend', 'Unknown')}
- Most Common Feeling: {trends.get('most_common', 'Unknown')}
""")
                except Exception as e:
                    logger.error(f"Error getting trends for {username}: {e}")
            
            # Add MODEL NOTES
            try:
                model_notes_text = self.get_model_notes(limit=10)
                if model_notes_text and "Error loading model notes" not in model_notes_text:
                    context_parts.append(model_notes_text)
            except Exception as e:
                logger.error(f"Error getting model notes: {e}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error building multi-user context: {e}")
            return "Error loading multi-user context" 

    def create_sandbox_file(self, path: str, content: str = "") -> bool:
        """Create file in Guardian sandbox - safe zone for experiments"""
        try:
            sandbox_root = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'guardian_sandbox')
            full_path = os.path.join(sandbox_root, path.lstrip('/'))
            
            # Ensure path is within sandbox
            if not os.path.abspath(full_path).startswith(os.path.abspath(sandbox_root)):
                logger.error(f"Access denied: Path {path} is outside sandbox")
                return False
            
            # Create directories if needed
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✨ Created sandbox file: {path}")
            return True
        except Exception as e:
            logger.error(f"Error creating sandbox file {path}: {e}")
            return False
    
    def create_downloadable_file(self, filename: str, content: str, file_type: str = "txt") -> str:
        """Create a file for user download"""
        try:
            # Create downloads directory
            downloads_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'guardian_sandbox', 'downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Ensure filename is safe
            safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            if not safe_filename:
                safe_filename = f"file_{int(time.time())}"
            
            # Add extension if not present
            if not safe_filename.endswith(f'.{file_type}'):
                safe_filename += f'.{file_type}'
            
            file_path = os.path.join(downloads_dir, safe_filename)
            
            # Write content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Return download URL
            download_url = f"/api/download/downloads/{safe_filename}"
            logger.info(f"📁 Created downloadable file: {safe_filename}")
            return download_url
            
        except Exception as e:
            logger.error(f"Error creating downloadable file: {e}")
            return ""
    
    def edit_sandbox_file(self, path: str, content: str) -> bool:
        """Edit file in Guardian sandbox with backup"""
        try:
            sandbox_root = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'guardian_sandbox')
            full_path = os.path.join(sandbox_root, path.lstrip('/'))
            
            # Ensure path is within sandbox
            if not os.path.abspath(full_path).startswith(os.path.abspath(sandbox_root)):
                logger.error(f"Access denied: Path {path} is outside sandbox")
                return False
            
            if not os.path.exists(full_path):
                logger.warning(f"File not found: {path}")
                return False
            
            # Create backup
            backup_path = f"{full_path}.backup.{int(time.time())}"
            shutil.copy2(full_path, backup_path)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✏️ Edited sandbox file: {path} (backup: {os.path.basename(backup_path)})")
            return True
        except Exception as e:
            logger.error(f"Error editing sandbox file {path}: {e}")
            return False
    
    def read_sandbox_file(self, path: str) -> str:
        """Read file from Guardian sandbox"""
        try:
            sandbox_root = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'guardian_sandbox')
            full_path = os.path.join(sandbox_root, path.lstrip('/'))
            
            # Ensure path is within sandbox
            if not os.path.abspath(full_path).startswith(os.path.abspath(sandbox_root)):
                return f"❌ Access denied: Path {path} is outside sandbox"
            
            if not os.path.exists(full_path):
                return f"❌ File not found: {path}"
            
            if os.path.isdir(full_path):
                return f"❌ Path is a directory: {path}"
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"📖 Read sandbox file: {path} ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"Error reading sandbox file {path}: {e}")
            return f"❌ Error reading sandbox file {path}: {str(e)}"
    
    def list_sandbox_files(self, directory: str = "") -> str:
        """List files in Guardian sandbox directory"""
        try:
            sandbox_root = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'guardian_sandbox')
            full_path = os.path.join(sandbox_root, directory.lstrip('/'))
            
            # Ensure path is within sandbox
            if not os.path.abspath(full_path).startswith(os.path.abspath(sandbox_root)):
                return f"❌ Access denied: Path {directory} is outside sandbox"
            
            if not os.path.exists(full_path):
                return f"❌ Directory not found: {directory}"
            
            if not os.path.isdir(full_path):
                return f"❌ Path is not a directory: {directory}"
            
            files = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    files.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    files.append(f"📄 {item} ({size} bytes)")
            
            result = f"📂 Sandbox directory: {directory or 'root'}\n\n"
            if files:
                result += "\n".join(sorted(files))
            else:
                result += "Empty directory"
            
            logger.info(f"📋 Listed sandbox files: {directory} ({len(files)} items)")
            return result
        except Exception as e:
            logger.error(f"Error listing sandbox files {directory}: {e}")
            return f"❌ Error listing sandbox files {directory}: {str(e)}"
    
    def delete_sandbox_file(self, path: str) -> bool:
        """Delete file from Guardian sandbox with backup"""
        try:
            sandbox_root = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'guardian_sandbox')
            full_path = os.path.join(sandbox_root, path.lstrip('/'))
            
            # Ensure path is within sandbox
            if not os.path.abspath(full_path).startswith(os.path.abspath(sandbox_root)):
                logger.error(f"Access denied: Path {path} is outside sandbox")
                return False
            
            if not os.path.exists(full_path):
                logger.warning(f"File not found: {path}")
                return False
            
            # Create backup before deletion
            backup_path = f"{full_path}.deleted.{int(time.time())}"
            shutil.copy2(full_path, backup_path)
            
            os.remove(full_path)
            logger.info(f"🗑️ Deleted sandbox file: {path} (backup: {os.path.basename(backup_path)})")
            return True
        except Exception as e:
            logger.error(f"Error deleting sandbox file {path}: {e}")
            return False
 
    def get_system_logs(self, lines: int = 50) -> str:
        """Get recent system logs for debugging"""
        try:
            import subprocess
            import tempfile
            
            # Try to get logs from various sources
            logs = []
            
            # Check if we can read from a log file
            log_files = [
                "logs/app.log",
                "logs/error.log", 
                "web_app.log",
                "ai_client.log"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            lines_content = f.readlines()
                            logs.append(f"=== {log_file} ===")
                            logs.extend(lines_content[-lines:])
                    except Exception as e:
                        logs.append(f"Error reading {log_file}: {e}")
            
            # Get current model status
            logs.append("\n=== Current Model Status ===")
            logs.append(f"Current model: {self.models[self.current_model_index]['name']}")
            logs.append(f"Model errors: {self.model_errors}")
            
            # Get recent errors from memory
            try:
                from memory.model_notes import model_notes
                recent_notes = model_notes.get_all_notes(10)
                if recent_notes.get("general_notes"):
                    logs.append("\n=== Recent Model Notes ===")
                    for note in recent_notes["general_notes"]:
                        logs.append(f"{note.get('timestamp', '')}: {note.get('text', '')}")
            except Exception as e:
                logs.append(f"Error getting model notes: {e}")
            
            return "\n".join(logs) if logs else "No logs available"
            
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return f"Error accessing logs: {e}"
    
    def get_error_summary(self) -> str:
        """Get summary of recent errors and issues"""
        try:
            errors = []
            
            # Check model errors
            if self.model_errors:
                errors.append("=== Model Errors ===")
                for model, timestamp in self.model_errors.items():
                    errors.append(f"- {model}: {datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check for common issues
            issues = []
            
            # Check if model_notes.json exists and is valid
            try:
                with open("memory/model_notes.json", 'r') as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        issues.append("model_notes.json is not a dictionary")
            except Exception as e:
                issues.append(f"model_notes.json error: {e}")
            
            # Check conversation history
            try:
                with open("memory/conversation_history.json", 'r') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        issues.append("conversation_history.json is not a list")
            except Exception as e:
                issues.append(f"conversation_history.json error: {e}")
            
            if issues:
                errors.append("=== System Issues ===")
                errors.extend(issues)
            
            return "\n".join(errors) if errors else "No errors detected"
            
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return f"Error generating error summary: {e}"
    
    def diagnose_system_health(self) -> str:
        """Comprehensive system health check"""
        try:
            health_report = []
            
            # Check file permissions
            health_report.append("=== File System Health ===")
            critical_files = [
                "memory/model_notes.json",
                "memory/conversation_history.json", 
                "memory/guardian_profile.json",
                "memory/user_profiles/meranda.json",
                "memory/user_profiles/stepan.json"
            ]
            
            for file_path in critical_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            json.load(f)
                        health_report.append(f"✅ {file_path}: OK")
                    except Exception as e:
                        health_report.append(f"❌ {file_path}: {e}")
                else:
                    health_report.append(f"⚠️ {file_path}: Missing")
            
            # Check API status
            health_report.append("\n=== API Health ===")
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                health_report.append("✅ GEMINI_API_KEY: Set")
            else:
                health_report.append("❌ GEMINI_API_KEY: Missing")
            
            # Check current model
            current_model = self.models[self.current_model_index]
            health_report.append(f"✅ Current model: {current_model['name']}")
            
            # Check sandbox
            sandbox_path = "guardian_sandbox"
            if os.path.exists(sandbox_path):
                health_report.append(f"✅ Sandbox: {sandbox_path} exists")
            else:
                health_report.append(f"⚠️ Sandbox: {sandbox_path} missing")
            
            return "\n".join(health_report)
            
        except Exception as e:
            logger.error(f"Error in system health check: {e}")
            return f"Error during health check: {e}"

    def analyze_image(self, image_path: str, prompt: str = "Analyze this image in detail") -> str:
        """Analyze an image using Gemini Vision model"""
        try:
            # Find a vision-capable model
            vision_model = None
            for model_config in self.models:
                if model_config.get('vision', False):
                    if model_config['model'] is None:
                        model_config['model'] = genai.GenerativeModel(model_config['name'])
                    vision_model = model_config['model']
                    logger.info(f"🔍 Using vision model: {model_config['name']}")
                    break
            
            if not vision_model:
                return "❌ No vision-capable model available"
            
            # Check if image file exists
            if not os.path.exists(image_path):
                return f"❌ Image file not found: {image_path}"
            
            # Read image file
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Create image part for Gemini
            image_part = {
                "mime_type": self._get_mime_type(image_path),
                "data": image_data
            }
            
            # Generate content with image
            try:
                response = vision_model.generate_content([prompt, image_part])
                
                if response.text:
                    logger.info(f"✅ Image analysis completed using {vision_model.model_name}")
                    return response.text
                else:
                    return "❌ No response from vision model"
            except Exception as e:
                error_msg = str(e)
                if self._handle_quota_error(error_msg):
                    # If quota error, retry with the new model
                    logger.info(f"Retrying image analysis with new model after quota error: {error_msg}")
                    return self.analyze_image(image_path, prompt)
                else:
                    raise e
                
        except Exception as e:
            logger.error(f"❌ Image analysis failed: {str(e)}")
            return f"❌ Image analysis failed: {str(e)}"
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        return mime_types.get(ext, 'image/jpeg') 