"""
Smart Home Module for ΔΣ Stack
Умный дом с интеграцией AI и систем безопасности
"""

from .core import SmartHomeController
from .sensors import SensorManager
from .actuators import ActuatorManager
from .automation import AutomationEngine
from .llm_integration import LLMHomeAssistant

__version__ = "1.0.0"
__all__ = [
    "SmartHomeController",
    "SensorManager", 
    "ActuatorManager",
    "AutomationEngine",
    "LLMHomeAssistant"
] 