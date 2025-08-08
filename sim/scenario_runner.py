from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import yaml

from sim.emulator.world import World


@dataclass
class ScenarioResult:
    success: bool
    steps: int
    invariant_violations: List[str]
    telemetry_path: str | None = None


def _eval_invariants(invariants: List[str], context: Dict[str, Any]) -> List[str]:
    violations: List[str] = []
    for inv in invariants:
        try:
            ok = bool(eval(inv, {"__builtins__": {}}, context))
        except Exception:
            ok = False
        if not ok:
            violations.append(inv)
    return violations


def run_scenario(
    scenario_yaml_path: str,
    telemetry_out_path: str | None = None,
) -> ScenarioResult:
    with open(scenario_yaml_path, "r", encoding="utf-8") as f:
        scenario = yaml.safe_load(f)

    seed: int = int(scenario.get("seed", 1337))
    max_steps: int = int(scenario.get("steps", 100))
    invariants: List[str] = list(scenario.get("invariants", []))
    actions: List[Dict[str, Any]] = list(scenario.get("actions", []))

    # prepare action schedule: step -> action dict
    schedule: Dict[int, Dict[str, Any]] = {}
    for item in actions:
        at = int(item.get("at", 0))
        schedule[at] = dict(item.get("action", {}))

    world = World(seed=seed)
    obs = world.reset(seed=seed)

    # telemetry
    telem: List[Tuple[int, Dict[str, Any]]] = [(0, obs)]
    invariant_violations: List[str] = []

    for step in range(1, max_steps + 1):
        act = schedule.get(step, None)
        obs = world.step(act)

        # context for invariants
        ctx = {**obs}
        ctx["step"] = step
        violations = _eval_invariants(invariants, ctx)
        invariant_violations.extend(violations)
        telem.append((step, obs))

    # write telemetry if requested
    if telemetry_out_path:
        with open(telemetry_out_path, "w", encoding="utf-8") as fw:
            for step, o in telem:
                fw.write(json.dumps({"step": step, **o}) + "\n")

    success = len(invariant_violations) == 0
    return ScenarioResult(success=success, steps=max_steps, invariant_violations=invariant_violations, telemetry_path=telemetry_out_path)


def main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run Virtual ΔΣ House scenario")
    parser.add_argument("scenario", help="Path to YAML scenario file")
    parser.add_argument("--telem", default=None, help="Telemetry JSONL output path")
    args = parser.parse_args()

    result = run_scenario(args.scenario, args.telem)
    print(json.dumps({
        "success": result.success,
        "steps": result.steps,
        "violations": result.invariant_violations,
        "telemetry": result.telemetry_path,
    }))
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()


