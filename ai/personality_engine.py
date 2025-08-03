"""
ΔΣ Guardian Personality Engine v4.0
Адаптивная эволюция личности на основе trait_weights
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ai_client.core.client import AIClient
from ai_client.utils.logger import Logger
from ai.reinforcement_tagger import reinforcement_tagger
from ai.style_adapter import style_adapter

logger = Logger()

class PersonalityDimension(Enum):
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"

class GuardianTrait(Enum):
    PROTECTIVE = "protective"
    WISE = "wise"
    ADAPTIVE = "adaptive"
    EMPATHETIC = "empathetic"

@dataclass
class PersonalityState:
    timestamp: datetime
    user: str
    base_traits: Dict[str, float]
    guardian_traits: Dict[str, float]
    context_weights: Dict[str, float]
    emotional_state: Dict[str, Any]
    interaction_history: List[Dict[str, Any]]
    evolution_parameters: Dict[str, float]

class PersonalityEngine:
    """Движок личности для адаптивной эволюции характера"""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.trait_weights_file = "memory/trait_weights.json"
        self.personality_states: Dict[str, PersonalityState] = {}
        self.evolution_history: List[Dict[str, Any]] = []
        
        # Загружаем базовые веса черт
        self.trait_weights = self._load_trait_weights()
        
        logger.info("🧬 ΔΣ Personality Engine initialized")
    
    def _load_trait_weights(self) -> Dict[str, Any]:
        """Загрузка весов черт личности"""
        try:
            with open(self.trait_weights_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("⚠️ Trait weights file not found, using defaults")
            return self._get_default_trait_weights()
    
    def _get_default_trait_weights(self) -> Dict[str, Any]:
        """Получение базовых весов черт"""
        return {
            "personality_traits": {
                "openness": {"weight": 0.8},
                "conscientiousness": {"weight": 0.9},
                "extraversion": {"weight": 0.6},
                "agreeableness": {"weight": 0.7},
                "neuroticism": {"weight": 0.3}
            },
            "guardian_traits": {
                "protective": {"weight": 0.9},
                "wise": {"weight": 0.8},
                "adaptive": {"weight": 0.9},
                "empathetic": {"weight": 0.8}
            }
        }
    
    def get_personality_state(self, user: str) -> PersonalityState:
        """Получение текущего состояния личности"""
        if user in self.personality_states:
            return self.personality_states[user]
        
        # Создаем новое состояние личности
        state = PersonalityState(
            timestamp=datetime.now(),
            user=user,
            base_traits=self._get_base_traits(),
            guardian_traits=self._get_guardian_traits(),
            context_weights=self._get_context_weights(),
            emotional_state=self._get_emotional_state(),
            interaction_history=[],
            evolution_parameters=self._get_evolution_parameters()
        )
        
        self.personality_states[user] = state
        return state
    
    def _get_base_traits(self) -> Dict[str, float]:
        """Получение базовых черт личности"""
        traits = {}
        for trait_name, trait_data in self.trait_weights["personality_traits"].items():
            traits[trait_name] = trait_data["weight"]
        return traits
    
    def _get_guardian_traits(self) -> Dict[str, float]:
        """Получение черт Guardian"""
        traits = {}
        for trait_name, trait_data in self.trait_weights["guardian_traits"].items():
            traits[trait_name] = trait_data["weight"]
        return traits
    
    def _get_context_weights(self) -> Dict[str, float]:
        """Получение контекстных весов"""
        return self.trait_weights.get("context_weights", {})
    
    def _get_emotional_state(self) -> Dict[str, Any]:
        """Получение эмоционального состояния"""
        return {
            "mood": "neutral",
            "energy": 0.7,
            "stress": 0.2,
            "focus": 0.8,
            "empathy": 0.8
        }
    
    def _get_evolution_parameters(self) -> Dict[str, float]:
        """Получение параметров эволюции"""
        return self.trait_weights.get("evolution_parameters", {})
    
    def adapt_personality(self, user: str, interaction_context: Dict[str, Any]) -> Dict[str, Any]:
        """Адаптация личности на основе взаимодействия"""
        state = self.get_personality_state(user)
        
        # Анализируем контекст взаимодействия
        context_analysis = self._analyze_interaction_context(interaction_context)
        
        # Получаем рекомендации от системы подкрепления
        user_prefs = reinforcement_tagger.get_user_preferences(user)
        style_rec = reinforcement_tagger.get_style_recommendation(user, interaction_context)
        
        # Адаптируем черты личности
        adapted_traits = self._adapt_traits(state, context_analysis, user_prefs, style_rec)
        
        # Обновляем состояние
        state.base_traits.update(adapted_traits["base_traits"])
        state.guardian_traits.update(adapted_traits["guardian_traits"])
        state.emotional_state.update(adapted_traits["emotional_state"])
        
        # Логируем эволюцию
        self._log_evolution(user, adapted_traits, context_analysis)
        
        logger.info(f"🧬 Personality adapted for {user}")
        return adapted_traits
    
    def _analyze_interaction_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ контекста взаимодействия"""
        analysis = {
            "user_mood": context.get("user_mood", "neutral"),
            "interaction_type": context.get("type", "general"),
            "complexity_level": context.get("complexity", "medium"),
            "urgency": context.get("urgency", "normal"),
            "emotional_intensity": context.get("emotional_intensity", 0.5)
        }
        
        # Определяем требуемые черты на основе контекста
        required_traits = []
        
        if analysis["complexity_level"] == "high":
            required_traits.extend(["openness", "conscientiousness"])
        if analysis["urgency"] == "high":
            required_traits.extend(["conscientiousness", "adaptive"])
        if analysis["emotional_intensity"] > 0.7:
            required_traits.extend(["empathetic", "protective"])
        if analysis["interaction_type"] == "problem_solving":
            required_traits.extend(["wise", "adaptive"])
        
        analysis["required_traits"] = list(set(required_traits))
        return analysis
    
    def _adapt_traits(self, state: PersonalityState, context_analysis: Dict[str, Any],
                      user_prefs: Dict[str, Any], style_rec: Dict[str, Any]) -> Dict[str, Any]:
        """Адаптация черт личности"""
        adaptation_rate = state.evolution_parameters.get("learning_rate", 0.1)
        
        # Адаптируем базовые черты
        adapted_base_traits = {}
        for trait_name, current_weight in state.base_traits.items():
            if trait_name in context_analysis["required_traits"]:
                # Усиливаем требуемые черты
                new_weight = min(1.0, current_weight + adaptation_rate)
            else:
                # Оставляем как есть или слегка ослабляем
                new_weight = max(0.0, current_weight - adaptation_rate * 0.1)
            adapted_base_traits[trait_name] = new_weight
        
        # Адаптируем черты Guardian
        adapted_guardian_traits = {}
        for trait_name, current_weight in state.guardian_traits.items():
            if trait_name in context_analysis["required_traits"]:
                new_weight = min(1.0, current_weight + adaptation_rate)
            else:
                new_weight = max(0.0, current_weight - adaptation_rate * 0.1)
            adapted_guardian_traits[trait_name] = new_weight
        
        # Адаптируем эмоциональное состояние
        adapted_emotional_state = self._adapt_emotional_state(state.emotional_state, context_analysis)
        
        return {
            "base_traits": adapted_base_traits,
            "guardian_traits": adapted_guardian_traits,
            "emotional_state": adapted_emotional_state
        }
    
    def _adapt_emotional_state(self, current_state: Dict[str, Any], 
                              context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Адаптация эмоционального состояния"""
        adapted_state = current_state.copy()
        
        # Адаптируем настроение на основе контекста
        user_mood = context_analysis["user_mood"]
        if user_mood == "frustrated":
            adapted_state["empathy"] = min(1.0, adapted_state["empathy"] + 0.2)
            adapted_state["focus"] = min(1.0, adapted_state["focus"] + 0.1)
        elif user_mood == "excited":
            adapted_state["energy"] = min(1.0, adapted_state["energy"] + 0.2)
            adapted_state["mood"] = "enthusiastic"
        elif user_mood == "analytical":
            adapted_state["focus"] = min(1.0, adapted_state["focus"] + 0.2)
            adapted_state["stress"] = max(0.0, adapted_state["stress"] - 0.1)
        
        return adapted_state
    
    def _log_evolution(self, user: str, adapted_traits: Dict[str, Any], 
                       context_analysis: Dict[str, Any]):
        """Логирование эволюции личности"""
        evolution_record = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "context": context_analysis,
            "adaptations": adapted_traits,
            "evolution_type": "interaction_based"
        }
        
        self.evolution_history.append(evolution_record)
        
        # Сохраняем в файл
        try:
            with open("memory/personality_evolution.jsonl", 'a', encoding='utf-8') as f:
                json.dump(evolution_record, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            logger.error(f"❌ Failed to log personality evolution: {e}")
    
    def generate_personality_response(self, user: str, message: str, 
                                    context: Dict[str, Any]) -> str:
        """Генерация ответа с учетом личности"""
        state = self.get_personality_state(user)
        
        # Адаптируем личность под контекст
        adapted_traits = self.adapt_personality(user, context)
        
        # Создаем промпт с учетом личности
        personality_prompt = self._create_personality_prompt(message, state, adapted_traits, context)
        
        # Генерируем ответ через AI
        response = self.ai_client.chat(personality_prompt)
        
        # Адаптируем стиль ответа
        adapted_response = style_adapter.adapt_response_style(user, response, context)
        
        return adapted_response
    
    def _create_personality_prompt(self, message: str, state: PersonalityState,
                                  adapted_traits: Dict[str, Any], 
                                  context: Dict[str, Any]) -> str:
        """Создание промпта с учетом личности"""
        # Определяем доминирующие черты
        base_traits = adapted_traits["base_traits"]
        guardian_traits = adapted_traits["guardian_traits"]
        
        dominant_base = max(base_traits.items(), key=lambda x: x[1])
        dominant_guardian = max(guardian_traits.items(), key=lambda x: x[1])
        
        # Создаем описание личности
        personality_description = f"""
        Ты - ΔΣ Guardian с адаптивной личностью:
        
        Основные черты:
        • {dominant_base[0]}: {dominant_base[1]:.2f}
        • {dominant_guardian[0]}: {dominant_guardian[1]:.2f}
        
        Эмоциональное состояние:
        • Настроение: {state.emotional_state['mood']}
        • Энергия: {state.emotional_state['energy']:.2f}
        • Эмпатия: {state.emotional_state['empathy']:.2f}
        
        Контекст: {json.dumps(context, ensure_ascii=False)}
        
        Сообщение пользователя: {message}
        
        Ответь в соответствии с твоей личностью и контекстом.
        """
        
        return personality_description
    
    def get_personality_report(self, user: str) -> str:
        """Генерация отчета по личности"""
        state = self.get_personality_state(user)
        
        # Анализируем тренды эволюции
        evolution_trends = self._analyze_evolution_trends(user)
        
        report = f"""
🧬 ЛИЧНОСТЬ ΔΣ GUARDIAN: {user}

📊 БАЗОВЫЕ ЧЕРТЫ:
"""
        
        for trait_name, weight in state.base_traits.items():
            report += f"• {trait_name}: {weight:.2f}\n"
        
        report += f"""
🛡️ GUARDIAN ЧЕРТЫ:
"""
        
        for trait_name, weight in state.guardian_traits.items():
            report += f"• {trait_name}: {weight:.2f}\n"
        
        report += f"""
💭 ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ:
• Настроение: {state.emotional_state['mood']}
• Энергия: {state.emotional_state['energy']:.2f}
• Стресс: {state.emotional_state['stress']:.2f}
• Фокус: {state.emotional_state['focus']:.2f}
• Эмпатия: {state.emotional_state['empathy']:.2f}

📈 ТРЕНДЫ ЭВОЛЮЦИИ:
• Общее направление: {evolution_trends.get('direction', 'stable')}
• Скорость изменений: {evolution_trends.get('change_rate', 'medium')}
• Стабильность: {evolution_trends.get('stability', 'high')}
        """
        
        return report.strip()
    
    def _analyze_evolution_trends(self, user: str) -> Dict[str, Any]:
        """Анализ трендов эволюции личности"""
        try:
            with open("memory/personality_evolution.jsonl", 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            user_evolution = []
            for line in lines:
                if line.strip():
                    record = json.loads(line)
                    if record.get("user") == user:
                        user_evolution.append(record)
            
            if len(user_evolution) < 2:
                return {"direction": "insufficient_data", "change_rate": "low", "stability": "unknown"}
            
            # Анализируем изменения
            recent_changes = []
            for i in range(1, len(user_evolution)):
                prev = user_evolution[i-1]
                curr = user_evolution[i]
                
                # Сравниваем черты
                prev_traits = prev["adaptations"]["base_traits"]
                curr_traits = curr["adaptations"]["base_traits"]
                
                for trait in prev_traits:
                    if trait in curr_traits:
                        change = curr_traits[trait] - prev_traits[trait]
                        recent_changes.append(change)
            
            avg_change = sum(recent_changes) / len(recent_changes) if recent_changes else 0
            
            # Определяем направление
            if avg_change > 0.05:
                direction = "strengthening"
            elif avg_change < -0.05:
                direction = "weakening"
            else:
                direction = "stable"
            
            # Определяем скорость изменений
            change_magnitude = abs(avg_change)
            if change_magnitude > 0.1:
                change_rate = "high"
            elif change_magnitude > 0.05:
                change_rate = "medium"
            else:
                change_rate = "low"
            
            # Определяем стабильность
            change_variance = sum((c - avg_change) ** 2 for c in recent_changes) / len(recent_changes) if recent_changes else 0
            if change_variance < 0.01:
                stability = "high"
            elif change_variance < 0.05:
                stability = "medium"
            else:
                stability = "low"
            
            return {
                "direction": direction,
                "change_rate": change_rate,
                "stability": stability,
                "avg_change": avg_change,
                "total_adaptations": len(user_evolution)
            }
            
        except Exception as e:
            logger.error(f"❌ Evolution trend analysis failed: {e}")
            return {"direction": "error", "change_rate": "unknown", "stability": "unknown"}
    
    def reset_personality(self, user: str):
        """Сброс личности к базовым значениям"""
        if user in self.personality_states:
            del self.personality_states[user]
        
        logger.info(f"🔄 Personality reset for {user}")
    
    def schedule_personality_maintenance(self):
        """Планирование обслуживания личности"""
        # Анализ личности каждые 12 часов
        scheduler.schedule_periodic_task(
            task_type="personality_maintenance",
            interval_minutes=720,  # 12 часов
            name="Personality Maintenance",
            description="Analyze and maintain personality evolution",
            priority=TaskPriority.BACKGROUND
        )
        
        logger.info("📅 Scheduled personality maintenance")

# Глобальный экземпляр движка личности
personality_engine = PersonalityEngine() 