"""
Guardian Policy Layer
- Codifies protective heuristics and reactions
- Consumes events and issues high-priority actions
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List
import logging


logger = logging.getLogger(__name__)


@dataclass
class PolicyDecision:
    allow: bool
    actions: List[Dict[str, Any]]
    rationale: str


class GuardianPolicy:
    """Minimal MVP of safety/defense policy."""

    def evaluate_event(self, event_type: str, data: Dict[str, Any]) -> PolicyDecision:
        # Examples of protective logic
        if event_type == "sensor_alert":
            alert_type = data.get("alert_type", "")
            if alert_type in {"critical", "above_max"}:
                # Immediate protective actions (sirens, lights)
                return PolicyDecision(
                    allow=True,
                    actions=[
                        {"type": "actuator_command", "actuator_id": "siren_main", "command": "activate", "parameters": {"volume": "high"}},
                        {"type": "actuator_command", "actuator_id": "strobe_lights", "command": "activate", "parameters": {"pattern": "emergency"}},
                    ],
                    rationale=f"Critical sensor alert: {data.get('message','')}",
                )

        if event_type.startswith("security_"):
            return PolicyDecision(allow=True, actions=[], rationale="Security event acknowledged")

        # Default: no enforced actions
        return PolicyDecision(allow=True, actions=[], rationale="No policy action required")


