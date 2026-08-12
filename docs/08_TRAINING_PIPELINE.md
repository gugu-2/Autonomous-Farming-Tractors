# AGRO-AI: Training Pipeline Architecture (08_TRAINING_PIPELINE)

## 1. Overview

This document outlines the training infrastructure for all 40 machine types in the AGRO-AI ecosystem. Due to resource constraints and the requirement to keep R&D costs low, we rely primarily on **Google Colab T4 instances** (16GB VRAM, roughly 12 hours of compute per session).

The overall pipeline dictates how we orchestrate Reinforcement Learning (RL), Behavior Cloning (BC), and Computer Vision (CV) training across intermittent cloud environments while retaining state and ensuring robust model convergence.

### Key Objectives
*   **Cost-efficiency:** Leverage free/cheap Google Colab compute.
*   **Fault-tolerance:** Gracefully handle Colab session disconnects using frequent checkpointing.
*   **Scalability:** Standardized scripts to support rapid scaling to new machine variants.
*   **Sim-to-Real capability:** Bridge the gap between PyBullet simulation and real-world hydraulic/kinematic performance.

---

## 2. The Google Drive Checkpoint Strategy

Google Colab sessions are ephemeral and subject to random disconnections or strict 12-hour limits. To prevent loss of training progress, we employ a robust Google Drive Checkpoint Strategy.

### Architecture Flow

```text
+---------------------+        +-------------------------+        +--------------------------+
| Google Colab Node   |        | Google Drive (Mounted)  |        | Local Dev Machine        |
| (T4 GPU, 16GB VRAM) | <====> | (/content/drive/MyDrive)| <====> | (Monitoring/Inference)   |
+---------------------+        +-------------------------+        +--------------------------+
          |                               |
          | 1. Mount Drive                |
          |------------------------------>|
          |                               |
          | 2. Check for latest model.pt  |
          |<------------------------------|
          |                               |
          | 3. Train for 60 mins          |
          |                               |
          | 4. Save checkpoint to Drive   |
          |------------------------------>|
```

### Technical Implementation

We utilize a custom callback in Stable-Baselines3 (or raw PyTorch training loops) to flush model state and replay buffer to disk, and then synchronize it to Google Drive every 60 minutes.

#### Python Code: Mounting and Checkpointing

```python
import os
import torch
import shutil
from google.colab import drive
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

# 1. Mount Google Drive
drive.mount('/content/drive')
DRIVE_CHECKPOINT_DIR = '/content/drive/MyDrive/AGRO_AI/checkpoints/excavator_v1'
os.makedirs(DRIVE_CHECKPOINT_DIR, exist_ok=True)

# 2. Checkpoint Callback
class DriveCheckpointCallback(BaseCallback):
    def __init__(self, save_freq: int, save_path: str, verbose=1):
        super(DriveCheckpointCallback, self).__init__(verbose)
        self.save_freq = save_freq
        self.save_path = save_path
        self.local_temp_path = '/content/temp_checkpoint.zip'

    def _on_step(self) -> bool:
        if self.n_calls % self.save_freq == 0:
            # Save locally first for speed
            self.model.save(self.local_temp_path)
            # Copy to drive to ensure atomic writes
            target_path = os.path.join(self.save_path, f"model_step_{self.num_timesteps}.zip")
            shutil.copy(self.local_temp_path, target_path)
            
            # Save replay buffer if applicable
            if hasattr(self.model, "replay_buffer") and self.model.replay_buffer is not None:
                buffer_path = os.path.join(self.save_path, f"buffer_{self.num_timesteps}.pkl")
                self.model.save_replay_buffer(buffer_path)
                
            if self.verbose > 0:
                print(f"Checkpoint saved to Google Drive at step {self.num_timesteps}")
        return True

# 3. Resume Logic
def load_latest_checkpoint(env):
    checkpoints = [f for f in os.listdir(DRIVE_CHECKPOINT_DIR) if f.startswith('model_step_') and f.endswith('.zip')]
    if not checkpoints:
        print("Starting fresh training session.")
        return PPO("MlpPolicy", env, verbose=1, learning_rate=3e-4)
    
    # Sort by step number
    checkpoints.sort(key=lambda x: int(x.split('_')[2].split('.')[0]))
    latest_cp = checkpoints[-1]
    latest_path = os.path.join(DRIVE_CHECKPOINT_DIR, latest_cp)
    
    print(f"Resuming training from {latest_path}")
    model = PPO.load(latest_path, env=env)
    
    # Optional: Load replay buffer
    # buffer_path = latest_path.replace("model_step_", "buffer_").replace(".zip", ".pkl")
    # if os.path.exists(buffer_path):
    #     model.load_replay_buffer(buffer_path)
        
    return model
```

### Detecting New vs. Resumed Sessions
The pipeline inherently checks for the presence of files in `DRIVE_CHECKPOINT_DIR`. If the directory is empty or missing, it initializes a new model. If checkpoints exist, it parses the filenames to find the highest step count, loads the `.zip` archive (which contains the PyTorch `state_dict`, optimizer state, and hyperparameters), and resumes the training loop.

---

## 3. Simulation Environments

Training AI to control heavy machinery requires fast, accurate simulation.

### PyBullet Setup for Construction Machines (Tier 1 Arm Machines)

We use **PyBullet** for excavators, loaders, and backhoes because it provides a good balance between physics fidelity and compute speed, allowing us to run headless vector environments on Colab.

*   **URDF Modeling:** The excavator arm is modeled using URDF (Unified Robot Description Format).
    *   **Base:** Fixed or continuous joint (swing).
    *   **Boom, Stick, Bucket:** Revolute joints.
    *   **Limits & Masses:** We extract exact masses (e.g., boom = 800kg) and joint limits (e.g., bucket curl -45 to +60 degrees) from manufacturer CAD data.
*   **Simplified Hydraulics:** Standard PyBullet positional control acts instantly, which is unrealistic. We implement a custom wrapper `HydraulicJointControl` that simulates hydraulic lag and pressure buildup.
    *   $v_{joint} = k \cdot (P_{pump} - P_{cylinder}) \cdot A_{valve}$
    *   We use a low-pass filter on action commands to simulate the spool valve opening time (~150ms).
*   **Soil Interaction (Particle-based):** True DEM (Discrete Element Method) is too slow. We use a heightmap grid with pseudo-particles. When the bucket mesh intersects the heightmap, we lower the heightmap z-values and add mass to the bucket end-effector to simulate payload.
*   **Domain Randomization:** At reset, we randomize:
    *   Terrain roughness (Perlin noise).
    *   Soil density ($\pm 20\%$).
    *   Joint friction and damping.
    *   Hydraulic response latency (100ms - 250ms).

### Custom 2D Environments for GPS Tasks
For tractors performing headland turns, 3D physics is overkill. We built a custom 2D kinematic bicycle model environment using OpenAI Gym / Gymnasium. State includes $[x, y, \theta, v, \delta]$ (position, heading, velocity, steering angle).

### Isaac Sim Note
NVIDIA Isaac Sim offers superior rendering and physics (via PhysX 5), but requires RTX 3080+ class hardware. We reserve Isaac Sim exclusively for **crane simulations** (where cable dynamics and pendulum sway require high fidelity) running on local workstations, NOT Colab.

---

## 4. RL Training Details for Each Machine Tier

### Tier 1 Arm Machines (Excavator)

*   **Algorithm:** PPO (Proximal Policy Optimization) with continuous action space.
*   **Network Architecture:** MLP feature extractor with 3 layers `[512, 512, 256]`, using `tanh` activations (smoother action outputs for hydraulics than ReLU).
*   **Hyperparameters:**
    *   Learning Rate: `3e-4`, linear decay to `1e-5` over 10M steps.
    *   Steps per update (`n_steps`): 2048.
    *   Batch size: 64.
    *   Epochs (`n_epochs`): 10.
    *   Gamma ($\gamma$): 0.99.
    *   GAE Lambda ($\lambda$): 0.95.

#### Training Curriculum (5 Days on Colab)

1.  **Stage 1 (Day 1):** Reach target point in 3D space from a random start pose. No obstacles.
2.  **Stage 2 (Day 2):** Reach target point AND maintain position for 1.0 seconds (teaches stabilization).
3.  **Stage 3 (Days 3-4):** Full single dig cycle. (Reach soil -> Drag bucket -> Lift -> Swing -> Dump in virtual truck).
4.  **Stage 4 (Day 5):** Multi-cycle excavation with terrain heightmap updating (continuous operation).

#### Reward Function (Python)

```python
def calculate_reward(self, achieved_pos, target_pos, action, payload_mass, is_dumping):
    # 1. Distance penalty (L2 norm)
    distance = np.linalg.norm(achieved_pos - target_pos)
    r_dist = -distance * 10.0
    
    # 2. Energy/Smoothness penalty (penalize large jerky actions)
    r_ctrl = -np.sum(np.square(action)) * 0.1
    
    # 3. Payload reward (only positive when digging/lifting)
    r_payload = 0
    if payload_mass > 0 and not is_dumping:
        r_payload = payload_mass * 0.5
        
    # 4. Dump success reward
    r_dump = 0
    if is_dumping and distance < 0.5:
        r_dump = 50.0  # Sparse reward for successful completion
        
    # 5. Collision penalty
    r_collide = 0
    if self.check_collision():
        r_collide = -100.0
        self.done = True
        
    total_reward = r_dist + r_ctrl + r_payload + r_dump + r_collide
    return total_reward
```

### Tier 1 GPS Machines (Tractor Headland Turning)

*   **Algorithm Pipeline:** Behavior Cloning (BC) $\rightarrow$ DAgger $\rightarrow$ PPO Fine-tuning.
*   **Data Collection:** We collect 3 hours of real human demonstration data (GPS RTK traces, steering angle, speed) while a human operator executes perfect headland turns.
*   **Behavior Cloning (Supervised):** Train an MLP to map $(state \rightarrow action)$ using MSE loss against the human actions.
*   **PPO Fine-tuning:** Initialize PPO actor network with BC weights. Train online in the 2D kinematic sim to optimize cross-track error and smoothness.
*   **Time:** 2-3 days on Colab T4.

### Vision Models (YOLOv8 Weed Detection for Sprayers)

For agricultural sprayers, we need robust visual detection of weeds versus crops.

*   **Dataset:** Formatted as YOLO YAML (`dataset.yaml`). Annotated using **Roboflow** (utilizing the free tier limit of 10,000 images).
*   **Training Command (Colab CLI):**
    ```bash
    yolo task=detect mode=train model=yolov8s.pt data=weeds.yaml epochs=100 imgsz=640 batch=16 device=0
    ```
*   **TensorRT Export:** To run at 30+ FPS on the edge hardware (Jetson Orin), we export to a TensorRT engine:
    ```bash
    yolo export model=runs/detect/train/weights/best.pt format=engine device=0
    ```
*   **Training Time:** 3-4 hours on Colab T4 for a 5,000 image dataset (100 epochs).

---

## 5. Sim-to-Real Transfer

Deploying a policy trained in PyBullet directly to a 20-ton excavator is extremely dangerous due to the "Reality Gap".

### 1. Domain Randomization
As mentioned, we vary physics parameters wildly during training. The policy learns a robust strategy that doesn't overfit to one specific hydraulic latency or soil friction coefficient.

### 2. System Identification
Before AI takes control, we run a "calibration routine" on the real machine. We inject step inputs (e.g., 50% PWM to boom up) and record the actual cylinder displacement via IMUs. We use this data to fine-tune the parameters in our PyBullet simulation to match that specific machine's wear and tear, then retrain for a few hours.

### 3. Residual Learning
We train a base policy $\pi_{base}(s)$ in simulation. On the real machine, we run a small, fast-adapting residual network $\pi_{res}(s)$. The final action is $a = \pi_{base}(s) + \pi_{res}(s)$. The residual network is trained online using sparse real-world data to correct small systematic errors.

### 4. Deployment Protocol
1.  **Shadow Mode:** AI predicts actions, but human controls machine. Log divergence.
2.  **Supervised Mode (30 mins):** AI controls machine at 25% speed. Operator holds dead-man switch.
3.  **Full Autonomous Mode:** Normal operating speed within geofence.

---

## 6. Model Versioning and Management

Tracking which model is deployed on which tractor across continents requires strict MLOps.

*   **Experiment Tracking:** We use **MLflow** (self-hosted on a cheap DigitalOcean droplet) to log metrics (loss, reward), hyperparameters, and git commits. Colab scripts push metrics directly to MLflow.
*   **Data Versioning:** **DVC** tracks our image datasets and demonstration logs, storing the actual heavy data in AWS S3 or Google Drive, while keeping tiny `.dvc` pointers in our Git repository.
*   **Model Registry:**
    ```text
    Google Drive /
    ├── Models /
    │   ├── Excavator /
    │   │   ├── v1.0_excavator_20231015.pt  (Baseline)
    │   │   ├── v1.1_excavator_20231102.pt  (Improved digging)
    │   ├── Sprayer /
    │   │   ├── v2.0_sprayer_yolo_20240110.engine
    ```
*   **Naming Convention:** `v{major}.{minor}_{machine}_{date}.{ext}` (e.g., `v1.2_dozer_20240520.pt`).

---

## 7. Colab Training Scripts Structure

The codebase is organized to maximize reuse across machine types.

*   **`train_excavator.py`**: Instantiates `ExcavatorEnv`, loads PPO, sets up curriculum callbacks, and runs the 5-day training loop with Google Drive checkpointing.
*   **`train_dozer.py`**: Instantiates `DozerEnv` (uses a different reward focusing on blade load and grading accuracy). Uses SAC (Soft Actor-Critic) instead of PPO for better sample efficiency.
*   **`train_sprayer_yolo.py`**: Wrapper script that downloads data via Roboflow API, executes the ultralytics YOLO training loop, and runs evaluation metrics.
*   **`common/env_utils.py`**: Contains `HydraulicJointControl`, `HeightmapSoilSim`, and normalization wrappers.
*   **`common/checkpoint.py`**: Contains the `DriveCheckpointCallback` and `load_latest_checkpoint` logic defined above.

---

## 8. Training Time Summary Table

| Machine Type | Tier | Algorithm | Simulation Environment | Compute Time (Colab T4) | Hardware Deployed |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Excavator** | 1 | PPO | PyBullet (3D) | 5 Days | Jetson Orin Nano |
| **Tractor (Row Crop)** | 1 | BC + PPO | Custom Kinematic (2D)| 3 Days | Raspberry Pi 4 + TPU |
| **Combine Harvester** | 2 | SAC | PyBullet (3D) | 7 Days | Jetson Orin NX |
| **Sprayer (Vision)** | 1 | YOLOv8 | N/A (Image Dataset) | 4 Hours | Jetson Orin Nano |
| **Bulldozer** | 2 | SAC | PyBullet (3D) | 6 Days | Jetson Orin NX |
| **Crane (Tower)** | 3 | PPO | Isaac Sim | 10 Days (Local RTX 4090)| Jetson AGX Orin |
| **Skid Steer** | 1 | PPO | PyBullet (3D) | 4 Days | Jetson Orin Nano |
| **Wheel Loader** | 2 | PPO | PyBullet (3D) | 6 Days | Jetson Orin NX |
| **... (up to 40)** | ... | ... | ... | ... | ... |

*(Document concludes here)*
