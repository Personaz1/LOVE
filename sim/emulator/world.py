from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple
import random


@dataclass
class WorldState:
    step: int = 0
    time_s: float = 0.0
    robot_xy: Tuple[float, float] = (0.0, 0.0)
    door_state: str = "closed"


class World:
    def __init__(self, dt: float = 0.05, seed: int = 1337) -> None:
        self.dt = dt
        self._rng = random.Random(seed)
        self.state = WorldState()

    def reset(self, seed: int | None = None) -> Dict:
        if seed is not None:
            self._rng.seed(seed)
        self.state = WorldState(step=0, time_s=0.0, robot_xy=(0.0, 0.0), door_state="closed")
        return self._observe()

    def step(self, action: Dict | None = None) -> Dict:
        self.state.step += 1
        self.state.time_s += self.dt
        # trivial dynamics for MVP
        if action and action.get("action") == "open_door":
            self.state.door_state = "open"
        return self._observe()

    def _observe(self) -> Dict:
        return {
            "step": self.state.step,
            "time_s": self.state.time_s,
            "door_state": self.state.door_state,
            "robot_xy": self.state.robot_xy,
        }


