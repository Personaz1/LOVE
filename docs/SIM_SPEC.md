# Virtual ΔΣ House Simulation Spec (v1)

## Goals
- Deterministic, reproducible, model-agnostic simulation for smart home tasks
- Stable data contracts (observations/actions/telemetry) reusable across engines (UE5, emulator)
- Headless emulator for CI + pluggable real-time 3D backends

## Determinism
- Fixed-step simulation (dt) and seeded RNG
- Synchronous control via step/stepped handshake for RL
- Virtual time; no wall-clock coupling in headless mode

## Protocol (MVP)
- Transport: MQTT v5
- Topics:
  - smart_home/sensors/<type>/<id>/data
  - smart_home/actuators/<type>/<id>/command
  - smart_home/actuators/<type>/<id>/status
  - sim/control/step, sim/control/stepped (sync)
- Payload: JSON as defined in API_CONTRACT.md

## Observations (examples)
- MotionObs, DoorState, LidarScan, CameraMeta, CameraFrame (out-of-band)

## Actions (examples)
- ActuatorCommand: door/light/lock/siren/robot

## Episode Lifecycle
1) reset(seed) → initial state published
2) loop: agent sends action; sim advances one step; publishes observations/telemetry
3) done/terminated when goals or max_steps reached

## Testing Strategy
- Unit: schema round-trip, deterministic step(seed)
- Integration: MQTT QoS1, reconnect, backpressure
- E2E: scenario DSL → invariants; golden traces for regression

## Performance
- Emulator targets ≥1000× real-time without video
- Camera frames throttled or provided via side channel (WS/RTSP) when needed


