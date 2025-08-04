"""
Smart Home LLM Integration
Интеграция LLM для управления умным домом
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

# Import AIClient only when needed to avoid circular import
# from ai_client.core.client import AIClient
from ai_client.utils.cache import system_cache

logger = logging.getLogger(__name__)

@dataclass
class LLMCommand:
    """Команда LLM"""
    command_id: str
    user_input: str
    interpreted_command: str
    parameters: Dict[str, Any]
    confidence: float
    timestamp: datetime
    executed: bool = False
    result: str = None
    error: str = None

class LLMHomeAssistant:
    """LLM ассистент для умного дома"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.logger = logger
        self.cache = system_cache
        
        # История команд
        self.command_history: List[LLMCommand] = []
        
        # Подписчики на команды
        self.command_subscribers: List[Callable] = []
        
        # Контекст системы
        self.system_context: Dict[str, Any] = {}
        
        # Промпт для LLM
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        """Получение системного промпта для LLM"""
        return """
Ты - AI ассистент для управления умным домом. Твоя задача - интерпретировать естественные команды пользователя и преобразовывать их в конкретные действия системы.

Доступные типы устройств:
- Сенсоры: motion, temperature, humidity, pressure, light, sound, vibration, gas, smoke, door, window, water_leak, electricity, magnetic, infrared, ultrasonic, lidar, thermal, radar
- Актуаторы: light, lock, siren, camera, valve, motor, heater, cooler, ventilator, blind, curtain, gate, door, window, turret, laser, strobe, speaker, pump, compressor

Доступные команды:
- Для света: turn_on, turn_off, set_brightness, set_color
- Для замков: lock, unlock, toggle
- Для сирен: activate, deactivate, set_pattern
- Для камер: pan, tilt, zoom, record
- Для клапанов: open, close, set_position
- Для моторов: start, stop, set_speed
- Для турелей: aim, track, fire

Примеры команд:
- "Включи свет в гостиной" → light_command: turn_on, location: living_room
- "Закрой все двери" → lock_command: lock, all_doors: true
- "Активируй тревогу" → siren_command: activate, volume: high
- "Покажи камеру заднего двора" → camera_command: pan, location: backyard

Всегда отвечай в формате JSON с полями:
{
    "command_type": "тип_команды",
    "device_type": "тип_устройства", 
    "device_id": "id_устройства",
    "action": "действие",
    "parameters": {"параметр": "значение"},
    "confidence": 0.95,
    "explanation": "объяснение команды"
}
"""
    
    async def process_user_command(self, user_input: str, context: Dict[str, Any] = None) -> LLMCommand:
        """Обработка команды пользователя"""
        try:
            # Обновление контекста
            if context:
                self.system_context.update(context)
            
            # Формирование промпта с контекстом
            full_prompt = self._build_prompt(user_input)
            
            # Запрос к LLM
            response = await self.ai_client.chat(
                messages=[{"role": "system", "content": self.system_prompt},
                         {"role": "user", "content": full_prompt}],
                temperature=0.1
            )
            
            # Парсинг ответа
            command_data = self._parse_llm_response(response)
            
            # Создание команды
            command = LLMCommand(
                command_id=f"cmd_{datetime.now().timestamp()}",
                user_input=user_input,
                interpreted_command=command_data.get("command_type", "unknown"),
                parameters=command_data.get("parameters", {}),
                confidence=command_data.get("confidence", 0.0),
                timestamp=datetime.now()
            )
            
            # Добавление в историю
            self.command_history.append(command)
            
            # Уведомление подписчиков
            await self._notify_command_subscribers(command)
            
            self.logger.info(f"🤖 LLM processed command: {command.interpreted_command}")
            
            return command
            
        except Exception as e:
            self.logger.error(f"❌ LLM command processing error: {e}")
            return None
    
    def _build_prompt(self, user_input: str) -> str:
        """Построение промпта с контекстом"""
        context_info = ""
        
        if self.system_context:
            context_info = f"\nКонтекст системы:\n{json.dumps(self.system_context, indent=2, ensure_ascii=False)}"
        
        return f"""
Пользователь сказал: "{user_input}"

{context_info}

Интерпретируй команду и верни JSON ответ.
"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Парсинг ответа LLM"""
        try:
            # Поиск JSON в ответе
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback - попытка извлечь JSON из всего ответа
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"⚠️ Failed to parse LLM response: {e}")
            return {
                "command_type": "unknown",
                "parameters": {},
                "confidence": 0.0,
                "explanation": "Failed to parse LLM response"
            }
    
    async def execute_command(self, command: LLMCommand) -> bool:
        """Выполнение команды LLM"""
        try:
            command_type = command.interpreted_command
            parameters = command.parameters
            
            # Выполнение в зависимости от типа команды
            if command_type == "light_command":
                result = await self._execute_light_command(parameters)
            elif command_type == "lock_command":
                result = await self._execute_lock_command(parameters)
            elif command_type == "siren_command":
                result = await self._execute_siren_command(parameters)
            elif command_type == "camera_command":
                result = await self._execute_camera_command(parameters)
            elif command_type == "valve_command":
                result = await self._execute_valve_command(parameters)
            elif command_type == "motor_command":
                result = await self._execute_motor_command(parameters)
            elif command_type == "turret_command":
                result = await self._execute_turret_command(parameters)
            elif command_type == "system_command":
                result = await self._execute_system_command(parameters)
            else:
                result = False
                command.error = f"Unknown command type: {command_type}"
            
            # Обновление статуса команды
            command.executed = True
            command.result = "success" if result else "failed"
            
            self.logger.info(f"✅ Executed LLM command: {command_type}")
            return result
            
        except Exception as e:
            command.executed = True
            command.error = str(e)
            self.logger.error(f"❌ LLM command execution error: {e}")
            return False
    
    async def _execute_light_command(self, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды освещения"""
        action = parameters.get("action")
        device_id = parameters.get("device_id")
        
        if action == "turn_on":
            # Включение света
            return True
        elif action == "turn_off":
            # Выключение света
            return True
        elif action == "set_brightness":
            # Установка яркости
            brightness = parameters.get("brightness", 100)
            return 0 <= brightness <= 100
        elif action == "set_color":
            # Установка цвета
            return True
        
        return False
    
    async def _execute_lock_command(self, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды замка"""
        action = parameters.get("action")
        device_id = parameters.get("device_id")
        
        if action == "lock":
            # Блокировка
            return True
        elif action == "unlock":
            # Разблокировка
            return True
        elif action == "toggle":
            # Переключение
            return True
        
        return False
    
    async def _execute_siren_command(self, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды сирены"""
        action = parameters.get("action")
        volume = parameters.get("volume", "medium")
        
        if action == "activate":
            # Активация сирены
            return volume in ["low", "medium", "high"]
        elif action == "deactivate":
            # Деактивация сирены
            return True
        
        return False
    
    async def _execute_camera_command(self, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды камеры"""
        action = parameters.get("action")
        
        if action == "pan":
            # Поворот по горизонтали
            angle = parameters.get("angle", 0)
            return -180 <= angle <= 180
        elif action == "tilt":
            # Поворот по вертикали
            angle = parameters.get("angle", 0)
            return -90 <= angle <= 90
        elif action == "zoom":
            # Зум
            level = parameters.get("level", 1)
            return 1 <= level <= 10
        elif action == "record":
            # Запись
            return True
        
        return False
    
    async def _execute_valve_command(self, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды клапана"""
        action = parameters.get("action")
        
        if action == "open":
            # Открытие клапана
            return True
        elif action == "close":
            # Закрытие клапана
            return True
        elif action == "set_position":
            # Установка позиции
            position = parameters.get("position", 0)
            return 0 <= position <= 100
        
        return False
    
    async def _execute_motor_command(self, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды мотора"""
        action = parameters.get("action")
        
        if action == "start":
            # Запуск мотора
            return True
        elif action == "stop":
            # Остановка мотора
            return True
        elif action == "set_speed":
            # Установка скорости
            speed = parameters.get("speed", 0)
            return 0 <= speed <= 100
        
        return False
    
    async def _execute_turret_command(self, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды турели"""
        action = parameters.get("action")
        
        if action == "aim":
            # Наведение на цель
            x = parameters.get("x", 0)
            y = parameters.get("y", 0)
            return -180 <= x <= 180 and -90 <= y <= 90
        elif action == "track":
            # Слежение за целью
            target_id = parameters.get("target_id")
            return target_id is not None
        elif action == "fire":
            # Стрельба (концептуально)
            return True
        
        return False
    
    async def _execute_system_command(self, parameters: Dict[str, Any]) -> bool:
        """Выполнение системной команды"""
        action = parameters.get("action")
        
        if action == "get_status":
            # Получение статуса системы
            return True
        elif action == "set_mode":
            # Установка режима
            mode = parameters.get("mode")
            return mode in ["home", "away", "night", "vacation"]
        elif action == "emergency":
            # Аварийный режим
            return True
        
        return False
    
    async def _notify_command_subscribers(self, command: LLMCommand):
        """Уведомление подписчиков о командах"""
        for subscriber in self.command_subscribers:
            try:
                await subscriber(command)
            except Exception as e:
                self.logger.error(f"❌ Command subscriber error: {e}")
    
    def subscribe_to_commands(self, callback: Callable):
        """Подписка на команды LLM"""
        self.command_subscribers.append(callback)
    
    def get_command_history(self, limit: int = 50) -> List[LLMCommand]:
        """Получение истории команд"""
        return self.command_history[-limit:] if self.command_history else []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы LLM"""
        total_commands = len(self.command_history)
        successful_commands = len([c for c in self.command_history if c.executed and c.result == "success"])
        failed_commands = len([c for c in self.command_history if c.executed and c.result == "failed"])
        
        # Статистика по типам команд
        command_types = {}
        for cmd in self.command_history:
            cmd_type = cmd.interpreted_command
            command_types[cmd_type] = command_types.get(cmd_type, 0) + 1
        
        return {
            "total_commands": total_commands,
            "successful_commands": successful_commands,
            "failed_commands": failed_commands,
            "command_types": command_types,
            "timestamp": datetime.now().isoformat()
        }
    
    async def update_system_context(self, context: Dict[str, Any]):
        """Обновление контекста системы"""
        self.system_context.update(context)
        self.logger.info(f"🔄 Updated system context: {len(context)} items")
    
    async def clear_context(self):
        """Очистка контекста"""
        self.system_context.clear()
        self.logger.info("🗑️ Cleared system context")
    
    def export_history(self) -> Dict[str, Any]:
        """Экспорт истории команд"""
        return {
            "commands": [
                {
                    "command_id": cmd.command_id,
                    "user_input": cmd.user_input,
                    "interpreted_command": cmd.interpreted_command,
                    "parameters": cmd.parameters,
                    "confidence": cmd.confidence,
                    "timestamp": cmd.timestamp.isoformat(),
                    "executed": cmd.executed,
                    "result": cmd.result,
                    "error": cmd.error
                }
                for cmd in self.command_history
            ]
        } 