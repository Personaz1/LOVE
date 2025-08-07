"""
SystemAnalysisAgent
- Periodically synthesizes a live system analysis from subsystems and memory
- Exposes a simple async API to get latest analysis JSON
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ai_client.core.client import AIClient
from ai_client.utils.cache import system_cache


logger = logging.getLogger(__name__)


class SystemAnalysisAgent:
    def __init__(self, ai_client: Optional[AIClient] = None) -> None:
        self.ai_client = ai_client or AIClient()
        self._lock = asyncio.Lock()
        self._last_analysis: Optional[Dict[str, Any]] = None
        self._ttl_seconds: int = 300

    async def synthesize(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run LLM over the provided context and store result."""
        async with self._lock:
            try:
                additional_prompt = (
                    "Ты живой системный наблюдатель. Синтезируй статус, риски, рекомендации. "
                    "Верни JSON с полями: system_status, risks, actions, recommendations, timestamp."
                )
                message = (
                    "Сгенерируй краткий живой анализ системы на основе контекста. "
                    f"Контекст: {str(context)[:12000]}"
                )
                response = self.ai_client.chat(
                    message=message,
                    additional_prompt=additional_prompt,
                )
                data = {
                    "system_status": response[:8000],
                    "timestamp": datetime.now().isoformat(),
                }
                self._last_analysis = data
                system_cache.set("live_system_analysis", data, params=None, ttl_seconds=self._ttl_seconds)
                logger.info("🧠 SystemAnalysisAgent synthesized analysis")
                return data
            except Exception as e:
                logger.error(f"SystemAnalysisAgent error: {e}")
                # Fallback to last or cache
                cached = system_cache.get("live_system_analysis", params=None, ttl_seconds=3600)
                return cached or {"error": str(e), "timestamp": datetime.now().isoformat()}

    def get_last(self) -> Optional[Dict[str, Any]]:
        return self._last_analysis or system_cache.get("live_system_analysis", params=None, ttl_seconds=3600)


