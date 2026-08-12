# AGRO-AI Comprehensive Testing Report

The following report details the mock-execution results for all executable Python nodes and training scripts in the codebase. Since `rclpy` is not present in this testing environment, all nodes gracefully fall back to their offline mock routines to verify structural and syntax integrity.

### Summary
- **Total Scripts Tested**: 17
- **Passed**: 17
- **Failed**: 0

## core\actuator\agro_ai_actuator\nozzle_controller.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
ROS2 not installed. Running a simple test instance...
[INFO] Connecting to Arduino on COM3 @ 1000000 baud...
[WARN] Failed to connect to serial port COM3: could not open port 'COM3': FileNotFoundError(2, 'The system cannot find the file specified.', None, 2). Running mocked.
Sending test bitmask: 0b1100000000000011100000
[INFO] BOOM: [-----XXX------------XX--------------]
Test complete.
```

## core\actuator\can_bus_transceiver\can_node.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] CAN Bus Transceiver Node initialized.
[INFO] Processed cmd_vel to CAN frame.
```

## core\actuator\pwm_valve_driver\pwm_node.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] PWM Valve Driver Node initialized.
[INFO] Processed hydraulic cmds to PWM.
```

## core\perception\camera_pipeline_ros2\camera_node.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] Camera Node initialized (Intel RealSense mock).
[INFO] Published mock RGB frame (1920x1080x3).
```

## core\perception\ekf_localization\ekf_node.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] EKF Localization Node initialized.
[INFO] Published global pose: [0. 0. 0. 0.]
```

## core\perception\lidar_processor\pointcloud_downsampler.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] LiDAR Processor Node initialized.
[INFO] Received raw point cloud, outputting downsampled mock.
```

## core\safety\hardware_interrupt_handler\estop_node.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] Hardware Interrupt E-Stop Node initialized.
[INFO] Processed potential E-Stop trigger.
```

## core\safety\human_detector_watchdog\watchdog_node.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] Human Detector Watchdog initialized.
[INFO] Evaluated YOLO detections for safety breaches.
```

## core\telemetry\agro_ai_telemetry\mqtt_bridge_node.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] [MOCK MQTT PUBLISH] Topic: telemetry/agro_ai_robot_001 | Payload: {"timestamp": 1786528871.4496393, "device_id": "agro_ai_robot_001", "health": "UNKNOWN", "battery_level": 0.0}
```

## core\world_model\agro_ai_world_model\trt_yolo_node.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
Running in mock mode, disabling real YOLO initialization.
ROS2 not installed. Running a simple test instance...
[INFO] Loading YOLO model from: yolov8s.pt
[INFO] YOLO Detector node initialized and waiting for images.
Simulating camera frame arrival...
[PUBLISH] {"timestamp": 1786528871.633443, "detections": [{"cam": 4, "x": 320.0, "y": 320.0, "conf": 0.92}], "latency_ms": 15.610456466674805}
[DEBUG] Published 1 weeds from cam 4
Test complete.
```

## core\world_model\octomap_server\voxel_map_node.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] Voxel Map Node initialized.
[INFO] Processed downsampled point cloud into Voxel Map.
```

## machines\construction\bulldozer\agro_ai_bulldozer\grading_mpc_node.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] Bulldozer MPC Grading Node initialized.
[INFO] Z: 6.50 | Target: 5.00 | Blade Pitch Cmd: -1.000
[INFO] Z: 6.49 | Target: 5.00 | Blade Pitch Cmd: -1.000
[INFO] Z: 6.47 | Target: 5.00 | Blade Pitch Cmd: -1.000
[INFO] Z: 6.44 | Target: 5.00 | Blade Pitch Cmd: -1.000
[INFO] Z: 6.40 | Target: 5.00 | Blade Pitch Cmd: -1.000
[INFO] Z: 6.35 | Target: 5.00 | Blade Pitch Cmd: -1.000
[INFO] Z: 6.29 | Target: 5.00 | Blade Pitch Cmd: -1.000
[INFO] Z: 6.22 | Target: 5.00 | Blade Pitch Cmd: -1.000
[INFO] Z: 6.14 | Target: 5.00 | Blade Pitch Cmd: -1.000
[INFO] Z: 6.05 | Target: 5.00 | Blade Pitch Cmd: -1.000
```

## machines\construction\crane\agro_ai_crane\anti_sway_controller.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] Mock-loading RL Anti-Sway policy (Isaac Sim exported ONNX).
[INFO] Crane Anti-Sway Node initialized.
[INFO] Target: [5.0, 5.0] | Sway (deg): (0.0, 0.0) | Trolley Cmd: (1.00, 1.00)
[INFO] Target: [5.0, 5.0] | Sway (deg): (9.7, 0.0) | Trolley Cmd: (1.00, 1.00)
[INFO] Target: [5.0, 5.0] | Sway (deg): (10.5, 0.0) | Trolley Cmd: (1.00, 1.00)
[INFO] Target: [5.0, 5.0] | Sway (deg): (1.6, 0.0) | Trolley Cmd: (1.00, 1.00)
[INFO] Target: [5.0, 5.0] | Sway (deg): (-8.8, 0.0) | Trolley Cmd: (1.00, 1.00)
[INFO] Target: [5.0, 5.0] | Sway (deg): (-11.1, 0.0) | Trolley Cmd: (1.00, 1.00)
[INFO] Target: [5.0, 5.0] | Sway (deg): (-3.3, 0.0) | Trolley Cmd: (1.00, 1.00)
[INFO] Target: [5.0, 5.0] | Sway (deg): (7.6, 0.0) | Trolley Cmd: (1.00, 1.00)
[INFO] Target: [5.0, 5.0] | Sway (deg): (11.4, 0.0) | Trolley Cmd: (1.00, 1.00)
[INFO] Target: [5.0, 5.0] | Sway (deg): (4.8, 0.0) | Trolley Cmd: (1.00, 1.00)
```

## machines\construction\excavator\agro_ai_excavator\trenching_rl_inference.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] Could not load policy from mock_path, using mock. Error: The provided filename mock_path does not exist
[INFO] Excavator RL Trenching Node initialized.
[INFO] Obs: [ 0.5  1.2 -0.5  0.   0.  -2. ] -> Valve Cmds (boom, stick, bucket): [0.1, -0.2, 0.5]
[INFO] Obs: [ 0.4  1.  -0.4  0.   0.  -2. ] -> Valve Cmds (boom, stick, bucket): [0.1, -0.2, 0.5]
[INFO] Obs: [ 0.3  0.8 -0.3  0.   0.  -2. ] -> Valve Cmds (boom, stick, bucket): [0.1, -0.2, 0.5]
```

## machines\farming\combine\agro_ai_combine\header_height_control.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] Combine Header Height PID Controller initialized.
[INFO] Height: 0.150m | Target: 0.150m | Error: 0.000m | Hydraulic Cmd: 0.000
[INFO] Height: 0.140m | Target: 0.150m | Error: 0.010m | Hydraulic Cmd: 0.017
[INFO] Height: 0.100m | Target: 0.150m | Error: 0.050m | Hydraulic Cmd: 0.080
[INFO] Height: 0.050m | Target: 0.150m | Error: 0.100m | Hydraulic Cmd: 0.146
[INFO] Height: 0.080m | Target: 0.150m | Error: 0.070m | Hydraulic Cmd: 0.071
[INFO] Height: 0.120m | Target: 0.150m | Error: 0.030m | Hydraulic Cmd: 0.019
[INFO] Height: 0.150m | Target: 0.150m | Error: 0.000m | Hydraulic Cmd: -0.012
```

## machines\farming\sprayer\agro_ai_sprayer\precision_spray_logic.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
ROS2 not installed. Running a simple test instance...
Simulating weed detection message...
[INFO] Buffered 2 targets to fire in 0.36s
Delay buffer size: 2. Advancing time manually to trigger...
[INFO] MOCK PUB -> Nozzle State: 0b100000000000000000001000000000
[INFO] MOCK PUB -> Nozzle State: 0b0
Test complete.
```

## machines\farming\tractor\agro_ai_tractor\pure_pursuit_node.py - ✅ PASS
```text
WARNING: rclpy not found. Running in mock mode.
[INFO] Tractor Pure Pursuit node initialized.
[INFO] Target: (5.00, 0.00) | Steer Angle: 16.9 deg
```
