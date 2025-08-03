"""
ΔΣ Guardian Reinforcement Tagger v4.0
Система подкрепления для обучения от взаимодействий
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

from ai_client.core.client import AIClient
from ai_client.utils.logger import Logger
from core.scheduler import scheduler, TaskPriority

logger = Logger()

class FeedbackType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

class LearningCategory(Enum):
    STYLE_PREFERENCE = "style_preference"
    COMMUNICATION_LEVEL = "communication_level"
    RESPONSE_SPEED = "response_speed"
    TECHNICAL_DEPTH = "technical_depth"
    INTERACTION_PATTERN = "interaction_pattern"
    EMOTIONAL_RESPONSE = "emotional_response"

@dataclass
class InteractionRecord:
    timestamp: datetime
    user: str
    action: str
    context: Dict[str, Any]
    response: Dict[str, Any]
    feedback: Dict[str, Any]
    learning_insights: Dict[str, Any]

class ReinforcementTagger:
    """Система подкрепления для обучения от взаимодействий"""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.interaction_log_file = "memory/interaction_log.jsonl"
        self.learning_patterns: Dict[str, Any] = {}
        self.feedback_weights: Dict[str, float] = {
            "explicit_positive": 1.0,
            "explicit_negative": -1.0,
            "implicit_positive": 0.5,
            "implicit_negative": -0.5,
            "neutral": 0.0
        }
        
        # Загружаем существующие паттерны
        self._load_learning_patterns()
        
        logger.info("🎯 ΔΣ Reinforcement Tagger initialized")
    
    def _load_learning_patterns(self):
        """Загрузка паттернов обучения"""
        try:
            with open("memory/learning_patterns.json", 'r', encoding='utf-8') as f:
                self.learning_patterns = json.load(f)
        except FileNotFoundError:
            self.learning_patterns = {
                "user_preferences": {},
                "style_adaptations": {},
                "communication_patterns": {},
                "feedback_analysis": {}
            }
    
    def _save_learning_patterns(self):
        """Сохранение паттернов обучения"""
        try:
            with open("memory/learning_patterns.json", 'w', encoding='utf-8') as f:
                json.dump(self.learning_patterns, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Failed to save learning patterns: {e}")
    
    def log_interaction(self, user: str, action: str, context: Dict[str, Any],
                       response: Dict[str, Any], feedback: Dict[str, Any]) -> str:
        """Логирование взаимодействия"""
        record = InteractionRecord(
            timestamp=datetime.now(),
            user=user,
            action=action,
            context=context,
            response=response,
            feedback=feedback,
            learning_insights={}
        )
        
        # Анализируем взаимодействие для извлечения инсайтов
        insights = self._analyze_interaction(record)
        record.learning_insights = insights
        
        # Сохраняем в JSONL файл
        self._save_interaction_record(record)
        
        # Обновляем паттерны обучения
        self._update_learning_patterns(record)
        
        logger.info(f"📝 Interaction logged: {action} by {user}")
        return record.timestamp.isoformat()
    
    def _analyze_interaction(self, record: InteractionRecord) -> Dict[str, Any]:
        """AI-анализ взаимодействия для извлечения инсайтов"""
        analysis_prompt = f"""
        Анализируй это взаимодействие и извлеки ключевые инсайты для обучения:
        
        Пользователь: {record.user}
        Действие: {record.action}
        Контекст: {json.dumps(record.context, ensure_ascii=False)}
        Ответ: {json.dumps(record.response, ensure_ascii=False)}
        Обратная связь: {json.dumps(record.feedback, ensure_ascii=False)}
        
        Проанализируй:
        1. Предпочтения пользователя в стиле общения
        2. Уровень технической глубины
        3. Скорость взаимодействия
        4. Эмоциональные паттерны
        5. Предпочтительные форматы ответов
        
        Верни анализ в JSON формате.
        """
        
        try:
            response = self.ai_client.chat(analysis_prompt)
            return self._extract_json_from_response(response)
        except Exception as e:
            logger.error(f"❌ Interaction analysis failed: {e}")
            return {"error": str(e)}
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Извлечение JSON из AI-ответа"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"raw_response": response}
        except:
            return {"raw_response": response}
    
    def _save_interaction_record(self, record: InteractionRecord):
        """Сохранение записи взаимодействия в JSONL"""
        try:
            with open(self.interaction_log_file, 'a', encoding='utf-8') as f:
                json.dump({
                    "timestamp": record.timestamp.isoformat(),
                    "type": "interaction",
                    "user": record.user,
                    "action": record.action,
                    "context": record.context,
                    "response": record.response,
                    "feedback": record.feedback,
                    "learning_insights": record.learning_insights
                }, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            logger.error(f"❌ Failed to save interaction record: {e}")
    
    def _update_learning_patterns(self, record: InteractionRecord):
        """Обновление паттернов обучения на основе взаимодействия"""
        user = record.user
        insights = record.learning_insights
        
        # Обновляем предпочтения пользователя
        if user not in self.learning_patterns["user_preferences"]:
            self.learning_patterns["user_preferences"][user] = {}
        
        user_prefs = self.learning_patterns["user_preferences"][user]
        
        # Анализируем обратную связь
        feedback_score = self._calculate_feedback_score(record.feedback)
        
        # Обновляем стилевые адаптации
        if "style_preference" in insights:
            self._update_style_adaptation(user, insights["style_preference"], feedback_score)
        
        # Обновляем коммуникационные паттерны
        if "communication_level" in insights:
            self._update_communication_pattern(user, insights["communication_level"], feedback_score)
        
        # Обновляем техническую глубину
        if "technical_depth" in insights:
            self._update_technical_depth(user, insights["technical_depth"], feedback_score)
        
        # Сохраняем обновленные паттерны
        self._save_learning_patterns()
    
    def _calculate_feedback_score(self, feedback: Dict[str, Any]) -> float:
        """Расчет оценки обратной связи"""
        score = 0.0
        
        # Явная обратная связь
        if feedback.get("explicit") == "positive":
            score += self.feedback_weights["explicit_positive"]
        elif feedback.get("explicit") == "negative":
            score += self.feedback_weights["explicit_negative"]
        
        # Неявная обратная связь
        if feedback.get("implicit") == "positive":
            score += self.feedback_weights["implicit_positive"]
        elif feedback.get("implicit") == "negative":
            score += self.feedback_weights["implicit_negative"]
        
        return score
    
    def _update_style_adaptation(self, user: str, style: str, feedback_score: float):
        """Обновление стилевой адаптации"""
        if "style_adaptations" not in self.learning_patterns:
            self.learning_patterns["style_adaptations"] = {}
        
        if user not in self.learning_patterns["style_adaptations"]:
            self.learning_patterns["style_adaptations"][user] = {}
        
        user_styles = self.learning_patterns["style_adaptations"][user]
        
        if style not in user_styles:
            user_styles[style] = {"weight": 0.5, "confidence": 0.0, "usage_count": 0}
        
        # Обновляем вес стиля на основе обратной связи
        current_weight = user_styles[style]["weight"]
        learning_rate = 0.1
        new_weight = current_weight + (feedback_score * learning_rate)
        user_styles[style]["weight"] = max(0.0, min(1.0, new_weight))
        user_styles[style]["usage_count"] += 1
        user_styles[style]["confidence"] = min(1.0, user_styles[style]["usage_count"] / 10.0)
    
    def _update_communication_pattern(self, user: str, level: str, feedback_score: float):
        """Обновление коммуникационного паттерна"""
        if "communication_patterns" not in self.learning_patterns:
            self.learning_patterns["communication_patterns"] = {}
        
        if user not in self.learning_patterns["communication_patterns"]:
            self.learning_patterns["communication_patterns"][user] = {}
        
        user_patterns = self.learning_patterns["communication_patterns"][user]
        
        if level not in user_patterns:
            user_patterns[level] = {"weight": 0.5, "confidence": 0.0, "usage_count": 0}
        
        # Обновляем вес уровня коммуникации
        current_weight = user_patterns[level]["weight"]
        learning_rate = 0.1
        new_weight = current_weight + (feedback_score * learning_rate)
        user_patterns[level]["weight"] = max(0.0, min(1.0, new_weight))
        user_patterns[level]["usage_count"] += 1
        user_patterns[level]["confidence"] = min(1.0, user_patterns[level]["usage_count"] / 10.0)
    
    def _update_technical_depth(self, user: str, depth: str, feedback_score: float):
        """Обновление технической глубины"""
        if "technical_depth" not in self.learning_patterns:
            self.learning_patterns["technical_depth"] = {}
        
        if user not in self.learning_patterns["technical_depth"]:
            self.learning_patterns["technical_depth"][user] = {}
        
        user_depth = self.learning_patterns["technical_depth"][user]
        
        if depth not in user_depth:
            user_depth[depth] = {"weight": 0.5, "confidence": 0.0, "usage_count": 0}
        
        # Обновляем вес технической глубины
        current_weight = user_depth[depth]["weight"]
        learning_rate = 0.1
        new_weight = current_weight + (feedback_score * learning_rate)
        user_depth[depth]["weight"] = max(0.0, min(1.0, new_weight))
        user_depth[depth]["usage_count"] += 1
        user_depth[depth]["confidence"] = min(1.0, user_depth[depth]["usage_count"] / 10.0)
    
    def get_user_preferences(self, user: str) -> Dict[str, Any]:
        """Получение предпочтений пользователя"""
        if user not in self.learning_patterns["user_preferences"]:
            return {}
        
        return self.learning_patterns["user_preferences"][user]
    
    def get_style_recommendation(self, user: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Получение рекомендации по стилю для пользователя"""
        if user not in self.learning_patterns["style_adaptations"]:
            return {"style": "default", "confidence": 0.0}
        
        user_styles = self.learning_patterns["style_adaptations"][user]
        
        # Выбираем стиль с наибольшим весом
        best_style = max(user_styles.items(), key=lambda x: x[1]["weight"])
        
        return {
            "style": best_style[0],
            "weight": best_style[1]["weight"],
            "confidence": best_style[1]["confidence"],
            "all_styles": user_styles
        }
    
    def get_communication_level(self, user: str) -> Dict[str, Any]:
        """Получение уровня коммуникации для пользователя"""
        if user not in self.learning_patterns["communication_patterns"]:
            return {"level": "standard", "confidence": 0.0}
        
        user_patterns = self.learning_patterns["communication_patterns"][user]
        
        # Выбираем уровень с наибольшим весом
        best_level = max(user_patterns.items(), key=lambda x: x[1]["weight"])
        
        return {
            "level": best_level[0],
            "weight": best_level[1]["weight"],
            "confidence": best_level[1]["confidence"],
            "all_levels": user_patterns
        }
    
    def get_technical_depth(self, user: str) -> Dict[str, Any]:
        """Получение технической глубины для пользователя"""
        if user not in self.learning_patterns["technical_depth"]:
            return {"depth": "medium", "confidence": 0.0}
        
        user_depth = self.learning_patterns["technical_depth"][user]
        
        # Выбираем глубину с наибольшим весом
        best_depth = max(user_depth.items(), key=lambda x: x[1]["weight"])
        
        return {
            "depth": best_depth[0],
            "weight": best_depth[1]["weight"],
            "confidence": best_depth[1]["confidence"],
            "all_depths": user_depth
        }
    
    def analyze_feedback_trends(self, user: str, days: int = 7) -> Dict[str, Any]:
        """Анализ трендов обратной связи"""
        try:
            with open(self.interaction_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_interactions = []
            
            for line in lines:
                if line.strip():
                    record = json.loads(line)
                    if record.get("user") == user:
                        timestamp = datetime.fromisoformat(record["timestamp"])
                        if timestamp >= cutoff_date:
                            recent_interactions.append(record)
            
            # Анализируем тренды
            positive_count = sum(1 for r in recent_interactions 
                               if r.get("feedback", {}).get("implicit") == "positive")
            negative_count = sum(1 for r in recent_interactions 
                               if r.get("feedback", {}).get("implicit") == "negative")
            
            total_interactions = len(recent_interactions)
            satisfaction_rate = positive_count / total_interactions if total_interactions > 0 else 0.0
            
            return {
                "total_interactions": total_interactions,
                "positive_feedback": positive_count,
                "negative_feedback": negative_count,
                "satisfaction_rate": satisfaction_rate,
                "trend": "improving" if satisfaction_rate > 0.7 else "declining" if satisfaction_rate < 0.3 else "stable"
            }
            
        except Exception as e:
            logger.error(f"❌ Feedback trend analysis failed: {e}")
            return {"error": str(e)}
    
    def schedule_learning_cycle(self):
        """Планирование цикла обучения"""
        # Анализ трендов каждые 6 часов
        scheduler.schedule_periodic_task(
            task_type="learning_analysis",
            interval_minutes=360,  # 6 часов
            name="Learning Pattern Analysis",
            description="Analyze interaction patterns and update learning models",
            priority=TaskPriority.BACKGROUND
        )
        
        logger.info("📅 Scheduled learning cycle analysis")

# Глобальный экземпляр системы подкрепления
reinforcement_tagger = ReinforcementTagger() 