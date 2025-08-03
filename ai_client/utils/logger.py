"""
Система логирования - УПРОЩЕННАЯ ВЕРСИЯ
"""

import logging
import sys
from typing import Optional

class Logger:
    """Класс для управления логированием - УПРОЩЕННАЯ ВЕРСИЯ"""
    
    def __init__(self):
        """Инициализация логгера - без дублирования handlers"""
        self.logger = logging.getLogger('ai_client')
        # НЕ добавляем handlers - они уже настроены в web_app.py
        
    def info(self, message: str):
        """Логирование информационного сообщения"""
        self.logger.info(message)
    
    def error(self, message: str):
        """Логирование ошибки"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """Логирование предупреждения"""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Логирование отладочной информации"""
        self.logger.debug(message)
    
    def get_logger(self) -> logging.Logger:
        """Получить объект логгера"""
        return self.logger

# Экспортируем Logger для импорта
__all__ = ['Logger'] 