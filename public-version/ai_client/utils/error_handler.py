"""
Обработка ошибок
"""

import traceback
from typing import Optional, Dict, Any

class ErrorHandler:
    """Класс для обработки ошибок"""
    
    def __init__(self):
        """Инициализация обработчика ошибок"""
        pass
    
    def handle_api_error(self, error: Exception, context: str = "") -> str:
        """Обработка ошибок API"""
        error_msg = f"❌ API Error in {context}: {str(error)}"
        return error_msg
    
    def handle_file_error(self, error: Exception, file_path: str = "") -> str:
        """Обработка ошибок файловых операций"""
        error_msg = f"❌ File Error for {file_path}: {str(error)}"
        return error_msg
    
    def handle_validation_error(self, error: Exception, field: str = "") -> str:
        """Обработка ошибок валидации"""
        error_msg = f"❌ Validation Error for {field}: {str(error)}"
        return error_msg
    
    def get_error_traceback(self, error: Exception) -> str:
        """Получить полный traceback ошибки"""
        return traceback.format_exc()
    
    def is_quota_error(self, error_msg: str) -> bool:
        """Проверить является ли ошибка ошибкой квоты"""
        quota_keywords = ['quota', 'rate limit', '429', 'too many requests']
        return any(keyword in error_msg.lower() for keyword in quota_keywords)
    
    def is_network_error(self, error_msg: str) -> bool:
        """Проверить является ли ошибка сетевой"""
        network_keywords = ['connection', 'timeout', 'network', 'dns']
        return any(keyword in error_msg.lower() for keyword in network_keywords) 