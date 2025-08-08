from bridge.schemas import MotionObs, LidarScan, ActuatorCommand


def test_motion_obs_roundtrip():
    m = MotionObs(sensor_id="motion_1", value=True, timestamp="2025-08-08T00:00:00Z")
    payload = m.model_dump_json()
    m2 = MotionObs.model_validate_json(payload)
    assert m2.sensor_id == m.sensor_id
    assert m2.value is True


def test_lidar_scan_validate():
    scan = LidarScan(
        sensor_id="lidar_1",
        ranges=[0.5, 0.6],
        angle_min=-1.0,
        angle_max=1.0,
        angle_inc=0.1,
        timestamp="2025-08-08T00:00:00Z",
    )
    assert len(scan.ranges) == 2


def test_actuator_command_minimal():
    cmd = ActuatorCommand(
        device_type="door",
        device_id="door_1",
        action="open",
        timestamp="2025-08-08T00:00:00Z",
    )
    assert cmd.device_type == "door"


