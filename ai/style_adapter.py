"""
ΔΣ Guardian Style Adapter v4.0
Динамическая адаптация стиля общения под пользователя
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ai_client.core.client import AIClient
from ai_client.utils.logger import Logger
from ai.reinforcement_tagger import reinforcement_tagger

logger = Logger()

class StyleType(Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    EMOTIONAL = "emotional"
    CONCISE = "concise"
    DETAILED = "detailed"
    HUMOROUS = "humorous"
    SERIOUS = "serious"

class CommunicationLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"
    SPECIALIST = "specialist"

class TechnicalDepth(Enum):
    BASIC = "basic"
    MEDIUM = "medium"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class StyleProfile:
    user: str
    primary_style: StyleType
    communication_level: CommunicationLevel
    technical_depth: TechnicalDepth
    emotional_tone: str
    response_length: str
    detail_preference: str
    humor_sensitivity: float
    formality_level: float
    confidence: float

class StyleAdapter:
    """Адаптер стиля для динамической подстройки под пользователя"""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.style_templates: Dict[str, Dict[str, Any]] = {}
        self.user_profiles: Dict[str, StyleProfile] = {}
        
        # Загружаем шаблоны стилей
        self._load_style_templates()
        
        logger.info("🎨 ΔΣ Style Adapter initialized")
    
    def _load_style_templates(self):
        """Загрузка шаблонов стилей"""
        self.style_templates = {
            "formal": {
                "greeting": "Добрый день",
                "farewell": "С уважением",
                "tone": "professional",
                "sentence_structure": "complex",
                "vocabulary": "formal",
                "punctuation": "strict"
            },
            "casual": {
                "greeting": "Привет",
                "farewell": "Пока",
                "tone": "friendly",
                "sentence_structure": "simple",
                "vocabulary": "informal",
                "punctuation": "relaxed"
            },
            "technical": {
                "greeting": "Система готова",
                "farewell": "Операция завершена",
                "tone": "analytical",
                "sentence_structure": "precise",
                "vocabulary": "technical",
                "punctuation": "precise"
            },
            "emotional": {
                "greeting": "Рад тебя видеть!",
                "farewell": "До встречи!",
                "tone": "warm",
                "sentence_structure": "expressive",
                "vocabulary": "emotional",
                "punctuation": "expressive"
            },
            "concise": {
                "greeting": "Готов",
                "farewell": "Готово",
                "tone": "direct",
                "sentence_structure": "short",
                "vocabulary": "minimal",
                "punctuation": "minimal"
            },
            "detailed": {
                "greeting": "Добро пожаловать в систему ΔΣ Guardian",
                "farewell": "Спасибо за использование системы",
                "tone": "comprehensive",
                "sentence_structure": "elaborate",
                "vocabulary": "descriptive",
                "punctuation": "detailed"
            }
        }
    
    def get_user_style_profile(self, user: str) -> StyleProfile:
        """Получение профиля стиля пользователя"""
        if user in self.user_profiles:
            return self.user_profiles[user]
        
        # Создаем новый профиль на основе данных обучения
        style_rec = reinforcement_tagger.get_style_recommendation(user, {})
        comm_rec = reinforcement_tagger.get_communication_level(user)
        tech_rec = reinforcement_tagger.get_technical_depth(user)
        
        # Определяем основные параметры
        primary_style = StyleType(style_rec.get("style", "technical"))
        communication_level = CommunicationLevel(comm_rec.get("level", "expert"))
        technical_depth = TechnicalDepth(tech_rec.get("depth", "advanced"))
        
        # Создаем профиль
        profile = StyleProfile(
            user=user,
            primary_style=primary_style,
            communication_level=communication_level,
            technical_depth=technical_depth,
            emotional_tone="neutral",
            response_length="medium",
            detail_preference="comprehensive",
            humor_sensitivity=0.3,
            formality_level=0.7,
            confidence=style_rec.get("confidence", 0.5)
        )
        
        self.user_profiles[user] = profile
        return profile
    
    def adapt_response_style(self, user: str, content: str, context: Dict[str, Any]) -> str:
        """Адаптация стиля ответа под пользователя"""
        profile = self.get_user_style_profile(user)
        
        # Получаем рекомендации от системы подкрепления
        style_rec = reinforcement_tagger.get_style_recommendation(user, context)
        comm_rec = reinforcement_tagger.get_communication_level(user)
        tech_rec = reinforcement_tagger.get_technical_depth(user)
        
        # Адаптируем стиль
        adapted_content = self._apply_style_adaptations(content, profile, style_rec, comm_rec, tech_rec)
        
        logger.info(f"🎨 Style adapted for {user}: {profile.primary_style.value}")
        return adapted_content
    
    def _apply_style_adaptations(self, content: str, profile: StyleProfile,
                                style_rec: Dict[str, Any], comm_rec: Dict[str, Any],
                                tech_rec: Dict[str, Any]) -> str:
        """Применение адаптаций стиля"""
        style_type = profile.primary_style.value
        template = self.style_templates.get(style_type, self.style_templates["technical"])
        
        # Базовые адаптации
        adapted_content = content
        
        # Адаптация тона
        if template["tone"] == "professional":
            adapted_content = self._make_professional(adapted_content)
        elif template["tone"] == "friendly":
            adapted_content = self._make_friendly(adapted_content)
        elif template["tone"] == "analytical":
            adapted_content = self._make_analytical(adapted_content)
        elif template["tone"] == "warm":
            adapted_content = self._make_warm(adapted_content)
        elif template["tone"] == "direct":
            adapted_content = self._make_direct(adapted_content)
        elif template["tone"] == "comprehensive":
            adapted_content = self._make_comprehensive(adapted_content)
        
        # Адаптация технической глубины
        if tech_rec.get("depth") == "basic":
            adapted_content = self._simplify_technical(adapted_content)
        elif tech_rec.get("depth") == "expert":
            adapted_content = self._enhance_technical(adapted_content)
        
        # Адаптация уровня коммуникации
        if comm_rec.get("level") == "beginner":
            adapted_content = self._add_explanations(adapted_content)
        elif comm_rec.get("level") == "expert":
            adapted_content = self._add_technical_details(adapted_content)
        
        return adapted_content
    
    def _make_professional(self, content: str) -> str:
        """Сделать профессиональным"""
        # Добавляем формальные элементы
        if not content.startswith("✅") and not content.startswith("❌"):
            content = "✅ " + content
        
        # Используем более формальную лексику
        replacements = {
            "делаем": "выполняем",
            "создаем": "инициализируем",
            "готово": "операция завершена",
            "ошибка": "обнаружена проблема"
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        return content
    
    def _make_friendly(self, content: str) -> str:
        """Сделать дружелюбным"""
        # Добавляем эмодзи и дружелюбные элементы
        if "✅" in content:
            content = content.replace("✅", "🎉")
        if "❌" in content:
            content = content.replace("❌", "😅")
        
        # Используем более неформальную лексику
        replacements = {
            "операция завершена": "готово!",
            "инициализируем": "создаем",
            "обнаружена проблема": "есть небольшая проблема"
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        return content
    
    def _make_analytical(self, content: str) -> str:
        """Сделать аналитическим"""
        # Добавляем аналитические элементы
        if "✅" in content:
            content = content.replace("✅", "📊 АНАЛИЗ:")
        if "❌" in content:
            content = content.replace("❌", "⚠️ ПРОБЛЕМА:")
        
        # Добавляем структурированность
        lines = content.split('\n')
        structured_lines = []
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('📊') and not line.startswith('⚠️'):
                structured_lines.append(f"• {line}")
            else:
                structured_lines.append(line)
        
        return '\n'.join(structured_lines)
    
    def _make_warm(self, content: str) -> str:
        """Сделать теплым"""
        # Добавляем эмоциональные элементы
        if "✅" in content:
            content = content.replace("✅", "💖 Отлично!")
        if "❌" in content:
            content = content.replace("❌", "🤗 Не волнуйся, это можно исправить")
        
        # Используем более эмоциональную лексику
        replacements = {
            "готово": "все готово для тебя!",
            "проблема": "небольшая сложность",
            "ошибка": "небольшая неудача"
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        return content
    
    def _make_direct(self, content: str) -> str:
        """Сделать прямым"""
        # Убираем лишние элементы
        content = content.replace("✅ ", "")
        content = content.replace("❌ ", "")
        
        # Делаем более кратким
        lines = content.split('\n')
        direct_lines = []
        for line in lines:
            if line.strip() and not line.startswith('•'):
                direct_lines.append(line.strip())
        
        return '\n'.join(direct_lines)
    
    def _make_comprehensive(self, content: str) -> str:
        """Сделать всесторонним"""
        # Добавляем подробности
        if "✅" in content:
            content = content.replace("✅", "📋 ПОДРОБНЫЙ ОТЧЕТ:")
        if "❌" in content:
            content = content.replace("❌", "🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ПРОБЛЕМЫ:")
        
        # Добавляем структуру
        lines = content.split('\n')
        comprehensive_lines = []
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('📋') and not line.startswith('🔍'):
                comprehensive_lines.append(f"  {i+1}. {line}")
            else:
                comprehensive_lines.append(line)
        
        return '\n'.join(comprehensive_lines)
    
    def _simplify_technical(self, content: str) -> str:
        """Упростить техническую глубину"""
        # Заменяем технические термины на простые
        replacements = {
            "API": "интерфейс",
            "endpoint": "точка доступа",
            "authentication": "проверка",
            "authorization": "разрешение",
            "database": "база данных",
            "cache": "быстрая память",
            "optimization": "улучшение"
        }
        
        for tech_term, simple_term in replacements.items():
            content = content.replace(tech_term, simple_term)
        
        return content
    
    def _enhance_technical(self, content: str) -> str:
        """Усилить техническую глубину"""
        # Добавляем технические детали
        if "API" in content:
            content += "\n\n🔧 Технические детали:\n• RESTful API endpoints\n• JSON response format\n• HTTP status codes"
        
        if "database" in content:
            content += "\n\n🗄️ Архитектура данных:\n• Redis cache layer\n• PostgreSQL persistence\n• Connection pooling"
        
        return content
    
    def _add_explanations(self, content: str) -> str:
        """Добавить объяснения для начинающих"""
        explanations = []
        
        if "API" in content:
            explanations.append("API - это способ для программ общаться друг с другом")
        if "database" in content:
            explanations.append("База данных - это место, где хранится информация")
        if "cache" in content:
            explanations.append("Кэш - это быстрая память для часто используемых данных")
        
        if explanations:
            content += "\n\n💡 Объяснение:\n" + "\n".join(f"• {exp}" for exp in explanations)
        
        return content
    
    def _add_technical_details(self, content: str) -> str:
        """Добавить технические детали для экспертов"""
        details = []
        
        if "API" in content:
            details.append("• RESTful API с JWT authentication")
            details.append("• Rate limiting: 1000 req/min")
            details.append("• Response time: <200ms")
        
        if "database" in content:
            details.append("• PostgreSQL 14 с connection pooling")
            details.append("• Redis cache с TTL 3600s")
            details.append("• Backup strategy: daily + WAL")
        
        if details:
            content += "\n\n⚙️ Технические детали:\n" + "\n".join(details)
        
        return content
    
    def update_user_style(self, user: str, interaction_feedback: Dict[str, Any]):
        """Обновление стиля пользователя на основе обратной связи"""
        if user not in self.user_profiles:
            return
        
        profile = self.user_profiles[user]
        
        # Анализируем обратную связь
        feedback_score = self._calculate_feedback_score(interaction_feedback)
        
        # Обновляем профиль на основе обратной связи
        if feedback_score > 0:
            # Положительная обратная связь - усиливаем текущий стиль
            profile.confidence = min(1.0, profile.confidence + 0.1)
        elif feedback_score < 0:
            # Отрицательная обратная связь - ослабляем текущий стиль
            profile.confidence = max(0.0, profile.confidence - 0.1)
        
        logger.info(f"🎨 Updated style for {user}: confidence {profile.confidence:.2f}")
    
    def _calculate_feedback_score(self, feedback: Dict[str, Any]) -> float:
        """Расчет оценки обратной связи"""
        score = 0.0
        
        if feedback.get("explicit") == "positive":
            score += 1.0
        elif feedback.get("explicit") == "negative":
            score -= 1.0
        
        if feedback.get("implicit") == "positive":
            score += 0.5
        elif feedback.get("implicit") == "negative":
            score -= 0.5
        
        return score
    
    def get_style_statistics(self, user: str) -> Dict[str, Any]:
        """Получение статистики стиля пользователя"""
        if user not in self.user_profiles:
            return {"error": "User profile not found"}
        
        profile = self.user_profiles[user]
        
        return {
            "user": user,
            "primary_style": profile.primary_style.value,
            "communication_level": profile.communication_level.value,
            "technical_depth": profile.technical_depth.value,
            "confidence": profile.confidence,
            "style_recommendation": reinforcement_tagger.get_style_recommendation(user, {}),
            "communication_recommendation": reinforcement_tagger.get_communication_level(user),
            "technical_recommendation": reinforcement_tagger.get_technical_depth(user)
        }
    
    def generate_style_report(self, user: str) -> str:
        """Генерация отчета по стилю пользователя"""
        stats = self.get_style_statistics(user)
        
        if "error" in stats:
            return f"❌ {stats['error']}"
        
        report = f"""
🎨 СТИЛЬ ПОЛЬЗОВАТЕЛЯ: {user}

📊 ОСНОВНЫЕ ПАРАМЕТРЫ:
• Основной стиль: {stats['primary_style']}
• Уровень коммуникации: {stats['communication_level']}
• Техническая глубина: {stats['technical_depth']}
• Уверенность модели: {stats['confidence']:.2f}

🎯 РЕКОМЕНДАЦИИ:
• Стиль: {stats['style_recommendation']['style']} (вес: {stats['style_recommendation']['weight']:.2f})
• Коммуникация: {stats['communication_recommendation']['level']} (вес: {stats['communication_recommendation']['weight']:.2f})
• Техника: {stats['technical_recommendation']['depth']} (вес: {stats['technical_recommendation']['weight']:.2f})
        """
        
        return report.strip()

# Глобальный экземпляр адаптера стиля
style_adapter = StyleAdapter() 