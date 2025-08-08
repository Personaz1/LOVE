from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Dict, Any

from bridge.mqtt_bridge import MqttBridge
from bridge.topics import SENSOR_DATA, ACTUATOR_CMD, ACTUATOR_STATUS, SIM_STEP, SIM_STEPPED
from sim.emulator.world import World
from sim.telemetry import TelemetryWriter


logger = logging.getLogger(__name__)


def _iso_now() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class EmulatorMqttApp:
    def __init__(self, host: str = "localhost", port: int = 1883, dt_s: float = 0.05, telemetry_path: str | None = None) -> None:
        self.bridge = MqttBridge(host=host, port=port, client_id="emulator")
        self.world = World(dt=dt_s)
        self.step_index: int = 0
        self.telemetry = TelemetryWriter(telemetry_path) if telemetry_path else None

    def start(self, seed: int = 1337) -> None:
        self.bridge.connect()
        self.world.reset(seed=seed)

        # subscribe to step control and actuator commands
        self.bridge.subscribe(SIM_STEP, self._on_step)
        self.bridge.subscribe(ACTUATOR_CMD.format(device_type="door", device_id="door_1"), self._on_actuator_cmd)

    def _on_step(self, topic: str, payload: Dict[str, Any]) -> None:
        # advance world one step, publish observations, send step ack
        self.step_index = int(payload.get("step", self.step_index + 1))
        obs = self.world.step(None)

        # publish minimal sensor data: door state as a sensor
        sensor_topic = SENSOR_DATA.format(sensor_type="door", sensor_id="door_1")
        self.bridge.publish_json(
            sensor_topic,
            {
                "sensor_id": "door_1",
                "type": "door",
                "state": obs["door_state"],
                "timestamp": _iso_now(),
            },
        )

        # telemetry
        if self.telemetry:
            self.telemetry.write("step", {"step": self.step_index, "obs": obs})

        # send step ack
        self.bridge.publish_json(
            SIM_STEPPED,
            {
                "ack": True,
                "step": self.step_index,
                "timestamp": _iso_now(),
            },
        )

    def _on_actuator_cmd(self, topic: str, payload: Dict[str, Any]) -> None:
        action = payload.get("action")
        if action == "open":
            self.world.step({"action": "open_door"})
        # publish status
        self.bridge.publish_json(
            ACTUATOR_STATUS.format(device_type="door", device_id="door_1"),
            {
                "device_type": "door",
                "device_id": "door_1",
                "state": self.world.state.door_state,
                "ok": True,
                "timestamp": _iso_now(),
            },
        )
        if self.telemetry:
            self.telemetry.write("actuator_status", {"device_id": "door_1", "state": self.world.state.door_state})


def main() -> None:  # simple CLI
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--telem", default="guardian_sandbox/events/sim_telemetry.jsonl")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    app = EmulatorMqttApp(host=args.host, port=args.port, telemetry_path=args.telem)
    app.start(seed=args.seed)

    # idle loop; callbacks do the work
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()


