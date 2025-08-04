"""
Smart Home Automation Engine
Движок автоматизации умного дома
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AutomationTrigger(Enum):
    """Типы триггеров автоматизации"""
    SENSOR = "sensor"
    TIME = "time"
    EVENT = "event"
    CONDITION = "condition"
    MANUAL = "manual"

class AutomationCondition(Enum):
    """Типы условий автоматизации"""
    EQUALS = "equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    CONTAINS = "contains"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"

@dataclass
class AutomationRule:
    """Правило автоматизации"""
    rule_id: str
    name: str
    description: str
    enabled: bool = True
    trigger: AutomationTrigger = AutomationTrigger.SENSOR
    conditions: List[Dict] = None
    actions: List[Dict] = None
    schedule: Dict = None
    priority: int = 1
    created_at: datetime = None
    last_executed: datetime = None

class AutomationEngine:
    """Движок автоматизации умного дома"""
    
    def __init__(self):
        self.rules: Dict[str, AutomationRule] = {}
        self.logger = logger
        
        # Подписчики на события автоматизации
        self.execution_subscribers: List[Callable] = []
        
        # Контекст выполнения
        self.execution_context: Dict[str, Any] = {}
        
    async def add_rule(self, rule: AutomationRule):
        """Добавление правила автоматизации"""
        if rule.created_at is None:
            rule.created_at = datetime.now()
        
        self.rules[rule.rule_id] = rule
        self.logger.info(f"✅ Added automation rule: {rule.name}")
    
    async def remove_rule(self, rule_id: str):
        """Удаление правила автоматизации"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self.logger.info(f"🗑️ Removed automation rule: {rule_id}")
    
    async def enable_rule(self, rule_id: str):
        """Включение правила"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            self.logger.info(f"✅ Enabled automation rule: {rule_id}")
    
    async def disable_rule(self, rule_id: str):
        """Отключение правила"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            self.logger.info(f"❌ Disabled automation rule: {rule_id}")
    
    async def evaluate_rule(self, rule: AutomationRule, context: Dict[str, Any]) -> bool:
        """Оценка правила автоматизации"""
        if not rule.enabled:
            return False
        
        # Проверка триггера
        if not await self._check_trigger(rule, context):
            return False
        
        # Проверка условий
        if rule.conditions and not await self._evaluate_conditions(rule.conditions, context):
            return False
        
        return True
    
    async def _check_trigger(self, rule: AutomationRule, context: Dict[str, Any]) -> bool:
        """Проверка триггера"""
        trigger = rule.trigger
        
        if trigger == AutomationTrigger.SENSOR:
            return await self._check_sensor_trigger(rule, context)
        elif trigger == AutomationTrigger.TIME:
            return await self._check_time_trigger(rule, context)
        elif trigger == AutomationTrigger.EVENT:
            return await self._check_event_trigger(rule, context)
        elif trigger == AutomationTrigger.CONDITION:
            return await self._check_condition_trigger(rule, context)
        elif trigger == AutomationTrigger.MANUAL:
            return await self._check_manual_trigger(rule, context)
        
        return False
    
    async def _check_sensor_trigger(self, rule: AutomationRule, context: Dict[str, Any]) -> bool:
        """Проверка триггера сенсора"""
        sensor_data = context.get("sensor_data")
        if not sensor_data:
            return False
        
        # Проверка по ID сенсора
        if "sensor_id" in context and context["sensor_id"] == sensor_data.get("sensor_id"):
            return True
        
        # Проверка по типу сенсора
        if "sensor_type" in context and context["sensor_type"] == sensor_data.get("sensor_type"):
            return True
        
        return False
    
    async def _check_time_trigger(self, rule: AutomationRule, context: Dict[str, Any]) -> bool:
        """Проверка временного триггера"""
        schedule = rule.schedule
        if not schedule:
            return False
        
        current_time = datetime.now()
        
        # Проверка времени дня
        if "time" in schedule:
            time_str = schedule["time"]
            try:
                trigger_time = datetime.strptime(time_str, "%H:%M").time()
                current_time_only = current_time.time()
                
                # Допуск в 1 минуту
                time_diff = abs((current_time_only.hour * 60 + current_time_only.minute) - 
                               (trigger_time.hour * 60 + trigger_time.minute))
                return time_diff <= 1
            except ValueError:
                pass
        
        # Проверка дней недели
        if "days" in schedule:
            current_day = current_time.strftime("%A").lower()
            if current_day not in schedule["days"]:
                return False
        
        # Проверка интервала
        if "interval" in schedule:
            interval_minutes = schedule["interval"]
            last_executed = rule.last_executed
            if last_executed:
                time_since_last = (current_time - last_executed).total_seconds() / 60
                return time_since_last >= interval_minutes
        
        return True
    
    async def _check_event_trigger(self, rule: AutomationRule, context: Dict[str, Any]) -> bool:
        """Проверка триггера события"""
        event_type = context.get("event_type")
        if not event_type:
            return False
        
        # Проверка типа события
        if "event_types" in context:
            return event_type in context["event_types"]
        
        return True
    
    async def _check_condition_trigger(self, rule: AutomationRule, context: Dict[str, Any]) -> bool:
        """Проверка триггера условия"""
        return await self._evaluate_conditions(rule.conditions or [], context)
    
    async def _check_manual_trigger(self, rule: AutomationRule, context: Dict[str, Any]) -> bool:
        """Проверка ручного триггера"""
        manual_trigger = context.get("manual_trigger")
        return manual_trigger == rule.rule_id
    
    async def _evaluate_conditions(self, conditions: List[Dict], context: Dict[str, Any]) -> bool:
        """Оценка условий"""
        if not conditions:
            return True
        
        for condition in conditions:
            if not await self._evaluate_single_condition(condition, context):
                return False
        
        return True
    
    async def _evaluate_single_condition(self, condition: Dict, context: Dict[str, Any]) -> bool:
        """Оценка одного условия"""
        condition_type = condition.get("type")
        field = condition.get("field")
        value = condition.get("value")
        
        # Получение значения из контекста
        context_value = self._get_context_value(field, context)
        
        if condition_type == AutomationCondition.EQUALS.value:
            return context_value == value
        elif condition_type == AutomationCondition.GREATER_THAN.value:
            return context_value > value
        elif condition_type == AutomationCondition.LESS_THAN.value:
            return context_value < value
        elif condition_type == AutomationCondition.BETWEEN.value:
            min_val = value.get("min")
            max_val = value.get("max")
            return min_val <= context_value <= max_val
        elif condition_type == AutomationCondition.CONTAINS.value:
            return value in str(context_value)
        elif condition_type == AutomationCondition.EXISTS.value:
            return context_value is not None and context_value != ""
        elif condition_type == AutomationCondition.NOT_EXISTS.value:
            return context_value is None or context_value == ""
        
        return False
    
    def _get_context_value(self, field: str, context: Dict[str, Any]) -> Any:
        """Получение значения из контекста"""
        if "." in field:
            # Поддержка вложенных полей (например, "sensor_data.value")
            parts = field.split(".")
            value = context
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        else:
            return context.get(field)
    
    async def execute_rule(self, rule: AutomationRule, context: Dict[str, Any]):
        """Выполнение правила автоматизации"""
        try:
            self.logger.info(f"🚀 Executing automation rule: {rule.name}")
            
            # Обновление времени последнего выполнения
            rule.last_executed = datetime.now()
            
            # Выполнение действий
            if rule.actions:
                for action in rule.actions:
                    await self._execute_action(action, context)
            
            # Уведомление подписчиков
            await self._notify_execution_subscribers(rule, context, True)
            
            self.logger.info(f"✅ Automation rule executed: {rule.name}")
            
        except Exception as e:
            self.logger.error(f"❌ Automation rule execution error: {e}")
            await self._notify_execution_subscribers(rule, context, False, str(e))
    
    async def _execute_action(self, action: Dict, context: Dict[str, Any]):
        """Выполнение действия"""
        action_type = action.get("type")
        
        if action_type == "actuator_command":
            await self._execute_actuator_action(action, context)
        elif action_type == "notification":
            await self._execute_notification_action(action, context)
        elif action_type == "script":
            await self._execute_script_action(action, context)
        elif action_type == "scene":
            await self._execute_scene_action(action, context)
        else:
            self.logger.warning(f"⚠️ Unknown action type: {action_type}")
    
    async def _execute_actuator_action(self, action: Dict, context: Dict[str, Any]):
        """Выполнение действия актуатора"""
        actuator_id = action.get("actuator_id")
        command = action.get("command")
        parameters = action.get("parameters", {})
        
        # Здесь должна быть интеграция с ActuatorManager
        self.logger.info(f"📤 Actuator action: {actuator_id} -> {command}")
        
        # Временная заглушка
        await asyncio.sleep(0.1)
    
    async def _execute_notification_action(self, action: Dict, context: Dict[str, Any]):
        """Выполнение действия уведомления"""
        message = action.get("message", "")
        notification_type = action.get("notification_type", "info")
        
        self.logger.info(f"📱 Notification ({notification_type}): {message}")
    
    async def _execute_script_action(self, action: Dict, context: Dict[str, Any]):
        """Выполнение скриптового действия"""
        script_path = action.get("script_path")
        parameters = action.get("parameters", {})
        
        self.logger.info(f"📜 Script action: {script_path}")
    
    async def _execute_scene_action(self, action: Dict, context: Dict[str, Any]):
        """Выполнение сцены"""
        scene_id = action.get("scene_id")
        
        self.logger.info(f"🎬 Scene action: {scene_id}")
    
    async def _notify_execution_subscribers(self, rule: AutomationRule, context: Dict[str, Any], success: bool, error: str = None):
        """Уведомление подписчиков о выполнении"""
        execution_data = {
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        
        for subscriber in self.execution_subscribers:
            try:
                await subscriber(execution_data)
            except Exception as e:
                self.logger.error(f"❌ Execution subscriber error: {e}")
    
    async def process_event(self, event_type: str, event_data: Dict[str, Any]):
        """Обработка события"""
        context = {
            "event_type": event_type,
            "event_data": event_data,
            **event_data
        }
        
        # Поиск подходящих правил
        matching_rules = []
        
        for rule in self.rules.values():
            if await self.evaluate_rule(rule, context):
                matching_rules.append(rule)
        
        # Сортировка по приоритету
        matching_rules.sort(key=lambda r: r.priority, reverse=True)
        
        # Выполнение правил
        for rule in matching_rules:
            await self.execute_rule(rule, context)
    
    def subscribe_to_executions(self, callback: Callable):
        """Подписка на выполнение правил"""
        self.execution_subscribers.append(callback)
    
    def get_rule(self, rule_id: str) -> Optional[AutomationRule]:
        """Получение правила по ID"""
        return self.rules.get(rule_id)
    
    def get_rules_by_trigger(self, trigger: AutomationTrigger) -> List[AutomationRule]:
        """Получение правил по типу триггера"""
        return [rule for rule in self.rules.values() if rule.trigger == trigger]
    
    def get_enabled_rules(self) -> List[AutomationRule]:
        """Получение включенных правил"""
        return [rule for rule in self.rules.values() if rule.enabled]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы автоматизации"""
        total_rules = len(self.rules)
        enabled_rules = len(self.get_enabled_rules())
        
        # Статистика по триггерам
        trigger_stats = {}
        for trigger in AutomationTrigger:
            count = len(self.get_rules_by_trigger(trigger))
            if count > 0:
                trigger_stats[trigger.value] = count
        
        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "trigger_types": trigger_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def export_config(self) -> Dict[str, Any]:
        """Экспорт конфигурации"""
        return {
            "rules": {
                rule_id: {
                    "name": rule.name,
                    "description": rule.description,
                    "enabled": rule.enabled,
                    "trigger": rule.trigger.value,
                    "conditions": rule.conditions,
                    "actions": rule.actions,
                    "schedule": rule.schedule,
                    "priority": rule.priority,
                    "created_at": rule.created_at.isoformat() if rule.created_at else None,
                    "last_executed": rule.last_executed.isoformat() if rule.last_executed else None
                }
                for rule_id, rule in self.rules.items()
            }
        }
    
    async def import_config(self, config_data: Dict[str, Any]):
        """Импорт конфигурации"""
        rules_data = config_data.get("rules", {})
        
        for rule_id, rule_config in rules_data.items():
            rule = AutomationRule(
                rule_id=rule_id,
                name=rule_config["name"],
                description=rule_config["description"],
                enabled=rule_config.get("enabled", True),
                trigger=AutomationTrigger(rule_config["trigger"]),
                conditions=rule_config.get("conditions"),
                actions=rule_config.get("actions"),
                schedule=rule_config.get("schedule"),
                priority=rule_config.get("priority", 1),
                created_at=datetime.fromisoformat(rule_config["created_at"]) if rule_config.get("created_at") else None,
                last_executed=datetime.fromisoformat(rule_config["last_executed"]) if rule_config.get("last_executed") else None
            )
            
            await self.add_rule(rule)
        
        self.logger.info(f"📥 Imported {len(rules_data)} automation rules") 