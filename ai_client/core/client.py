"""
Основной класс AIClient - УПРОЩЕННАЯ АРХИТЕКТУРА
"""

import os
import time
import logging
import re
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime
import json
from dotenv import load_dotenv
import base64

# Импорты из модулей
from ..models.gemini_client import GeminiClient
from ..tools.file_tools import FileTools
from ..tools.memory_tools import MemoryTools
from ..tools.system_tools import SystemTools
from ..tools.tips_generator import TipsGenerator
from ..utils.config import Config
from ..utils.logger import Logger
from ..utils.error_handler import ErrorHandler

# Загружаем переменные окружения
load_dotenv()

class AIClient:
    """
    Упрощенный AI клиент - объединяет все модули
    """
    
    def __init__(self):
        """Инициализация AI клиента"""
        # Инициализируем утилиты
        self.config = Config()
        self.logger = Logger()
        self.error_handler = ErrorHandler()
        
        # Инициализируем модули
        self.gemini_client = GeminiClient()
        self.file_tools = FileTools()
        self.memory_tools = MemoryTools()
        self.system_tools = SystemTools()
        self.tips_generator = TipsGenerator()
        
        self.logger.info("🚀 AIClient initialized with simplified architecture")
    
    # Основные методы - делегируем в соответствующие модули
    
    def get_current_model(self) -> str:
        """Получить имя текущей модели"""
        return self.gemini_client.get_current_model()
    
    def switch_to_model(self, model_name: str) -> bool:
        """Переключиться на конкретную модель"""
        return self.gemini_client.switch_to_model(model_name)
    
    def get_model_status(self) -> Dict[str, Any]:
        """Получить статус моделей"""
        return self.gemini_client.get_model_status()
    
    # Методы генерации ответов
    async def generate_streaming_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Генерация streaming ответа"""
        async for chunk in self.gemini_client.generate_streaming_response(
            system_prompt, user_message, context, user_profile
        ):
            yield chunk
    
    def chat(
        self, 
        message: str, 
        user_profile: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Основной метод чата"""
        return self.gemini_client.chat(message, user_profile, conversation_context, system_prompt)
    
    # Прямой доступ к модулям для инструментов
    @property
    def files(self):
        """Доступ к файловым инструментам"""
        return self.file_tools
    
    @property
    def memory(self):
        """Доступ к инструментам памяти"""
        return self.memory_tools
    
    @property
    def system(self):
        """Доступ к системным инструментам"""
        return self.system_tools
    
    @property
    def tips(self):
        """Доступ к генератору советов"""
        return self.tips_generator
    
    # Утилитарные методы
    def _extract_tool_calls(self, text: str) -> List[str]:
        """Извлечение вызовов инструментов из текста"""
        return self.system_tools._extract_tool_calls(text)
    
    def _extract_nested_calls(self, text: str) -> List[str]:
        """Извлечение вложенных вызовов"""
        return self.system_tools._extract_nested_calls(text)
    
    def _parse_arguments(self, args_str: str, expected_params: List[str]) -> Dict[str, Any]:
        """Парсинг аргументов"""
        return self.system_tools._parse_arguments(args_str, expected_params)
    
    def _execute_tool_call(self, tool_call: str) -> str:
        """Выполнение вызова инструмента"""
        logger.info(f"🔧 AICLIENT: Executing tool call: {tool_call}")
        result = self.system_tools._execute_tool_call(tool_call)
        logger.info(f"✅ AICLIENT: Tool call result: {result[:200]}..." if len(result) > 200 else result)
        return result
    
    def _get_multi_user_context(self) -> str:
        """Получение контекста для нескольких пользователей"""
        return self.memory_tools._get_multi_user_context() 