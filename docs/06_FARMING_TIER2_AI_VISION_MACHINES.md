# AGRO-AI Architecture: Tier 2 Farming Equipment (AI Vision & Self-Propelled Machines)

## Overview
This document outlines the architecture, hardware, software, and AI training pipelines for Tier 2 Farming Equipment within the AGRO-AI ecosystem. Tier 2 encompasses self-propelled machines that require advanced AI computer vision and localized automation, moving beyond simple GPS auto-steer. 

The platforms covered in this document are:
1. Self-Propelled Boom Sprayer (Flagship Product)
2. Precision Planter
3. Windrower / Swather
4. Grain Cart / Auger Wagon
5. Mixer Wagon / TMR Feeder

---

## 1. SELF-PROPELLED BOOM SPRAYER — THE FLAGSHIP FARMING PRODUCT
**(Target Platforms: John Deere R4045, Case IH Patriot 4440, AGCO RoGator C Series)**

This product represents the highest Return on Investment (ROI) for modern row-crop farmers, providing chemical savings that pay for the system in a single season.

### 1.1 The Spot-Spraying Problem
* **Traditional Approach**: A conventional sprayer applies herbicide continuously across the entire field, regardless of weed presence. This coats every square meter, wasting expensive chemicals on bare soil and healthy crops. This results in $50-$80/acre in chemical waste.
* **Smart Spot-Spray (AGRO-AI Approach)**: Utilizing edge AI, cameras detect specific weeds in real-time. The system triggers individual nozzles to pulse precisely over the weed, resulting in 70%-90% herbicide savings.
* **Market Context**: John Deere's "See & Spray Ultimate" retails as an approximate USD 100,000 add-on.
* **AGRO-AI Target**: A robust, aftermarket retrofit or OEM-agnostic system targeting a retail price of USD 15,000 - 25,000, bringing advanced vision to mid-sized farms.

### 1.2 Computer Vision Pipeline
The system relies on a high-throughput, low-latency vision pipeline running on the edge.

* **Cameras**: 12x Raspberry Pi Camera Module 3 Wide, spaced evenly along the boom sections. Mounted facing downward.
* **Camera Geometry**: Height from ground: 50cm. Field of View (FOV): 120 degrees.
* **Resolution & Framerate**: Raw capture at 1920x1080 @ 30fps. Images are center-cropped and resized to 640x640 for YOLO inference.
* **AI Model**: YOLOv8s (Small) optimized with TensorRT. Runs one instance per camera or multiplexed across an NVIDIA Jetson Orin Nano.
* **Classes**: `[0: crop_row, 1: weed, 2: bare_soil, 3: crop_plant]`
* **Latency Budget**: Inference time must be <33ms per camera to keep up with the 30fps stream. Total system latency (camera -> inference -> nozzle actuation) must be <50ms.
* **Training Dataset**: 5,000 meticulously annotated images differentiating weeds from crops.
* **Data Sources**: PlantVillage, iNaturalist, and custom field-collected photos.
* **Data Augmentation Strategies**: Random brightness (±30%), contrast variations, random rotation (±15 degrees), Gaussian blur (for motion blur simulation during fast driving), and simulated shadow overlays to account for changing weather.

### 1.3 YOLO Training Details (Google Colab T4 Pipeline)
The model is trained in the cloud and deployed to the edge. The following details the pipeline using a Google Colab T4 instance.

* **Base Model**: YOLOv8s pretrained on the COCO dataset.
* **Fine-tuning**: Transfer learning onto the custom weed/crop dataset.
* **Hyperparameters**: 100 epochs, batch size 16, image size 640x640, learning rate 0.01 (SGD).
* **Training Time**: Expected 3-4 hours on a Colab T4 GPU for 5,000 images.
* **Performance Target**: Validation mAP (mean Average Precision) >85% on a held-out test set (IoU 0.50).
* **Deployment Format**: Exported to `.engine` format using NVIDIA TensorRT for FP16 precision inference on the Jetson Orin Nano.

#### Colab Training Code Outline
```python
# 1. Install dependencies
!pip install ultralytics roboflow

# 2. Import YOLO
from ultralytics import YOLO
import torch

# 3. Download Dataset (e.g., from Roboflow)
from roboflow import Roboflow
rf = Roboflow(api_key="YOUR_API_KEY")
project = rf.workspace("agro-ai").project("weed-detection")
dataset = project.version(1).download("yolov8")

# 4. Initialize Model
model = YOLO('yolov8s.pt') # Load pretrained weights

# 5. Train Model
results = model.train(
    data=f"{dataset.location}/data.yaml",
    epochs=100,
    imgsz=640,
    batch=16,
    device=0, # T4 GPU
    name="agro_ai_sprayer_v1",
    augment=True,
    hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, # Augmentations
    degrees=15.0, translate=0.1, scale=0.5, shear=0.0,
    flipud=0.0, fliplr=0.5, mosaic=1.0, mixup=0.0
)

# 6. Validate
metrics = model.val()
print(f"mAP50: {metrics.box.map50}")

# 7. Export to ONNX (Intermediate step before TensorRT on Jetson)
success = model.export(format='onnx', half=True)
```

### 1.4 Boom Nozzle Control Hardware
Converting AI predictions into physical spraying action requires precise, microsecond-accurate hardware.

* **Boom Configuration**: Assume a standard boom divided into 36 individual nozzle sections (1 nozzle per 50cm).
* **Valves**: TeeJet DSV25 Pulse-Width Modulation (PWM) nozzle valves (approx USD 18 each). These allow variable rate application and fast on/off switching.
* **Controller**: A custom PCB based on the Arduino Mega 2560 microcontroller.
* **Actuation Topology**: The Arduino controls the 36 high-current solenoid valves using an array of 10x 74HC595 shift registers and MOSFET driver stages.
* **Communication Link**: The NVIDIA Jetson Orin Nano communicates with the Arduino via a high-speed USB Serial link (baud rate: 1,000,000), sending a 36-bit bitmask of nozzle states at 30Hz.
* **Timing & GPS Look-ahead**: 
  * At a spraying speed of 15 km/h (4.16 m/s), a delay of 50ms means the boom travels 20cm.
  * The cameras view the ground approximately 1.5m *ahead* of the physical nozzle position.
  * A software delay buffer, informed by the u-blox F9P RTK GPS speed and heading, calculates exactly *when* the physical nozzle will pass over the coordinate where the camera saw the weed, triggering the pulse at that exact millisecond.

#### Hardware Schematic (ASCII)
```text
Jetson Orin Nano  -->  USB Serial  -->  Arduino Mega 2560
(YOLO Inference)       (1M baud)        (Nozzle Timing logic)
                                              |
                                              v
                                       74HC595 Shift Registers (x10)
                                              |
                                              v
                                       MOSFET Bank (IRLZ44N) x36
                                              |
                                              v
                                       TeeJet DSV25 PWM Solenoid Valves (x36)
```

#### Nozzle Control Firmware Snippet (C++)
```cpp
// Arduino Mega Nozzle Control Firmware snippet
#define NUM_NOZZLES 36
uint8_t latchPin = 8;
uint8_t clockPin = 12;
uint8_t dataPin = 11;

void setup() {
    Serial.begin(1000000); // 1M baud for low latency
    pinMode(latchPin, OUTPUT);
    pinMode(clockPin, OUTPUT);
    pinMode(dataPin, OUTPUT);
}

void loop() {
    if (Serial.available() >= 5) { // Expecting 5 bytes (40 bits, 36 used)
        uint8_t buffer[5];
        Serial.readBytes(buffer, 5);
        
        digitalWrite(latchPin, LOW);
        for(int i=4; i>=0; i--) {
            shiftOut(dataPin, clockPin, MSBFIRST, buffer[i]);
        }
        digitalWrite(latchPin, HIGH); // Apply all nozzle states instantly
    }
}
```

### 1.5 ROS2 Architecture for Sprayer
The system uses ROS2 Humble for asynchronous messaging between components.

```text
[ROS2 Node Graph - Spot Sprayer]

  +-------------------+        +--------------------+
  | camera_driver_01  | -----> |                    |
  +-------------------+ image  |                    |        +-------------------+
          ...                  |    yolo_detector   | -----> |                   |
  +-------------------+        |  (TensorRT infer)  | bboxes | nozzle_controller | ---> [Arduino Serial]
  | camera_driver_12  | -----> |                    |        |  (Delay Buffer)   |
  +-------------------+ image  +--------------------+        +-------------------+
                                                                       ^
  +-------------------+                                                |
  |    gps_driver     | -----------------------------------------------+
  |  (u-blox F9P)     |  odom / speed / heading
  +-------------------+
           |
           v
  +-------------------+
  |  coverage_mapper  |  <--- Logs sprayed coordinates for farmer dashboards
  +-------------------+
```

**ROS2 Topic Definitions**:
* `/camera_N/image_raw` (`sensor_msgs/msg/Image`): 640x640 RGB image at 30fps.
* `/vision/weed_detections` (`vision_msgs/msg/Detection2DArray`): Bounding boxes and class probabilities.
* `/gps/fix` (`sensor_msgs/msg/NavSatFix`): RTK GPS coordinates.
* `/gps/vel` (`geometry_msgs/msg/TwistWithCovarianceStamped`): Vehicle velocity vector.
* `/hardware/nozzle_cmd` (`std_msgs/msg/UInt64`): Bitmask where each bit represents a nozzle on/off state.

**Launch File Structure (`sprayer_bringup.launch.py`)**:
Initializes 12 camera drivers, 1 batched TensorRT YOLO node, the GPS driver, and the hardware interface node, setting real-time scheduling priorities for the hardware interface.

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    nodes = []
    
    # Launch 12 Camera nodes
    for i in range(1, 13):
        nodes.append(
            Node(
                package='v4l2_camera',
                executable='v4l2_camera_node',
                name=f'camera_driver_{i:02d}',
                parameters=[{'video_device': f'/dev/video{i}'}]
            )
        )
        
    # TensorRT YOLO Node
    nodes.append(
        Node(
            package='agro_ai_vision',
            executable='trt_yolo_node',
            name='yolo_detector',
            parameters=[{'model_path': '/opt/agro_ai/models/weed_yolov8s.engine'}]
        )
    )
    
    # Hardware Interface
    nodes.append(
        Node(
            package='agro_ai_hardware',
            executable='nozzle_controller',
            name='nozzle_controller',
            parameters=[{'serial_port': '/dev/ttyACM0', 'baud_rate': 1000000}]
        )
    )
    
    return LaunchDescription(nodes)
```

### 1.6 Training Data Collection Strategy
A robust model requires field-specific data.
* **How farmer collects images**: A specialized mode in the AGRO-AI cab display allows the farmer to drive the field slowly (5 km/h) before spraying. The system logs raw images along with GPS tags.
* **Labeling**: Images are uploaded via LTE to Roboflow. Farmers or remote annotators draw bounding boxes around prevailing weed species.
* **Transfer Learning Pipeline**: The base model (trained on generalized mid-western weeds) is fine-tuned for 20 epochs on the specific farm's dataset. This "Farm-Specific Fit" takes <1 hour on the cloud backend and pushes a new `.engine` file OTA to the Jetson.

---

## 2. PRECISION PLANTER
**(Target Platforms: John Deere ExactEmerge, Case IH Early Riser)**

Precision planters operate at high speeds (up to 10 mph) and require microsecond timing to achieve uniform seed spacing.

* **Row-by-Row Control**: Traditional planters are mechanically linked. Tier 2 planters utilize electric motors on each row unit to control seed metering independently.
* **Population Prescription**: An ISOBUS Task Controller (TC) reads a shapefile mapping desired seed population density to GPS coordinates. As the planter moves, the seeding rate adjusts dynamically based on soil type zones.
* **Skip Compensation**: If an optical sensor in the seed tube detects a missed seed (a "skip"), the system immediately accelerates the meter to place a makeup seed, maintaining total population.
* **Down-Force Control**: Electro-pneumatic or hydraulic cylinders dynamically adjust the downward pressure on each row unit. Load pins measure ground contact, ensuring consistent planting depth regardless of soil compaction.
* **Singulation Monitoring**: Dual-beam optical sensors count every single seed dropping through the tube, reporting doubles or skips to the cab monitor.
* **AI Addition (Computer Vision)**: Cameras mounted facing rearward analyze the closed trench post-planting. Using a YOLO model trained to detect clods, open trenches, and exposed seeds, it provides a real-time "Trench Quality Score".
* **Training Time**: Training the trench-quality model on a Colab T4 takes approximately 2-3 days for a dataset of 15,000 images covering various soil types and moisture levels.

#### Trench Quality Vision Pipeline
```text
[Camera Rear View] -> [Image Preprocessing (Auto Exposure/White Balance)] -> [YOLOv8 Trench Model]
                                                                                      |
                                                                                      v
                                                                        [Metrics Aggregation]
                                                                        - Exposed Seed Count
                                                                        - Clod Density
                                                                        - Trench Closure %
                                                                                      |
                                                                                      v
                                                                           [Cab UI Display]
```

---

## 3. WINDROWER / SWATHER
**(Target Platforms: MacDon FD145 + M205, John Deere W155)**

Self-propelled windrowers cut crop and lay it in fluffy rows (windrows) to dry before harvesting or baling.

* **Auto-Steer Integration**: Utilizes the standard AGRO-AI RTK-GPS architecture for centimeter-level steering, ensuring no overlap and maximum cutting width utilization.
* **Header Height Control (HHC)**: Uses an array of ultrasonic sensors pointing at the ground. A PID controller adjusts hydraulic lift cylinders to maintain a strict 5cm cutting height over highly uneven terrain, preventing soil ingestion.
* **Automatic Header Reverser**: Torque sensors on the hydraulic drives monitor the header reel and draper canvas. If a sudden spike in torque indicates a crop plug (bunching), the controller automatically halts forward motion, reverses the header hydraulics to spit out the plug, and resumes.
* **Crop Sensing (Moisture/Yield)**: Near-Infrared (NIR) sensors mounted in the conditioning rolls measure the moisture content of the crop as it is cut, generating a moisture map.
* **RL Agent for HHC**: Training an advanced Reinforcement Learning (RL) agent (e.g., PPO) to predictively adjust header height based on forward-looking LiDAR (anticipating bumps rather than reacting to them).
* **Training**: 3-4 days on Colab T4 for the header height RL agent simulating terrain profiles and hydraulic system latency.

#### RL Agent State & Action Space for HHC
* **State Space ($S_t$)**: Current header height (m), hydraulic pressure (psi), pitch angle (rad), LiDAR forward terrain profile (vector of 10 points ahead), current vehicle speed (m/s).
* **Action Space ($A_t$)**: Continuous control signal [-1.0, 1.0] for proportional hydraulic lift valve.
* **Reward Function ($R_t$)**: Penalty for cutting height deviating from 5cm, massive penalty for ground contact (header crash).

---

## 4. GRAIN CART / AUGER WAGON
**(Target Platforms: Kinze 1100, Unverferth 1115)**

The "Follow-Me" grain cart solves the critical labor shortage of requiring a skilled tractor operator to drive perfectly parallel to a moving combine during unloading.

* **The Challenge**: The combine harvester never stops. The grain cart must drive alongside it, maintain a precise distance, and match speed, while avoiding field obstacles.
* **Follow-Me GPS (V2V Communication)**: The combine harvester broadcasts its RTK-GPS position, heading, and speed over a localized 900MHz LoRa radio link (V2V). 
* **Formation Driving**: The grain cart's controller receives this stream and computes a target offset coordinate (e.g., exactly 3.0 meters to the left, 1.0 meters behind the combine's spout). A pure-pursuit algorithm drives the tractor steering and throttle to hold this formation at 6 km/h.
* **Auger Automation**: Using a stereo camera on the combine's spout looking down at the grain cart, a vision model detects the fill level of the cart. It automatically swings the auger spout to fill the cart evenly from front to back, preventing spilling.
* **Training**: 4-5 days on Colab T4 for the formation driving controller and the auger fill-level volume estimation model.

#### V2V Comm Packet Structure
```json
// Example LoRa Packet transmitted at 10Hz by the Combine
{
  "timestamp_ms": 1691234567890,
  "vehicle_id": "COMBINE_ALPHA",
  "gps": {
    "lat": 41.8781,
    "lon": -87.6298,
    "alt_m": 182.5,
    "heading_deg": 45.2,
    "rtk_status": "FIX"
  },
  "velocity": {
    "speed_kph": 6.2,
    "yaw_rate_rads": 0.01
  },
  "status": {
    "grain_tank_level": 85,
    "auger_extended": true
  }
}
```

---

## 5. MIXER WAGON / TMR FEEDER
**(Target Platforms: Trioliet Trio Feedlane, BvL V-Mix)**

Automating feeding on livestock farms reduces daily manual labor and ensures consistent feeding schedules for dairy cows.

* **Environment**: Operates indoors/outdoors on concrete, driving through narrow barn aisles between cow stalls.
* **Navigation (LiDAR SLAM)**: GPS is unreliable indoors. The machine uses 2D/3D LiDAR (e.g., Ouster OS1 or Sick TiM) for SLAM (Simultaneous Localization and Mapping). The farmer drives the route manually once; the system records the point cloud map. It then navigates autonomously using AMCL (Adaptive Monte Carlo Localization) or cartographer.
* **Feed Level Detection**: A side-facing camera analyzes the feed bunk in front of the cows. A semantic segmentation model detects empty concrete vs. remaining feed. 
* **Variable Discharge**: As the wagon drives autonomously down the aisle, it modulates the variable-speed discharge conveyor to deposit more feed in areas where the cows have eaten it all, and less where feed remains.
* **Training**: 2-3 days on Colab T4 to train the semantic segmentation model (UNet or YOLOv8-Seg) for TMR feed vs. concrete detection in various barn lighting conditions.

#### Semantic Segmentation Architecture
* **Input**: 640x480 RGB image from side-facing barn camera.
* **Model**: YOLOv8-Seg (segmentation variant).
* **Classes**: `Feed_TMR`, `Concrete_Floor`, `Cow_Head`, `Stall_Barrier`.
* **Output Processing**: Calculate the pixel area ratio of `Feed_TMR` to `Concrete_Floor` in the designated feed bunk region of interest (ROI). Map this ratio to a proportional control signal for the discharge conveyor speed.

---

## 6. HARDWARE BOM FOR SMART SPRAYER

This Bill of Materials (BOM) highlights the aggressive cost optimization of the AGRO-AI system compared to legacy OEM solutions.

| Component | Quantity | Unit Cost (USD) | Total Cost (USD) | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Raspberry Pi Camera Module 3 Wide | 12 | $35.00 | $420.00 | 120 deg FOV, global shutter preferred if available. |
| NVIDIA Jetson Orin Nano 8GB | 1 | $499.00 | $499.00 | Main AI Inference Engine. Runs 12x YOLO streams. |
| TeeJet DSV25 Solenoid Valves | 36 | $18.00 | $648.00 | PWM capable, high flow rate, chemical resistant. |
| Arduino Mega 2560 (Clone/Custom) | 1 | $45.00 | $45.00 | Handles hard real-time IO and PWM generation. |
| u-blox F9P RTK GPS Module | 1 | $149.00 | $149.00 | Centimeter-level positioning for nozzle timing. |
| 74HC595 Shift Register ICs | 10 | $1.20 | $12.00 | Expands Arduino GPIO to drive 36 MOSFETs. |
| MOSFETs (IRLZ44N or similar) | 36 | $0.80 | $28.80 | High current drivers for 12V solenoids. |
| IP67 Aluminum Electronics Enclosure | 1 | $80.00 | $80.00 | Dust/Waterproof for harsh agricultural environments. |
| Custom Cable Harness & Connectors | 1 | $200.00 | $200.00 | Weatherpak connectors, shielded twisted pair for cameras. |
| Power Management IC (PMIC) / DCDC | 1 | $60.00 | $60.00 | 12V automotive power conditioning, surge protection. |
| Heat Sinks & Thermal Paste | 1 | $15.00 | $15.00 | Passive cooling for the Orin Nano module. |
| **TOTAL HARDWARE COST** | | | **~$2,156.80** | |

* **AGRO-AI Suggested Retail Price**: USD $18,000 - $25,000
* **Competitor Benchmark (John Deere See & Spray)**: ~USD $100,000
* **Value Proposition**: The AGRO-AI system achieves 95% of the performance of OEM systems at 20% of the cost, making edge-AI precision agriculture accessible to mid-tier farming operations globally. This disruption creates a high-margin, scalable software-as-a-service (SaaS) business model around the subscription for updated seasonal weed models.

---

## 7. CLOUD TO EDGE OVER-THE-AIR (OTA) UPDATES

Ensuring that remote farming equipment receives the latest model updates reliably over intermittent cellular connections requires a resilient OTA architecture.

### 7.1 OTA Architecture Setup
* **Update Server**: AWS IoT Greengrass or Azure IoT Edge serves as the backbone for managing fleet updates.
* **Payload Generation**: After cloud training on Colab T4, the updated weights are automatically compiled into TensorRT `.engine` files.
* **Delta Updates**: To save cellular data (which can be expensive in rural areas), updates utilize binary delta encoding (e.g., `bsdiff` or `mender-artifact`), ensuring that only changes in the neural network weights and system configuration files are transmitted.
* **Rollback Mechanism**: Utilizing A/B partition schemes on the Jetson Orin Nano, if a downloaded model fails to initialize correctly or causes segmentation faults, the system reverts to the previously working partition automatically.

### 7.2 Telemetry & Diagnostics Pipeline
Continuous monitoring of machine health and model performance in the field is vital.
* **Data Collected**: Engine RPM, hydraulic temperature, AI confidence scores, inference latency, camera temperatures, GPS fix status.
* **Protocol**: MQTT over LTE/5G.
* **Dashboard**: Hosted on Grafana for support technicians, displaying real-time geographic distribution of active sprayers and potential faults.

---

## 8. SAFETY AND FUNCTIONAL SAFETY (ISO 25119)

Agricultural machinery presents significant safety risks due to size and autonomy. The system complies with the principles of ISO 25119 (Tractors and machinery for agriculture and forestry — Safety-related parts of control systems).

### 8.1 Failsafe Mechanisms
* **Heartbeat Monitoring**: The Arduino and the Jetson Orin Nano exchange a 10Hz heartbeat over the serial link. If the Jetson hangs, the Arduino automatically defaults all sprayer nozzles to OFF within 150ms.
* **E-Stop Integration**: Physical hardware emergency stop buttons in the cab and on the exterior of the machine are hardwired to cut power directly to the implement's hydraulic solenoids or electric actuators.
* **Geofencing Verification**: Before the autonomous system can activate, it checks its RTK GPS coordinates against a predefined KML boundary file. If the machine breaches the boundary, operation halts immediately.

### 8.2 Redundancy in Vision
* **Camera Blindness**: If mud or debris obscures a camera lens, the YOLO object detector confidence drops significantly, or the image becomes homogeneously brown. A secondary anomaly detection algorithm flags the lens as obstructed and notifies the operator. It may optionally fall back to a "broadcast spray" mode for that specific boom section until cleaned.

---

## 9. SIMULATION ENVIRONMENTS (NVIDIA ISAAC SIM)

Prior to field deployment, all software updates are verified in simulation to reduce risk and accelerate development.

### 9.1 Isaac Sim Integration
* **Digital Twin**: High-fidelity 3D models of the Boom Sprayer and Mixer Wagon are imported into NVIDIA Isaac Sim.
* **Crop and Weed Generation**: Procedural generation algorithms create varied fields with randomized weed placement, crop rows, soil textures, and lighting conditions (time of day, shadows from clouds).
* **Sensor Simulation**: Virtual cameras simulate the exact field of view, distortion, and noise characteristics of the Raspberry Pi Camera Module 3. GPS simulation includes RTK drift and multipath errors.
* **ROS2 Bridging**: Isaac Sim interfaces natively with the AGRO-AI ROS2 stack. The `camera_driver` nodes subscribe to synthetic images from the simulator rather than physical hardware.
* **CI/CD Pipeline**: Every pull request triggering a new model version initiates an automated test run in Isaac Sim. The sprayer must navigate a 10-acre virtual field and achieve >90% weed hit rate and <5% crop damage rate before the PR can be merged.

---

## 10. DEPLOYMENT AND CALIBRATION PROCEDURE

Field setup is streamlined to allow non-technical operators to commission the system quickly.

### 10.1 System Calibration
1. **Camera Alignment**: Using a checkerboard pattern laid on the ground under the boom, the system runs an automated extrinsic calibration routine to compute the exact projection matrix mapping pixels to real-world coordinates relative to the GPS antenna.
2. **Latency Tuning**: The operator runs a single boom section over a water-sensitive paper strip at operational speed. The system fires a test pulse. The offset between the intended target and the actual water mark allows the software to fine-tune the delay buffer (compensating for mechanical solenoid activation latency).
3. **Flow Rate Verification**: Standard catch-test procedures are used to verify that the PWM duty cycle maps accurately to the requested volume per hectare.

### 10.2 Continuous Learning Loop
The system embraces a data flywheel effect:
* As farmers use the system, edge cases (e.g., newly evolved weed phenotypes, unusual soil colors) are automatically flagged by low-confidence model predictions.
* These image frames are saved locally and uploaded via Wi-Fi when the machine returns to the barn.
* The AGRO-AI data team annotates these edge cases, pushing them back into the Colab T4 training pipeline to continuously improve the baseline model for all users in the region.

---

## 11. SOFTWARE DEPENDENCIES AND NETWORK TOPOLOGY

The system relies on modern AI and robotics software stacks.

### 11.1 Key Software Dependencies

| Component | Software / Library | Version | Purpose |
| :--- | :--- | :--- | :--- |
| OS | Ubuntu Linux | 22.04 LTS | Operating System on Jetson |
| Middleware | ROS2 | Humble Hawksbill | Inter-process communication |
| AI Framework | PyTorch / TensorRT | 2.0 / 8.5 | Model training & edge inference |
| Computer Vision | OpenCV | 4.8.0 | Image processing & camera I/O |
| Microcontroller | Arduino Core | 1.8.x | Firmware for Mega 2560 |
| V2V Comms | LoRaWAN stack | Custom | P2P radio link for Grain Cart |

### 11.2 Typical Diagnostic Codes (Troubleshooting Guide)

| Error Code | Component | Description | Action Required |
| :--- | :--- | :--- | :--- |
| `ERR_VIS_01` | Camera Array | Node 04 failed to publish frames | Check shielding on cam 04 cable. |
| `ERR_GPS_12` | RTK Receiver | RTK Fix lost (Float/Single) | Wait for satellite lock, check NTRIP. |
| `ERR_SER_03` | Arduino Mega | Serial CRC mismatch | Inspect USB link, check for EMI. |
| `ERR_MOD_99` | YOLO Infer | TensorRT context failure | Soft reboot Jetson device. |

---

## 12. POWER DISTRIBUTION AND WIRING HARNESS

In agriculture, 90% of field failures are due to wiring and connector issues. AGRO-AI mitigates this with a robust power architecture.

### 12.1 Power Architecture
* **Source**: The tractor/implement's 12V or 24V DC alternator system.
* **Filtering**: A heavy-duty DC-DC converter (Mean Well or similar) isolates the sensitive Jetson and Arduino electronics from massive voltage spikes caused by the tractor's starter motor and large hydraulic solenoids.
* **Camera Cabling**: Uses industrial Ethernet (M12 X-coded) or Shielded Twisted Pair (STP) cables to prevent Electro-Magnetic Interference (EMI) from degrading the high-speed MIPI CSI-2 or USB camera signals.
* **Solenoid Cabling**: Heavy-gauge wires (14 AWG) route power to the PWM solenoids to minimize voltage drop over the 30-meter boom length.

### 12.2 Environmental Sealing
* **Connectors**: All external connections use Deutsch DT series or Amphenol IP67 rated automotive connectors.
* **Enclosures**: The main compute box is an extruded aluminum enclosure (IP67) acting as a massive heatsink for the Jetson Orin Nano, eliminating the need for cooling fans which would ingest dust.

---

## 13. FIELD DATA STORAGE AND PRIVACY (FARMER DATA OWNERSHIP)

Data privacy is a major concern for modern farmers who fear OEM lock-in and corporate surveillance. AGRO-AI differentiates by adopting a farmer-first data policy.

### 13.1 Local Storage
* All raw camera feeds and high-resolution weed maps are stored locally on a 1TB ruggedized SSD inside the implement enclosure.
* Data is not automatically uploaded to the cloud without explicit opt-in.

### 13.2 Anonymization
* If the farmer opts in to the "Community Learning Pool" (sharing edge cases to improve the global AI model), all GPS coordinates and farm identifiers are scrubbed from the images *before* they leave the edge device.

### 13.3 Exportability
* The weed density maps and chemical usage logs are exported in standard open formats (GeoJSON, shapefiles, ISO-XML) rather than proprietary encodings. This allows the farmer to import their data into independent Farm Management Information Systems (FMIS) like QGIS or AgLeader SMS.

---

## Appendix A: Detailed Cloud Training Cost Estimations

### AWS Infrastructure Estimations for Training
* **Compute Instance**: p3.2xlarge (1x NVIDIA V100 GPU)
* **Spot Instance Price**: ~$0.91/hr
* **Average Training Job**: 4 hours per specific weed model
* **Cost per model version**: ~$3.64
* **Storage**: Amazon S3 standard tier for datasets (approx $0.023 per GB/month). An average dataset of 100,000 images is around 50GB, leading to minimal storage costs.

### Google Cloud Infrastructure (Colab Pro+ / Vertex AI)
* **Compute Instance**: n1-standard-4 with 1x NVIDIA T4 GPU
* **Preemptible Price**: ~$0.11/hr
* **Average Training Job**: 5 hours
* **Cost per model version**: ~$0.55 (Highly optimized for initial R&D and smaller datasets)

## Appendix B: Glossary of Terms
* **RTK (Real-Time Kinematic)**: Satellite navigation technique used to enhance the precision of position data derived from satellite-based positioning systems, up to centimeter-level accuracy.
* **PWM (Pulse-Width Modulation)**: A method of reducing the average power delivered by an electrical signal, by effectively chopping it up into discrete parts, used here to control flow through the nozzle solenoid.
* **ISOBUS (ISO 11783)**: The standard communication protocol for the agriculture industry. It enables tractors, implements, and farm management software to communicate seamlessly.
* **SLAM (Simultaneous Localization and Mapping)**: Computational problem of constructing or updating a map of an unknown environment while simultaneously keeping track of an agent's location within it, critical for indoor robotic operations like the TMR Feeder.

---
*Document Version: 1.4.0*
*Author: Senior Systems Architect, AGRO-AI*
*Confidentiality: Internal Use Only*
*Status: Approved for Engineering Handoff*
