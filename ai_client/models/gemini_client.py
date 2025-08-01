"""
Gemini API клиент
"""

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
    """Класс для работы с Gemini API"""
    
    def __init__(self):
        """Инициализация Gemini клиента"""
        self.config = Config()
        self.error_handler = ErrorHandler()
        
        # Инициализируем Gemini
        api_key = self.config.get_gemini_api_key()
        genai.configure(api_key=api_key)
        
        # Инициализируем Vision API
        self.vision_client = None
        try:
            vision_api_key = self.config.get_vision_api_key()
            if vision_api_key:
                self.vision_api_key = vision_api_key
                logger.info("✅ Google Cloud Vision API key configured")
            else:
                logger.warning("⚠️ No Google Cloud Vision API key provided")
        except Exception as e:
            logger.warning(f"⚠️ Google Cloud Vision API not available: {e}")
        
        # Определяем доступные модели
        self.models = [
            {
                'name': 'gemini-2.5-pro',
                'quota': 100,
                'model': None,
                'vision': True
            },
            {
                'name': 'gemini-1.5-pro',
                'quota': 150,
                'model': None,
                'vision': True
            },
            {
                'name': 'gemini-2.5-flash',
                'quota': 250,
                'model': None,
                'vision': True
            },
            {
                'name': 'gemini-1.5-flash',
                'quota': 500,
                'model': None,
                'vision': True
            },
            {
                'name': 'gemini-2.0-flash', 
                'quota': 200,
                'model': None,
                'vision': True
            },
            {
                'name': 'gemini-2.0-flash-lite',
                'quota': 1000,
                'model': None,
                'vision': False
            },
            {
                'name': 'gemini-2.5-flash-lite',
                'quota': 1000,
                'model': None,
                'vision': False
            }
        ]
        
        self.current_model_index = 0
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Получить список моделей"""
        return self.models
    
    def _get_current_model(self):
        """Получить текущую модель"""
        return self.models[self.current_model_index]['name']
    
    def _get_current_model_index(self):
        """Получить индекс текущей модели"""
        return self.current_model_index
    
    def _switch_to_next_model(self):
        """Переключиться на следующую модель"""
        self.current_model_index = (self.current_model_index + 1) % len(self.models)
        model_name = self.models[self.current_model_index]['name']
        logger.info(f"🚀 Using model: {model_name}")
        return model_name
    
    def switch_to_model(self, model_name: str) -> bool:
        """Переключиться на конкретную модель"""
        for i, model in enumerate(self.models):
            if model['name'] == model_name:
                self.current_model_index = i
                logger.info(f"🚀 Switched to model: {model_name}")
                return True
        logger.error(f"❌ Model {model_name} not found")
        return False
    
    def _handle_quota_error(self, error_msg: str):
        """Обработка ошибок квоты"""
        if self.error_handler.is_quota_error(error_msg):
            logger.warning(f"⚠️ Quota exceeded for {self._get_current_model()}, switching model")
            return self._switch_to_next_model()
        return None
    
    def get_model_status(self) -> Dict[str, Any]:
        """Получить статус моделей"""
        current_model = self._get_current_model()
        current_quota = "undefined"  # Будем получать из модели
        
        # Формируем полную информацию о моделях
        available_models = []
        model_errors = 0
        
        for i, model in enumerate(self.models):
            model_info = {
                'name': model['name'],
                'quota': model.get('quota', 'undefined'),
                'has_error': False  # Будем проверять при необходимости
            }
            available_models.append(model_info)
        
        return {
            'current_model': current_model,
            'current_quota': current_quota,
            'model_index': self.current_model_index,
            'total_models': len(self.models),
            'available_models': available_models,
            'model_errors': model_errors
        }
    
    def get_current_model(self) -> str:
        """Получить имя текущей модели"""
        return self._get_current_model()
    
    def _analyze_image_with_vision_api(self, image_path: str) -> str:
        """Анализ изображения через Vision API"""
        try:
            if not self.config.is_vision_configured():
                return "❌ Vision API not configured"
            
            # Читаем изображение
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            # Создаем запрос к Vision API
            import requests
            
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.vision_api_key}"
            
            request_data = {
                "requests": [
                    {
                        "image": {
                            "content": content.decode('latin1')
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
                                "type": "OBJECT_LOCALIZATION",
                                "maxResults": 5
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(url, json=request_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Извлекаем результаты
                analysis = []
                
                # Labels
                if 'labelAnnotations' in result['responses'][0]:
                    labels = [label['description'] for label in result['responses'][0]['labelAnnotations']]
                    analysis.append(f"Labels: {', '.join(labels)}")
                
                # Text
                if 'textAnnotations' in result['responses'][0]:
                    text = result['responses'][0]['textAnnotations'][0]['description']
                    analysis.append(f"Text: {text}")
                
                # Faces
                if 'faceAnnotations' in result['responses'][0]:
                    faces = len(result['responses'][0]['faceAnnotations'])
                    analysis.append(f"Faces detected: {faces}")
                
                # Objects
                if 'localizedObjectAnnotations' in result['responses'][0]:
                    objects = [obj['name'] for obj in result['responses'][0]['localizedObjectAnnotations']]
                    analysis.append(f"Objects: {', '.join(objects)}")
                
                return " | ".join(analysis)
            else:
                return f"❌ Vision API error: {response.status_code}"
                
        except Exception as e:
            return f"❌ Vision API error: {str(e)}"
    
    async def generate_streaming_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Генерация streaming ответа"""
        async for chunk in self._generate_gemini_streaming_response(
            system_prompt, user_message, context, user_profile
        ):
            yield chunk
    
    async def _generate_gemini_streaming_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ):
        """Внутренний метод для streaming ответов"""
        try:
            # Получаем текущую модель
            model_name = self._get_current_model()
            model = genai.GenerativeModel(model_name)
            
            # Строим промпт
            full_prompt = self._build_prompt(system_prompt, user_message, context, user_profile)
            
            # Генерируем ответ
            response = model.generate_content(full_prompt, stream=True)
            
            # Проверяем finish_reason перед обработкой
            if hasattr(response, 'finish_reason'):
                finish_reason = response.finish_reason
                if finish_reason == 1:  # SAFETY
                    yield "❌ Ответ заблокирован системой безопасности"
                    return
                elif finish_reason == 2:  # RECITATION
                    yield "❌ Ответ заблокирован из-за рецитации"
                    return
                elif finish_reason == 3:  # OTHER
                    yield "❌ Ответ заблокирован по другим причинам"
                    return
            
            # Обрабатываем streaming ответ
            for chunk in response:
                # Проверяем разные способы получения текста
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
                elif hasattr(chunk, 'parts') and chunk.parts:
                    # Обрабатываем сложные ответы через parts
                    for part in chunk.parts:
                        if hasattr(part, 'text') and part.text:
                            yield part.text
                elif hasattr(chunk, 'candidates') and chunk.candidates:
                    # Обрабатываем через candidates
                    for candidate in chunk.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        yield part.text
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Gemini streaming error: {error_msg}")
            
            # Пробуем переключить модель при ошибке
            if self._handle_quota_error(error_msg):
                # Рекурсивно пробуем с новой моделью
                async for chunk in self._generate_gemini_streaming_response(
                    system_prompt, user_message, context, user_profile
                ):
                    yield chunk
            else:
                yield f"❌ Error: {error_msg}"
    
    async def _generate_gemini_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Генерация обычного ответа"""
        try:
            # Получаем текущую модель
            model_name = self._get_current_model()
            model = genai.GenerativeModel(model_name)
            
            # Строим промпт
            full_prompt = self._build_prompt(system_prompt, user_message, context, user_profile)
            
            # Генерируем ответ
            response = model.generate_content(full_prompt)
            
            # Проверяем finish_reason
            if hasattr(response, 'finish_reason'):
                finish_reason = response.finish_reason
                if finish_reason == 1:  # SAFETY
                    return "❌ Ответ заблокирован системой безопасности"
                elif finish_reason == 2:  # RECITATION
                    return "❌ Ответ заблокирован из-за рецитации"
                elif finish_reason == 3:  # OTHER
                    return "❌ Ответ заблокирован по другим причинам"
            
            # Проверяем наличие текста
            if hasattr(response, 'text') and response.text:
                return response.text
            elif hasattr(response, 'parts') and response.parts:
                # Обрабатываем сложные ответы через parts
                text_parts = []
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    return "".join(text_parts)
            
            # Если нет текста, пробуем получить через candidates
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return "".join(text_parts)
            
            return "❌ Не удалось сгенерировать ответ"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Gemini non-streaming error: {error_msg}")
            
            # Пробуем переключить модель при ошибке
            if self._handle_quota_error(error_msg):
                # Рекурсивно пробуем с новой моделью
                return await self._generate_gemini_response(
                    system_prompt, user_message, context, user_profile
                )
            else:
                return f"❌ Error: {error_msg}"
    
    def chat(
        self, 
        message: str, 
        user_profile: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Основной метод чата"""
        try:
            # Используем стандартный промпт если не указан
            if not system_prompt:
                system_prompt = "You are a helpful AI assistant."
            
            # Генерируем ответ синхронно через sync версию
            response = self._generate_gemini_response_sync(
                system_prompt, message, conversation_context, user_profile
            )
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Chat error: {error_msg}")
            return f"❌ Error: {error_msg}"

    def _generate_gemini_response_sync(
        self, 
        system_prompt: str, 
        user_message: str, 
        conversation_context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Синхронная версия генерации ответа"""
        try:
            # Формируем промпт
            full_prompt = self._build_prompt_sync(system_prompt, user_message, conversation_context, user_profile)
            
            # Получаем модель
            model_name = self._get_current_model()
            model = genai.GenerativeModel(model_name)
            
            # Устанавливаем таймаут и ограничения
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            # Генерируем ответ
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # Проверяем finish_reason
            if hasattr(response, 'finish_reason'):
                finish_reason = response.finish_reason
                if finish_reason == 1:  # SAFETY
                    return "❌ Ответ заблокирован системой безопасности"
                elif finish_reason == 2:  # RECITATION
                    return "❌ Ответ заблокирован из-за рецитации"
                elif finish_reason == 3:  # OTHER
                    return "❌ Ответ заблокирован по другим причинам"
            
            # Проверяем наличие текста - пробуем разные способы
            text_content = ""
            
            # Способ 1: прямой доступ к text
            if hasattr(response, 'text') and response.text:
                text_content = response.text
            # Способ 2: через parts
            elif hasattr(response, 'parts') and response.parts:
                text_parts = []
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    text_content = "".join(text_parts)
            # Способ 3: через candidates
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            text_content = "".join(text_parts)
                    elif hasattr(candidate.content, 'text') and candidate.content.text:
                        text_content = candidate.content.text
            
            if text_content:
                return text_content
            
            return "❌ Не удалось сгенерировать ответ"
    
    def chat(
        self, 
        message: str, 
        user_profile: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Основной метод чата"""
        try:
            # Используем стандартный промпт если не указан
            if not system_prompt:
                system_prompt = "You are a helpful AI assistant."
            
            # Генерируем ответ синхронно через sync версию
            response = self._generate_gemini_response_sync(
                system_prompt, message, conversation_context, user_profile
            )
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Chat error: {error_msg}")
            return f"❌ Error: {error_msg}"

    def _generate_gemini_response_sync(
        self, 
        system_prompt: str, 
        user_message: str, 
        conversation_context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Синхронная версия генерации ответа"""
        try:
            # Формируем промпт
            full_prompt = self._build_prompt_sync(system_prompt, user_message, conversation_context, user_profile)
            
            # Получаем модель
            model_name = self._get_current_model()
            model = genai.GenerativeModel(model_name)
            
            # Устанавливаем таймаут и ограничения
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            # Генерируем ответ
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # Проверяем finish_reason
            if hasattr(response, 'finish_reason'):
                finish_reason = response.finish_reason
                if finish_reason == 1:  # SAFETY
                    return "❌ Ответ заблокирован системой безопасности"
                elif finish_reason == 2:  # RECITATION
                    return "❌ Ответ заблокирован из-за рецитации"
                elif finish_reason == 3:  # OTHER
                    return "❌ Ответ заблокирован по другим причинам"
            
            # Проверяем наличие текста
            if hasattr(response, 'text') and response.text:
                return response.text
            elif hasattr(response, 'parts') and response.parts:
                # Обрабатываем сложные ответы через parts
                text_parts = []
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    return "".join(text_parts)
            
            # Если нет текста, пробуем получить через candidates
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return "".join(text_parts)
            
            return "❌ Не удалось сгенерировать ответ"
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Sync generation error: {error_msg}")
            
            # Если таймаут или квота - пробуем другую модель
            if "504" in error_msg or "Deadline" in error_msg or "429" in error_msg or "quota" in error_msg.lower():
                logger.warning("⚠️ API ошибка (таймаут/квота), пробуем другую модель...")
                return self._try_fallback_model_sync(system_prompt, user_message, conversation_context, user_profile)
            
            return f"❌ Error: {error_msg}"

    def _build_prompt_sync(
        self, 
        system_prompt: str, 
        user_message: str, 
        conversation_context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Синхронная версия построения промпта"""
        prompt_parts = [system_prompt]
        
        # Добавляем контекст пользователя
        if user_profile:
            prompt_parts.append(f"\nUser Profile: {json.dumps(user_profile, ensure_ascii=False)}")
        
        # Добавляем контекст разговора
        if conversation_context:
            prompt_parts.append(f"\nConversation Context: {conversation_context}")
        
        # Добавляем сообщение пользователя
        prompt_parts.append(f"\nUser: {user_message}")
        prompt_parts.append("\nAssistant:")
        
        return "\n".join(prompt_parts)

    def _try_fallback_model_sync(
        self, 
        system_prompt: str, 
        user_message: str, 
        conversation_context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Пробуем другую модель при ошибках API"""
        current_index = self._get_current_model_index()
        
        # Пробуем все доступные модели, начиная со следующей
        for attempt in range(len(self.models) - 1):  # -1 чтобы не пробовать ту же модель
            try:
                # Получаем следующую модель
                next_index = (current_index + attempt + 1) % len(self.models)
                fallback_model_dict = self.models[next_index]
                fallback_model_name = fallback_model_dict['name']
                
                logger.info(f"🔄 Попытка {attempt + 1}: переключаемся на модель: {fallback_model_name}")
                
                # Формируем промпт
                full_prompt = self._build_prompt_sync(system_prompt, user_message, conversation_context, user_profile)
                
                # Создаем модель с fallback
                model = genai.GenerativeModel(fallback_model_name)
                
                # Генерируем с более строгими ограничениями
                generation_config = {
                    "temperature": 0.5,
                    "top_p": 0.7,
                    "top_k": 30,
                    "max_output_tokens": 1024,
                }
                
                response = model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                
                # Проверяем finish_reason и text
                if hasattr(response, 'finish_reason') and response.finish_reason == 1:  # SAFETY
                    logger.warning(f"⚠️ Модель {fallback_model_name} заблокирована системой безопасности")
                    continue
                elif response.text:
                    logger.info(f"✅ Успешно использована модель: {fallback_model_name}")
                    return response.text
                    
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"⚠️ Модель {fallback_model_name} недоступна: {error_msg}")
                continue
        
        # Если все модели недоступны
        logger.error("❌ Все модели недоступны")
        return "❌ Все модели недоступны. Попробуйте позже."
    
    def _build_prompt(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Построение полного промпта"""
        prompt_parts = []
        
        # Системный промпт
        prompt_parts.append(system_prompt)
        
        # Контекст пользователя
        if user_profile:
            profile_text = f"User profile: {json.dumps(user_profile, indent=2)}"
            prompt_parts.append(profile_text)
        
        # Дополнительный контекст
        if context:
            prompt_parts.append(f"Context: {context}")
        
        # Сообщение пользователя
        prompt_parts.append(f"User: {user_message}")
        
        return "\n\n".join(prompt_parts) 