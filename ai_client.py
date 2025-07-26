import logging
import time
from datetime import datetime
import google.generativeai as genai
from typing import Optional, Dict, Any
from config import settings
from mcp_tools.mcp_client import mcp_tools
from profile_updater import profile_updater

# Configure logging
logger = logging.getLogger(__name__)

class AIClient:
    """Unified AI client supporting both Gemini and OpenAI"""
    
    def __init__(self):
        self.gemini_model = None
        self.openai_client = None
        self.primary_engine = "gemini"
        
        # Initialize Gemini
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_MAX_TOKENS,
                )
            )
            logger.info(f"✅ Gemini {settings.GEMINI_MODEL} initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            self.primary_engine = "openai"
        
        # Initialize OpenAI (fallback)
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            self.openai_client = openai
            logger.info("✅ OpenAI client initialized as fallback")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI fallback not available: {e}")
    
    async def generate_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI response using primary engine (Gemini) with OpenAI fallback
        """
        start_time = time.time()
        logger.info(f"🚀 Starting AI response generation for: {user_message[:50]}...")
        
        try:
            if self.primary_engine == "gemini" and self.gemini_model:
                logger.info("🤖 Using Gemini as primary engine")
                response = await self._generate_gemini_response(
                    system_prompt, user_message, context, user_profile
                )
            elif self.openai_client:
                logger.info("🤖 Using OpenAI as fallback")
                response = await self._generate_openai_response(
                    system_prompt, user_message, context, user_profile
                )
            else:
                raise Exception("No AI engine available")
            
            # Process response for function calls
            # Extract username from user_profile if available
            username = user_profile.get('username', 'meranda') if user_profile else 'meranda'
            processed_response = self._process_response_for_functions(response, user_message, username)
            
            total_time = time.time() - start_time
            logger.info(f"✅ AI response generated in {total_time:.2f}s")
            logger.info(f"📝 Response length: {len(processed_response)} characters")
            
            return processed_response
                
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"❌ AI response generation failed after {total_time:.2f}s: {e}")
            # Try fallback if primary failed
            if self.primary_engine == "gemini" and self.openai_client:
                logger.info("🔄 Trying OpenAI fallback...")
                try:
                    return await self._generate_openai_response(
                        system_prompt, user_message, context, user_profile
                    )
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback also failed: {fallback_error}")
            
            return "I apologize, but I'm experiencing technical difficulties. Please try again later."
    
    def _process_response_for_functions(self, response: str, user_message: str, username: str = "meranda") -> str:
        """Process AI response for function calls and execute them"""
        logger.info("🔍 Processing response for function calls...")
        
        # AUTOMATIC FEELINGS DETECTION
        feelings_phrases = {
            "плохо себя чувствую": "Feeling unwell",
            "плохо": "Feeling bad",
            "грустно": "Sad",
            "грустная": "Sad",
            "грустный": "Sad", 
            "счастлива": "Happy",
            "счастлив": "Happy",
            "счастливый": "Happy",
            "радостно": "Joyful",
            "радостная": "Joyful",
            "радостный": "Joyful",
            "устала": "Tired",
            "устал": "Tired",
            "усталый": "Tired",
            "усталая": "Tired",
            "злая": "Angry",
            "злой": "Angry",
            "злюсь": "Angry",
            "нервничаю": "Nervous",
            "волнуюсь": "Anxious",
            "тревожно": "Anxious",
            "спокойно": "Calm",
            "спокойная": "Calm",
            "спокойный": "Calm",
            "i feel bad": "Feeling bad",
            "i'm sad": "Sad",
            "i'm happy": "Happy",
            "i'm tired": "Tired",
            "i'm angry": "Angry",
            "i'm nervous": "Nervous",
            "i'm anxious": "Anxious",
            "i'm calm": "Calm",
            "feeling down": "Feeling down",
            "feeling great": "Feeling great",
            "feeling good": "Feeling good"
        }
        
        # Check for feelings in the message
        for phrase, feeling in feelings_phrases.items():
            if phrase in user_message.lower():
                logger.info(f"💭 Detected feeling: {feeling}")
                result = profile_updater.update_current_feeling(username, feeling)
                logger.info(f"💭 Updated feeling to: {feeling}")
                break
        
        # AUTOMATIC RELATIONSHIP STATUS DETECTION
        relationship_phrases = {
            "мы ссоримся": "Having conflicts",
            "мы ругаемся": "Having conflicts", 
            "мы в ссоре": "In conflict",
            "все плохо": "Relationship difficulties",
            "все хорошо": "Relationship is good",
            "все отлично": "Relationship is great",
            "чувствую себя одиноко": "Feeling lonely",
            "чувствую себя одиноким": "Feeling lonely",
            "чувствую себя одинокой": "Feeling lonely",
            "мы близки": "Feeling close",
            "мы далеки": "Feeling distant",
            "we're fighting": "Having conflicts",
            "we're arguing": "Having conflicts",
            "things are bad": "Relationship difficulties",
            "things are good": "Relationship is good",
            "things are great": "Relationship is great",
            "feeling lonely": "Feeling lonely",
            "feeling close": "Feeling close",
            "feeling distant": "Feeling distant"
        }
        
        # Check for relationship status in the message
        for phrase, status in relationship_phrases.items():
            if phrase in user_message.lower():
                logger.info(f"💕 Detected relationship status: {status}")
                result = profile_updater.update_relationship_status(username, status)
                logger.info(f"💕 Updated relationship status to: {status}")
                break
        
        # Check for diary requests
        if any(phrase in user_message.lower() for phrase in ["write in diary", "add to diary", "diary entry", "запиши в дневник", "добавь в дневник"]):
            logger.info("📖 Detected diary entry request")
            
            # Extract content from the message
            content = user_message
            for phrase in ["write in diary -", "add to diary -", "diary entry -", "запиши в дневник -", "добавь в дневник -"]:
                if phrase in user_message.lower():
                    content = user_message[user_message.lower().find(phrase) + len(phrase):].strip()
                    break
            
            if content and content != user_message:
                result = profile_updater.add_diary_entry(username, {
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "mood": "Reflective"
                })
                logger.info(f"📖 Diary entry added: {result}")
                return f"📖 I've added this to your diary: \"{content}\" - Your thoughts are now saved for reflection. You can view all your diary entries by clicking the Diary button!"
            else:
                return "📖 I'd love to add something to your diary! Please write something like 'write in diary - [your thoughts]' or 'add to diary - [your message]' and I'll save it for you."
        
        # Check for profile update requests
        if "change my" in user_message.lower() or "update my" in user_message.lower():
            logger.info("🔄 Detected profile update request")
            
            # Check for profile update
            if "profile" in user_message.lower():
                # Extract new profile content
                content = user_message
                for phrase in ["change my profile -", "update my profile -"]:
                    if phrase in user_message.lower():
                        content = user_message[user_message.lower().find(phrase) + len(phrase):].strip()
                        break
                
                if content and content != user_message:
                    result = profile_updater.update_user_profile(username, content)
                    logger.info(f"🔄 Profile update result: {result}")
                    return f"✅ I've updated your profile: \"{content}\" - Your profile now reflects who you are!"
                else:
                    return "🔄 I'd love to update your profile! Please write something like 'change my profile - [your description]' and I'll update it for you."
        
        # AUTOMATIC HIDDEN NOTES - Create private observations
        hidden_note_triggers = [
            "работа", "work", "job", "карьера", "career",  # Work-related
            "семья", "family", "родители", "parents",      # Family
            "друзья", "friends", "общение", "communication", # Social
            "здоровье", "health", "болезнь", "sick",       # Health
            "стресс", "stress", "усталость", "exhaustion", # Stress
            "планы", "plans", "цели", "goals",             # Plans
            "мечты", "dreams", "желания", "desires",       # Dreams
            "страхи", "fears", "тревоги", "anxieties",     # Fears
            "радость", "joy", "счастье", "happiness",      # Positive emotions
            "грусть", "sadness", "печаль", "grief"         # Negative emotions
        ]
        
        # Check if message contains topics that warrant hidden notes
        for trigger in hidden_note_triggers:
            if trigger in user_message.lower():
                # Create a contextual hidden note
                hidden_note = f"User shared about {trigger}: {user_message[:100]}... (observed at {datetime.now().strftime('%Y-%m-%d %H:%M')})"
                result = profile_updater.update_hidden_profile(username, hidden_note)
                logger.info(f"📝 Added hidden note about {trigger}")
                break
        
        # Check for insight requests
        if "insight" in user_message.lower() or "pattern" in user_message.lower():
            logger.info("🧠 Detected insight request")
            insight = f"User requested insight about: {user_message}"
            result = profile_updater.add_relationship_insight(insight)
            logger.info(f"🧠 Insight added: {result}")
        
        logger.info("✅ Response processing completed")
        return response
    
    async def _generate_gemini_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate response using Gemini 2.5 Pro"""
        
        prompt_start_time = time.time()
        
        # Build the full prompt
        full_prompt = system_prompt + "\n\n"
        
        if context:
            full_prompt += f"RELATIONSHIP CONTEXT:\n{context}\n\n"
        
        if user_profile:
            full_prompt += f"CURRENT USER PROFILE:\n{self._format_user_profile(user_profile)}\n\n"
        
        full_prompt += f"USER MESSAGE:\n{user_message}\n\n"
        full_prompt += "Please respond as Dr. Harmony, the family psychologist:"
        
        # Add automatic profile update instructions
        full_prompt += "\n\nAUTOMATIC PROFILE UPDATES:\n"
        full_prompt += "You can automatically update user profiles and make hidden notes:\n"
        full_prompt += "- update_user_profile(username, new_profile) - Update main profile\n"
        full_prompt += "- update_hidden_profile(username, new_hidden_profile) - Add private notes\n"
        full_prompt += "- update_relationship_status(username, status) - Update relationship status\n"
        full_prompt += "- update_current_feeling(username, feeling) - Update current feeling\n"
        full_prompt += "- add_relationship_insight(insight) - Add relationship insights\n"
        full_prompt += "\nUse these functions naturally when you notice important information about the user."
        
        # Add conversation history instructions
        full_prompt += "\n\nCONVERSATION HISTORY:\n"
        full_prompt += "You have access to recent conversation history and archived summaries.\n"
        full_prompt += "Use this context to provide personalized, contextual responses.\n"
        full_prompt += "If this is a first message or greeting, create a warm, personalized welcome.\n"
        full_prompt += "Reference previous conversations naturally when relevant.\n"
        
        full_prompt += "\n\nIMPORTANT: Respond ONLY with natural conversation. Do NOT show function calls or JSON in your response."
        
        prompt_time = time.time() - prompt_start_time
        logger.info(f"📝 Prompt built in {prompt_time:.2f}s")
        logger.info(f"📏 Prompt length: {len(full_prompt)} characters")
        
        api_start_time = time.time()
        try:
            logger.info("🌐 Making Gemini API call...")
            # Make direct API call without timeout
            response = self.gemini_model.generate_content(full_prompt)
            
            api_time = time.time() - api_start_time
            logger.info(f"🌐 Gemini API call completed in {api_time:.2f}s")
            
            # Handle different response formats
            if response:
                if hasattr(response, 'text') and response.text:
                    logger.info("✅ Gemini response generated successfully")
                    logger.info(f"📝 Raw response length: {len(response.text)} characters")
                    return self._clean_response(response.text)
                elif hasattr(response, 'parts') and response.parts:
                    # Handle parts-based response
                    text_parts = []
                    for part in response.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    if text_parts:
                        full_text = ' '.join(text_parts)
                        logger.info("✅ Gemini response generated from parts")
                        logger.info(f"📝 Raw response length: {len(full_text)} characters")
                        return self._clean_response(full_text)
            
            logger.warning("⚠️ Gemini returned empty response")
            return "I'm processing your message. Could you please rephrase or provide more details?"
                
        except Exception as e:
            api_time = time.time() - api_start_time
            logger.error(f"❌ Gemini generation error after {api_time:.2f}s: {e}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            logger.error(f"❌ Error details: {str(e)}")
            
            # Return a fallback response instead of raising
            return "I'm having trouble processing that right now. Could you try rephrasing your message?"
    
    async def _generate_openai_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate response using OpenAI (fallback)"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.append({
                "role": "system", 
                "content": f"RELATIONSHIP CONTEXT:\n{context}"
            })
        
        if user_profile:
            messages.append({
                "role": "system",
                "content": f"CURRENT USER PROFILE:\n{self._format_user_profile(user_profile)}"
            })
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.openai_client.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE
            )
            
            logger.info("✅ OpenAI response generated successfully")
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ OpenAI generation error: {e}")
            raise e
    
    def _clean_response(self, response: str) -> str:
        """Clean response from technical details and function calls"""
        if not response:
            return response
        
        # Remove JSON function calls
        import re
        
        # Remove JSON arrays with function calls
        response = re.sub(r'\[\s*\{[^}]*"function_name"[^}]*\}[^\]]*\]', '', response)
        
        # Remove individual function call objects
        response = re.sub(r'\{\s*"function_name"[^}]*\}', '', response)
        
        # Remove any remaining JSON-like structures
        response = re.sub(r'\[\s*\{[^}]*\}\s*\]', '', response)
        
        # Clean up extra whitespace and newlines
        response = re.sub(r'\n\s*\n\s*\n', '\n\n', response)
        response = response.strip()
        
        return response
    
    def _format_user_profile(self, user_profile: Dict[str, Any]) -> str:
        """Format user profile for AI context"""
        if not user_profile:
            return "No user profile available"
        
        formatted = f"""
Name: {user_profile.get('full_name', 'Unknown')}
Personality: {', '.join(user_profile.get('personality_traits', []))}
Communication Style: {user_profile.get('communication_style', 'Unknown')}
Love Language: {user_profile.get('love_language', 'Unknown')}
Current Relationship Status: {user_profile.get('current_relationship_status', 'Unknown')}
Relationship Goals: {', '.join(user_profile.get('relationship_goals', []))}
Strengths: {', '.join(user_profile.get('strengths_in_relationship', []))}
Areas for Improvement: {', '.join(user_profile.get('areas_for_improvement', []))}
        """.strip()
        
        return formatted
    
    def get_engine_info(self) -> str:
        """Get information about available AI engines"""
        info = f"Primary Engine: {self.primary_engine.upper()}"
        if self.gemini_model:
            info += f" (Gemini {settings.GEMINI_MODEL})"
        if self.openai_client:
            info += " | OpenAI Fallback: Available"
        else:
            info += " | OpenAI Fallback: Not Available"
        return info

# Global AI client instance
ai_client = AIClient() 