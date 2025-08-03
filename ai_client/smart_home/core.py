"""
Smart Home Core Controller
Центральный контроллер умного дома с AI интеграцией
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

import paho.mqtt.client as mqtt
from ai_client.utils.cache import system_cache

logger = logging.getLogger(__name__)

class SecurityMode(Enum):
    """Режимы безопасности"""
    DISARMED = "disarmed"
    ARMED_HOME = "armed_home" 
    ARMED_AWAY = "armed_away"
    ARMED_NIGHT = "armed_night"
    LOCKDOWN = "lockdown"

@dataclass
class SensorData:
    """Данные сенсора"""
    sensor_id: str
    sensor_type: str
    value: Any
    timestamp: datetime
    location: str
    zone: str
    status: str = "normal"

@dataclass
class ActuatorCommand:
    """Команда актуатору"""
    actuator_id: str
    command: str
    parameters: Dict[str, Any]
    priority: int = 1
    timestamp: datetime = None

class SmartHomeController:
    """Центральный контроллер умного дома"""
    
    def __init__(self, mqtt_broker: str = "localhost", mqtt_port: int = 1883):
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        
        # Состояние системы
        self.security_mode = SecurityMode.DISARMED
        self.sensors: Dict[str, SensorData] = {}
        self.actuators: Dict[str, Any] = {}
        self.automations: List[Dict] = []
        
        # Подписчики на события
        self.event_subscribers: List[Callable] = []
        
        # Кэш для быстрого доступа
        self.cache = system_cache
        
        # Логирование
        self.logger = logger
        
    async def initialize(self):
        """Инициализация контроллера"""
        try:
            # Подключение к MQTT
            await self._setup_mqtt()
            
            # Загрузка конфигурации
            await self._load_config()
            
            # Запуск мониторинга
            asyncio.create_task(self._monitor_system())
            
            self.logger.info("✅ Smart Home Controller initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Smart Home Controller: {e}")
            raise
    
    async def _setup_mqtt(self):
        """Setup MQTT connection with error handling"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_message = self._on_mqtt_message
            
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            # Подписки на топики
            topics = [
                "smart_home/sensors/+/data",
                "smart_home/actuators/+/status", 
                "smart_home/security/events",
                "smart_home/automation/triggers"
            ]
            
            for topic in topics:
                self.mqtt_client.subscribe(topic)
                
            logger.info(f"✅ MQTT connected to {self.mqtt_broker}:{self.mqtt_port}")
        except Exception as e:
            logger.warning(f"⚠️ MQTT connection failed: {e}")
            logger.info("ℹ️ Smart Home will work without MQTT connection")
            # Don't raise exception - allow system to continue without MQTT
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Обработчик подключения MQTT"""
        self.logger.info(f"✅ Connected to MQTT broker: {self.mqtt_broker}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Обработчик сообщений MQTT"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Создаем задачу для асинхронной обработки
            asyncio.create_task(self._process_mqtt_message(topic, payload))
                
        except Exception as e:
            self.logger.error(f"❌ MQTT message processing error: {e}")
    
    async def _process_mqtt_message(self, topic: str, payload: Dict):
        """Асинхронная обработка MQTT сообщений"""
        try:
            # Обработка данных сенсоров
            if "sensors" in topic and "data" in topic:
                await self._handle_sensor_data(payload)
            
            # Обработка статуса актуаторов
            elif "actuators" in topic and "status" in topic:
                await self._handle_actuator_status(payload)
            
            # Обработка событий безопасности
            elif "security/events" in topic:
                await self._handle_security_event(payload)
                
        except Exception as e:
            self.logger.error(f"❌ MQTT message processing error: {e}")
    
    async def _handle_sensor_data(self, data: Dict):
        """Обработка данных сенсора"""
        sensor_id = data.get("sensor_id")
        sensor_data = SensorData(
            sensor_id=sensor_id,
            sensor_type=data.get("type"),
            value=data.get("value"),
            timestamp=datetime.fromisoformat(data.get("timestamp")),
            location=data.get("location"),
            zone=data.get("zone"),
            status=data.get("status", "normal")
        )
        
        # Обновление кэша
        self.sensors[sensor_id] = sensor_data
        await self._cache_sensor_data(sensor_data)
        
        # Проверка автоматизаций
        await self._check_automations(sensor_data)
        
        # Уведомление подписчиков
        await self._notify_subscribers("sensor_update", sensor_data)
    
    async def _handle_actuator_status(self, data: Dict):
        """Обработка статуса актуатора"""
        actuator_id = data.get("actuator_id")
        self.actuators[actuator_id] = data
        
        await self._notify_subscribers("actuator_update", data)
    
    async def _handle_security_event(self, data: Dict):
        """Обработка события безопасности"""
        event_type = data.get("event_type")
        
        if event_type == "intrusion_detected":
            await self._handle_intrusion(data)
        elif event_type == "fire_detected":
            await self._handle_fire(data)
        elif event_type == "gas_leak":
            await self._handle_gas_leak(data)
    
    async def _handle_intrusion(self, data: Dict):
        """Обработка вторжения"""
        self.logger.warning("🚨 INTRUSION DETECTED")
        
        # Активация режима тревоги
        await self.set_security_mode(SecurityMode.LOCKDOWN)
        
        # Включение сирен и прожекторов
        await self._activate_alarm_system()
        
        # Отправка уведомлений
        await self._send_notifications("🚨 Вторжение обнаружено!")
    
    async def _handle_fire(self, data: Dict):
        """Обработка пожара"""
        self.logger.warning("🔥 FIRE DETECTED")
        
        # Отключение газа
        await self._shut_off_gas()
        
        # Разблокировка всех выходов
        await self._unlock_all_exits()
        
        # Отправка уведомлений
        await self._send_notifications("🔥 Обнаружен пожар!")
    
    async def _handle_gas_leak(self, data: Dict):
        """Обработка утечки газа"""
        self.logger.warning("⚠️ GAS LEAK DETECTED")
        
        # Отключение газа
        await self._shut_off_gas()
        
        # Включение вентиляции
        await self._activate_ventilation()
        
        # Отправка уведомлений
        await self._send_notifications("⚠️ Обнаружена утечка газа!")
    
    async def set_security_mode(self, mode: SecurityMode):
        """Установка режима безопасности"""
        self.security_mode = mode
        self.logger.info(f"🔒 Security mode changed to: {mode.value}")
        
        # Публикация в MQTT
        self.mqtt_client.publish(
            "smart_home/security/mode",
            json.dumps({"mode": mode.value, "timestamp": datetime.now().isoformat()})
        )
        
        await self._notify_subscribers("security_mode_change", {"mode": mode.value})
    
    async def _activate_alarm_system(self):
        """Активация системы тревоги"""
        commands = [
            ActuatorCommand("siren_main", "activate", {"volume": "high"}),
            ActuatorCommand("strobe_lights", "activate", {"pattern": "emergency"}),
            ActuatorCommand("spotlights", "activate", {"brightness": "max"})
        ]
        
        for cmd in commands:
            await self._send_actuator_command(cmd)
    
    async def _shut_off_gas(self):
        """Отключение газа"""
        cmd = ActuatorCommand("gas_valve", "close", {})
        await self._send_actuator_command(cmd)
    
    async def _unlock_all_exits(self):
        """Разблокировка всех выходов"""
        exits = ["front_door", "back_door", "garage_door", "emergency_exit"]
        
        for exit_id in exits:
            cmd = ActuatorCommand(exit_id, "unlock", {})
            await self._send_actuator_command(cmd)
    
    async def _activate_ventilation(self):
        """Активация вентиляции"""
        cmd = ActuatorCommand("ventilation_system", "activate", {"mode": "emergency"})
        await self._send_actuator_command(cmd)
    
    async def _send_actuator_command(self, command: ActuatorCommand):
        """Отправка команды актуатору"""
        if command.timestamp is None:
            command.timestamp = datetime.now()
        
        payload = asdict(command)
        payload["timestamp"] = command.timestamp.isoformat()
        
        topic = f"smart_home/actuators/{command.actuator_id}/command"
        self.mqtt_client.publish(topic, json.dumps(payload))
        
        self.logger.info(f"📤 Sent command to {command.actuator_id}: {command.command}")
    
    async def _cache_sensor_data(self, sensor_data: SensorData):
        """Кэширование данных сенсора"""
        cache_key = f"sensor_{sensor_data.sensor_id}"
        await self.cache.set(
            "smart_home_sensor",
            asdict(sensor_data),
            {"sensor_id": sensor_data.sensor_id},
            ttl_seconds=3600
        )
    
    async def _check_automations(self, sensor_data: SensorData):
        """Проверка автоматизаций"""
        for automation in self.automations:
            if await self._evaluate_automation_condition(automation, sensor_data):
                await self._execute_automation(automation)
    
    async def _evaluate_automation_condition(self, automation: Dict, sensor_data: SensorData) -> bool:
        """Оценка условия автоматизации"""
        condition = automation.get("condition", {})
        
        # Простая проверка по типу сенсора и значению
        if condition.get("sensor_type") == sensor_data.sensor_type:
            if condition.get("value") == sensor_data.value:
                return True
        
        return False
    
    async def _execute_automation(self, automation: Dict):
        """Выполнение автоматизации"""
        actions = automation.get("actions", [])
        
        for action in actions:
            actuator_id = action.get("actuator_id")
            command = action.get("command")
            parameters = action.get("parameters", {})
            
            cmd = ActuatorCommand(actuator_id, command, parameters)
            await self._send_actuator_command(cmd)
    
    async def _notify_subscribers(self, event_type: str, data: Any):
        """Уведомление подписчиков"""
        for subscriber in self.event_subscribers:
            try:
                await subscriber(event_type, data)
            except Exception as e:
                self.logger.error(f"❌ Subscriber notification error: {e}")
    
    async def _send_notifications(self, message: str):
        """Отправка уведомлений"""
        # Здесь интеграция с системой уведомлений
        self.logger.info(f"📱 Notification: {message}")
    
    async def _load_config(self):
        """Загрузка конфигурации"""
        # Загрузка из файла или базы данных
        pass
    
    async def _monitor_system(self):
        """Мониторинг системы"""
        while True:
            try:
                # Проверка состояния сенсоров
                await self._check_sensor_health()
                
                # Проверка состояния актуаторов
                await self._check_actuator_health()
                
                await asyncio.sleep(30)  # Проверка каждые 30 секунд
                
            except Exception as e:
                self.logger.error(f"❌ System monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_sensor_health(self):
        """Проверка здоровья сенсоров"""
        current_time = datetime.now()
        
        for sensor_id, sensor_data in self.sensors.items():
            # Проверка актуальности данных (не старше 5 минут)
            if (current_time - sensor_data.timestamp) > timedelta(minutes=5):
                self.logger.warning(f"⚠️ Sensor {sensor_id} data is stale")
    
    async def _check_actuator_health(self):
        """Проверка здоровья актуаторов"""
        # Проверка доступности актуаторов
        pass
    
    def subscribe_to_events(self, callback: Callable):
        """Подписка на события"""
        self.event_subscribers.append(callback)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        return {
            "security_mode": self.security_mode.value,
            "sensors_count": len(self.sensors),
            "actuators_count": len(self.actuators),
            "automations_count": len(self.automations),
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Завершение работы контроллера"""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        self.logger.info("🔄 Smart Home Controller shutdown complete") 

    def publish_message(self, topic: str, message: str):
        """Publish message to MQTT topic with connection check"""
        try:
            if hasattr(self, 'mqtt_client') and self.mqtt_client:
                self.mqtt_client.publish(topic, message)
                logger.info(f"📡 MQTT published to {topic}: {message}")
            else:
                logger.warning(f"⚠️ MQTT not connected, skipping publish to {topic}")
        except Exception as e:
            logger.error(f"❌ MQTT publish error: {e}") 