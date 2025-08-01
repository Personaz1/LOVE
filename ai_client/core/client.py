"""
Основной класс AIClient - точка входа в систему
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
from ..utils.config import Config
from ..utils.logger import Logger
from ..utils.error_handler import ErrorHandler

# Загружаем переменные окружения
load_dotenv()

class AIClient:
    """
    Основной класс AI клиента - объединяет все модули
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
        
        # Основные атрибуты
        self.current_model_index = 0
        self.models = self.gemini_client.get_models()
        
        self.logger.info("🚀 AIClient initialized with modular architecture")
    
    # Основные методы - делегируем в соответствующие модули
    
    def _get_current_model(self):
        """Получить текущую модель"""
        return self.gemini_client.get_current_model()
    
    def _switch_to_next_model(self):
        """Переключиться на следующую модель"""
        return self.gemini_client.switch_to_next_model()
    
    def switch_to_model(self, model_name: str) -> bool:
        """Переключиться на конкретную модель"""
        return self.gemini_client.switch_to_model(model_name)
    
    def _handle_quota_error(self, error_msg: str):
        """Обработка ошибок квоты"""
        return self.gemini_client.handle_quota_error(error_msg)
    
    def get_model_status(self) -> Dict[str, Any]:
        """Получить статус моделей"""
        return self.gemini_client.get_model_status()
    
    def get_current_model(self) -> str:
        """Получить имя текущей модели"""
        return self.gemini_client.get_current_model()
    
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
    
    async def _generate_gemini_streaming_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ):
        """Внутренний метод для streaming ответов"""
        return self.gemini_client._generate_gemini_streaming_response(
            system_prompt, user_message, context, user_profile
        )
    
    async def _generate_gemini_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Генерация обычного ответа"""
        return await self.gemini_client._generate_gemini_response(
            system_prompt, user_message, context, user_profile
        )
    
    def chat(
        self, 
        message: str, 
        user_profile: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Основной метод чата"""
        return self.gemini_client.chat(message, user_profile, conversation_context, system_prompt)
    
    # Делегируем все остальные методы в соответствующие модули
    
    # File tools
    def read_file(self, path: str) -> str:
        return self.file_tools.read_file(path)
    
    def write_file(self, path: str, content: str) -> bool:
        return self.file_tools.write_file(path, content)
    
    def create_file(self, path: str, content: str = "") -> bool:
        return self.file_tools.create_file(path, content)
    
    def edit_file(self, path: str, content: str) -> bool:
        return self.file_tools.edit_file(path, content)
    
    def list_files(self, directory: str = "") -> str:
        return self.file_tools.list_files(directory)
    
    def search_files(self, query: str) -> str:
        return self.file_tools.search_files(query)
    
    def get_file_info(self, path: str) -> str:
        return self.file_tools.get_file_info(path)
    
    def delete_file(self, path: str) -> bool:
        return self.file_tools.delete_file(path)
    
    def create_directory(self, path: str) -> bool:
        return self.file_tools.create_directory(path)
    
    # Memory tools
    def update_current_feeling(self, username: str, feeling: str, context: str = "") -> bool:
        return self.memory_tools.update_current_feeling(username, feeling, context)
    
    def update_relationship_status(self, username: str, status: str) -> bool:
        return self.memory_tools.update_relationship_status(username, status)
    
    def update_user_profile(self, username: str, new_profile_text: str) -> bool:
        return self.memory_tools.update_user_profile(username, new_profile_text)
    
    def add_relationship_insight(self, username: str, insight: str) -> bool:
        return self.memory_tools.add_relationship_insight(username, insight)
    
    def add_model_note(self, note_text: str, category: str = "general") -> bool:
        return self.memory_tools.add_model_note(note_text, category)
    
    def add_user_observation(self, username: str, observation: str) -> bool:
        return self.memory_tools.add_user_observation(username, observation)
    
    def add_personal_thought(self, thought: str) -> bool:
        return self.memory_tools.add_personal_thought(thought)
    
    def add_system_insight(self, insight: str) -> bool:
        return self.memory_tools.add_system_insight(insight)
    
    def get_model_notes(self, limit: int = 20) -> str:
        return self.memory_tools.get_model_notes(limit)
    
    def read_user_profile(self, username: str) -> str:
        return self.memory_tools.read_user_profile(username)
    
    def read_emotional_history(self, username: str) -> str:
        return self.memory_tools.read_emotional_history(username)
    
    def write_insight_to_file(self, username: str, insight: str) -> bool:
        return self.memory_tools.write_insight_to_file(username, insight)
    
    def search_user_data(self, username: str, query: str) -> str:
        return self.memory_tools.search_user_data(username, query)
    
    # System tools
    def get_system_logs(self, lines: int = 50) -> str:
        return self.system_tools.get_system_logs(lines)
    
    def get_error_summary(self) -> str:
        return self.system_tools.get_error_summary()
    
    def diagnose_system_health(self) -> str:
        """Диагностика здоровья системы"""
        self.logger.info("🔧 SYSTEM TOOLS: Executing diagnose_system_health()")
        result = self.system_tools.diagnose_system_health()
        self.logger.info(f"✅ SYSTEM TOOLS: diagnose_system_health completed - {len(result.split())} words")
        return result
    
    def analyze_image(self, image_path: str, user_context: str = "") -> str:
        return self.system_tools.analyze_image(image_path, user_context)
    
    def get_project_structure(self) -> str:
        return self.system_tools.get_project_structure()
    
    def find_images(self) -> str:
        return self.system_tools.find_images()
    
    def _generate_login_greeting(self, user_profile: Optional[Dict[str, Any]] = None) -> str:
        return self.system_tools._generate_login_greeting(user_profile)
    
    # ReAct architecture
    def plan_step(self, goal: str) -> str:
        return self.system_tools.plan_step(goal)
    
    def act_step(self, tool_name: str, tool_input: str) -> str:
        return self.system_tools.act_step(tool_name, tool_input)
    
    def reflect(self, history: List[str]) -> str:
        return self.system_tools.reflect(history)
    
    def react_cycle(self, goal: str, max_steps: int = 20) -> str:
        return self.system_tools.react_cycle(goal, max_steps)
    
    # Web tools
    def web_search(self, query: str) -> str:
        return self.system_tools.web_search(query)
    
    def fetch_url(self, url: str) -> str:
        return self.system_tools.fetch_url(url)
    
    def call_api(self, endpoint: str, payload: str = "") -> str:
        return self.system_tools.call_api(endpoint, payload)
    
    def integrate_api(self, name: str, base_url: str, auth: str = "", schema: str = "") -> bool:
        return self.system_tools.integrate_api(name, base_url, auth, schema)
    
    def call_custom_api(self, name: str, endpoint: str, data: str = "") -> str:
        return self.system_tools.call_custom_api(name, endpoint, data)
    
    def get_weather(self, location: str) -> str:
        return self.system_tools.get_weather(location)
    
    def translate_text(self, text: str, target_language: str = "en") -> str:
        return self.system_tools.translate_text(text, target_language)
    
    # Vector memory
    def store_embedding_memory(self, text: str, label: str = "general") -> bool:
        return self.memory_tools.store_embedding_memory(text, label)
    
    def search_embedding_memory(self, query: str, top_k: int = 5) -> str:
        return self.memory_tools.search_embedding_memory(query, top_k)
    
    def summarize_conversation(self, conversation_history: List[str]) -> str:
        return self.memory_tools.summarize_conversation(conversation_history)
    
    def get_memory_stats(self) -> str:
        return self.memory_tools.get_memory_stats()
    
    def clear_vector_memory(self) -> bool:
        return self.memory_tools.clear_vector_memory()
    
    # Event management
    def create_event(self, title: str, description: str, date: str, time: str = "", priority: str = "medium") -> bool:
        return self.system_tools.create_event(title, description, date, time, priority)
    
    def get_upcoming_events(self, days: int = 7) -> str:
        return self.system_tools.get_upcoming_events(days)
    
    def reschedule_event(self, event_id: int, new_date: str, new_time: str = "") -> bool:
        return self.system_tools.reschedule_event(event_id, new_date, new_time)
    
    def complete_event(self, event_id: int) -> bool:
        return self.system_tools.complete_event(event_id)
    
    def get_event_statistics(self) -> str:
        return self.system_tools.get_event_statistics()
    
    def create_task_list(self, title: str, tasks: str) -> bool:
        return self.system_tools.create_task_list(title, tasks)
    
    def list_tasks(self, context: str = "") -> str:
        return self.system_tools.list_tasks(context)
    
    # Terminal and system
    def run_terminal_command(self, command: str) -> str:
        return self.system_tools.run_terminal_command(command)
    
    def get_system_info(self) -> str:
        return self.system_tools.get_system_info()
    
    def diagnose_network(self) -> str:
        return self.system_tools.diagnose_network()
    
    # Sandbox operations
    def create_sandbox_file(self, path: str, content: str = "") -> bool:
        return self.file_tools.create_sandbox_file(path, content)
    
    def create_downloadable_file(self, filename: str, content: str, file_type: str = "txt") -> str:
        return self.file_tools.create_downloadable_file(filename, content, file_type)
    
    def edit_sandbox_file(self, path: str, content: str) -> bool:
        return self.file_tools.edit_sandbox_file(path, content)
    
    def read_sandbox_file(self, path: str) -> str:
        return self.file_tools.read_sandbox_file(path)
    
    def list_sandbox_files(self, directory: str = "") -> str:
        return self.file_tools.list_sandbox_files(directory)
    
    def delete_sandbox_file(self, path: str) -> bool:
        return self.file_tools.delete_sandbox_file(path)
    
    # Tool execution - основной метод для выполнения инструментов
    def _extract_tool_calls(self, text: str) -> List[str]:
        """Извлечение вызовов инструментов из текста"""
        return self.system_tools._extract_tool_calls(text)
    
    def _extract_nested_calls(self, text: str) -> List[str]:
        """Извлечение вложенных вызовов"""
        return self.system_tools._extract_nested_calls(text)
    
    def _parse_arguments(self, args_str: str, expected_params: List[str]) -> Dict[str, Any]:
        """Универсальный парсер аргументов"""
        return self.system_tools._parse_arguments(args_str, expected_params)
    
    def _execute_tool_call(self, tool_call: str) -> str:
        """Выполнение вызова инструмента"""
        return self.system_tools._execute_tool_call(tool_call)
    
    def _get_multi_user_context(self) -> str:
        """Получение контекста нескольких пользователей"""
        return self.memory_tools._get_multi_user_context() 