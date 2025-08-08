from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class MotionObs(BaseModel):
    sensor_id: str
    type: Literal["motion"] = "motion"
    value: bool
    timestamp: str
    location: Optional[str] = None
    zone: Optional[str] = None
    status: Literal["normal", "alert", "error"] = "normal"


class DoorState(BaseModel):
    sensor_id: str
    type: Literal["door"] = "door"
    state: Literal["open", "closed", "moving"]
    timestamp: str
    location: Optional[str] = None


class LidarScan(BaseModel):
    sensor_id: str
    type: Literal["lidar"] = "lidar"
    ranges: List[float]
    angle_min: float
    angle_max: float
    angle_inc: float
    timestamp: str


class CameraMeta(BaseModel):
    sensor_id: str
    type: Literal["camera"] = "camera"
    width: int
    height: int
    fps: float
    format: Literal["jpeg", "png"] = "jpeg"


class ActuatorCommand(BaseModel):
    device_type: str
    device_id: str
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str


class ActuatorStatus(BaseModel):
    device_type: str
    device_id: str
    state: str
    ok: bool = True
    timestamp: str


class SimStep(BaseModel):
    dt: float
    sync: bool = True
    step: int


class StepAck(BaseModel):
    ack: bool
    step: int
    timestamp: str


