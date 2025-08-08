from __future__ import annotations

from typing import Tuple, Dict, Any

try:
    import gymnasium as gym
    from gymnasium import spaces
except Exception:  # pragma: no cover
    gym = None
    spaces = None

from sim.emulator.world import World


class VirtualHouseEnv(gym.Env if gym else object):  # type: ignore
    metadata = {"render.modes": ["none"]}

    def __init__(self, dt: float = 0.05, seed: int = 1337) -> None:
        self.world = World(dt=dt, seed=seed)
        # minimal observation/action spaces for MVP
        if spaces:
            self.observation_space = spaces.Dict(
                {
                    "step": spaces.Discrete(10_000_000),
                    "time_s": spaces.Box(low=0.0, high=1e9, shape=()),
                }
            )
            self.action_space = spaces.Discrete(2)  # 0: noop, 1: open_door

    def reset(self, seed: int | None = None, options: Dict[str, Any] | None = None):
        obs = self.world.reset(seed=seed)
        return {"step": obs["step"], "time_s": obs["time_s"]}, {}

    def step(self, action: int) -> Tuple[Dict[str, Any], float, bool, bool, Dict[str, Any]]:
        act = {"action": "open_door"} if action == 1 else {"action": "noop"}
        obs = self.world.step(act)
        reward = 1.0 if obs["door_state"] == "open" else 0.0
        terminated = False
        truncated = False
        info: Dict[str, Any] = {}
        return {"step": obs["step"], "time_s": obs["time_s"]}, reward, terminated, truncated, info


