"""
AutonomousSupervisor
- Background loop that continuously pulls subsystem snapshots and feeds SystemAnalysisAgent
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any

from .integration_hub import IntegrationHub
from .system_analysis_agent import SystemAnalysisAgent
from .guardian_policy import GuardianPolicy


logger = logging.getLogger(__name__)


class AutonomousSupervisor:
    def __init__(self, hub: IntegrationHub, agent: SystemAnalysisAgent, interval_seconds: int = 120, policy: Optional[GuardianPolicy] = None) -> None:
        self.hub = hub
        self.agent = agent
        self.interval_seconds = interval_seconds
        self.policy = policy or GuardianPolicy()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop(), name="autonomous_supervisor_loop")
        logger.info("🚀 AutonomousSupervisor started")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5)
            except asyncio.TimeoutError:
                self._task.cancel()
        logger.info("🛑 AutonomousSupervisor stopped")

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                snapshot = self.hub.get_status_snapshot()
                # Apply policy to recent alerts or sensor states (simple MVP: no history yet)
                # We can scan sensor stats for anomalies and trigger policy-driven actions later.
                await self.agent.synthesize(snapshot)
            except Exception as e:
                logger.error(f"AutonomousSupervisor loop error: {e}")
            finally:
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_seconds)
                except asyncio.TimeoutError:
                    pass


