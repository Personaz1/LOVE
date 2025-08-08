from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TelemetryWriter:
    file_path: str

    def __post_init__(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        # create/clear file
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("")

    def write(self, event_type: str, payload: Dict[str, Any]) -> None:
        entry = {"ts": time.time(), "type": event_type, **payload}
        line = json.dumps(entry, ensure_ascii=False)
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


