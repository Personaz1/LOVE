"""
Конфигурация системы
"""

import os
from typing import Dict, Any

class Config:
    """Класс для управления конфигурацией системы"""
    
    def __init__(self):
        """Инициализация конфигурации"""
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.vision_api_key = os.getenv('GOOGLE_CLOUD_VISION_API_KEY')
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Валидация обязательных переменных
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
    
    def get_gemini_api_key(self) -> str:
        """Получить API ключ Gemini"""
        return self.gemini_api_key
    
    def get_vision_api_key(self) -> str:
        """Получить API ключ Vision"""
        return self.vision_api_key
    
    def get_project_root(self) -> str:
        """Получить корневую директорию проекта"""
        return self.project_root
    
    def is_vision_configured(self) -> bool:
        """Проверить настройку Vision API"""
        return bool(self.vision_api_key) 