"""
Система логирования
"""

import logging
import sys
from typing import Optional

class Logger:
    """Класс для управления логированием"""
    
    def __init__(self):
        """Инициализация логгера"""
        self.logger = logging.getLogger('ai_client')
        self.logger.setLevel(logging.INFO)
        
        # Проверяем, не добавлены ли уже обработчики
        if not self.logger.handlers:
            # Создаем форматтер
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Добавляем обработчик для консоли
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # Добавляем обработчик для файла
            file_handler = logging.FileHandler('app.log')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        else:
            # Если обработчики уже есть, просто используем существующий логгер
            pass
    
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