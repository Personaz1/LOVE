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
        
        # Определяем доступные модели
        self.models = [
            {'name': 'gemini-2.5-pro', 'quota': 100},
            {'name': 'gemini-1.5-pro', 'quota': 150},
            {'name': 'gemini-2.5-flash', 'quota': 250},
            {'name': 'gemini-1.5-flash', 'quota': 500},
            {'name': 'gemini-2.0-flash', 'quota': 200},
            {'name': 'gemini-2.0-flash-lite', 'quota': 1000},
            {'name': 'gemini-2.5-flash-lite', 'quota': 1000}
        ]
        
        self.current_model_index = 0
    
    def _parse_gemini_response(self, response) -> str:
        """УНИВЕРСАЛЬНЫЙ ПАРСЕР - обрабатывает любой формат ответа Gemini"""
        try:
            # Проверяем finish_reason
            if hasattr(response, 'finish_reason'):
                finish_reason = response.finish_reason
                if finish_reason == 1:  # SAFETY
                    return "❌ Ответ заблокирован системой безопасности"
                elif finish_reason == 2:  # RECITATION
                    return "❌ Ответ заблокирован из-за рецитации"
                elif finish_reason == 3:  # OTHER
                    return "❌ Ответ заблокирован по другим причинам"
            
            # Способ 1: прямой доступ к text
            if hasattr(response, 'text') and response.text:
                return response.text
            
            # Способ 2: через parts
            if hasattr(response, 'parts') and response.parts:
                text_parts = []
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    return "".join(text_parts)
            
            # Способ 3: через candidates
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
                    elif hasattr(candidate.content, 'text') and candidate.content.text:
                        return candidate.content.text
            
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
        """Генерируем стриминг ответ"""
        try:
            model_name = self._get_current_model()
            model = genai.GenerativeModel(model_name)
            
            full_prompt = self._build_prompt(system_prompt, user_message, context, user_profile)
            response = model.generate_content(full_prompt, stream=True)
            
            for chunk in response:
                # Используем универсальный парсер для каждого chunk
                chunk_text = self._parse_gemini_response(chunk)
                if chunk_text and not chunk_text.startswith("❌"):
                    yield chunk_text
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Gemini streaming error: {error_msg}")
            
            # Простой fallback - переключаем модель и пробуем еще раз
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning("⚠️ Quota exceeded, switching model...")
                self._switch_to_next_model()
                # Рекурсивно пробуем с новой моделью
                async for chunk in self.generate_streaming_response(system_prompt, user_message, context, user_profile):
                    yield chunk
            else:
                yield f"❌ Error: {error_msg}"
    
    def chat(self, message: str, user_profile: Optional[Dict[str, Any]] = None, conversation_context: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Основной метод чата - УПРОЩЕННАЯ ВЕРСИЯ"""
        try:
            if not system_prompt:
                system_prompt = "You are a helpful AI assistant."
            
            model_name = self._get_current_model()
            model = genai.GenerativeModel(model_name)
            
            full_prompt = self._build_prompt(system_prompt, message, conversation_context, user_profile)
            response = model.generate_content(full_prompt)
            
            return self._parse_gemini_response(response)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Chat error: {error_msg}")
            
            # Простой fallback
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning("⚠️ Quota exceeded, switching model...")
                self._switch_to_next_model()
                return self.chat(message, user_profile, conversation_context, system_prompt)
            else:
                return f"❌ Error: {error_msg}"
    
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