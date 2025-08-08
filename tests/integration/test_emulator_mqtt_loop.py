import os
import socket
import time

import pytest

from bridge.mqtt_bridge import MqttBridge
from bridge.topics import SIM_STEP, SIM_STEPPED, SENSOR_DATA, ACTUATOR_CMD, ACTUATOR_STATUS
from sim.emulator.mqtt_loop import EmulatorMqttApp


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
def test_emulator_step_ack_and_sensor():
    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    if not _port_open(host, port):
        pytest.skip("MQTT broker not available on localhost:1883")

    app = EmulatorMqttApp(host=host, port=port)
    app.start(seed=1)

    bridge = MqttBridge(host=host, port=port, client_id="test_client")
    assert bridge.connect() is True

    got_ack = {}
    got_sensor = {}

    def on_ack(topic, payload):
        got_ack.update(payload)

    def on_sensor(topic, payload):
        got_sensor.update(payload)

    bridge.subscribe(SIM_STEPPED, on_ack)
    bridge.subscribe(SENSOR_DATA.format(sensor_type="door", sensor_id="door_1"), on_sensor)

    # publish a step
    bridge.publish_json(SIM_STEP, {"dt": 0.05, "sync": True, "step": 1})

    for _ in range(40):
        if got_ack.get("ack") and got_sensor.get("type") == "door":
            break
        time.sleep(0.05)

    assert got_ack.get("ack") is True
    assert got_ack.get("step") == 1
    assert got_sensor.get("type") == "door"

    # command open door
    status = {}
    bridge.subscribe(ACTUATOR_STATUS.format(device_type="door", device_id="door_1"), lambda t, p: status.update(p))
    bridge.publish_json(ACTUATOR_CMD.format(device_type="door", device_id="door_1"), {"action": "open"})

    for _ in range(40):
        if status.get("state") == "open":
            break
        time.sleep(0.05)

    assert status.get("state") == "open"


