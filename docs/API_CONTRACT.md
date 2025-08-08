# API Contract (v1)

Transport: MQTT v5

## Topics
- smart_home/sensors/<type>/<id>/data
- smart_home/actuators/<type>/<id>/command
- smart_home/actuators/<type>/<id>/status
- sim/control/step
- sim/control/stepped

## JSON Schemas (conceptual)

MotionObs
```json
{
  "sensor_id": "motion_hall_1",
  "type": "motion",
  "value": true,
  "timestamp": "2025-08-08T12:00:00Z",
  "location": "hall",
  "zone": "floor1",
  "status": "normal"
}
```

LidarScan
```json
{
  "sensor_id": "lidar_1",
  "type": "lidar",
  "ranges": [0.5, 0.52, 0.49],
  "angle_min": -1.57,
  "angle_max": 1.57,
  "angle_inc": 0.005,
  "timestamp": "2025-08-08T12:00:00Z"
}
```

ActuatorCommand
```json
{
  "device_type": "door",
  "device_id": "door_1",
  "action": "open",
  "parameters": {"speed": 0.5},
  "timestamp": "2025-08-08T12:00:00Z"
}
```

SimStep / StepAck
```json
{"dt": 0.05, "sync": true, "step": 42}
{"ack": true, "step": 42, "timestamp": "2025-08-08T12:00:00Z"}
```

Notes
- Camera frames are out-of-band (WebSocket/RTSP) or base64 JPEG with throttling
- All timestamps are ISO8601
