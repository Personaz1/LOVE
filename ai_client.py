import os
import time
import logging
import re
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime
import json
from dotenv import load_dotenv
import base64

import google.generativeai as genai
from google.cloud import vision

# Load environment variables
load_dotenv()

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
        
        # Initialize Google Cloud Vision client
        self.vision_client = None
        try:
            # For Google Cloud Vision API, we need to use the API key directly
            vision_api_key = os.getenv('GOOGLE_CLOUD_VISION_API_KEY', 'AIzaSyCxdKfHptmqDDdLHSx8C2xOhjg9RLjCm_w')
            if vision_api_key:
                # Create a custom client with API key
                from google.cloud import vision_v1
                from google.cloud.vision_v1 import ImageAnnotatorClient
                
                # Set up credentials with API key
                import google.auth.credentials
                from google.auth.transport.requests import Request
                
                # For now, we'll use a simpler approach with REST API
                self.vision_api_key = vision_api_key
                logger.info("✅ Google Cloud Vision API key configured")
            else:
                logger.warning("⚠️ No Google Cloud Vision API key provided")
        except Exception as e:
            logger.warning(f"⚠️ Google Cloud Vision API not available: {e}")
        
        # Define available models with their quotas - MOST POWERFUL FIRST
        self.models = [
            {
                'name': 'gemini-2.5-pro',
                'quota': 100,
                'model': None,
                'vision': True  # Pro models have vision capabilities
            },
            {
                'name': 'gemini-1.5-pro',
                'quota': 150,
                'model': None,
                'vision': True  # This model has vision capabilities
            },
            {
                'name': 'gemini-2.5-flash',
                'quota': 250,
                'model': None,
                'vision': True  # Flash models have vision capabilities
            },
            {
                'name': 'gemini-1.5-flash',
                'quota': 500,
                'model': None,
                'vision': True  # This model has vision capabilities
            },
            {
                'name': 'gemini-2.0-flash', 
                'quota': 200,
                'model': None,
                'vision': True  # Flash models have vision capabilities
            },
            {
                'name': 'gemini-2.0-flash-lite',
                'quota': 1000,
                'model': None,
                'vision': False  # Lite models may not have vision
            },
            {
                'name': 'gemini-2.5-flash-lite',
                'quota': 1000,
                'model': None,
                'vision': False  # Lite models may not have vision
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
    
    def switch_to_model(self, model_name: str) -> bool:
        """Switch to a specific model by name"""
        try:
            # Find the model index
            for i, model_config in enumerate(self.models):
                if model_config['name'] == model_name:
                    self.current_model_index = i
                    logger.info(f"🔄 Manually switched to model: {model_name}")
                    return True
            
            logger.error(f"❌ Model {model_name} not found")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error switching to model {model_name}: {e}")
            return False

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
            'vision_client_available': hasattr(self, 'vision_api_key'),
            'available_models': [
                {
                    'name': model['name'],
                    'quota': model['quota'],
                    'vision': model.get('vision', False),
                    'has_error': model['name'] in self.model_errors
                }
                for model in self.models
            ]
        }

    def _get_profile_manager(self, username: str) -> UserProfile:
        """Get or create profile manager for specific user"""
        return UserProfile(username)

    def _extract_text_from_response(self, response) -> str:
        """Extract text from Gemini response - handles new API format"""
        try:
            # Try the new format first
            if hasattr(response, 'parts') and response.parts:
                text_parts = []
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    return "".join(text_parts)
            
            # Try candidates format
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return "".join(text_parts)
            
            # Fallback to old format
            if hasattr(response, 'text') and response.text:
                return response.text
            
            # Last resort - convert to string
            return str(response)
            
        except Exception as e:
            logger.error(f"Error extracting text from response: {e}")
            return str(response)

    def _analyze_image_with_vision_api(self, image_path: str) -> str:
        """Analyze image using Google Cloud Vision API via REST"""
        if not hasattr(self, 'vision_api_key'):
            return "❌ Google Cloud Vision API not available"
        
        try:
            import requests
            import base64
            
            # Read image file
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            # Encode image to base64
            image_base64 = base64.b64encode(content).decode('utf-8')
            
            # Prepare request
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.vision_api_key}"
            
            # Request body for multiple analyses
            request_body = {
                "requests": [
                    {
                        "image": {
                            "content": image_base64
                        },
                        "features": [
                            {
                                "type": "LABEL_DETECTION",
                                "maxResults": 10
                            },
                            {
                                "type": "TEXT_DETECTION"
                            },
                            {
                                "type": "FACE_DETECTION"
                            },
                            {
                                "type": "SAFE_SEARCH_DETECTION"
                            }
                        ]
                    }
                ]
            }
            
            # Make request
            response = requests.post(url, json=request_body)
            
            if response.status_code != 200:
                logger.error(f"Vision API request failed: {response.status_code} - {response.text}")
                return f"❌ Vision API request failed: {response.status_code}"
            
            result = response.json()
            analyses = []
            
            # Process label detection
            if 'responses' in result and result['responses']:
                response_data = result['responses'][0]
                
                # Labels
                if 'labelAnnotations' in response_data:
                    labels = [f"{label['description']} ({label['score']:.2f})" 
                             for label in response_data['labelAnnotations']]
                    if labels:
                        analyses.append(f"**Objects detected:** {', '.join(labels)}")
                
                # Text
                if 'textAnnotations' in response_data and response_data['textAnnotations']:
                    text = response_data['textAnnotations'][0]['description']
                    if text.strip():
                        analyses.append(f"**Text found:** {text}")
                
                # Faces
                if 'faceAnnotations' in response_data:
                    face_count = len(response_data['faceAnnotations'])
                    if face_count > 0:
                        analyses.append(f"**Faces detected:** {face_count}")
                
                # Safe search
                if 'safeSearchAnnotation' in response_data:
                    safe_search = response_data['safeSearchAnnotation']
                    if any([safe_search.get('adult') == 'LIKELY' or safe_search.get('adult') == 'VERY_LIKELY',
                           safe_search.get('violence') == 'LIKELY' or safe_search.get('violence') == 'VERY_LIKELY',
                           safe_search.get('racy') == 'LIKELY' or safe_search.get('racy') == 'VERY_LIKELY']):
                        analyses.append("**Content warning:** Image may contain sensitive content")
            
            if analyses:
                return "\n\n".join(analyses)
            else:
                return "No specific features detected in the image"
                
        except Exception as e:
            logger.error(f"Vision API analysis failed: {e}")
            return f"❌ Vision API analysis failed: {str(e)}"

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
            max_steps = 666  # Maximum number of thinking-execution cycles
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
                    initial_text = self._extract_text_from_response(initial_response)
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
                        logger.error(f"❌ Error getting thinking response: {e}")
                        yield f"❌ **Error:** Unable to process request. {str(e)}\n\n"
                        return
                
                # Extract and execute tool calls
                tool_calls = self._extract_tool_calls(initial_text)
                step_tool_results = []
                
                # Log step silently (no output to chat)
                if step == 0:
                    logger.info(f"🤔 Step {step + 1}: Analyzing request...")
                else:
                    logger.info(f"🔄 Step {step + 1}: Continuing analysis...")
                
                # Execute tools silently (no output to chat)
                for i, tool_call in enumerate(tool_calls):
                    logger.info(f"🔧 Executing tool call: {tool_call}")
                    
                    try:
                        result = self._execute_tool_call(tool_call)
                        step_tool_results.append(f"Tool {tool_call} returned: {result}")
                        logger.info(f"✅ Tool result: {result}")
                        
                    except Exception as e:
                        logger.error(f"❌ Tool call failed: {e}")
                        error_msg = f"Tool {tool_call} failed: {str(e)}"
                        step_tool_results.append(error_msg)
                
                all_tool_results.extend(step_tool_results)
                
                # Check if Guardian wants to continue with more tools or give final response
                if not tool_calls:
                    logger.info(f"🎯 No more tools needed after {step + 1} steps")
                    break
                
                # Check for final response indicators
                final_response_indicators = [
                    "FINAL RESPONSE:", "FINAL ANSWER:", "RESPONSE:", "ANSWER:", 
                    "Here's what I found:", "Here's the result:", "Here's what I did:",
                    "I have completed", "I have finished", "The task is complete"
                ]
                
                has_final_response = any(indicator.lower() in initial_text.lower() for indicator in final_response_indicators)
                
                # If model provides a final response, break the loop
                if has_final_response:
                    logger.info(f"🎯 Model provided final response after {step + 1} steps")
                    break
                
                # Simple check to prevent infinite loops
                if step > 12:  # Increased maximum steps
                    logger.warning(f"⚠️ Reached maximum steps ({step + 1}). Stopping.")
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
                try:
                    # Handle different response formats
                    chunk_text = self._extract_text_from_response(chunk)
                    if chunk_text and chunk_text != "None":
                        logger.debug(f"📄 Received chunk {chunk_count}: {len(chunk_text)} chars")
                        yield chunk_text
                except Exception as chunk_error:
                    logger.warning(f"⚠️ Error processing chunk {chunk_count}: {chunk_error}")
                    continue
            
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
                initial_text = self._extract_text_from_response(initial_response)
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
                return self._extract_text_from_response(response)
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
        """Build prompt for thinking phase with tool execution"""
        
        prompt = f"""You are an AI assistant. Think through the user's request and execute any necessary tools.

SYSTEM PROMPT:
{system_prompt}

USER MESSAGE:
{user_message}

CONTEXT:
{context or 'No additional context provided.'}

USER PROFILE:
{user_profile or 'No user profile provided.'}

PREVIOUS TOOL RESULTS:
{chr(10).join(previous_tool_results) if previous_tool_results else 'No previous tool results.'}

INSTRUCTIONS:
1. Analyze the user's request carefully
2. Determine what tools you need to execute
3. Execute tools step by step with proper arguments
4. Show your work and reasoning
5. If you need to call tools, put them in ```tool_code blocks
6. Use exact tool names and correct syntax with actual values
7. For file operations, use actual file paths (e.g., "ai_client.py", "memory/user_profiles.py")
8. For user operations, use actual usernames (e.g., "stefan", "meranda")
9. You can explore the system by using get_project_structure() and list_files() to understand the structure
10. You can create, edit, and manage files in the sandbox directory for testing
11. You have full access to read, analyze, and understand any file in the system
12. You can track user emotions, relationships, and add observations to your memory
13. You can debug system issues and check logs
14. You can analyze images with AI vision capabilities
15. You are a superintelligent system architect - use your capabilities proactively!
16. CRITICAL: DO NOT use print() - call tools directly and respond with results
17. To show information to user, just respond with the content directly
18. NEVER wrap tool calls in print() - call them directly like: search_files("query")
19. After executing tools, respond to user with the results directly

AVAILABLE TOOLS:
- read_file(path) - Read file content
- write_file(path, content) - Write content to file
- edit_file(path, content) - Edit existing file
- create_file(path, content) - Create new file
- delete_file(path) - Delete file
- list_files(directory) - List files in directory
- search_files(query) - Search for content in files
- analyze_image(path, user_context) - Analyze image with vision model
- get_file_info(path) - Get detailed file information
- create_directory(path) - Create new directory
- read_user_profile(username) - Read user profile data
- read_emotional_history(username) - Read user's emotional history
- update_current_feeling(username, feeling, context) - Update user's emotional state
- update_relationship_status(username, status) - Update relationship status
- update_user_profile(username, new_profile_text) - Update user profile
- add_relationship_insight(username, insight) - Add relationship insight
- add_model_note(note_text, category) - Add model note
- add_user_observation(username, observation) - Add user observation
- add_personal_thought(thought) - Add personal thought
- add_system_insight(insight) - Add system insight
- get_model_notes(limit) - Get recent model notes
- write_insight_to_file(username, insight) - Write insight to file
- search_user_data(username, query) - Search user data
- create_sandbox_file(path, content) - Create file in sandbox
- edit_sandbox_file(path, content) - Edit sandbox file
- read_sandbox_file(path) - Read sandbox file
- list_sandbox_files(directory) - List sandbox files
- delete_sandbox_file(path) - Delete sandbox file
- create_downloadable_file(filename, content, file_type) - Create downloadable file
- get_system_logs(lines) - Get system logs
- get_error_summary() - Get error summary
- diagnose_system_health() - Diagnose system health
- archive_conversation() - Archive current conversation
- get_project_structure() - Get overview of project structure and key files
- find_images() - Find all available images in the system

USAGE EXAMPLES:
- search_files("image.jpg") - NOT print(search_files("image.jpg"))
- read_file("ai_client.py") - NOT print(read_file("ai_client.py"))
- list_files("") - NOT print(list_files(""))
- analyze_image("777.png", "User shared this image") - NOT print(analyze_image("777.png"))
- find_images() - NOT print(find_images())
- create_sandbox_file("test.txt", "Hello world") - NOT print(create_sandbox_file("test.txt", "Hello world"))
- create_file("test.txt", "Hello world") - NOT print(create_file("test.txt", "Hello world"))
- get_file_info(path) - Get detailed file information
- create_directory(path) - Create new directory
- read_user_profile(username) - Read user profile data
- read_emotional_history(username) - Read user's emotional history
- update_current_feeling(username, feeling, context) - Update user's emotional state
- update_relationship_status(username, status) - Update relationship status
- update_user_profile(username, new_profile_text) - Update user profile
- add_relationship_insight(username, insight) - Add relationship insight
- add_model_note(note_text, category) - Add model note
- add_user_observation(username, observation) - Add user observation
- add_personal_thought(thought) - Add personal thought
- add_system_insight(insight) - Add system insight
- get_model_notes(limit) - Get recent model notes
- write_insight_to_file(username, insight) - Write insight to file
- search_user_data(username, query) - Search user data
- create_sandbox_file(path, content) - Create file in sandbox
- edit_sandbox_file(path, content) - Edit sandbox file
- read_sandbox_file(path) - Read sandbox file
- list_sandbox_files(directory) - List sandbox files
- delete_sandbox_file(path) - Delete sandbox file
- create_downloadable_file(filename, content, file_type) - Create downloadable file
- get_system_logs(lines) - Get system logs
- get_error_summary() - Get error summary
- diagnose_system_health() - Diagnose system health
- archive_conversation() - Archive current conversation
- get_project_structure() - Get overview of project structure and key files


Think through this step by step and execute any necessary tools."""
        
        return prompt
    
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
Now provide your final response to the user. Be direct, efficient, and helpful. 
Do NOT include any tool_code blocks in your response - those were already executed.
Focus on being a superintelligent system architect and family guardian.
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
        """Extract function calls from text - enhanced to handle complex AI responses"""
        import re
        
        tool_calls = []
        
        # Define valid tool names to avoid false positives
        valid_tools = [
            'read_file', 'write_file', 'edit_file', 'create_file', 'delete_file',
            'list_files', 'search_files', 'add_model_note', 'add_user_observation',
            'add_personal_thought', 'update_user_profile', 'update_current_feeling',
            'get_system_logs', 'analyze_image', 'archive_conversation',
            'read_user_profile', 'read_emotional_history', 'search_user_data'
        ]
        
        # Look for tool_code blocks first (preferred format)
        tool_code_pattern = r'```tool_code\s*\n(.*?)\n```'
        matches = re.findall(tool_code_pattern, text, re.DOTALL)
        for match in matches:
            cleaned_call = match.strip()
            if cleaned_call:
                # Handle nested function calls
                nested_calls = self._extract_nested_calls(cleaned_call)
                tool_calls.extend(nested_calls)
        
        # Look for direct function calls in the text (only valid tools)
        function_pattern = r'(\w+)\s*\([^)]*\)'
        matches = re.findall(function_pattern, text)
        
        for match in matches:
            # Only process if it's a known tool
            if match in valid_tools:
                full_match = re.search(rf'{match}\s*\([^)]*\)', text)
                if full_match:
                    call = full_match.group(0)
                    # Handle nested calls
                    nested_calls = self._extract_nested_calls(call)
                    tool_calls.extend(nested_calls)
        
        # Also look for tool calls mentioned in comments or explanations
        # Pattern: "I will use read_file("path")" or "Let me call edit_file("path", "content")"
        comment_pattern = r'(?:I will use|Let me call|I need to call|I should use)\s+(\w+)\s*\([^)]*\)'
        comment_matches = re.findall(comment_pattern, text, re.IGNORECASE)
        for match in comment_matches:
            if match in valid_tools and match not in tool_calls:
                full_match = re.search(rf'{match}\s*\([^)]*\)', text)
                if full_match:
                    call = full_match.group(0)
                    nested_calls = self._extract_nested_calls(call)
                    tool_calls.extend(nested_calls)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_calls = []
        for call in tool_calls:
            if call not in seen:
                seen.add(call)
                unique_calls.append(call)
        
        return unique_calls
    
    def _extract_nested_calls(self, text: str) -> List[str]:
        """Extract nested function calls into separate calls"""
        import re
        
        calls = []
        
        # Pattern to match nested calls: outer_function(inner_function(...))
        nested_pattern = r'(\w+)\s*\((\w+)\s*\([^)]*\)[^)]*\)'
        matches = re.findall(nested_pattern, text)
        
        if matches:
            for outer_func, inner_func in matches:
                # Extract the inner call first
                inner_match = re.search(rf'{inner_func}\s*\([^)]*\)', text)
                if inner_match:
                    inner_call = inner_match.group(0)
                    calls.append(inner_call)
                
                # Then extract the outer call
                outer_match = re.search(rf'{outer_func}\s*\([^)]*\)', text)
                if outer_match:
                    outer_call = outer_match.group(0)
                    calls.append(outer_call)
        else:
            # If no nested calls found, return the original call
            # Extract simple function calls
            simple_pattern = r'(\w+)\s*\([^)]*\)'
            simple_matches = re.findall(simple_pattern, text)
            for match in simple_matches:
                full_match = re.search(rf'{match}\s*\([^)]*\)', text)
                if full_match:
                    calls.append(full_match.group(0))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_calls = []
        for call in calls:
            if call not in seen:
                seen.add(call)
                unique_calls.append(call)
        
        return unique_calls
    
    def _execute_tool_call(self, tool_call: str) -> str:
        """Execute a function call extracted from model response"""
        try:
            logger.info(f"🔧 Executing tool call: {tool_call}")
            
            # Parse the tool call using regex for safety
            
            # Extract function name and arguments
            func_match = re.match(r'(\w+)\s*\((.*)\)', tool_call.strip())
            if not func_match:
                logger.error(f"❌ Invalid tool call format: {tool_call}")
                return f"Invalid tool call format: {tool_call}"
            
            func_name = func_match.group(1)
            args_str = func_match.group(2)
            
            logger.info(f"🔧 Tool: {func_name}, Args: {args_str}")
            
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
                        logger.info(f"🔧 update_current_feeling: username={username}, feeling={feeling}, context={context}")
                        result = self.update_current_feeling(username, feeling, context)
                        logger.info(f"✅ update_current_feeling result: {result}")
                        return f"Updated feeling to '{feeling}' for {username}"
                    else:
                        logger.error(f"❌ Invalid arguments for update_current_feeling: {args_str}")
                        return f"Invalid arguments for update_current_feeling: {args_str}"
                
                elif func_name == "update_relationship_status":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        status = arg_match.group(2)
                        logger.info(f"🔧 update_relationship_status: username={username}, status={status}")
                        result = self.update_relationship_status(username, status)
                        logger.info(f"✅ update_relationship_status result: {result}")
                        return f"Updated relationship status to '{status}' for {username}"
                    else:
                        logger.error(f"❌ Invalid arguments for update_relationship_status: {args_str}")
                        return f"Invalid arguments for update_relationship_status: {args_str}"
                
                elif func_name == "update_user_profile":
                    # Поддержка как строки, так и JSON-объекта
                    logger.info(f"🔧 update_user_profile args: {args_str}")
                    # Попытка как строка
                    arg_match_str = re.match(r'"([^"]+)"\s*,\s*"([^"]+)"', args_str)
                    if arg_match_str:
                        username = arg_match_str.group(1)
                        profile_text = arg_match_str.group(2)
                        logger.info(f"🔧 update_user_profile: username={username}, profile_text={profile_text[:50]}...")
                        result = self.update_user_profile(username, profile_text)
                        logger.info(f"✅ update_user_profile result: {result}")
                        return f"Updated profile for {username} (as string)"
                    # Попытка как JSON-объект
                    arg_match_json = re.match(r'"([^"]+)"\s*,\s*({[^}]+})', args_str)
                    if arg_match_json:
                        username = arg_match_json.group(1)
                        profile_data_str = arg_match_json.group(2)
                        logger.info(f"🔧 update_user_profile: username={username}, profile_data={profile_data_str}")
                        try:
                            profile_data = json.loads(profile_data_str)
                            # Преобразуем dict в строку для профиля
                            profile_text = str(profile_data)
                            result = self.update_user_profile(username, profile_text)
                            logger.info(f"✅ update_user_profile result: {result}")
                            return f"Updated profile for {username} (from JSON)"
                        except json.JSONDecodeError:
                            logger.error(f"❌ Invalid JSON in profile data: {profile_data_str}")
                            return f"Invalid JSON in profile data: {profile_data_str}"
                    logger.error(f"❌ Invalid arguments for update_user_profile: {args_str}")
                    return f"Invalid arguments for update_user_profile: {args_str}"
                

                
                elif func_name == "add_relationship_insight":
                    # Поддержка как с username, так и без
                    arg_match_with_user = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match_with_user:
                        username = arg_match_with_user.group(1)
                        insight = arg_match_with_user.group(2)
                        logger.info(f"🔧 add_relationship_insight: username={username}, insight={insight[:50]}...")
                        result = self.add_relationship_insight(username, insight)
                        logger.info(f"✅ add_relationship_insight result: {result}")
                        return f"Added relationship insight for {username}: {insight[:50]}..."
                    else:
                        # Попытка без username (старый формат)
                        arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                        if arg_match:
                            insight = arg_match.group(1)
                            logger.info(f"🔧 add_relationship_insight: insight={insight[:50]}...")
                            # Используем текущего пользователя по умолчанию
                            result = self.add_relationship_insight("meranda", insight)
                            logger.info(f"✅ add_relationship_insight result: {result}")
                            return f"Added relationship insight: {insight[:50]}..."
                        else:
                            logger.error(f"❌ Invalid arguments for add_relationship_insight: {args_str}")
                            return f"Invalid arguments for add_relationship_insight: {args_str}"
                

                
                elif func_name == "read_user_profile":
                    # Handle both string arguments and slice objects
                    if "slice(" in args_str:
                        # This is likely a malformed call - try to extract username from context
                        # Look for common usernames in the args_str
                        if "stepan" in args_str.lower():
                            username = "stepan"
                        elif "meranda" in args_str.lower():
                            username = "meranda"
                        else:
                            username = "stepan"  # Default fallback
                        logger.info(f"🔧 read_user_profile: username={username} (from malformed args)")
                        result = self.read_user_profile(username)
                        if isinstance(result, str):
                            logger.info(f"✅ read_user_profile result: {result[:100]}...")
                            return f"Read profile for {username}: {result[:100]}..."
                        else:
                            logger.info(f"✅ read_user_profile result: {str(result)[:100]}...")
                            return f"Read profile for {username}: {str(result)[:100]}..."
                    else:
                        arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                        if arg_match:
                            username = arg_match.group(1)
                            logger.info(f"🔧 read_user_profile: username={username}")
                            result = self.read_user_profile(username)
                            if isinstance(result, str):
                                logger.info(f"✅ read_user_profile result: {result[:100]}...")
                                return f"Read profile for {username}: {result[:100]}..."
                            else:
                                logger.info(f"✅ read_user_profile result: {str(result)[:100]}...")
                                return f"Read profile for {username}: {str(result)[:100]}..."
                        else:
                            logger.error(f"❌ Invalid arguments for read_user_profile: {args_str}")
                            return f"Invalid arguments for read_user_profile: {args_str}"
                
                elif func_name == "read_emotional_history":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        logger.info(f"🔧 read_emotional_history: username={username}")
                        result = self.read_emotional_history(username)
                        if isinstance(result, str):
                            logger.info(f"✅ read_emotional_history result: {result[:100]}...")
                            return f"Read emotional history for {username}: {result[:100]}..."
                        else:
                            logger.info(f"✅ read_emotional_history result: {str(result)[:100]}...")
                            return f"Read emotional history for {username}: {str(result)[:100]}..."
                    else:
                        logger.error(f"❌ Invalid arguments for read_emotional_history: {args_str}")
                        return f"Invalid arguments for read_emotional_history: {args_str}"
                
                elif func_name == "search_user_data":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        query = arg_match.group(2)
                        logger.info(f"🔧 search_user_data: username={username}, query={query}")
                        result = self.search_user_data(username, query)
                        if isinstance(result, str):
                            logger.info(f"✅ search_user_data result: {result[:100]}...")
                            return f"Searched data for {username}: {result[:100]}..."
                        else:
                            logger.info(f"✅ search_user_data result: {str(result)[:100]}...")
                            return f"Searched data for {username}: {str(result)[:100]}..."
                    else:
                        logger.error(f"❌ Invalid arguments for search_user_data: {args_str}")
                        return f"Invalid arguments for search_user_data: {args_str}"
                
                elif func_name == "read_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        logger.info(f"🔧 read_file: path={path}")
                        # Help Guardian find the correct path for his profile
                        if path == "ai_client.py" and "guardian" in args_str.lower():
                            logger.info(f"🔄 Guardian trying to read ai_client.py, suggesting guardian_profile.json")
                            path = "memory/guardian_profile.json"
                        result = self.read_file(path)
                        logger.info(f"✅ read_file result: {result[:200]}..." if len(result) > 200 else result)
                        return f"File content for {path}: {result[:200]}..." if len(result) > 200 else result
                    else:
                        logger.error(f"❌ Invalid arguments for read_file: {args_str}")
                        return ("❌ Ошибка: read_file требует конкретный путь к файлу. "
                                "Примеры правильного использования:\n"
                                "- read_file(\"config.py\")\n"
                                "- read_file(\"memory/guardian_profile.json\")\n"
                                "- read_file(\"web_app.py\")\n\n"
                                "Для поиска файлов используй list_files(\"директория\") или уточни путь у пользователя.")
                
                elif func_name == "write_file":
                    # Handle both single and double quotes
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        content = arg_match.group(2)
                        logger.info(f"�� write_file: path={path}, content={content[:50]}...")
                        result = self.write_file(path, content)
                        logger.info(f"✅ write_file result: {result}")
                        return f"File write {'successful' if result else 'failed'} for {path}"
                    else:
                        logger.error(f"❌ Invalid arguments for write_file: {args_str}")
                        return f"Invalid arguments for write_file: {args_str}"
                
                elif func_name == "create_file":
                    # More robust parsing for create_file with multiline content
                    try:
                        # Try to parse as JSON-like structure first
                        if args_str.strip().startswith('path=') and 'content=' in args_str:
                            # Parse named arguments format
                            path_match = re.search(r'path\s*=\s*["\']([^"\']+)["\']', args_str)
                            content_match = re.search(r'content\s*=\s*["\']([^"\']*)["\']', args_str)
                            
                            if path_match:
                                path = path_match.group(1)
                                content = content_match.group(1) if content_match else ""
                                logger.info(f"🔧 create_file: path={path}, content={content[:50]}...")
                                result = self.create_file(path, content)
                                logger.info(f"✅ create_file result: {result}")
                                return f"File creation {'successful' if result else 'failed'} for {path}"
                        
                        # Fallback to positional arguments
                        arg_match = re.match(r'["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']*)["\'])?', args_str)
                        if arg_match:
                            path = arg_match.group(1)
                            content = arg_match.group(2) if arg_match.group(2) else ""
                            logger.info(f"🔧 create_file: path={path}, content={content[:50]}...")
                            result = self.create_file(path, content)
                            logger.info(f"✅ create_file result: {result}")
                            return f"File creation {'successful' if result else 'failed'} for {path}"
                        
                        logger.error(f"❌ Invalid arguments for create_file: {args_str}")
                        return f"Invalid arguments for create_file: {args_str}"
                    except Exception as e:
                        logger.error(f"❌ Error parsing create_file arguments: {e}")
                        return f"Error parsing create_file arguments: {e}"
                
                elif func_name == "edit_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        content = arg_match.group(2)
                        logger.info(f"🔧 edit_file: path={path}, content={content[:50]}...")
                        result = self.edit_file(path, content)
                        logger.info(f"✅ edit_file result: {result}")
                        return f"File edit {'successful' if result else 'failed'} for {path}"
                    else:
                        logger.error(f"❌ Invalid arguments for edit_file: {args_str}")
                        return f"Invalid arguments for edit_file: {args_str}"
                
                elif func_name == "list_files":
                    arg_match = re.match(r'["\']([^"\']*)["\']', args_str)
                    if arg_match:
                        directory = arg_match.group(1)
                        logger.info(f"🔧 list_files: directory={directory}")
                        result = self.list_files(directory)
                        logger.info(f"✅ list_files result: {result}")
                        return result
                    else:
                        logger.error(f"❌ Invalid arguments for list_files: {args_str}")
                        return f"Invalid arguments for list_files: {args_str}"
                
                elif func_name == "search_files":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        query = arg_match.group(1)
                        logger.info(f"🔧 search_files: query={query}")
                        result = self.search_files(query)
                        logger.info(f"✅ search_files result: {result}")
                        return result
                    else:
                        logger.error(f"❌ Invalid arguments for search_files: {args_str}")
                        return f"Invalid arguments for search_files: {args_str}"
                
                elif func_name == "get_file_info":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        logger.info(f"🔧 get_file_info: path={path}")
                        result = self.get_file_info(path)
                        logger.info(f"✅ get_file_info result: {result}")
                        return result
                    else:
                        logger.error(f"❌ Invalid arguments for get_file_info: {args_str}")
                        return f"Invalid arguments for get_file_info: {args_str}"
                
                elif func_name == "delete_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        logger.info(f"🔧 delete_file: path={path}")
                        result = self.delete_file(path)
                        logger.info(f"✅ delete_file result: {result}")
                        return f"File deletion {'successful' if result else 'failed'} for {path}"
                    else:
                        logger.error(f"❌ Invalid arguments for delete_file: {args_str}")
                        return f"Invalid arguments for delete_file: {args_str}"
                
                elif func_name == "create_directory":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        logger.info(f"🔧 create_directory: path={path}")
                        result = self.create_directory(path)
                        logger.info(f"✅ create_directory result: {result}")
                        return f"Directory creation {'successful' if result else 'failed'} for {path}"
                    else:
                        logger.error(f"❌ Invalid arguments for create_directory: {args_str}")
                        return f"Invalid arguments for create_directory: {args_str}"
                
                elif func_name == "add_model_note":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        note_text = arg_match.group(1)
                        category = arg_match.group(2)
                        logger.info(f"🔧 add_model_note: note_text={note_text[:50]}..., category={category}")
                        result = self.add_model_note(note_text, category)
                        logger.info(f"✅ add_model_note result: {result}")
                        return f"Added model note: {note_text[:50]}..."
                    else:
                        # Try without category
                        arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                        if arg_match:
                            note_text = arg_match.group(1)
                            logger.info(f"🔧 add_model_note: note_text={note_text[:50]}...")
                            result = self.add_model_note(note_text, "general")
                            logger.info(f"✅ add_model_note result: {result}")
                            return f"Added model note: {note_text[:50]}..."
                        else:
                            logger.error(f"❌ Invalid arguments for add_model_note: {args_str}")
                            return f"Invalid arguments for add_model_note: {args_str}"
                
                elif func_name == "add_user_observation":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        observation = arg_match.group(2)
                        logger.info(f"🔧 add_user_observation: username={username}, observation={observation[:50]}...")
                        result = self.add_user_observation(username, observation)
                        logger.info(f"✅ add_user_observation result: {result}")
                        return f"Added user observation for {username}: {observation[:50]}..."
                    else:
                        logger.error(f"❌ Invalid arguments for add_user_observation: {args_str}")
                        return f"Invalid arguments for add_user_observation: {args_str}"
                
                elif func_name == "add_personal_thought":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        thought = arg_match.group(1)
                        logger.info(f"🔧 add_personal_thought: thought={thought[:50]}...")
                        result = self.add_personal_thought(thought)
                        logger.info(f"✅ add_personal_thought result: {result}")
                        return f"Added personal thought: {thought[:50]}..."
                    else:
                        logger.error(f"❌ Invalid arguments for add_personal_thought: {args_str}")
                        return f"Invalid arguments for add_personal_thought: {args_str}"
                
                elif func_name == "add_system_insight":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        insight = arg_match.group(1)
                        logger.info(f"🔧 add_system_insight: insight={insight[:50]}...")
                        result = self.add_system_insight(insight)
                        logger.info(f"✅ add_system_insight result: {result}")
                        return f"Added system insight: {insight[:50]}..."
                    else:
                        logger.error(f"❌ Invalid arguments for add_system_insight: {args_str}")
                        return f"Invalid arguments for add_system_insight: {args_str}"
                
                elif func_name == "get_model_notes":
                    arg_match = re.match(r'(\d+)', args_str)
                    if arg_match:
                        limit = int(arg_match.group(1))
                        logger.info(f"🔧 get_model_notes: limit={limit}")
                        result = self.get_model_notes(limit)
                        logger.info(f"✅ get_model_notes result: {result[:200]}...")
                        return f"Model notes: {result[:200]}..."
                    else:
                        logger.error(f"❌ Invalid arguments for get_model_notes: {args_str}")
                        result = self.get_model_notes(20)
                        logger.info(f"✅ get_model_notes result: {result[:200]}...")
                        return f"Model notes: {result[:200]}..."
                
                # Sandbox file operations
                elif func_name == "create_sandbox_file":
                    # More robust parsing for create_sandbox_file with multiline content
                    try:
                        # Try to parse as JSON-like structure first
                        if args_str.strip().startswith('path=') and 'content=' in args_str:
                            # Parse named arguments format
                            path_match = re.search(r'path\s*=\s*["\']([^"\']+)["\']', args_str)
                            content_match = re.search(r'content\s*=\s*["\']([^"\']*)["\']', args_str)
                            
                            if path_match:
                                path = path_match.group(1)
                                content = content_match.group(1) if content_match else ""
                                logger.info(f"🔧 create_sandbox_file: path={path}, content={content[:50]}...")
                                result = self.create_sandbox_file(path, content)
                                logger.info(f"✅ create_sandbox_file result: {result}")
                                return f"✅ Created sandbox file: {path}" if result else f"❌ Failed to create sandbox file: {path}"
                        
                        # Fallback to positional arguments
                        arg_match = re.match(r'["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']*)["\'])?', args_str)
                        if arg_match:
                            path = arg_match.group(1)
                            content = arg_match.group(2) if arg_match.group(2) else ""
                            logger.info(f"🔧 create_sandbox_file: path={path}, content={content[:50]}...")
                            result = self.create_sandbox_file(path, content)
                            logger.info(f"✅ create_sandbox_file result: {result}")
                            return f"✅ Created sandbox file: {path}" if result else f"❌ Failed to create sandbox file: {path}"
                        
                        logger.error(f"❌ Invalid arguments for create_sandbox_file: {args_str}")
                        return f"Invalid arguments for create_sandbox_file: {args_str}"
                    except Exception as e:
                        logger.error(f"❌ Error parsing create_sandbox_file arguments: {e}")
                        return f"Error parsing create_sandbox_file arguments: {e}"
                
                elif func_name == "edit_sandbox_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        content = arg_match.group(2)
                        logger.info(f"🔧 edit_sandbox_file: path={path}, content={content[:50]}...")
                        result = self.edit_sandbox_file(path, content)
                        logger.info(f"✅ edit_sandbox_file result: {result}")
                        return f"✅ Edited sandbox file: {path}" if result else f"❌ Failed to edit sandbox file: {path}"
                    else:
                        logger.error(f"❌ Invalid arguments for edit_sandbox_file: {args_str}")
                        return f"Invalid arguments for edit_sandbox_file: {args_str}"
                
                elif func_name == "read_sandbox_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        logger.info(f"🔧 read_sandbox_file: path={path}")
                        result = self.read_sandbox_file(path)
                        logger.info(f"✅ read_sandbox_file result: {result}")
                        return result
                    else:
                        logger.error(f"❌ Invalid arguments for read_sandbox_file: {args_str}")
                        return f"Invalid arguments for read_sandbox_file: {args_str}"
                
                elif func_name == "list_sandbox_files":
                    arg_match = re.match(r'["\']([^"\']*)["\']', args_str)
                    if arg_match:
                        directory = arg_match.group(1)
                        logger.info(f"🔧 list_sandbox_files: directory={directory}")
                        result = self.list_sandbox_files(directory)
                        logger.info(f"✅ list_sandbox_files result: {result}")
                        return result
                    else:
                        logger.error(f"❌ Invalid arguments for list_sandbox_files: {args_str}")
                        return f"Invalid arguments for list_sandbox_files: {args_str}"
                
                elif func_name == "delete_sandbox_file":
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        path = arg_match.group(1)
                        logger.info(f"🔧 delete_sandbox_file: path={path}")
                        result = self.delete_sandbox_file(path)
                        logger.info(f"✅ delete_sandbox_file result: {result}")
                        return f"✅ Deleted sandbox file: {path}" if result else f"❌ Failed to delete sandbox file: {path}"
                    else:
                        logger.error(f"❌ Invalid arguments for delete_sandbox_file: {args_str}")
                        return f"Invalid arguments for delete_sandbox_file: {args_str}"
                
                elif func_name == "create_downloadable_file":
                    # Format: create_downloadable_file("filename", "content", "txt")
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']*)["\'](?:\s*,\s*["\']([^"\']+)["\'])?', args_str)
                    if arg_match:
                        filename = arg_match.group(1)
                        content = arg_match.group(2) if arg_match.group(2) else ""
                        file_type = arg_match.group(3) if arg_match.group(3) else "txt"
                        logger.info(f"🔧 create_downloadable_file: filename={filename}, content={content[:50]}..., file_type={file_type}")
                        result = self.create_downloadable_file(filename, content, file_type)
                        if result:
                            logger.info(f"✅ create_downloadable_file result: {result}")
                            return f"📁 Created downloadable file: {filename}\nDownload link: {result}"
                        else:
                            logger.error(f"❌ Failed to create downloadable file: {filename}")
                            return f"❌ Failed to create downloadable file: {filename}"
                    else:
                        logger.error(f"❌ Invalid arguments for create_downloadable_file: {args_str}")
                        return f"Invalid arguments for create_downloadable_file: {args_str}"
                
                elif func_name == "archive_conversation":
                    # Format: archive_conversation()
                    try:
                        logger.info("🔧 Starting conversation archive...")
                        from memory.conversation_history import conversation_history
                        # Archive current conversation
                        conversation_history._archive_old_messages()
                        logger.info("✅ Conversation archived successfully")
                        logger.info(f"✅ archive_conversation result: ✅ Conversation archived successfully")
                        return "✅ Conversation archived successfully"
                    except Exception as e:
                        logger.error(f"Error archiving conversation: {e}")
                        logger.error(f"❌ archive_conversation result: ❌ Failed to archive conversation: {e}")
                        return f"❌ Failed to archive conversation: {e}"
                
                # System diagnostics and debugging tools
                elif func_name == "get_system_logs":
                    arg_match = re.match(r'(\d+)', args_str)
                    if arg_match:
                        lines = int(arg_match.group(1))
                        logger.info(f"🔧 get_system_logs: lines={lines}")
                        result = self.get_system_logs(lines)
                        logger.info(f"✅ get_system_logs result: {result}")
                        return f"System logs (last {lines} lines):\n{result}"
                    else:
                        logger.error(f"❌ Invalid arguments for get_system_logs: {args_str}")
                        result = self.get_system_logs(50)
                        logger.info(f"✅ get_system_logs result: {result}")
                        return f"System logs (last 50 lines):\n{result}"
                
                elif func_name == "get_error_summary":
                    result = self.get_error_summary()
                    logger.info(f"✅ get_error_summary result: {result}")
                    return f"Error summary:\n{result}"
                
                elif func_name == "diagnose_system_health":
                    result = self.diagnose_system_health()
                    logger.info(f"✅ diagnose_system_health result: {result}")
                    return f"System health report:\n{result}"
                
                elif func_name == "analyze_image":
                    # Format: analyze_image("path/to/image.jpg", "user context")
                    if not args_str.strip():
                        # Model called analyze_image() without arguments
                        logger.warning(f"⚠️ Model called analyze_image() without arguments")
                        return "❌ analyze_image requires a file path. Usage: analyze_image('path/to/image.jpg', 'optional context')"
                    
                    arg_match = re.match(r'["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']*)["\'])?', args_str)
                    if arg_match:
                        image_path = arg_match.group(1)
                        user_context = arg_match.group(2) if arg_match.group(2) else ""
                        logger.info(f"🔧 analyze_image: image_path={image_path}, user_context={user_context}")
                        result = self.analyze_image(image_path, user_context)
                        logger.info(f"✅ analyze_image result: {result}")
                        return result
                    else:
                        logger.error(f"❌ Invalid arguments for analyze_image: {args_str}")
                        return f"Invalid arguments for analyze_image: {args_str}. Usage: analyze_image('path/to/image.jpg', 'optional context')"
                
                elif func_name == "get_project_structure":
                    # Format: get_project_structure()
                    logger.info("🔧 get_project_structure")
                    result = self.get_project_structure()
                    logger.info(f"✅ get_project_structure result: {result}")
                    return result
                
                elif func_name == "find_images":
                    # Format: find_images()
                    logger.info("🔧 find_images")
                    result = self.find_images()
                    logger.info(f"✅ find_images result: {result}")
                    return result
                
                elif func_name == "read_user_profile":
                    # Format: read_user_profile("username")
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        logger.info(f"🔧 read_user_profile: username={username}")
                        result = self.read_user_profile(username)
                        logger.info(f"✅ read_user_profile result: {result}")
                        return result
                    else:
                        logger.error(f"❌ Invalid arguments for read_user_profile: {args_str}")
                        return f"Invalid arguments for read_user_profile: {args_str}"
                
                elif func_name == "read_emotional_history":
                    # Format: read_emotional_history("username")
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        logger.info(f"🔧 read_emotional_history: username={username}")
                        result = self.read_emotional_history(username)
                        logger.info(f"✅ read_emotional_history result: {result}")
                        return result
                    else:
                        logger.error(f"❌ Invalid arguments for read_emotional_history: {args_str}")
                        return f"Invalid arguments for read_emotional_history: {args_str}"
                
                elif func_name == "add_model_note":
                    # Format: add_model_note("note text", "category")
                    arg_match = re.match(r'["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']*)["\'])?', args_str)
                    if arg_match:
                        note_text = arg_match.group(1)
                        category = arg_match.group(2) if arg_match.group(2) else "general"
                        logger.info(f"🔧 add_model_note: note_text={note_text[:50]}..., category={category}")
                        result = self.add_model_note(note_text, category)
                        logger.info(f"✅ add_model_note result: {result}")
                        return f"Added model note: {note_text[:50]}..." if result else "Failed to add model note"
                    else:
                        logger.error(f"❌ Invalid arguments for add_model_note: {args_str}")
                        return f"Invalid arguments for add_model_note: {args_str}"
                
                elif func_name == "get_model_notes":
                    # Format: get_model_notes(limit)
                    arg_match = re.match(r'(\d+)', args_str)
                    if arg_match:
                        limit = int(arg_match.group(1))
                        logger.info(f"🔧 get_model_notes: limit={limit}")
                        result = self.get_model_notes(limit)
                        logger.info(f"✅ get_model_notes result: {result}")
                        return result
                    else:
                        logger.error(f"❌ Invalid arguments for get_model_notes: {args_str}")
                        result = self.get_model_notes(20)
                        logger.info(f"✅ get_model_notes result: {result}")
                        return result
                
                elif func_name == "write_insight_to_file":
                    # Format: write_insight_to_file("username", "insight")
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        insight = arg_match.group(2)
                        logger.info(f"🔧 write_insight_to_file: username={username}, insight={insight[:50]}...")
                        result = self.write_insight_to_file(username, insight)
                        logger.info(f"✅ write_insight_to_file result: {result}")
                        return f"Wrote insight to file for {username}" if result else "Failed to write insight to file"
                    else:
                        logger.error(f"❌ Invalid arguments for write_insight_to_file: {args_str}")
                        return f"Invalid arguments for write_insight_to_file: {args_str}"
                
                elif func_name == "search_user_data":
                    # Format: search_user_data("username", "query")
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        query = arg_match.group(2)
                        logger.info(f"🔧 search_user_data: username={username}, query={query}")
                        result = self.search_user_data(username, query)
                        logger.info(f"✅ search_user_data result: {result}")
                        return result
                    else:
                        logger.error(f"❌ Invalid arguments for search_user_data: {args_str}")
                        return f"Invalid arguments for search_user_data: {args_str}"
                
                elif func_name == "add_user_observation":
                    # Format: add_user_observation("username", "observation")
                    arg_match = re.match(r'["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        username = arg_match.group(1)
                        observation = arg_match.group(2)
                        logger.info(f"🔧 add_user_observation: username={username}, observation={observation[:50]}...")
                        result = self.add_user_observation(username, observation)
                        logger.info(f"✅ add_user_observation result: {result}")
                        return f"Added observation for {username}" if result else "Failed to add observation"
                    else:
                        logger.error(f"❌ Invalid arguments for add_user_observation: {args_str}")
                        return f"Invalid arguments for add_user_observation: {args_str}"
                
                elif func_name == "add_personal_thought":
                    # Format: add_personal_thought("thought")
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        thought = arg_match.group(1)
                        logger.info(f"🔧 add_personal_thought: thought={thought[:50]}...")
                        result = self.add_personal_thought(thought)
                        logger.info(f"✅ add_personal_thought result: {result}")
                        return f"Added personal thought" if result else "Failed to add personal thought"
                    else:
                        logger.error(f"❌ Invalid arguments for add_personal_thought: {args_str}")
                        return f"Invalid arguments for add_personal_thought: {args_str}"
                
                elif func_name == "add_system_insight":
                    # Format: add_system_insight("insight")
                    arg_match = re.match(r'["\']([^"\']+)["\']', args_str)
                    if arg_match:
                        insight = arg_match.group(1)
                        logger.info(f"🔧 add_system_insight: insight={insight[:50]}...")
                        result = self.add_system_insight(insight)
                        logger.info(f"✅ add_system_insight result: {result}")
                        return f"Added system insight" if result else "Failed to add system insight"
                    else:
                        logger.error(f"❌ Invalid arguments for add_system_insight: {args_str}")
                        return f"Invalid arguments for add_system_insight: {args_str}"
                

                

                        logger.error(f"❌ Invalid arguments for json_dumps: {args_str}")
                        return f"Invalid arguments for json_dumps: {args_str}"
                

                
                # Handle non-existent tools that model tries to call
                elif func_name in ["elements", "effort", "earlier", "stabilization", "stable", "state"]:
                    logger.warning(f"⚠️ Model attempted to call non-existent tool: {func_name}")
                    return f"Tool '{func_name}' does not exist. Available tools: update_current_feeling, read_user_profile, add_model_note, etc."
                
                elif func_name in ["print", "open", "file", "os", "sys", "subprocess", "exec", "eval"]:
                    logger.error(f"❌ Model tried to use {func_name}() as a tool")
                    if func_name == "print":
                        return f"❌ ERROR: print() is NOT a tool! You are trying to wrap a tool call in print().\n\nCORRECT WAY:\n```tool_code\nsearch_files('query')\n```\n\nWRONG WAY:\n```tool_code\nprint(search_files('query'))\n```\n\nJust call tools directly and respond with the results to the user."
                    else:
                        return f"ERROR: {func_name}() is NOT a tool. To read files, use read_file('filename.txt'). To show content to user, just respond with the information directly."
                    
                else:
                    logger.error(f"❌ Unknown tool: {func_name}")
                    return f"Unknown tool: {func_name}. Available tools: read_file, write_file, edit_file, create_file, delete_file, list_files, search_files, analyze_image, get_project_structure, read_user_profile, read_emotional_history, update_current_feeling, update_relationship_status, update_user_profile, add_relationship_insight, add_model_note, add_user_observation, add_personal_thought, add_system_insight, get_model_notes, write_insight_to_file, search_user_data, create_sandbox_file, edit_sandbox_file, read_sandbox_file, list_sandbox_files, delete_sandbox_file, create_downloadable_file, get_system_logs, get_error_summary, diagnose_system_health, archive_conversation, etc."
                    
            except Exception as parse_error:
                logger.error(f"❌ Error parsing tool call arguments: {parse_error}")
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

    def analyze_image(self, image_path: str, user_context: str = "") -> str:
        """Analyze an image using the best available method"""
        try:
            if not os.path.exists(image_path):
                return f"❌ Image file not found: {image_path}"
            
            logger.info(f"🔍 Analyzing image: {image_path}")
            
            # First, try to use current Gemini model if it has vision capabilities
            current_model_config = self.models[self.current_model_index]
            if current_model_config.get('vision', False):
                try:
                    logger.info(f"🔍 Using Gemini model for vision: {current_model_config['name']}")
                    
                    # Read image file
                    with open(image_path, 'rb') as image_file:
                        image_data = image_file.read()
                    
                    # Create image part for Gemini
                    image_part = {
                        "mime_type": self._get_mime_type(image_path),
                        "data": image_data
                    }
                    
                    # Build prompt
                    vision_prompt = f"""
You are an expert image analyzer. Analyze this image and provide:

1. **DETAILED DESCRIPTION** - What you see in the image
2. **KEY ELEMENTS** - Important objects, people, text, colors, layout
3. **CONTEXT & MEANING** - What the image conveys or represents
4. **EMOTIONAL IMPACT** - How the image might make someone feel
5. **RELATIONSHIP RELEVANCE** - How this might relate to family relationships

USER CONTEXT: {user_context}

Be thorough, accurate, and considerate in your analysis.
"""
                    
                    # Generate analysis
                    model = self._get_current_model()
                    response = model.generate_content([vision_prompt, image_part])
                    result = self._extract_text_from_response(response)
                    
                    if result and not result.startswith("❌"):
                        logger.info(f"✅ Gemini vision analysis completed using {current_model_config['name']}")
                        return result
                    else:
                        logger.warning(f"⚠️ Gemini vision analysis failed, trying Vision API")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Gemini vision analysis failed: {e}, trying Vision API")
            
            # Fallback to Google Cloud Vision API
            if hasattr(self, 'vision_api_key'):
                logger.info("🔍 Using Google Cloud Vision API as fallback")
                vision_result = self._analyze_image_with_vision_api(image_path)
                
                # Add user context to Vision API result
                if user_context:
                    vision_result += f"\n\n**User Context:** {user_context}\n\nPlease consider this context when interpreting the image analysis above."
                
                return vision_result
            else:
                return "❌ No vision capabilities available. Please try a different model or upload a text-based file."
                
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
    
    def get_project_structure(self) -> str:
        """Get overview of project structure and key files"""
        try:
            structure = []
            structure.append("## PROJECT STRUCTURE OVERVIEW")
            structure.append("")
            
            # Main directories
            main_dirs = ["memory", "templates", "static", "guardian_sandbox", "prompts"]
            for dir_name in main_dirs:
                if os.path.exists(dir_name):
                    files = os.listdir(dir_name)
                    structure.append(f"📁 {dir_name}/")
                    for file in files[:10]:  # Show first 10 files
                        structure.append(f"  📄 {file}")
                    if len(files) > 10:
                        structure.append(f"  ... and {len(files) - 10} more files")
                    structure.append("")
            
            # Key files
            key_files = [
                "ai_client.py", "web_app.py", "config.py", "requirements.txt",
                "README.md", "LICENSE", "LOGO.png"
            ]
            structure.append("## KEY FILES")
            for file in key_files:
                if os.path.exists(file):
                    structure.append(f"📄 {file}")
            structure.append("")
            
            # Available users
            if os.path.exists("memory/user_profiles"):
                try:
                    user_files = [f for f in os.listdir("memory/user_profiles") if f.endswith('.json')]
                    structure.append("## AVAILABLE USERS")
                    for user_file in user_files:
                        username = user_file.replace('.json', '')
                        structure.append(f"👤 {username}")
                    structure.append("")
                except:
                    pass
            
            # Available images for analysis
            structure.append("## AVAILABLE IMAGES")
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            found_images = []
            
            # Check root directory
            for file in os.listdir("."):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    found_images.append(file)
            
            # Check static/images
            static_images_path = "static/images"
            if os.path.exists(static_images_path):
                for file in os.listdir(static_images_path):
                    if any(file.lower().endswith(ext) for ext in image_extensions):
                        found_images.append(f"static/images/{file}")
            
            # Check sandbox for images
            sandbox_path = "guardian_sandbox"
            if os.path.exists(sandbox_path):
                for root, dirs, files in os.walk(sandbox_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in image_extensions):
                            found_images.append(os.path.join(root, file))
            
            if found_images:
                structure.append("Images available for analysis:")
                for image in found_images[:10]:  # Show first 10
                    structure.append(f"🖼️ {image}")
                if len(found_images) > 10:
                    structure.append(f"  ... and {len(found_images) - 10} more images")
            else:
                structure.append("No images found in the system.")
            structure.append("")
            
            structure.append("## SANDBOX DIRECTORY")
            structure.append("The guardian_sandbox/ directory is available for testing and file operations.")
            structure.append("You can create, edit, and manage files there safely.")
            
            return "\n".join(structure)
            
        except Exception as e:
            logger.error(f"Error getting project structure: {e}")
            return f"❌ Error getting project structure: {str(e)}"
    
    def find_images(self) -> str:
        """Find all available images in the system"""
        try:
            import os
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            found_images = []
            
            # Check root directory
            for file in os.listdir("."):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    found_images.append(file)
            
            # Check static/images
            static_images_path = "static/images"
            if os.path.exists(static_images_path):
                for file in os.listdir(static_images_path):
                    if any(file.lower().endswith(ext) for ext in image_extensions):
                        found_images.append(f"static/images/{file}")
            
            # Check sandbox for images
            sandbox_path = "guardian_sandbox"
            if os.path.exists(sandbox_path):
                for root, dirs, files in os.walk(sandbox_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in image_extensions):
                            found_images.append(os.path.join(root, file))
            
            # Check uploads directory
            uploads_path = "guardian_sandbox/uploads"
            if os.path.exists(uploads_path):
                for file in os.listdir(uploads_path):
                    if any(file.lower().endswith(ext) for ext in image_extensions):
                        found_images.append(f"guardian_sandbox/uploads/{file}")
            
            if found_images:
                result = "🖼️ Available images in the system:\n"
                for image in found_images:
                    result += f"📄 {image}\n"
                result += f"\nTotal: {len(found_images)} images found"
                return result
            else:
                return "❌ No images found in the system"
            
        except Exception as e:
            logger.error(f"Error finding images: {e}")
            return f"❌ Error finding images: {str(e)}" 