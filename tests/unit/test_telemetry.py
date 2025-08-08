import os
import tempfile

from sim.telemetry import TelemetryWriter


def test_telemetry_writer_jsonl():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "telem.jsonl")
        tw = TelemetryWriter(path)
        tw.write("step", {"step": 1, "obs": {"door_state": "closed"}})
        tw.write("actuator_status", {"device_id": "door_1", "state": "open"})
        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        assert len(lines) == 2
        assert '"type": "step"' in lines[0]
        assert '"type": "actuator_status"' in lines[1]


