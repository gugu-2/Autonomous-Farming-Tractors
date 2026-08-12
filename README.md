# AGRO-AI: Universal Autonomy for Heavy Machinery

AGRO-AI is a state-of-the-art, modular artificial intelligence platform designed to retrofit existing heavy machinery—across the agricultural and construction industries—into fully autonomous, self-driving robots.

Unlike competitors who attempt to manufacture proprietary vehicles from scratch, AGRO-AI provides a **Universal Autonomy Kit**. We supply the ruggedized hardware "Brain" and sensors, which bolt onto any machine (John Deere, CAT, Komatsu). The specific AI capabilities are then downloaded as a software subscription based on the vehicle type.

## Core Architecture

The AGRO-AI system is split into two primary components:

1. **The Universal Hardware Kit:** A ruggedized, IP67-rated edge computing enclosure powered by the NVIDIA Jetson AGX Orin, connected to an array of LiDAR, Multi-spectral cameras, and RTK-GPS sensors.
2. **The Swappable Software Brains:** A modular AI architecture. The base Operating System (ROS2) is universal, but the AI Neural Networks (JEPA + DreamerV3 RL) are dynamically loaded based on the machine (e.g., a "Farming Brain" vs. an "Excavator Brain").

## Documentation Directory

Comprehensive documentation detailing our architecture, business model, and deployment strategies can be found in the `docs/` directory:

### Architecture & Technology
*   [`00_MASTER_ARCHITECTURE.md`](docs/00_MASTER_ARCHITECTURE.md) - The overarching software and hardware architecture.
*   [`01_CORE_PLATFORM_ARCHITECTURE.md`](docs/01_CORE_PLATFORM_ARCHITECTURE.md) - Deep dive into the ROS2 middleware and JEPA/RL pipelines.
*   [`08_TRAINING_PIPELINE.md`](docs/08_TRAINING_PIPELINE.md) - How we train the DreamerV3 models using Isaac Sim.

### Business & Strategy
*   [`11_BUSINESS_MODEL_AND_DEPLOYMENT.md`](docs/11_BUSINESS_MODEL_AND_DEPLOYMENT.md) - Our Hardware-Enabled SaaS business model and sales channels.
*   [`12_PRODUCT_AND_HARDWARE_CHALLENGES.md`](docs/12_PRODUCT_AND_HARDWARE_CHALLENGES.md) - Analysis of physical, computational, and market challenges.
*   [`13_UNIVERSAL_INTEGRATION_GUIDE.md`](docs/13_UNIVERSAL_INTEGRATION_GUIDE.md) - How we integrate one universal device into thousands of different OEM vehicles.

### Vehicle Tiers
*   [`02_CONSTRUCTION_TIER1_STATIONARY_ARMS.md`](docs/02_CONSTRUCTION_TIER1_STATIONARY_ARMS.md)
*   [`03_CONSTRUCTION_TIER2_DRIVING_MACHINES.md`](docs/03_CONSTRUCTION_TIER2_DRIVING_MACHINES.md)
*   [`05_FARMING_TIER1_GPS_AUTOSTEER.md`](docs/05_FARMING_TIER1_GPS_AUTOSTEER.md)
*   [`06_FARMING_TIER2_AI_VISION_MACHINES.md`](docs/06_FARMING_TIER2_AI_VISION_MACHINES.md)

## The Dashboard
The `frontend/` directory contains our Next.js 14 Fleet Management Dashboard. This web application allows fleet managers to monitor telemetry, view live camera feeds, and trigger global E-STOPs from any iPad or computer.

## Getting Started

To run the Next.js Fleet Management Dashboard locally:
```bash
cd frontend
npm install
npm run dev
```

To run the ROS2 backend nodes (requires ROS2 Humble/Iron and Python 3.10+):
```bash
colcon build
source install/setup.bash
ros2 launch core agro_ai_core.launch.py
```
