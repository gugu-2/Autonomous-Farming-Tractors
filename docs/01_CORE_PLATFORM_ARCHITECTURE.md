# AGRO-AI Core Platform Architecture
**Version:** 1.0.0
**Status:** Approved for Implementation
**Author:** AI Systems Architect

## 1. Core Platform Overview

The AGRO-AI core platform forms the foundational intelligence layer installed on every piece of equipment across all 40 machine types (excavators, tractors, cranes, combine harvesters, etc.). The design philosophy follows a strict separation of concerns between **shared autonomy infrastructure** (The Core Platform) and **machine-specific execution logic** (The Task Planners).

### 1.1 Shared vs. Machine-Specific Modules

**Shared Modules (Core Platform - Present on ALL machines):**
- **Layer 1 & 2: Perception Pipeline:** Sensor drivers, calibration, ROS2 topic bridging, synchronization, and raw data filtering (Voxel grids, image undistortion).
- **Layer 3: World Model:** YOLOv8 object detection, 3D bounding box generation, Occupancy Grid Mapping (OGM), Bird's Eye View (BEV) projection, and target zone detection.
- **Layer 4: State Estimation & Localization:** EKF (Extended Kalman Filter) sensor fusion (RTK GPS + IMU + Odometry).
- **Layer 7: Safety Module:** Hardware/software watchdog, emergency stops, human detection zones, ISO 13849 compliance.
- **Communications Layer:** ROS2 DDS, MQTT telemetry, WebRTC video streaming.
- **Logging Layer:** ROS2 bag selective recording, edge-case data collection.

**Machine-Specific Modules (Task Planners - Unique per machine):**
- **Layer 5: Behavioral Planning:** E.g., Trench digging logic (Excavator) vs. Field swathing (Tractor).
- **Layer 6: Actuator Interface:** E.g., ISOBUS implement control (Farming) vs. 0-10V DAC proportional hydraulic valve control (Construction).

---

## 2. Perception Module (Layer 1 & 2)

The perception module ingests raw data from the standard sensor suite, timestamps it, and applies foundational processing.

### 2.1 Hardware Sensor Suite

| Sensor | Make/Model | Purpose | Price (Est) |
| :--- | :--- | :--- | :--- |
| **RGB-D Camera** | Intel RealSense D435i | Short-range depth, color vision | $300 |
| **3D LiDAR** | Ouster OS1-32 | Long-range 360° point cloud (50m) | $5,000 |
| **RTK GPS** | u-blox F9P | Centimeter-level absolute positioning | $250 |
| **IMU** | TDK ICM-42688-P | High-frequency attitude/acceleration | $15 |

### 2.2 Camera Pipeline
The Intel RealSense D435i feeds directly into the Jetson Orin via USB 3.2.
1. **Driver:** `realsense2_camera` ROS2 node.
2. **Undistortion:** `image_proc` ROS2 package performs debayering and lens undistortion using camera intrinsics.
3. **Inference:** The rectified image is passed to the TensorRT-optimized YOLOv8 node (`agro_yolo_node`).

**ROS2 Topics:**
- `/camera/color/image_raw` (`sensor_msgs/msg/Image`)
- `/camera/color/camera_info` (`sensor_msgs/msg/CameraInfo`)
- `/camera/depth/image_rect_raw` (`sensor_msgs/msg/Image`)
- `/perception/yolo/detections` (`vision_msgs/msg/Detection2DArray`)

### 2.3 LiDAR Pipeline
The Ouster OS1-32 communicates via Gigabit Ethernet.
1. **Driver:** `ros2_ouster` node.
2. **Filtering:** Point clouds are heavily downsampled using a Voxel Grid Filter (leaf size: 0.1m) in the `pcl_ros` node.
3. **Ground Segmentation:** RANSAC plane fitting to remove the ground plane.
4. **Occupancy Grid:** Filtered points are projected to a 2D occupancy grid (`nav_msgs/msg/OccupancyGrid`) for path planning.

**ROS2 Topics:**
- `/ouster/points` (`sensor_msgs/msg/PointCloud2`)
- `/perception/lidar/filtered` (`sensor_msgs/msg/PointCloud2`)
- `/perception/occupancy_grid` (`nav_msgs/msg/OccupancyGrid`)

### 2.4 Localization Pipeline (GPS + IMU)
1. **GPS:** u-blox F9P providing NMEA over serial. The `nmea_navsat_driver` parses this into `/gps/fix` (`sensor_msgs/msg/NavSatFix`).
2. **IMU:** ICM-42688-P read via SPI. A complementary filter runs at 400Hz to estimate orientation (`sensor_msgs/msg/Imu`).
3. **Fusion:** `robot_localization` package uses an Extended Kalman Filter (EKF) to fuse GPS, IMU, and optionally wheel/track odometry.

**ROS2 Topics:**
- `/gps/fix` (`sensor_msgs/msg/NavSatFix`)
- `/imu/data` (`sensor_msgs/msg/Imu`)
- `/odometry/filtered` (`nav_msgs/msg/Odometry`)
- **TF Tree:** `map` -> `odom` -> `base_link` -> `sensor_frames`

### 2.5 Perception Data Flow Diagram

```text
[RealSense D435i] ---> /camera/color/image_raw ---> [image_proc] ---> [agro_yolo_node] ---> /perception/objects
                                                                                                    |
[Ouster OS1-32] -----> /ouster/points ------------> [pcl_voxel] ----> [ground_filter] ---> [occupancy_grid_node]
                                                                                                    |
[u-blox F9P] --------> /gps/fix ----------------------\                                             |
                                                       +---> [EKF_node] ---> /odom (TF) <-----------/
[ICM-42688-P] -------> /imu/data ---------------------/
```

---

## 3. World Model Module (Layer 3)

The World Model fuses 2D detections, 3D point clouds, and localization data into a cohesive representation of the machine's surroundings.

### 3.1 YOLOv8 Object Detection
- **Model Choice:** YOLOv8s (Small) trained in PyTorch and exported to TensorRT FP16 format for Jetson Orin. YOLOv8n (Nano) is used as a fallback if thermal throttling occurs.
- **Inference Speed:** ~60 FPS on Jetson Orin NX 16GB.
- **Classes (AGRO-COCO Custom Dataset):** `0: human`, `1: machine`, `2: material_pile`, `3: truck`, `4: obstacle`, `5: target_zone` (e.g., a trench line or harvest path).

### 3.2 3D Bounding Box Generation
2D bounding boxes from YOLOv8 are combined with the RealSense depth map and Ouster LiDAR point cloud.
1. The 2D ROI is projected into the LiDAR point cloud using camera-LiDAR extrinsic calibration.
2. Points falling within the frustum are clustered using Euclidean Cluster Extraction.
3. A 3D bounding box (AABB or OBB) is fitted to the cluster.

**Topic:** `/world_model/objects_3d` (`vision_msgs/msg/Detection3DArray`)

### 3.3 Occupancy Grid Map (OGM) & BEV
- **Grid Specs:** 2D grid, 5cm (0.05m) resolution, covering a 50x50m area around the `base_link`.
- **BEV Projection:** The 3D world model is flattened into a Bird's Eye View map, annotating grid cells not just with 'occupied/free', but with semantic labels (e.g., 'occupied by human', 'occupied by material_pile').

---

## 4. Safety Module (Layer 7) — MOST CRITICAL

Safety is paramount in heavy machinery automation. The AGRO-AI platform implements a defense-in-depth strategy.

### 4.1 Human Detection Zones
The safety node (`agro_safety_supervisor`) subscribes to `/world_model/objects_3d` and monitors human classes.
- **Zone 1 (Warning):** 10m radius. Machine commanded to SLOW DOWN to 30% of max speed. Flashing amber beacons activated.
- **Zone 2 (Critical):** 5m radius. HARD STOP triggered immediately. Red beacons activated.

### 4.2 YOLOv8-Pose for Advanced Safety
Standard object detection can miss occluded workers. We run a secondary lightweight YOLOv8-pose model focused solely on identifying human keypoints (heads, shoulders, arms) visible behind equipment or trenches.

### 4.3 Hardware Safety Architecture (ISO 13849 Compliant)
Software alone is insufficient for functional safety.
- **Emergency Stop Relay:** A hardware PILZ safety relay circuit sits between the power supply and the hydraulic valve solenoids.
- **Physical E-Stops:** Mushroom buttons on all 4 corners of the machine break the relay circuit directly (hardware bypasses software).
- **Remote Kill Switch:** A 900MHz LoRa radio module (e.g., Ebyte E22) paired with a remote operator handheld. Loss of heartbeat (timeout > 500ms) or explicit kill command drops the PILZ relay.

### 4.4 Software Watchdog
A hardware watchdog timer on the Jetson Orin requires the `agro_safety_supervisor` to toggle a GPIO pin every 50ms. If the AI crashes, the ROS2 node hangs, or the OS freezes, the pin stops toggling, and the watchdog drops power to the pilot hydraulic manifold within 100ms.

---

## 5. Actuator Interface Module (Layer 6)

The system must interface with varying physical actuators across agriculture and construction.

### 5.1 Hydraulic Valve Control (Construction - Excavators, Cranes)
Most heavy construction equipment uses proportional hydraulic valves requiring a 0-10V or PWM signal.
- **Hardware:** Jetson Orin I2C bus -> MCP4922 DAC (Digital to Analog Converter) -> Op-Amp level shifter -> 0-10V analog output.
- **Wiring:** Jetson is isolated via optocouplers to prevent ground loops and voltage spikes from the inductive solenoid coils.

### 5.2 CAN Bus & ISOBUS (Agriculture - Tractors, Harvesters)
Farming equipment adheres to J1939 and ISO 11783 (ISOBUS).
- **Interface:** CANable Pro (Isolated USB to CAN) -> Linux `socketcan` (`can0`).
- **Software:** ROS2 `ros2_canopen` and custom J1939 parsers interpret steering angles and send implement control commands (e.g., lower hitch, activate PTO).
- **PWM Servo Control:** For retrofitted older tractors, steering is controlled via high-torque PWM DC motors acting on the steering column, driven by an MD10C motor driver via PWM.

### 5.3 Safety Interlock
The output of the Actuator Interface is physically routed through the PILZ safety relay. Even if the AI outputs a "drive forward 100%" command, if the safety relay is open (due to E-Stop or Watchdog), power cannot reach the hydraulic solenoids.

---

## 6. Communication Architecture

### 6.1 Onboard Communications (ROS2 DDS)
- **Middleware:** Eclipse Cyclone DDS is configured for the onboard network. It is tuned for zero-copy transport via shared memory for massive data streams (Image/PointCloud) to reduce CPU load.
- **QoS Profiles:** Sensor data uses `BestEffort` (prefer newest data over reliable delivery). Safety commands use `Reliable` QoS.

### 6.2 Cloud & Telemetry (MQTT)
- **Transport:** Cellular LTE/5G modem (e.g., Teltonika RUT240).
- **Protocol:** MQTT (Mosquitto broker hosted on AWS).
- **Telemetry Data:** Every 5 seconds, the `telemetry_agent` node publishes a compressed JSON payload containing: GPS coordinates, heading, current state (idle, digging, driving), fuel/battery level, and error codes.

### 6.3 Remote Operation & Video (WebRTC)
For teleoperation or remote monitoring, raw video streams are too heavy for MQTT.
- We utilize **WebRTC** via the `webrtc_ros` package. It provides sub-200ms latency video streaming from the RealSense cameras to a remote operator dashboard on a web browser.

### 6.4 OTA Updates (Over-The-Air)
- AI model weights (TensorRT `.engine` files) and Docker container updates are managed via **AWS IoT Greengrass**.
- Updates are only applied when the machine is in the `MAINTENANCE` state and the engine is off.

---

## 7. Configuration System

To support 40 different machine types with a unified codebase, configuration is externalized.

### 7.1 YAML Parameter Files
Each machine has a specific profile. Example `excavator_cat320.yaml`:
```yaml
perception:
  camera:
    extrinsics: [0.5, 0.0, 2.1, 0, 0, 0] # x, y, z, r, p, y relative to base_link
  yolo:
    confidence_threshold: 0.65
    model_path: "/opt/agro_ai/models/yolov8s_agro_v2.engine"

safety:
  human_zone_critical_radius: 5.0
  human_zone_warning_radius: 10.0

actuators:
  boom_valve_deadband: 0.12 # 12% deadband on hydraulic spool
```

### 7.2 ROS2 Parameter Server
The YAML files are loaded at launch into the ROS2 Parameter Server. Nodes declare parameters and use parameter callbacks to adjust behavior dynamically (e.g., tuning PID gains via the remote dashboard without restarting the node).

---

## 8. Logging & Data Collection

Data is the lifeblood of the AI platform. We must collect edge cases without filling the hard drive with redundant data.

### 8.1 ROS2 Bag Recording
- A 1TB automotive-grade NVMe SSD is used for local logging.
- `rosbag2` runs continuously in a ring-buffer mode, keeping only the last 30 minutes of full sensor data (Images, LiDAR, Odometry).

### 8.2 Selective Upload (Triggered Logging)
If a critical event occurs (e.g., Human entering Zone 1, E-Stop pressed, or High uncertainty in YOLOv8 inference), a Python script triggers a snapshot.
- The 15 seconds preceding and 5 seconds following the event are extracted from the ring buffer.
- This subset bag file is compressed and queued for LTE upload to the AWS S3 Data Lake for model retraining.

### 8.3 Data Anonymization
Before uploading to the cloud, images containing human faces are blurred on the edge device using a lightweight Haar Cascade or YOLO face model to comply with GDPR and privacy regulations. Absolute GPS coordinates are optionally shifted relative to a local datum if requested by the customer.

---
*End of Document. Prepared for the AGRO-AI Engineering Team.*
