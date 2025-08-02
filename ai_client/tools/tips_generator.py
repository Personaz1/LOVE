"""
Модуль для генерации динамических советов
"""

import logging
from typing import List, Dict, Any, Optional
from ..models.gemini_client import GeminiClient
from prompts.tips_prompt import build_tips_prompt

logger = logging.getLogger(__name__)

class TipsGenerator:
    """Генератор динамических советов на основе контекста"""
    
    def __init__(self):
        """Инициализация генератора советов"""
        self.gemini_client = GeminiClient()
        logger.info("🚀 TipsGenerator initialized")
    
    def generate_tips(self, context: str = "", user_profile: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Генерирует 3 динамических совета на основе контекста
        
        Args:
            context: Контекст ситуации
            user_profile: Профиль пользователя
            
        Returns:
            List[str]: Список из 3 советов
        """
        try:
            # Используем отдельный промпт для генерации советов
            prompt = build_tips_prompt(context, user_profile)
            
            # Генерируем советы через LLM
            response = self.gemini_client.chat(
                message=prompt,
                user_profile=user_profile,
                system_prompt="You are a relationship and personal development expert. Generate exactly 3 practical, actionable tips based on the context provided. Keep each tip concise and specific."
            )
            
            # Парсим ответ и извлекаем советы
            tips = self._parse_tips_response(response)
            
            logger.info(f"✅ Generated {len(tips)} dynamic tips")
            return tips
            
        except Exception as e:
            logger.error(f"❌ Error generating tips: {e}")
            # Fallback на базовые советы - только в крайнем случае
            return self._get_fallback_tips()
    
    def _parse_tips_response(self, response: str) -> List[str]:
        """Парсит ответ LLM и извлекает советы"""
        try:
            # Ищем нумерованный список
            lines = response.strip().split('\n')
            tips = []
            
            for line in lines:
                line = line.strip()
                # Ищем строки с цифрами в начале (1., 2., 3.)
                if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    # Убираем номер/маркер и лишние пробелы
                    tip = line.lstrip('0123456789.•-* ').strip()
                    if tip:
                        tips.append(tip)
            
            # Если нашли 3+ совета, берем первые 3
            if len(tips) >= 3:
                return tips[:3]
            # Если нашли меньше 3, дополняем базовыми
            elif len(tips) > 0:
                fallback_tips = self._get_fallback_tips()
                return tips + fallback_tips[:3-len(tips)]
            else:
                # Если ничего не нашли, возвращаем базовые
                return self._get_fallback_tips()
                
        except Exception as e:
            logger.error(f"❌ Error parsing tips response: {e}")
            return self._get_fallback_tips()

    def _get_fallback_tips(self) -> List[str]:
        """Возвращает базовые советы для fallback"""
        return [
            "Focus on open communication",
            "Practice active listening", 
            "Take time for self-care"
        ]

# Экспортируем для использования
__all__ = ['TipsGenerator'] 