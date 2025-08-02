"""
Gemini API клиент - УПРОЩЕННАЯ АРХИТЕКТУРА
"""

import base64
import os
import time
import logging
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime
import json

import google.generativeai as genai
from google.cloud import vision

from ..utils.config import Config
from ..utils.logger import Logger
from ..utils.error_handler import ErrorHandler

logger = Logger()

class GeminiClient:
    """Упрощенный класс для работы с Gemini API"""
    
    def __init__(self):
        """Инициализация Gemini клиента"""
        self.config = Config()
        self.error_handler = ErrorHandler()
        
        # Инициализируем Gemini
        api_key = self.config.get_gemini_api_key()
        genai.configure(api_key=api_key)
        
        # Инициализируем Vision API
        self.vision_client = None
        self.vision_api_key = None
        try:
            vision_api_key = self.config.get_vision_api_key()
            if vision_api_key:
                self.vision_api_key = vision_api_key
                self.vision_client = True  # Mark as available
                logger.info("✅ Google Cloud Vision API key configured")
            else:
                logger.warning("⚠️ No Google Cloud Vision API key provided")
        except Exception as e:
            logger.warning(f"⚠️ Google Cloud Vision API not available: {e}")
        
        # Определяем доступные модели с gemini-2.5-flash-lite по умолчанию
        self.models = [
            {'name': 'gemini-2.5-flash-lite', 'quota': 1000},  # МОДЕЛЬ ПО УМОЛЧАНИЮ
            {'name': 'gemini-2.5-pro', 'quota': 100},
            {'name': 'gemini-1.5-pro', 'quota': 150},
            {'name': 'gemini-2.5-flash', 'quota': 250},
            {'name': 'gemini-1.5-flash', 'quota': 500},
            {'name': 'gemini-2.0-flash', 'quota': 200},
            {'name': 'gemini-2.0-flash-lite', 'quota': 1000}
        ]
        
        self.current_model_index = 0  # gemini-2.5-flash-lite
    
    def _parse_gemini_response(self, response) -> str:
        """УНИВЕРСАЛЬНЫЙ ПАРСЕР - обрабатывает любой формат ответа Gemini"""
        try:
            # Отладочное логирование
            logger.info(f"🔍 Parsing response type: {type(response)}")
            logger.info(f"🔍 Response attributes: {dir(response)}")
            
            # Проверяем finish_reason
            if hasattr(response, 'finish_reason'):
                finish_reason = response.finish_reason
                logger.info(f"🔍 Finish reason: {finish_reason}")
                if finish_reason == 1:  # SAFETY
                    return "❌ Ответ заблокирован системой безопасности"
                elif finish_reason == 2:  # RECITATION
                    return "❌ Ответ заблокирован из-за рецитации"
                elif finish_reason == 3:  # OTHER
                    return "❌ Ответ заблокирован по другим причинам"
            
            # Способ 1: прямой доступ к text
            if hasattr(response, 'text') and response.text:
                logger.info(f"✅ Found text directly: {response.text[:100]}...")
                return response.text
            
            # Способ 2: через parts
            if hasattr(response, 'parts') and response.parts:
                logger.info(f"🔍 Found {len(response.parts)} parts")
                text_parts = []
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    result = "".join(text_parts)
                    logger.info(f"✅ Found text via parts: {result[:100]}...")
                    return result
            
            # Способ 3: через candidates
            if hasattr(response, 'candidates') and response.candidates:
                logger.info(f"🔍 Found {len(response.candidates)} candidates")
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        logger.info(f"🔍 Found {len(candidate.content.parts)} content parts")
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            result = "".join(text_parts)
                            logger.info(f"✅ Found text via candidates: {result[:100]}...")
                            return result
                    elif hasattr(candidate.content, 'text') and candidate.content.text:
                        logger.info(f"✅ Found text via candidate content: {candidate.content.text[:100]}...")
                        return candidate.content.text
            
            logger.warning("⚠️ No text found in response")
            return "❌ Не удалось сгенерировать ответ"
            
        except Exception as e:
            logger.error(f"❌ Parse error: {e}")
            return f"❌ Parse error: {str(e)}"
    
    def _get_current_model(self) -> str:
        """Получаем текущую модель"""
        return self.models[self.current_model_index]['name']
    
    def _switch_to_next_model(self):
        """Переключаемся на следующую модель"""
        self.current_model_index = (self.current_model_index + 1) % len(self.models)
        logger.info(f"🚀 Using model: {self._get_current_model()}")
    
    def switch_to_model(self, model_name: str) -> bool:
        """Переключаемся на конкретную модель"""
        for i, model in enumerate(self.models):
            if model['name'] == model_name:
                self.current_model_index = i
                logger.info(f"🚀 Switched to model: {model_name}")
                return True
        return False
    
    def get_model_status(self) -> Dict[str, Any]:
        """Получаем статус моделей"""
        current_model = self.models[self.current_model_index]
        return {
            'current_model': current_model['name'],
            'current_quota': current_model['quota'],
            'available_models': [model['name'] for model in self.models],
            'model_index': self.current_model_index
        }
    
    def get_current_model(self) -> str:
        """Получаем имя текущей модели"""
        return self._get_current_model()
    
    def _build_prompt(self, system_prompt: str, user_message: str, context: Optional[str] = None, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """Строим промпт с контекстом"""
        full_prompt = system_prompt
        
        if context:
            full_prompt += f"\n\nContext: {context}"
        
        if user_profile:
            profile_info = f"User Profile: {json.dumps(user_profile, ensure_ascii=False)}"
            full_prompt += f"\n\n{profile_info}"
        
        full_prompt += f"\n\nUser: {user_message}"
        return full_prompt
    
    async def generate_streaming_response(self, system_prompt: str, user_message: str, context: Optional[str] = None, user_profile: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Генерируем стриминг ответ с улучшенным fallback"""
        
        # Пробуем все модели с fallback
        for attempt in range(len(self.models)):
            try:
                model_name = self._get_current_model()
                logger.info(f"🔄 Streaming attempt {attempt + 1}: Using model {model_name}")
                
                model = genai.GenerativeModel(model_name)
                
                full_prompt = self._build_prompt(system_prompt, user_message, context, user_profile)
                response = model.generate_content(full_prompt, stream=True)
                
                for chunk in response:
                    # Используем универсальный парсер для каждого chunk
                    chunk_text = self._parse_gemini_response(chunk)
                    if chunk_text and not chunk_text.startswith("❌"):
                        yield chunk_text
                
                # Если дошли сюда, значит стриминг успешен
                logger.info(f"✅ Streaming success with model {model_name}")
                return
                    
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"⚠️ Streaming error with model {self._get_current_model()}: {error_msg}")
                
                # Проверяем тип ошибки для fallback
                if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    logger.warning(f"⚠️ Quota/rate limit exceeded, switching to next model...")
                    self._switch_to_next_model()
                    continue
                elif "safety" in error_msg.lower() or "blocked" in error_msg.lower():
                    logger.warning(f"⚠️ Safety block, switching to next model...")
                    self._switch_to_next_model()
                    continue
                else:
                    # Для других ошибок тоже пробуем следующую модель
                    logger.warning(f"⚠️ Other error, switching to next model...")
                    self._switch_to_next_model()
                    continue
        
        # Если все модели исчерпаны
        logger.error("❌ All models exhausted in streaming")
        yield "❌ Все модели недоступны. Попробуйте позже или обратитесь к администратору."
    
    def chat(self, message: str, user_profile: Optional[Dict[str, Any]] = None, conversation_context: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Основной метод для чата с Gemini с reasoning через промпт и fallback"""
        
        # Пробуем все модели с fallback
        for attempt in range(len(self.models)):
            try:
                # Получаем текущую модель
                model_name = self._get_current_model()
                logger.info(f"🔄 Attempt {attempt + 1}: Using model {model_name}")
                
                model = genai.GenerativeModel(model_name)
                
                # Строим промпт с reasoning
                prompt = self._build_prompt_with_reasoning(system_prompt or "You are a helpful AI assistant.", message, conversation_context, user_profile)
                
                # Генерируем ответ
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        top_p=0.8,
                        top_k=40,
                        max_output_tokens=8192
                    )
                )
                
                result = self._parse_gemini_response(response)
                logger.info(f"✅ Success with model {model_name}, result: {result[:100]}...")
                return result
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"⚠️ Error with model {self._get_current_model()}: {error_msg}")
                
                # Проверяем тип ошибки для fallback
                if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    logger.warning(f"⚠️ Quota/rate limit exceeded, switching to next model...")
                    self._switch_to_next_model()
                    continue
                elif "safety" in error_msg.lower() or "blocked" in error_msg.lower():
                    logger.warning(f"⚠️ Safety block, switching to next model...")
                    self._switch_to_next_model()
                    continue
                else:
                    # Для других ошибок тоже пробуем следующую модель
                    logger.warning(f"⚠️ Other error, switching to next model...")
                    self._switch_to_next_model()
                    continue
        
        # Если все модели исчерпаны
        logger.error("❌ All models exhausted")
        return "❌ Все модели недоступны. Попробуйте позже или обратитесь к администратору."
    
    def _build_prompt_with_reasoning(self, system_prompt: str, user_message: str, context: Optional[str] = None, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """Строит промпт с reasoning через step-by-step анализ"""
        
        reasoning_prompt = f"""
{system_prompt}

**REASONING INSTRUCTIONS:**
When responding, use this format:

🤖 **THOUGHT PROCESS:**
[Your step-by-step reasoning, analysis, and decision-making process]

💬 **FINAL RESPONSE:**
[Your actual response to the user]

**CONTEXT:**
{context or "No previous context"}

**USER PROFILE:**
{json.dumps(user_profile, indent=2) if user_profile else "No user profile"}

**USER MESSAGE:**
{user_message}

**RESPONSE FORMAT:**
Always start with 🤖 **THOUGHT PROCESS:** followed by your reasoning, then 💬 **FINAL RESPONSE:** with your actual answer.
"""
        
        return reasoning_prompt
    
    def _parse_gemini_response_with_thoughts(self, response) -> Dict[str, Any]:
        """Парсер ответа с reasoning частями через промпт"""
        try:
            result = {
                'thoughts': [],
                'final_answer': '',
                'parts': [],
                'tool_calls': []  # Добавляем tool_calls
            }
            
            # Получаем текст ответа с отладочным логированием
            logger.info(f"🔍 Parsing response with thoughts...")
            
            # Если response уже строка, используем её напрямую
            if isinstance(response, str):
                response_text = response
                logger.info(f"🔍 Response is already string: {response_text[:200]}...")
            else:
                response_text = self._parse_gemini_response(response)
                logger.info(f"🔍 Parsed response text: {response_text[:200]}...")
            
            # Парсим reasoning из промпта
            if "🤖 **THOUGHT PROCESS:**" in response_text and "💬 **FINAL RESPONSE:**" in response_text:
                logger.info(f"✅ Found reasoning markers")
                # Разделяем на thought и final response
                parts = response_text.split("💬 **FINAL RESPONSE:**")
                if len(parts) == 2:
                    thought_part = parts[0].replace("🤖 **THOUGHT PROCESS:**", "").strip()
                    final_part = parts[1].strip()
                    
                    logger.info(f"🔍 Thought part: {thought_part[:100]}...")
                    logger.info(f"🔍 Final part: {final_part[:100]}...")
                    
                    # Добавляем thought
                    if thought_part:
                        result['thoughts'].append(thought_part)
                        result['parts'].append({
                            'text': thought_part,
                            'thought': True
                        })
                    
                    # Добавляем final response
                    if final_part:
                        result['final_answer'] = final_part
                        result['parts'].append({
                            'text': final_part,
                            'thought': False
                        })
                else:
                    logger.warning(f"⚠️ Could not split reasoning parts")
                    # Если не удалось разделить, считаем весь ответ как final
                    result['final_answer'] = response_text
                    result['parts'].append({
                        'text': response_text,
                        'thought': False
                    })
            else:
                logger.info(f"✅ No reasoning markers, treating as final response")
                # Если нет маркеров reasoning, считаем весь ответ как final
                result['final_answer'] = response_text
                result['parts'].append({
                    'text': response_text,
                    'thought': False
                })
            
            # Извлекаем tool calls из всего ответа (и из thoughts, и из final)
            all_text = response_text
            tool_calls = self._extract_tool_calls_from_text(all_text)
            result['tool_calls'] = tool_calls
            
            logger.info(f"✅ Final result: thoughts={len(result['thoughts'])}, final_answer={len(result['final_answer'])}, tool_calls={len(tool_calls)}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error parsing response with thoughts: {e}")
            return {
                'thoughts': [],
                'final_answer': f"❌ Error parsing response: {str(e)}",
                'parts': [{"text": f"❌ Error parsing response: {str(e)}", "thought": False}],
                'tool_calls': []
            }
    
    def _extract_tool_calls_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает tool calls из текста ответа"""
        try:
            logger.info(f"🔧 TOOL EXTRACTION: Processing text: {text[:100]}...")
            
            # Ищем паттерны tool calls в тексте
            tool_calls = []
            
            # Паттерн: {"tool_code": "..."}
            import re
            tool_pattern = r'\{[^}]*"tool_code"[^}]*\}'
            matches = re.findall(tool_pattern, text)
            
            for match in matches:
                try:
                    # Пытаемся распарсить JSON с обработкой экранирования
                    import json
                    
                    # Заменяем экранированные символы
                    cleaned_match = match.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
                    
                    tool_call = json.loads(cleaned_match)
                    if 'tool_code' in tool_call:
                        tool_calls.append(tool_call)
                        logger.info(f"🔧 Found tool call: {tool_call['tool_code'][:50]}...")
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Failed to parse tool call JSON: {match[:100]}... Error: {e}")
                    # Пробуем альтернативный парсинг
                    try:
                        # Ищем tool_code в тексте напрямую с более гибким regex
                        tool_code_pattern = r'"tool_code":\s*"((?:[^"\\]|\\.)*)"'
                        tool_code_match = re.search(tool_code_pattern, match)
                        if tool_code_match:
                            tool_code = tool_code_match.group(1)
                            # Декодируем экранированные символы
                            tool_code = tool_code.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
                            tool_calls.append({"tool_code": tool_code})
                            logger.info(f"🔧 Found tool call via regex: {tool_code[:50]}...")
                    except Exception as regex_error:
                        logger.warning(f"⚠️ Failed regex parsing: {regex_error}")
                    continue
            
            logger.info(f"🔧 TOOL EXTRACTION: Final result: {len(tool_calls)} tool calls")
            return tool_calls
            
        except Exception as e:
            logger.error(f"❌ Error extracting tool calls: {e}")
            return []
    
    async def generate_streaming_response_with_thoughts(self, system_prompt: str, user_message: str, context: Optional[str] = None, user_profile: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Стриминг ответа с reasoning частями через промпт с fallback"""
        
        # Пробуем все модели с fallback
        for attempt in range(len(self.models)):
            try:
                # Получаем текущую модель
                model_name = self._get_current_model()
                logger.info(f"🔄 Streaming thoughts attempt {attempt + 1}: Using model {model_name}")
                
                model = genai.GenerativeModel(model_name)
                
                # Строим промпт с reasoning
                prompt = self._build_prompt_with_reasoning(system_prompt, user_message, context, user_profile)
                
                # Генерируем ответ
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        top_p=0.8,
                        top_k=40,
                        max_output_tokens=8192
                    ),
                    stream=True
                )
                
                # Парсим стриминг с thoughts
                current_text = ""
                in_thought_section = False
                
                for chunk in response:
                    if hasattr(chunk, 'candidates') and chunk.candidates:
                        candidate = chunk.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        current_text += part.text
                                        
                                        # Проверяем маркеры reasoning
                                        if "🤖 **THOUGHT PROCESS:**" in current_text and not in_thought_section:
                                            in_thought_section = True
                                            # Отправляем начало thought
                                            yield {
                                                'text': "🤖 **THOUGHT PROCESS:**",
                                                'thought': True,
                                                'type': 'thought_start'
                                            }
                                        elif "💬 **FINAL RESPONSE:**" in current_text and in_thought_section:
                                            in_thought_section = False
                                            # Отправляем начало final response
                                            yield {
                                                'text': "💬 **FINAL RESPONSE:**",
                                                'thought': False,
                                                'type': 'answer_start'
                                            }
                                        else:
                                            # Отправляем обычный chunk
                                            yield {
                                                'text': part.text,
                                                'thought': in_thought_section,
                                                'type': 'thought' if in_thought_section else 'answer'
                                            }
                            elif hasattr(candidate.content, 'text') and candidate.content.text:
                                current_text += candidate.content.text
                                yield {
                                    'text': candidate.content.text,
                                    'thought': in_thought_section,
                                    'type': 'thought' if in_thought_section else 'answer'
                                }
                
                # Если дошли сюда, значит стриминг успешен
                logger.info(f"✅ Streaming thoughts success with model {model_name}")
                return
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"⚠️ Streaming thoughts error with model {self._get_current_model()}: {error_msg}")
                
                # Проверяем тип ошибки для fallback
                if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    logger.warning(f"⚠️ Quota/rate limit exceeded, switching to next model...")
                    self._switch_to_next_model()
                    continue
                elif "safety" in error_msg.lower() or "blocked" in error_msg.lower():
                    logger.warning(f"⚠️ Safety block, switching to next model...")
                    self._switch_to_next_model()
                    continue
                else:
                    # Для других ошибок тоже пробуем следующую модель
                    logger.warning(f"⚠️ Other error, switching to next model...")
                    self._switch_to_next_model()
                    continue
        
        # Если все модели исчерпаны
        logger.error("❌ All models exhausted in streaming thoughts")
        yield {
            'text': "❌ Все модели недоступны. Попробуйте позже или обратитесь к администратору.",
            'thought': False,
            'type': 'error'
        }
    
    def _analyze_image_with_llm(self, image_path: str, prompt: str = "") -> str:
        """Анализ изображения через LLM модель с vision"""
        try:
            import base64
            
            # Читаем изображение
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Кодируем в base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Создаем модель с vision
            model_name = self._get_current_model()
            model = genai.GenerativeModel(model_name)
            
            # Создаем prompt с изображением
            if not prompt:
                prompt = "Analyze this image and describe what you see in detail."
            
            # Генерируем ответ
            response = model.generate_content([
                prompt,
                {"mime_type": "image/png", "data": image_base64}
            ])
            
            return self._parse_gemini_response(response)
            
        except Exception as e:
            logger.error(f"LLM vision analysis error: {e}")
            return f"❌ LLM vision analysis failed: {str(e)}"
    
    def _analyze_image_with_vision_api(self, image_path: str) -> str:
        """Анализ изображения через Vision API"""
        try:
            if not self.vision_api_key:
                return "❌ Vision API not configured"
            
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            import requests
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.vision_api_key}"
            
            request_data = {
                "requests": [
                    {
                        "image": {"content": base64.b64encode(content).decode("utf-8")},
                        "features": [
                            {"type": "LABEL_DETECTION", "maxResults": 10},
                            {"type": "TEXT_DETECTION"},
                            {"type": "FACE_DETECTION"},
                            {"type": "OBJECT_LOCALIZATION", "maxResults": 5}
                        ]
                    }
                ]
            }
            
            response = requests.post(url, json=request_data)
            
            if response.status_code == 200:
                result = response.json()
                analysis = []
                
                if 'labelAnnotations' in result['responses'][0]:
                    labels = [label['description'] for label in result['responses'][0]['labelAnnotations']]
                    analysis.append(f"Labels: {', '.join(labels)}")
                
                if 'textAnnotations' in result['responses'][0]:
                    text = result['responses'][0]['textAnnotations'][0]['description']
                    analysis.append(f"Text: {text}")
                
                if 'faceAnnotations' in result['responses'][0]:
                    faces = len(result['responses'][0]['faceAnnotations'])
                    analysis.append(f"Faces detected: {faces}")
                
                if 'localizedObjectAnnotations' in result['responses'][0]:
                    objects = [obj['name'] for obj in result['responses'][0]['localizedObjectAnnotations']]
                    analysis.append(f"Objects: {', '.join(objects)}")
                
                return " | ".join(analysis)
            else:
                return f"❌ Vision API error: {response.status_code}"
                
        except Exception as e:
            return f"❌ Vision API error: {str(e)}" 