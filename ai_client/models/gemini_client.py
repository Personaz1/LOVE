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
        return {
            'current_model': self._get_current_model(),
            'model_index': self.current_model_index,
            'total_models': len(self.models),
            'models': [model['name'] for model in self.models]
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
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
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
            
            return response.text
            
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
            
            # Генерируем ответ синхронно
            import asyncio
            response = asyncio.run(self._generate_gemini_response(
                system_prompt, message, conversation_context, user_profile
            ))
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Chat error: {error_msg}")
            return f"❌ Error: {error_msg}"
    
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