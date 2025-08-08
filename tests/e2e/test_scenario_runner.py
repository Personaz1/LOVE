import os
import tempfile

from sim.scenario_runner import run_scenario


def _write_yaml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".yaml")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def test_scenario_runner_minimal():
    yaml_text = """
seed: 123
steps: 10
invariants:
  - "door_state in ['closed','open']"
actions:
  - at: 3
    action: {action: open_door}
"""
    scenario_path = _write_yaml(yaml_text)
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        telem_path = tf.name
    try:
        result = run_scenario(scenario_path, telem_path)
        assert result.success is True
        assert result.steps == 10
        assert os.path.exists(telem_path)
    finally:
        os.remove(scenario_path)
        os.remove(telem_path)


