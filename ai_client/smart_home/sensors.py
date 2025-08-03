"""
Smart Home Sensors Manager
Управление сенсорами умного дома
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class SensorType(Enum):
    """Типы сенсоров"""
    MOTION = "motion"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    LIGHT = "light"
    SOUND = "sound"
    VIBRATION = "vibration"
    GAS = "gas"
    SMOKE = "smoke"
    DOOR = "door"
    WINDOW = "window"
    WATER_LEAK = "water_leak"
    ELECTRICITY = "electricity"
    MAGNETIC = "magnetic"
    INFRARED = "infrared"
    ULTRASONIC = "ultrasonic"
    LIDAR = "lidar"
    THERMAL = "thermal"
    RADAR = "radar"

@dataclass
class SensorConfig:
    """Конфигурация сенсора"""
    sensor_id: str
    sensor_type: SensorType
    location: str
    zone: str
    description: str
    enabled: bool = True
    calibration: Dict[str, Any] = None
    thresholds: Dict[str, Any] = None

@dataclass
class SensorReading:
    """Показания сенсора"""
    sensor_id: str
    value: Any
    unit: str
    timestamp: datetime
    quality: float = 1.0
    status: str = "normal"

class SensorManager:
    """Менеджер сенсоров умного дома"""
    
    def __init__(self):
        self.sensors: Dict[str, SensorConfig] = {}
        self.readings: Dict[str, List[SensorReading]] = {}
        self.logger = logger
        
        # Подписчики на события сенсоров
        self.reading_subscribers: List[callable] = []
        self.alert_subscribers: List[callable] = []
        
    async def add_sensor(self, config: SensorConfig):
        """Добавление сенсора"""
        self.sensors[config.sensor_id] = config
        self.readings[config.sensor_id] = []
        
        self.logger.info(f"✅ Added sensor: {config.sensor_id} ({config.sensor_type.value})")
        
    async def remove_sensor(self, sensor_id: str):
        """Удаление сенсора"""
        if sensor_id in self.sensors:
            del self.sensors[sensor_id]
            del self.readings[sensor_id]
            self.logger.info(f"🗑️ Removed sensor: {sensor_id}")
    
    async def update_reading(self, sensor_id: str, value: Any, unit: str = "", quality: float = 1.0):
        """Обновление показаний сенсора"""
        if sensor_id not in self.sensors:
            self.logger.warning(f"⚠️ Unknown sensor: {sensor_id}")
            return
        
        sensor_config = self.sensors[sensor_id]
        reading = SensorReading(
            sensor_id=sensor_id,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            quality=quality
        )
        
        # Добавление показания в историю
        self.readings[sensor_id].append(reading)
        
        # Ограничение истории (последние 1000 показаний)
        if len(self.readings[sensor_id]) > 1000:
            self.readings[sensor_id] = self.readings[sensor_id][-1000:]
        
        # Проверка пороговых значений
        await self._check_thresholds(sensor_config, reading)
        
        # Уведомление подписчиков
        await self._notify_reading_subscribers(reading)
        
        self.logger.debug(f"📊 Sensor {sensor_id}: {value} {unit}")
    
    async def _check_thresholds(self, config: SensorConfig, reading: SensorReading):
        """Проверка пороговых значений"""
        if not config.thresholds:
            return
        
        thresholds = config.thresholds
        value = reading.value
        
        # Проверка минимального значения
        if "min" in thresholds and value < thresholds["min"]:
            await self._trigger_alert(config, reading, "below_min", f"Value {value} below minimum {thresholds['min']}")
        
        # Проверка максимального значения
        if "max" in thresholds and value > thresholds["max"]:
            await self._trigger_alert(config, reading, "above_max", f"Value {value} above maximum {thresholds['max']}")
        
        # Проверка критического значения
        if "critical" in thresholds and value >= thresholds["critical"]:
            await self._trigger_alert(config, reading, "critical", f"Critical value reached: {value}")
    
    async def _trigger_alert(self, config: SensorConfig, reading: SensorReading, alert_type: str, message: str):
        """Срабатывание тревоги"""
        alert_data = {
            "sensor_id": config.sensor_id,
            "sensor_type": config.sensor_type.value,
            "location": config.location,
            "zone": config.zone,
            "alert_type": alert_type,
            "message": message,
            "value": reading.value,
            "timestamp": reading.timestamp.isoformat()
        }
        
        self.logger.warning(f"🚨 Sensor alert: {message}")
        await self._notify_alert_subscribers(alert_data)
    
    async def _notify_reading_subscribers(self, reading: SensorReading):
        """Уведомление подписчиков о показаниях"""
        for subscriber in self.reading_subscribers:
            try:
                await subscriber(reading)
            except Exception as e:
                self.logger.error(f"❌ Reading subscriber error: {e}")
    
    async def _notify_alert_subscribers(self, alert_data: Dict):
        """Уведомление подписчиков о тревогах"""
        for subscriber in self.alert_subscribers:
            try:
                await subscriber(alert_data)
            except Exception as e:
                self.logger.error(f"❌ Alert subscriber error: {e}")
    
    def get_sensor_config(self, sensor_id: str) -> Optional[SensorConfig]:
        """Получение конфигурации сенсора"""
        return self.sensors.get(sensor_id)
    
    def get_latest_reading(self, sensor_id: str) -> Optional[SensorReading]:
        """Получение последнего показания сенсора"""
        readings = self.readings.get(sensor_id, [])
        return readings[-1] if readings else None
    
    def get_readings_history(self, sensor_id: str, hours: int = 24) -> List[SensorReading]:
        """Получение истории показаний"""
        readings = self.readings.get(sensor_id, [])
        if not readings:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [r for r in readings if r.timestamp >= cutoff_time]
    
    def get_sensors_by_type(self, sensor_type: SensorType) -> List[SensorConfig]:
        """Получение сенсоров по типу"""
        return [config for config in self.sensors.values() if config.sensor_type == sensor_type]
    
    def get_sensors_by_zone(self, zone: str) -> List[SensorConfig]:
        """Получение сенсоров по зоне"""
        return [config for config in self.sensors.values() if config.zone == zone]
    
    def get_sensors_by_location(self, location: str) -> List[SensorConfig]:
        """Получение сенсоров по местоположению"""
        return [config for config in self.sensors.values() if config.location == location]
    
    def subscribe_to_readings(self, callback: callable):
        """Подписка на показания сенсоров"""
        self.reading_subscribers.append(callback)
    
    def subscribe_to_alerts(self, callback: callable):
        """Подписка на тревоги сенсоров"""
        self.alert_subscribers.append(callback)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы сенсоров"""
        total_sensors = len(self.sensors)
        active_sensors = len([s for s in self.sensors.values() if s.enabled])
        
        # Статистика по типам сенсоров
        type_stats = {}
        for sensor_type in SensorType:
            count = len(self.get_sensors_by_type(sensor_type))
            if count > 0:
                type_stats[sensor_type.value] = count
        
        return {
            "total_sensors": total_sensors,
            "active_sensors": active_sensors,
            "sensor_types": type_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    async def calibrate_sensor(self, sensor_id: str, calibration_data: Dict[str, Any]):
        """Калибровка сенсора"""
        if sensor_id not in self.sensors:
            raise ValueError(f"Unknown sensor: {sensor_id}")
        
        self.sensors[sensor_id].calibration = calibration_data
        self.logger.info(f"🔧 Calibrated sensor: {sensor_id}")
    
    async def set_thresholds(self, sensor_id: str, thresholds: Dict[str, Any]):
        """Установка пороговых значений"""
        if sensor_id not in self.sensors:
            raise ValueError(f"Unknown sensor: {sensor_id}")
        
        self.sensors[sensor_id].thresholds = thresholds
        self.logger.info(f"⚙️ Set thresholds for sensor: {sensor_id}")
    
    async def enable_sensor(self, sensor_id: str):
        """Включение сенсора"""
        if sensor_id in self.sensors:
            self.sensors[sensor_id].enabled = True
            self.logger.info(f"✅ Enabled sensor: {sensor_id}")
    
    async def disable_sensor(self, sensor_id: str):
        """Отключение сенсора"""
        if sensor_id in self.sensors:
            self.sensors[sensor_id].enabled = False
            self.logger.info(f"❌ Disabled sensor: {sensor_id}")
    
    def export_config(self) -> Dict[str, Any]:
        """Экспорт конфигурации"""
        return {
            "sensors": {
                sensor_id: {
                    "sensor_type": config.sensor_type.value,
                    "location": config.location,
                    "zone": config.zone,
                    "description": config.description,
                    "enabled": config.enabled,
                    "calibration": config.calibration,
                    "thresholds": config.thresholds
                }
                for sensor_id, config in self.sensors.items()
            }
        }
    
    async def import_config(self, config_data: Dict[str, Any]):
        """Импорт конфигурации"""
        sensors_data = config_data.get("sensors", {})
        
        for sensor_id, sensor_config in sensors_data.items():
            config = SensorConfig(
                sensor_id=sensor_id,
                sensor_type=SensorType(sensor_config["sensor_type"]),
                location=sensor_config["location"],
                zone=sensor_config["zone"],
                description=sensor_config["description"],
                enabled=sensor_config.get("enabled", True),
                calibration=sensor_config.get("calibration"),
                thresholds=sensor_config.get("thresholds")
            )
            
            await self.add_sensor(config)
        
        self.logger.info(f"📥 Imported {len(sensors_data)} sensors") 