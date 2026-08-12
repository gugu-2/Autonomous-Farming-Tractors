# AGRO-AI TIER 1 CONSTRUCTION EQUIPMENT ARCHITECTURE: STATIONARY ARMS

This document outlines the architecture for Tier 1 construction equipment automation within the AGRO-AI project. Tier 1 equipment comprises machines with stationary arm control (where primary operation does not require continuous driving/locomotion during the core task execution). This includes Excavators, Backhoe Loaders, Telehandlers, Trenchers, Drillers/Augers, and Pipelayers.

---

## A. EXCAVATOR / JCB (e.g., CAT 320, JCB 220X, Hitachi ZX210)

### 1. Mechanical Overview
The excavator arm is modeled as a 4-Degree-of-Freedom (DOF) robotic manipulator.
- **Joint 1: Cabin Swing (Yaw):** 360-degree continuous rotation.
- **Joint 2: Boom (Pitch):** Primary lifting mechanism, driven by two parallel hydraulic cylinders. Typical range: -45° to +60° relative to horizontal.
- **Joint 3: Stick/Dipper (Pitch):** Extends reach, driven by a single hydraulic cylinder. Typical range: -120° to +30° relative to boom.
- **Joint 4: Bucket (Pitch):** Controls digging angle, driven by a single cylinder with linkage. Typical range: -180° to +45° relative to stick.

**Typical Digging Forces (20-ton class):**
- Bucket Breakout Force: ~150 kN
- Stick Tearout Force: ~105 kN

### 2. AI Problem Formulation
We frame the excavation task as a continuous control Reinforcement Learning (RL) problem.

- **State Space (S):** Continuous vector of size 20.
  - Joint Angles (4): $[\theta_{swing}, \theta_{boom}, \theta_{stick}, \theta_{bucket}]$
  - Joint Velocities (4): $[\dot{\theta}_{swing}, \dot{\theta}_{boom}, \dot{\theta}_{stick}, \dot{\theta}_{bucket}]$
  - Bucket Tip 3D Position (3): $[x, y, z]$ in local cabin frame
  - Target Excavation Point (3): $[x_{target}, y_{target}, z_{target}]$
  - Target Dump Point (3): $[x_{dump}, y_{dump}, z_{dump}]$
  - Nearest Obstacle Vector (3): Relative distance $[dx, dy, dz]$ to closest collision threat (from LiDAR/vision).

- **Action Space (A):** Continuous vector of size 4.
  - Proportional Valve Commands (4): $[V_{swing}, V_{boom}, V_{stick}, V_{bucket}]$, each clamped to $[-1.0, 1.0]$. 
    - 0.0 = Valve closed (hold position)
    - 1.0 = Max flow in positive direction (e.g., boom up)
    - -1.0 = Max flow in negative direction (e.g., boom down)

- **Reward Function (R):**
  - $R_{progress}$: $+10 \times \Delta(\text{distance to target})$ for moving bucket tip towards target.
  - $R_{digging}$: $+100$ for successfully scooping volume (estimated via pressure drop/force feedback upon curling bucket in soil).
  - $R_{dumping}$: $+100$ for opening bucket within 0.5m of dump target.
  - $R_{collision}$: $-500$ for arm collision with obstacle or self-collision.
  - $R_{spillage}$: $-20$ per timestep if bucket angle is pitched downwards while loaded and not at dump site.
  - $R_{energy}$: $-0.1 \times \sum (A_i^2)$ penalty for aggressive control (encourages smooth valve actuation).

### 3. Simulation Setup
- **Engine:** PyBullet (chosen for fast rigid body dynamics).
- **Model:** URDF (Unified Robot Description Format) derived from CAD of a standard 20-ton excavator.
- **Actuator Physics:** Modeled not as pure torque motors, but as hydraulic spring-dampers. We implement a custom PyBullet plugin to simulate fluid flow, valve deadbands (typically 10-15%), and non-linear pressure-force curves.
- **Soil Interaction:** Represented using a heightfield for terrain and a simplified resistive force model based on the Fundamental Earthmoving Equation (FEE) to compute draft forces based on cut depth and bucket width.

### 4. RL Algorithm Choice: PPO
- **Choice:** Proximal Policy Optimization (PPO) with continuous action spaces.
- **Why PPO over SAC/TD3?** 
  - *Stability:* PPO's trust region constraint prevents catastrophic policy updates, crucial for safety-critical heavy machinery. SAC (Soft Actor-Critic) often exhibits high variance in early training which can lead to wild, unpredictable arm flailing in sim, making sim-to-real transfer riskier.
  - *Sample Complexity:* While SAC is more sample efficient, we generate samples extremely fast in PyBullet. PPO scales better with distributed massive parallel rollouts (Vectorized Envs).
  - *Hyperparameter Robustness:* PPO requires significantly less tuning of learning rates and temperature parameters compared to SAC.

### 5. Network Architecture
- **Type:** Multi-Layer Perceptron (MLP).
- **Actor Network (Policy):**
  - Input: State vector (20)
  - Hidden Layers: 3 layers of sizes [512, 512, 256], activation: ReLU or Tanh.
  - Output: Mean vector $\mu$ (size 4), and a state-independent learned $\log(\sigma)$ vector (size 4) for exploration noise. Actions are sampled from $\mathcal{N}(\mu, \sigma)$ during training, deterministic $\mu$ during inference.
- **Critic Network (Value):**
  - Input: State vector (20)
  - Hidden Layers: 3 layers [512, 512, 256], activation: ReLU.
  - Output: Scalar Value $V(s)$.

### 6. Training Curriculum
To prevent local optima (like the arm just waving in the air to avoid collision penalties), we use Curriculum Learning:
1. **Stage 1 (Kinematic Reaching):** No soil. Agent learns to move bucket tip to random 3D coordinates.
2. **Stage 2 (Force Application):** Soil introduced. Agent learns to drag bucket through soil to overcome resistance without stalling.
3. **Stage 3 (Full Dig Cycle):** Target dig point -> Dig -> Move to dump point -> Open bucket.
4. **Stage 4 (Multi-cycle & Obstacles):** Continuous trenching operation with random obstacles (pipes, rocks) injected into the scene.

### 7. Sim-to-Real Transfer Strategy
Zero-shot transfer relies heavily on **Domain Randomization**:
- *Hydraulic Response Times:* Valve lag randomized between 50ms to 300ms.
- *Valve Deadbands:* Randomized between 5% and 20%.
- *Mass/Inertia:* Arm link masses randomized $\pm 15\%$.
- *Soil Resistance:* Cohesion and friction angle randomized to simulate clay, sand, and gravel.
- *Sensor Noise:* Gaussian noise injected into simulated IMU and joint encoders.

### 8. Hardware Specifications (Per Unit)
| Component | Make / Model | Purpose | Est. Cost (USD) |
| :--- | :--- | :--- | :--- |
| **Compute Node** | NVIDIA Jetson Orin Nano 8GB | Runs ROS2, Vision, RL Policy | $499 |
| **Depth Vision** | Intel RealSense D435i | Terrain mapping, obstacle detection | $179 |
| **GPS Antenna** | u-blox F9P RTK module | High-precision position (cm-level) | $149 |
| **RTK Base Board** | Ardusimple RTK2B | Handles RTCM corrections | $175 |
| **Valve DAC Board** | Custom (MCP4922 + Op-Amps) | Translates AI signals to 0-5V/4-20mA valve signals | $35 |
| **IMU / Tilt** | ICM-42688-P Breakout | High-freq chassis and boom tilt sensing | $25 |
| **CAN Bus Interface**| CANable Pro | Reads engine RPM, pressure sensors via J1939 | $45 |
| **Enclosure** | Custom IP67 Aluminum Box | Protects electronics from dust/rain/vibration | $80 |
| **TOTAL** | | | **~ $1,187** |

### 9. ROS2 Node Graph Architecture

```mermaid
graph TD
    A[realsense_camera_node] -->|Pointcloud2| B[terrain_mapping_node]
    C[gps_rtk_node] -->|NavSatFix| B
    D[imu_node] -->|Imu| E[state_estimator_node]
    F[can_j1939_node] -->|JointStates| E
    B -->|OccupancyGrid 3D| G[rl_policy_node]
    E -->|StateVector (20)| G
    G -->|ActionVector (4)| H[valve_controller_node]
    H -->|PWM/Voltage| I[Hydraulic Manifold]
```

**Key Topics:**
- `/perception/depth_pcl` (sensor_msgs/PointCloud2)
- `/localization/odom` (nav_msgs/Odometry)
- `/control/valve_cmds` (std_msgs/Float32MultiArray)
- `/machine/joint_states` (sensor_msgs/JointState)

### 10. Deployment Steps (Retrofit onto CAT 320)
1. **Hydraulic Intercept:** Splice custom DAC board into the pilot pressure lines between the cabin joysticks and the main control valve. Implement a physical safety bypass switch.
2. **Sensor Mounting:**
   - Mount Jetson enclosure securely in the cabin behind the seat.
   - Mount RealSense D435i on the cabin roof looking forward.
   - Mount GPS antenna on counterweight.
   - Attach string potentiometers or CAN encoders to Boom, Stick, and Bucket pivot pins.
3. **Calibration:** Run automated calibration script. The script pulses valves to measure deadbands and response curves mapping DAC voltage to joint velocity.
4. **Software Bring-up:** Start Dockerized ROS2 stack. Validate sensor streams. Engage AI control via dead-man switch on the joystick.

### 11. Google Colab T4 Training Script Outline
**Libraries:** `stable-baselines3`, `gymnasium`, `pybullet`, `numpy`, `torch`.

```python
# pseudo-code outline
import gymnasium as gym
import pybullet as p
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback

class ExcavatorEnv(gym.Env):
    def __init__(self):
        # Define action/observation space
        self.action_space = gym.spaces.Box(low=-1, high=1, shape=(4,))
        self.observation_space = gym.spaces.Box(low=-inf, high=inf, shape=(20,))
        # Load URDF
        self.excavatorId = p.loadURDF("excavator.urdf")
        
    def step(self, action):
        # Apply valve delays and non-linearities
        # Step pybullet simulation
        # Calculate rewards (progress, collision, energy)
        # Return obs, reward, done, info
        pass
        
    def reset(self):
        # Randomize domain (masses, friction)
        # Reset arm to random valid pose
        pass

# Vectorize environment for fast CPU simulation
env = SubprocVecEnv([lambda: ExcavatorEnv() for i in range(16)])

# Define MLP architecture
policy_kwargs = dict(net_arch=dict(pi=[512, 512, 256], vf=[512, 512, 256]))

model = PPO("MlpPolicy", env, verbose=1, policy_kwargs=policy_kwargs, 
            learning_rate=3e-4, n_steps=2048, batch_size=256)

checkpoint_callback = CheckpointCallback(save_freq=100000, save_path='./logs/')
model.learn(total_timesteps=50_000_000, callback=checkpoint_callback)
```

### 12. Expected Training Time
Using a Google Colab T4 GPU instance, simulating 16 environments in parallel, 50 million timesteps of PPO will take approximately **4-5 days running at 12 hours/day** (accounting for Colab session limits and checkpoints).

### 13. Performance Targets
- **Excavation Rate:** Achieve 85% of cubic meters per hour compared to an experienced human operator in standard topsoil.
- **Safety:** ZERO collision incidents with detected obstacles (pipes, fences) or self-collision (bucket hitting cabin).
- **Efficiency:** Smooth fluid motion minimizing hydraulic shock and pressure spikes.

---

## B. BACKHOE LOADER (e.g., JCB 3CX, CAT 416)

### 1. Unique Challenge: Two Separate Arms
A backhoe loader features a front loader bucket and a rear excavator-style backhoe. The challenge is handling two independent mechanical systems with different kinematics and tasks, operated from the same chassis.

**Solution:** Implement two distinct, independent RL agents.
- **Agent 1 (Front Loader Policy):** Trained for pushing, scooping from flat ground, and loading trucks.
- **Agent 2 (Rear Backhoe Policy):** Similar to the Excavator policy, trained for trenching and deep digging.

### 2. Switching Logic
The AI employs a high-level state machine (Behavior Tree) to manage which agent is active.
- **Task Assignment:** The user defines the job (e.g., "Trench 10m" vs. "Move spoil pile").
- **Seat Position / Mode:** Modern backhoes require the operator seat to swivel. The AI reads the seat position switch or a dedicated UI button.
- **Safety Lockout:** When Agent 1 is active, Agent 2's hydraulic manifold is electronically locked via relay, and vice versa. Only one arm moves at a time to maintain stability and prevent catastrophic fluid pressure drops.

### 3. Sub-system Configurations
- **Front Loader:** 2 DOF (Boom raise/lower, Bucket curl/dump). Action space size 2. State includes chassis pitch.
- **Rear Backhoe:** 4 DOF (Swing, Boom, Stick, Bucket). Architecture identical to Excavator (Section A). Stabilizer legs (outriggers) are controlled via a simple PID loop to level the chassis before Agent 2 engages.

### 4. Training Time
Training both policies sequentially. 
- Front Loader (2 DOF): ~1.5 days.
- Rear Backhoe (4 DOF): ~4.5 days.
- **Total Colab T4 Time:** ~6 days (12h/day).

---

## C. TELEHANDLER (e.g., JLG 742, Manitou MRT 2260)

### 1. Unique Challenge: Load Moment and Tipping Risk
Telehandlers feature a telescopic boom that greatly extends reach. The primary challenge is not complex trajectory planning, but dynamic stability. Extending a heavy load horizontally rapidly moves the Center of Gravity (CoG) forward, risking tipping.

### 2. Stability Envelope Calculation
The AI acts as an advanced Load Moment Indicator (LMI) and active constraint system.
- **Sensors:** Boom angle sensor, boom extension string pot, hydraulic pressure sensors on lift cylinders.
- **Calculation:** 
  $$\text{Load Moment} = \text{Payload Mass} \times g \times (\text{Boom Length} \times \cos(\text{Boom Angle}))$$
- **Safety Envelope:** The system maintains a 2D stability map based on the machine's load chart. If the RL policy attempts an action (e.g., extend boom) that approaches 90% of the tipping moment limit, the action is clamped.

### 3. Load Detection (Vision + Weight)
- **Weight Sensor:** Calculates payload mass dynamically using differential pressure between the bore and rod sides of the lift cylinder, adjusted for boom angle.
- **Computer Vision:** RealSense D435i mounted on the fork carriage runs a YOLOv8-nano model to identify payload types (e.g., "Standard Pallet", "Pipes", "Dirt Bucket"). This adjusts handling parameters (e.g., pipes require slower, smoother acceleration to prevent rolling).

### 4. Hardware Additions
- **Lift Cylinder Pressure Transducers (x2):** $80
- **Fork Load Cells (Optional direct measurement):** $120
- *(Other hardware identical to Excavator compute stack).*

### 5. Training Time
The RL agent here is primarily for semi-automated pallet fetching (aligning forks to pallet). It is a simpler 3-DOF task (Boom up/down, Boom in/out, Fork tilt).
- **Total Colab T4 Time:** 3-4 days.

---

## D. TRENCHER (e.g., Vermeer T655III, Ditch Witch RT45)

### 1. Control Strategy: Pure PLC + GPS
For trenchers, continuous RL is unnecessary overkill. The task is geometrically deterministic: cut a straight line at a constant depth. Neural networks introduce non-deterministic behavior which is undesirable here. We use pure GPS-guided Proportional-Integral-Derivative (PID) control via a Programmable Logic Controller (PLC) paradigm.

### 2. GPS Waypoint Path Execution
- **Interface:** User draws a line on a ruggedized tablet over a satellite map overlay (Google Maps API / QGIS backend).
- **Execution:** The coordinates are converted to local UTM. The vehicle steers using dual RTK GPS antennas to calculate heading. The steering cylinders follow a pure pursuit or Stanley controller algorithm to track the line.

### 3. Depth Control
- **Sensor:** An ultrasonic sensor or radar altimeter mounted on the main trencher boom measures distance to the ground surface.
- **Logic:** The operator sets target depth (e.g., 1.5m). The system compares boom angle + ultrasonic ground distance to calculate actual depth. A PID loop adjusts the boom lift cylinders to maintain exact depth regardless of terrain undulations.

### 4. PLC Code Logic (Pseudocode)
```iec-st
PROGRAM TrencherControl
VAR
    TargetDepth: REAL := 1.5;
    ActualDepth: REAL;
    BoomAngle: REAL;
    GroundDist: REAL;
    DepthError: REAL;
    Kp: REAL := 0.5; Ki: REAL := 0.05; Kd: REAL := 0.1;
    Integral: REAL := 0.0; LastError: REAL := 0.0;
    ValveCmd: REAL;
END_VAR

// Read sensors
BoomAngle := ReadAnalogIn(0); // degrees
GroundDist := ReadUltrasonic(); // meters

// Trigonometric depth calc
ActualDepth := (BoomLength * SIN(BoomAngle)) - GroundDist;

// PID Control
DepthError := TargetDepth - ActualDepth;
Integral := Integral + DepthError * dt;
Derivative := (DepthError - LastError) / dt;

ValveCmd := (Kp * DepthError) + (Ki * Integral) + (Kd * Derivative);

// Clamp output and send to DAC
ValveCmd := LIMIT(-1.0, ValveCmd, 1.0);
WriteDAC(ValveCmd);
LastError := DepthError;

END_PROGRAM
```

### 5. Hardware Specifications
- **Compute:** Arduino Mega 2560 (Industrial variant like Ruggeduino) - $50
- **GPS:** Single RTK setup (u-blox F9P) - $150
- **Depth Sensor:** MaxBotix MB7060 Ultrasonic - $40
- **TOTAL Cost:** ~ $240 (Significantly cheaper as no Orin Nano/Vision needed).

---

## E. DRILLER / AUGER (e.g., Caterpillar MD6250, Vermeer D24)

### 1. GPS Coordinate Input
Similar to the trencher, operation is highly deterministic.
- **Workflow:** Surveyors generate a CSV file containing hole coordinates (Latitude, Longitude) and target depths.
- **Input:** CSV is loaded into the onboard interface.

### 2. Drill Cycle Automation
The control system implements a finite state machine for the drilling cycle:
1. **Navigate:** Drive to GPS coordinate `N` (using RTK).
2. **Level:** Deploy outriggers to level chassis (using IMU).
3. **Collar:** Start rotation slowly, lower mast to engage ground.
4. **Drill:** Apply full feed pressure and rotation speed.
5. **Extract:** Reverse feed, maintain rotation to clear cuttings.
6. **Next:** Retract outriggers, increment `N`, loop.

### 3. Force Feedback & Rock Detection
- **Mechanism:** Hydraulic pressure on the rotary drive motor correlates directly with torque.
- **Logic:** If torque spikes rapidly (indicating hitting a hard rock layer), the system automatically reduces feed pressure (downward force) to prevent stalling the drill or snapping the bit, while maintaining or increasing RPM. If torque remains critically high, the cycle pauses and alerts the operator.

### 4. Hardware
- Identical to Trencher architecture (Arduino/PLC + RTK GPS + analog pressure sensors).

---

## F. PIPELAYER (e.g., CAT 572, Liebherr RL 64)

### 1. Unique Challenge: Pendulum Dynamics
Pipelayers use side-booms to lift and lower massive steel pipes into trenches. A suspended heavy load on a cable acts as a pendulum. Sudden machine movements or wind cause sway, which is highly dangerous. **Anti-sway control is critical.**

### 2. Anti-Sway Algorithm
We implement an active damping system.
- **Sensor:** A ruggedized IMU is mounted directly on the load hook/block.
- **Control:** The IMU transmits swing angle and angular velocity to the main controller (via wireless CAN or rugged cable). 
- **Action:** If sway is detected, the controller automatically injects micro-adjustments into the winch motor (hoist) and boom luffing cylinders to counteract the pendulum motion (e.g., if load swings forward, the boom translates slightly forward to "catch" it).

### 3. GPS Pipe Route Tracking
- The machine operates alongside the trench. It uses RTK GPS to follow the pre-surveyed trench line.
- Cooperative lifting: Multiple pipelayers often work in tandem. The AI system can sync winch speeds across multiple machines via a local mesh network to ensure the pipe is lowered perfectly horizontally.

### 4. Hardware Additions
- **Wireless Hook IMU:** Battery-powered, ruggedized IMU on the lifting hook block. Est. Cost: $40.
- *(Standard compute stack with Jetson Orin required for complex anti-sway kinematics).*

---
*End of Document. Version 1.0.*
