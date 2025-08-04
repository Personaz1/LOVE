"""
Smart Home Actuators Manager
Управление актуаторами умного дома
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ActuatorType(Enum):
    """Типы актуаторов"""
    LIGHT = "light"
    LOCK = "lock"
    SIREN = "siren"
    CAMERA = "camera"
    VALVE = "valve"
    MOTOR = "motor"
    HEATER = "heater"
    COOLER = "cooler"
    VENTILATOR = "ventilator"
    BLIND = "blind"
    CURTAIN = "curtain"
    GATE = "gate"
    DOOR = "door"
    WINDOW = "window"
    TURRET = "turret"
    LASER = "laser"
    STROBE = "strobe"
    SPEAKER = "speaker"
    PUMP = "pump"
    COMPRESSOR = "compressor"

@dataclass
class ActuatorConfig:
    """Конфигурация актуатора"""
    actuator_id: str
    actuator_type: ActuatorType
    location: str
    zone: str
    description: str
    enabled: bool = True
    parameters: Dict[str, Any] = None
    safety_limits: Dict[str, Any] = None

@dataclass
class ActuatorStatus:
    """Статус актуатора"""
    actuator_id: str
    state: str
    value: Any = None
    timestamp: datetime = None
    error: str = None

class ActuatorManager:
    """Менеджер актуаторов умного дома"""
    
    def __init__(self):
        self.actuators: Dict[str, ActuatorConfig] = {}
        self.status: Dict[str, ActuatorStatus] = {}
        self.logger = logger
        
        # Подписчики на события актуаторов
        self.status_subscribers: List[callable] = []
        self.command_subscribers: List[callable] = []
        
    async def add_actuator(self, config: ActuatorConfig):
        """Добавление актуатора"""
        self.actuators[config.actuator_id] = config
        self.status[config.actuator_id] = ActuatorStatus(
            actuator_id=config.actuator_id,
            state="unknown",
            timestamp=datetime.now()
        )
        
        self.logger.info(f"✅ Added actuator: {config.actuator_id} ({config.actuator_type.value})")
        
    async def remove_actuator(self, actuator_id: str):
        """Удаление актуатора"""
        if actuator_id in self.actuators:
            del self.actuators[actuator_id]
            del self.status[actuator_id]
            self.logger.info(f"🗑️ Removed actuator: {actuator_id}")
    
    async def send_command(self, actuator_id: str, command: str, parameters: Dict[str, Any] = None):
        """Отправка команды актуатору"""
        if actuator_id not in self.actuators:
            self.logger.warning(f"⚠️ Unknown actuator: {actuator_id}")
            return False
        
        actuator_config = self.actuators[actuator_id]
        
        # Проверка безопасности
        if not await self._check_safety_limits(actuator_config, command, parameters):
            self.logger.error(f"❌ Safety limit exceeded for actuator: {actuator_id}")
            return False
        
        # Выполнение команды
        try:
            result = await self._execute_command(actuator_config, command, parameters)
            
            # Обновление статуса
            await self._update_status(actuator_id, "active" if result else "error")
            
            # Уведомление подписчиков
            await self._notify_command_subscribers(actuator_id, command, parameters, result)
            
            self.logger.info(f"📤 Command sent to {actuator_id}: {command}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Command execution error for {actuator_id}: {e}")
            await self._update_status(actuator_id, "error", error=str(e))
            return False
    
    async def _check_safety_limits(self, config: ActuatorConfig, command: str, parameters: Dict[str, Any]) -> bool:
        """Проверка ограничений безопасности"""
        if not config.safety_limits:
            return True
        
        limits = config.safety_limits
        
        # Проверка команды
        if "allowed_commands" in limits and command not in limits["allowed_commands"]:
            self.logger.warning(f"⚠️ Command {command} not allowed for {config.actuator_id}")
            return False
        
        # Проверка параметров
        if parameters and "max_values" in limits:
            for param, value in parameters.items():
                if param in limits["max_values"]:
                    max_value = limits["max_values"][param]
                    if value > max_value:
                        self.logger.warning(f"⚠️ Parameter {param}={value} exceeds max {max_value}")
                        return False
        
        return True
    
    async def _execute_command(self, config: ActuatorConfig, command: str, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды актуатора"""
        actuator_type = config.actuator_type
        
        try:
            if actuator_type == ActuatorType.LIGHT:
                return await self._execute_light_command(config, command, parameters)
            elif actuator_type == ActuatorType.LOCK:
                return await self._execute_lock_command(config, command, parameters)
            elif actuator_type == ActuatorType.SIREN:
                return await self._execute_siren_command(config, command, parameters)
            elif actuator_type == ActuatorType.CAMERA:
                return await self._execute_camera_command(config, command, parameters)
            elif actuator_type == ActuatorType.VALVE:
                return await self._execute_valve_command(config, command, parameters)
            elif actuator_type == ActuatorType.MOTOR:
                return await self._execute_motor_command(config, command, parameters)
            elif actuator_type == ActuatorType.TURRET:
                return await self._execute_turret_command(config, command, parameters)
            else:
                # Общий обработчик для других типов
                return await self._execute_generic_command(config, command, parameters)
                
        except Exception as e:
            self.logger.error(f"❌ Command execution error: {e}")
            return False
    
    async def _execute_light_command(self, config: ActuatorConfig, command: str, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды освещения"""
        if command == "turn_on":
            # Включение света
            return True
        elif command == "turn_off":
            # Выключение света
            return True
        elif command == "set_brightness":
            # Установка яркости
            brightness = parameters.get("brightness", 100)
            return 0 <= brightness <= 100
        elif command == "set_color":
            # Установка цвета
            return True
        else:
            return False
    
    async def _execute_lock_command(self, config: ActuatorConfig, command: str, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды замка"""
        if command == "lock":
            # Блокировка
            return True
        elif command == "unlock":
            # Разблокировка
            return True
        elif command == "toggle":
            # Переключение состояния
            return True
        else:
            return False
    
    async def _execute_siren_command(self, config: ActuatorConfig, command: str, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды сирены"""
        if command == "activate":
            # Активация сирены
            volume = parameters.get("volume", "medium")
            return volume in ["low", "medium", "high"]
        elif command == "deactivate":
            # Деактивация сирены
            return True
        elif command == "set_pattern":
            # Установка паттерна
            pattern = parameters.get("pattern", "continuous")
            return pattern in ["continuous", "intermittent", "emergency"]
        else:
            return False
    
    async def _execute_camera_command(self, config: ActuatorConfig, command: str, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды камеры"""
        if command == "pan":
            # Поворот по горизонтали
            angle = parameters.get("angle", 0)
            return -180 <= angle <= 180
        elif command == "tilt":
            # Поворот по вертикали
            angle = parameters.get("angle", 0)
            return -90 <= angle <= 90
        elif command == "zoom":
            # Зум
            level = parameters.get("level", 1)
            return 1 <= level <= 10
        elif command == "record":
            # Запись
            return True
        else:
            return False
    
    async def _execute_valve_command(self, config: ActuatorConfig, command: str, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды клапана"""
        if command == "open":
            # Открытие клапана
            return True
        elif command == "close":
            # Закрытие клапана
            return True
        elif command == "set_position":
            # Установка позиции
            position = parameters.get("position", 0)
            return 0 <= position <= 100
        else:
            return False
    
    async def _execute_motor_command(self, config: ActuatorConfig, command: str, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды мотора"""
        if command == "start":
            # Запуск мотора
            return True
        elif command == "stop":
            # Остановка мотора
            return True
        elif command == "set_speed":
            # Установка скорости
            speed = parameters.get("speed", 0)
            return 0 <= speed <= 100
        else:
            return False
    
    async def _execute_turret_command(self, config: ActuatorConfig, command: str, parameters: Dict[str, Any]) -> bool:
        """Выполнение команды турели"""
        if command == "aim":
            # Наведение на цель
            x = parameters.get("x", 0)
            y = parameters.get("y", 0)
            return -180 <= x <= 180 and -90 <= y <= 90
        elif command == "track":
            # Слежение за целью
            target_id = parameters.get("target_id")
            return target_id is not None
        elif command == "fire":
            # Стрельба (концептуально)
            return True
        else:
            return False
    
    async def _execute_generic_command(self, config: ActuatorConfig, command: str, parameters: Dict[str, Any]) -> bool:
        """Общий обработчик команд"""
        # Базовая реализация для неизвестных типов актуаторов
        return True
    
    async def _update_status(self, actuator_id: str, state: str, value: Any = None, error: str = None):
        """Обновление статуса актуатора"""
        self.status[actuator_id] = ActuatorStatus(
            actuator_id=actuator_id,
            state=state,
            value=value,
            timestamp=datetime.now(),
            error=error
        )
        
        await self._notify_status_subscribers(actuator_id, self.status[actuator_id])
    
    async def _notify_status_subscribers(self, actuator_id: str, status: ActuatorStatus):
        """Уведомление подписчиков о статусе"""
        for subscriber in self.status_subscribers:
            try:
                await subscriber(actuator_id, status)
            except Exception as e:
                self.logger.error(f"❌ Status subscriber error: {e}")
    
    async def _notify_command_subscribers(self, actuator_id: str, command: str, parameters: Dict, result: bool):
        """Уведомление подписчиков о командах"""
        for subscriber in self.command_subscribers:
            try:
                await subscriber(actuator_id, command, parameters, result)
            except Exception as e:
                self.logger.error(f"❌ Command subscriber error: {e}")
    
    def get_actuator_config(self, actuator_id: str) -> Optional[ActuatorConfig]:
        """Получение конфигурации актуатора"""
        return self.actuators.get(actuator_id)
    
    def get_actuator_status(self, actuator_id: str) -> Optional[ActuatorStatus]:
        """Получение статуса актуатора"""
        return self.status.get(actuator_id)
    
    def get_actuators_by_type(self, actuator_type: ActuatorType) -> List[ActuatorConfig]:
        """Получение актуаторов по типу"""
        return [config for config in self.actuators.values() if config.actuator_type == actuator_type]
    
    def get_actuators_by_zone(self, zone: str) -> List[ActuatorConfig]:
        """Получение актуаторов по зоне"""
        return [config for config in self.actuators.values() if config.zone == zone]
    
    def get_actuators_by_location(self, location: str) -> List[ActuatorConfig]:
        """Получение актуаторов по местоположению"""
        return [config for config in self.actuators.values() if config.location == location]
    
    def subscribe_to_status(self, callback: callable):
        """Подписка на статус актуаторов"""
        self.status_subscribers.append(callback)
    
    def subscribe_to_commands(self, callback: callable):
        """Подписка на команды актуаторов"""
        self.command_subscribers.append(callback)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы актуаторов"""
        total_actuators = len(self.actuators)
        active_actuators = len([a for a in self.actuators.values() if a.enabled])
        error_actuators = len([s for s in self.status.values() if s.state == "error"])
        
        # Статистика по типам актуаторов
        type_stats = {}
        for actuator_type in ActuatorType:
            count = len(self.get_actuators_by_type(actuator_type))
            if count > 0:
                type_stats[actuator_type.value] = count
        
        return {
            "total_actuators": total_actuators,
            "active_actuators": active_actuators,
            "error_actuators": error_actuators,
            "actuator_types": type_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    async def enable_actuator(self, actuator_id: str):
        """Включение актуатора"""
        if actuator_id in self.actuators:
            self.actuators[actuator_id].enabled = True
            self.logger.info(f"✅ Enabled actuator: {actuator_id}")
    
    async def disable_actuator(self, actuator_id: str):
        """Отключение актуатора"""
        if actuator_id in self.actuators:
            self.actuators[actuator_id].enabled = False
            self.logger.info(f"❌ Disabled actuator: {actuator_id}")
    
    def export_config(self) -> Dict[str, Any]:
        """Экспорт конфигурации"""
        return {
            "actuators": {
                actuator_id: {
                    "actuator_type": config.actuator_type.value,
                    "location": config.location,
                    "zone": config.zone,
                    "description": config.description,
                    "enabled": config.enabled,
                    "parameters": config.parameters,
                    "safety_limits": config.safety_limits
                }
                for actuator_id, config in self.actuators.items()
            }
        }
    
    async def import_config(self, config_data: Dict[str, Any]):
        """Импорт конфигурации"""
        actuators_data = config_data.get("actuators", {})
        
        for actuator_id, actuator_config in actuators_data.items():
            config = ActuatorConfig(
                actuator_id=actuator_id,
                actuator_type=ActuatorType(actuator_config["actuator_type"]),
                location=actuator_config["location"],
                zone=actuator_config["zone"],
                description=actuator_config["description"],
                enabled=actuator_config.get("enabled", True),
                parameters=actuator_config.get("parameters"),
                safety_limits=actuator_config.get("safety_limits")
            )
            
            await self.add_actuator(config)
        
        self.logger.info(f"📥 Imported {len(actuators_data)} actuators") 