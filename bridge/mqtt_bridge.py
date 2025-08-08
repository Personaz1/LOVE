from __future__ import annotations

import json
import logging
from typing import Callable, Optional

try:
    import paho.mqtt.client as mqtt
except Exception:  # pragma: no cover
    mqtt = None


logger = logging.getLogger(__name__)


class MqttBridge:
    def __init__(self, host: str = "localhost", port: int = 1883, client_id: str = "guardian_bridge") -> None:
        self.host = host
        self.port = port
        self.client_id = client_id
        self._client: Optional["mqtt.Client"] = None
        self._connected: bool = False

    def connect(self) -> bool:
        if mqtt is None:
            logger.warning("paho-mqtt is not available; running in no-op mode")
            return False
        try:
            self._client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv5)
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            self._client.connect(self.host, self.port, keepalive=30)
            self._client.loop_start()
            return True
        except Exception as e:  # pragma: no cover (external dependency)
            logger.warning(f"MQTT connect failed: {e}")
            self._client = None
            self._connected = False
            return False

    def is_connected(self) -> bool:
        return self._connected

    def subscribe(self, topic: str, handler: Callable[[str, dict], None]) -> None:
        if not self._client:
            return
        self._client.subscribe(topic)

        def _handler(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
            except Exception:
                payload = {}
            handler(msg.topic, payload)

        # attach per-topic message callback
        self._client.message_callback_add(topic, _handler)

    def publish_json(self, topic: str, payload: dict, qos: int = 1) -> bool:
        if not self._client:
            return False
        try:
            self._client.publish(topic, json.dumps(payload), qos=qos)
            return True
        except Exception as e:  # pragma: no cover
            logger.warning(f"MQTT publish failed: {e}")
            return False

    # internal callbacks
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        self._connected = True
        logger.info(f"✅ MQTT connected: {self.host}:{self.port}")

    def _on_disconnect(self, client, userdata, reason_code, properties=None):
        self._connected = False
        logger.warning("🔌 MQTT disconnected")

    def _on_message(self, client, userdata, msg):
        # default handler is unused; per-topic handlers are attached via message_callback_add
        pass


