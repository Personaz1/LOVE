import os
import socket
import time

import pytest

from bridge.mqtt_bridge import MqttBridge


def _port_open(host: str, port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


@pytest.mark.integration
def test_mqtt_publish_subscribe():
    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    if not _port_open(host, port):
        pytest.skip("MQTT broker not available on localhost:1883")

    bridge = MqttBridge(host=host, port=port)
    assert bridge.connect() is True

    received = {}

    def handler(topic: str, payload: dict):
        received["topic"] = topic
        received["payload"] = payload

    topic = "sim/test/topic"
    bridge.subscribe(topic, handler)
    ok = bridge.publish_json(topic, {"hello": "world"})
    assert ok is True

    # wait briefly for message loop
    for _ in range(20):
        if received:
            break
        time.sleep(0.05)

    assert received.get("payload", {}).get("hello") == "world"


