# AGRO-AI Hardware Architecture and Integration Stack

## 1. Compute Hardware Architecture

The core of the AGRO-AI system relies on scalable, robust, and edge-ready compute platforms. We have categorized the compute requirements into three distinct tiers based on the complexity of the machine and the AI workloads required.

### Tier A — Light Compute
**Target Applications:** Simple machines (tractor auto-steer, trencher, driller)
**Hardware:** Raspberry Pi 4 Model B 4GB
**Cost:** USD 75
**When to use:** For machines that do not require complex AI vision or object detection. This tier is strictly for pure GPS mathematics, simple PID control loops, and basic telemetry.
**Limitations:** Cannot run YOLO inference, lacks hardware acceleration for deep learning, limited I/O throughput.

**Specifications:**
- CPU: Broadcom BCM2711, Quad core Cortex-A72 (ARM v8) 64-bit SoC @ 1.5GHz
- RAM: 4GB LPDDR4-3200
- Storage: 32GB High Endurance MicroSD
- Power: 5V/3A via USB-C (requires reliable 12V to 5V step-down)

### Tier B — Standard Compute
**Target Applications:** Most machines (excavator, bulldozer, sprayer, combine)
**Hardware:** NVIDIA Jetson Orin Nano 8GB
**Cost:** USD 499
**When to use:** This is the standard platform for the majority of our deployments. It is capable of running YOLOv8s at 45fps, PPO policy loops at 100Hz, and the full ROS2 Humble software stack simultaneously.

**Specifications:**
- AI Performance: 32 TOPS
- GPU: 1024 NVIDIA Ampere architecture CUDA cores with 32 Tensor Cores
- CPU: 6-core Arm Cortex-A78AE v8.2 64-bit CPU
- RAM: 8GB 128-bit LPDDR5
- Storage: 256GB NVMe SSD (M.2 Key M)
- Power: 10-15W (requires 12V regulated supply from machine electrical)
- Operating Temp: -25°C to 80°C

### Tier C — Heavy Compute
**Target Applications:** Complex machines (crane, autonomous combine with multiple AI tasks like yield monitoring + autonomous navigation)
**Hardware:** NVIDIA Jetson AGX Orin 32GB
**Cost:** USD 899
**When to use:** For machinery requiring massive parallel vision processing, multiple simultaneous LiDAR streams, and complex multi-agent reinforcement learning policies running on edge.

**Specifications:**
- AI Performance: 275 TOPS
- GPU: 2048 NVIDIA Ampere architecture CUDA cores with 64 Tensor Cores
- CPU: 12-core Arm Cortex-A78AE v8.2 64-bit CPU
- RAM: 32GB 256-bit LPDDR5
- Storage: 1TB NVMe SSD + 64GB eMMC
- Power: 15-40W configurable TDP
- Operating Temp: -25°C to 80°C

---

## 2. Vision Sensors and Perception Stack

The perception stack relies heavily on RGB-D cameras, thermal imaging, and LiDAR, depending on the machine's operational context.

### Primary Camera: Intel RealSense D435i
- **RGB Resolution:** 1920x1080 at 30fps
- **Depth Resolution:** 1280x720 at 90fps
- **Depth Range:** 0.3m to 10m range, ~1% accuracy
- **Built-in IMU:** Bosch BMI055 (6 DoF)
- **Price:** USD 179
- **ROS2 Driver:** `realsense2_camera`
- **Mounting:** Top of the machine cab, forward-facing. Requires a custom vibration-dampened 3D-printed or aluminum mount.
- **Connection:** USB 3.1 Gen 1 Type-C

### Downward-facing Camera (Sprayer Boom)
- **Hardware:** Raspberry Pi Camera Module 3 Wide
- **FOV:** 120° horizontal
- **Price:** USD 35
- **Interface:** CSI ribbon cable. For Jetson Orin Nano, use Arducam UC-593C USB adapter if CSI ports are occupied.
- **Application:** Row following, precise weed detection for spot spraying.

### Thermal Camera (Night/Military-Grade Safety)
- **Hardware:** FLIR Lepton 3.5
- **Resolution:** 160x120 thermal radiometric
- **Price:** USD 249 (module only)
- **Interface:** SPI on Jetson GPIO, utilizing the PureThermal 2 or 3 board.
- **Application:** Human/animal detection in zero-light conditions or heavy dust environments where standard RGB fails.

### LiDAR (360-degree Awareness)
- **Hardware:** Ouster OS0-32
- **Specs:** 32-beam, 50m range, 1280 points/rotation, ultra-wide field of view.
- **Price:** USD 3,000
- **ROS2 Driver:** `ouster-ros`
- **Mounting:** Roof mount, weatherproof (IP68, IP69K).
- **Application:** Crucial for skid-steers, cranes, and dump trucks operating in complex, dynamic environments.

### Low-cost LiDAR Alternative
- **Hardware:** Livox Mid-360
- **Specs:** Non-repetitive scanning pattern, 40m range at 10% reflectivity.
- **Price:** USD 999
- **Application:** Provides excellent value for most agricultural machines where extreme point density is not strictly required.

---

## 3. GPS / RTK Navigation Module

Precision agriculture requires centimeter-level accuracy, which standard GPS cannot provide. We utilize Real-Time Kinematic (RTK) positioning.

- **Module:** u-blox ZED-F9P
- **Board:** Ardusimple simpleRTK2B V3 (includes F9P + headers)
- **Price:** USD 175
- **Antenna:** u-blox ANN-MB-00 (IP67, multiband L1/L2)
- **Antenna Price:** USD 49
- **Correction Source:** NTRIP over 4G/LTE. In regions like the USA and EU, we utilize free public networks (e.g., RTK2go, EUREF-IP) or state-sponsored DOT CORS networks.
- **Accuracy with RTK:** ±2cm horizontal
- **Accuracy without RTK:** ±1.5m (insufficient for row-crop farming)
- **ROS2 Driver:** `ublox_dgnss` for F9P specific capabilities.

**Base Station Alternative:**
If the operational area lacks 4G cellular coverage (making NTRIP impossible), a local base station is required.
- **Hardware:** SparkFun GPS-RTK-SMA kit configured as a local base transmitting corrections via LoRa radio.
- **Price:** USD 200

---

## 4. Inertial Measurement Unit (IMU)

High-frequency, low-latency IMU data is required to fuse with GPS for stable heading and pitch/roll compensation, especially over uneven terrain.

- **Primary:** TDK InvenSense ICM-42688-P on a SparkFun Breakout board.
- **Price:** USD 25
- **High-Accuracy Alternative:** VectorNav VN-100 Rugged (for high-vibration applications like crane hooks).
- **Price:** USD 299
- **ROS2 Driver:** `imu_tools` utilizing the Madgwick filter for orientation estimation.

---

## 5. Hydraulic Interface and Control Hardware

Interfacing with the machine's actual movement mechanisms (steering, boom, tracks) is the most critical hardware integration step.

### Scenario A: Modern Machines (Electrohydraulic Proportional Valves)
Machines built post-2015 generally feature CAN bus control for their hydraulic systems.
- **Interface Hardware:** CANable Pro USB-to-CAN adapter (isolated).
- **Price:** USD 45
- **Software:** Linux `socketcan` subsystem + `ros-humble-ros2-socketcan`.
- **Integration:** Requires reverse-engineering the OEM CAN DBC files or establishing partnerships with manufacturers to obtain authorized CAN codes.

### Scenario B: Older Machines (Manual Pilot Hydraulics)
Machines without electronic control require physical retrofitting.
- **Hardware Modification:** Installation of a Sun Hydraulics proportional electrohydraulic valve manifold in series/parallel with the existing pilot lines.
- **Cost:** USD 800 - 1,500
- **Control Interface:** Texas Instruments DAC8830 (16-bit, 4 channels) to generate 0-5V or 4-20mA control signals.
- **DAC Cost:** USD 35
- **Circuitry:** Custom op-amp buffer circuit capable of driving the high-current demands of the hydraulic valve coils from the low-power DAC output.
- **Safety:** Must be installed and certified by a licensed hydraulic engineer.

```text
+----------------+      +-------------------+      +-----------------------+      +----------------+
|  Jetson Orin   | ---> |  TI DAC8830 (SPI) | ---> | Op-Amp Buffer Circuit | ---> | Sun Hydraulics |
| (Policy Output)|      |  (0-5V Output)    |      | (Voltage to Current)  |      | Proportional   |
|                |      |                   |      |                       |      | Valve Coil     |
+----------------+      +-------------------+      +-----------------------+      +----------------+
```

---

## 6. Communication & Networking

Reliable remote monitoring and fail-safes are mandatory.

- **Onboard LTE Router:** Peplink MAX BR1 Mini. Provides cellular connectivity for telemetry, NTRIP data, and OTA updates.
- **Price:** USD 299
- **LoRa Remote Kill Switch:** RYLR998 LoRa transceiver module (x2). One integrated into the machine's safety relay loop, the other in a handheld remote for the operator.
- **Price:** USD 25 each
- **Wi-Fi:** Built into the Jetson platform. Configured to automatically connect when the machine enters the service yard for high-bandwidth log offloading and firmware updates.

---

## 7. Power & Electrical Subsystem

Industrial machines have notoriously noisy electrical environments with large voltage spikes (load dumps).

- **Source:** Machine's 12V or 24V alternator/battery system.
- **Power Conditioning:** Pololu 12V/15A step-down/step-up voltage regulator with reverse voltage protection and transient voltage suppression (TVS) diodes.
- **Price:** USD 25
- **Distribution:** Fused terminal block. A 10A automotive blade fuse protects the AI computer and sensors.
- **Total Power Draw:** Typically 25-50W, representing a negligible fraction of a heavy machine's alternator capacity (often >1000W).

---

## 8. Mechanical Mounting and Weatherproofing

Agricultural and construction environments involve extreme dust, water, mud, and vibration.

- **Enclosure:** Hammond 1590 series IP67 die-cast aluminum enclosure. Provides EMI shielding and acts as a passive heatsink.
- **Price:** USD 80
- **Display Mounting:** RAM Mounts double-ball mount for the operator's tablet interface inside the cab.
- **Price:** USD 65
- **Connectivity:** Waterproof M12 circular connectors for all external sensor and power cables.
- **Price:** USD 8 each
- **Penetrations:** IP68 cable glands for all wire entries into the main enclosure.
- **Price:** USD 3 each

---

## 9. Complete Bill of Materials (BOM)

### Table 1: Tractor Auto-Steer Retrofit (Tier A)
| Component | Supplier | Unit Price (USD) | Qty | Total Price (USD) |
| :--- | :--- | :--- | :--- | :--- |
| Compute: Raspberry Pi 4 (4GB) | Adafruit | 75.00 | 1 | 75.00 |
| GPS: Ardusimple simpleRTK2B | Ardusimple | 175.00 | 1 | 175.00 |
| Antenna: u-blox ANN-MB-00 | Digi-Key | 49.00 | 1 | 49.00 |
| Interface: CANable Pro | Tindie | 45.00 | 1 | 45.00 |
| IMU: ICM-42688-P Breakout | SparkFun | 25.00 | 1 | 25.00 |
| Power: Pololu 12V Regulator | Pololu | 25.00 | 1 | 25.00 |
| Enclosure: Hammond IP67 | Mouser | 80.00 | 1 | 80.00 |
| Connectors/Wiring | Various | 50.00 | 1 | 50.00 |
| **Total Hardware Cost** | | | | **$524.00** |

### Table 2: Excavator Autonomous Arm (Tier B)
| Component | Supplier | Unit Price (USD) | Qty | Total Price (USD) |
| :--- | :--- | :--- | :--- | :--- |
| Compute: Jetson Orin Nano | NVIDIA | 499.00 | 1 | 499.00 |
| Vision: RealSense D435i | Intel | 179.00 | 2 | 358.00 |
| LiDAR: Livox Mid-360 | DJI | 999.00 | 1 | 999.00 |
| GPS: Ardusimple simpleRTK2B | Ardusimple | 175.00 | 1 | 175.00 |
| Comm: Peplink MAX BR1 Mini | Peplink | 299.00 | 1 | 299.00 |
| Hydraulic Interface (CAN) | Tindie | 45.00 | 2 | 90.00 |
| Power/Enclosure/Wiring | Various | 250.00 | 1 | 250.00 |
| **Total Hardware Cost** | | | | **$2,670.00** |

### Table 3: Combine Harvester AI Package (Tier C)
| Component | Supplier | Unit Price (USD) | Qty | Total Price (USD) |
| :--- | :--- | :--- | :--- | :--- |
| Compute: Jetson AGX Orin | NVIDIA | 899.00 | 1 | 899.00 |
| Vision: RealSense D435i | Intel | 179.00 | 4 | 716.00 |
| LiDAR: Ouster OS0-32 | Ouster | 3000.00 | 1 | 3000.00 |
| Thermal: FLIR Lepton 3.5 | Digi-Key | 249.00 | 1 | 249.00 |
| GPS: Ardusimple simpleRTK2B | Ardusimple | 175.00 | 2 | 350.00 |
| Comm: Peplink MAX BR1 Mini | Peplink | 299.00 | 1 | 299.00 |
| Power/Enclosure/Wiring | Various | 400.00 | 1 | 400.00 |
| **Total Hardware Cost** | | | | **$5,913.00** |
