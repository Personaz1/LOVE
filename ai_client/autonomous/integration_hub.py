"""
Integration Hub
- Wires SmartHome components (sensors, actuators, automations, LLM) together
- Provides a unified async event bus for sensor/actuator updates
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any, Callable

from ai_client.smart_home import (
    SmartHomeController,
    SensorManager,
    ActuatorManager,
    AutomationEngine,
    LLMHomeAssistant,
)
from ai_client.core.client import AIClient


logger = logging.getLogger(__name__)


class IntegrationHub:
    """Central wiring for smart home subsystems."""

    def __init__(self, ai_client: Optional[AIClient] = None) -> None:
        self.ai_client: AIClient = ai_client or AIClient()

        # Subsystems
        self.sensors = SensorManager()
        self.actuators = ActuatorManager()
        self.automations = AutomationEngine()
        self.controller = SmartHomeController()
        self.llm = LLMHomeAssistant(self.ai_client)

        # Async lifecycle
        self._started: bool = False
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._started:
                return

            # Subscribe internal bridges
            await self._wire_subsystems()

            # Initialize controller (starts MQTT and monitoring)
            await self.controller.initialize()

            self._started = True
            logger.info("✅ IntegrationHub started")

    async def stop(self) -> None:
        async with self._lock:
            if not self._started:
                return

            await self.controller.shutdown()
            self._started = False
            logger.info("🔻 IntegrationHub stopped")

    async def _wire_subsystems(self) -> None:
        """Connect callbacks between subsystems."""

        # 1) Sensor alerts feed controller security events
        async def on_sensor_alert(alert: Dict[str, Any]) -> None:
            try:
                event_payload = {
                    "event_type": f"sensor_alert:{alert.get('alert_type','unknown')}",
                    "sensor_id": alert.get("sensor_id"),
                    "sensor_type": alert.get("sensor_type"),
                    "message": alert.get("message"),
                    "value": alert.get("value"),
                    "timestamp": alert.get("timestamp"),
                }
                await self.controller._notify_subscribers("sensor_alert", event_payload)
            except Exception as e:
                logger.error(f"IntegrationHub alert bridge error: {e}")

        self.sensors.subscribe_to_alerts(on_sensor_alert)

        # 2) LLM commands can be observed to trigger automations or direct actuator calls later
        async def on_llm_command(cmd) -> None:  # LLMCommand
            try:
                await self.controller._notify_subscribers(
                    "llm_command",
                    {
                        "command_id": cmd.command_id,
                        "type": cmd.interpreted_command,
                        "parameters": cmd.parameters,
                        "confidence": cmd.confidence,
                        "timestamp": cmd.timestamp.isoformat(),
                    },
                )
            except Exception as e:
                logger.error(f"IntegrationHub LLM bridge error: {e}")

        self.llm.subscribe_to_commands(on_llm_command)

        # 3) Automations execution subscriber (for logging/telemetry)
        async def on_rule_exec(exec_data: Dict[str, Any]) -> None:
            logger.info(
                f"🎛️ Automation executed: {exec_data.get('rule_name')} success={exec_data.get('success')}"
            )

        self.automations.subscribe_to_executions(on_rule_exec)

        # 4) Route automation actuator actions through ActuatorManager
        async def actuator_command_handler(actuator_id: str, command: str, parameters: Dict[str, Any]):
            await self.actuators.send_command(actuator_id, command, parameters)

        self.automations.actuator_command_handler = actuator_command_handler

        # 5) Bridge SmartHomeController automation list to AutomationEngine (optional)
        #    Here we keep them separate but allow controller to forward events later

        # Feed controller events to automation engine
        async def controller_event_bridge(event_type: str, data: Dict[str, Any]):
            context = {"event_type": event_type, "event_data": data, **(data if isinstance(data, dict) else {})}
            await self.automations.process_event(event_type, context)

        self.controller.subscribe_to_events(controller_event_bridge)

    # Public accessors for external modules (web app, background loop)
    def get_status_snapshot(self) -> Dict[str, Any]:
        return {
            "controller": self.controller.get_system_status(),
            "sensors": self.sensors.get_system_status(),
            "actuators": self.actuators.get_system_status(),
            "automations": self.automations.get_system_status(),
            "llm": self.llm.get_system_status(),
        }


