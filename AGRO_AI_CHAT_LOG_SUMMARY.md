# AGRO-AI Project Chat History & Context

*This document serves as a fully separable record of the AGRO-AI project's conversation history, architectural decisions, and roadmap, ensuring all context is preserved within the repository.*

## 1. Project Vision
**Goal:** Create a "Universal Autonomy Kit" (a drop-in AI brain) for heavy machinery across the agricultural and construction industries. 
Instead of building vehicles from scratch, AGRO-AI provides a universal ruggedized hardware box equipped with sensors that can be retrofitted onto any machine (John Deere, CAT, Komatsu) to make it an autonomous AI robot.

## 2. The Modular "App Store" Architecture
A core realization during our chats was that while the physical hardware box is universal, the AI models must be specialized.
- **Universal Hardware:** An IP67 ruggedized enclosure housing an NVIDIA Jetson AGX Orin, connected to LiDAR, multi-spectral cameras, and RTK-GPS.
- **Swappable AI Brains (Software):** 
  - **Farming Brain:** Vision models for crop/weed detection, low-speed high-torque control.
  - **Construction Brain:** 3D Voxel mapping, inverse kinematics for controlling robotic arms (excavators).
  - **Robotaxi Brain:** High-speed road navigation, pedestrian detection.
- **Integration Layer:** A Vehicle Abstraction Layer (VAL) translates generic AI commands into specific CAN bus / ISOBUS signals for different manufacturers. Older vehicles use physical actuator retrofits (steering wheel motors, pedal pushers).

## 3. Technical Stack
- **AI Core:** JEPA (Joint Embedding Predictive Architecture) for world modeling and video prediction. DreamerV3 Reinforcement Learning for the control policy.
- **Middleware:** ROS2 (Robot Operating System) for inter-process communication, sensor fusion, and hardware interfaces.
- **Frontend Dashboard:** Next.js 14, `shadcn/ui` (Base UI primitives), Tailwind CSS v3.
- **Design Language:** "Premium Dark Mode" — deep midnight/glassmorphism backgrounds with vibrant neon-green primary accents to match industrial/machinery aesthetics.

## 4. Conversation & Development History

### Phase 1: Architectural Planning & Scaffolding
- Defined the multi-tier architecture for Farming and Construction.
- Generated the massive modular ROS2 Python codebase, splitting it into `core`, `machines`, `perception`, `sensor_fusion`, `telemetry`, and `training`.
- Discussed the difference between JEPA (understanding the world) and RL (taking action).

### Phase 2: Autonomous Testing & Code Audit
- Spawned multiple specialized AI subagents (JEPA Brain Fixer, RL Fixer, Construction Verifier, Farming Verifier).
- The agents audited the entire codebase and identified API mismatches, runtime crashes (❌ 16 files failed), and logic bugs (⚠️ 20 files warned). 
- *Next step pending: Executing these code fixes.*

### Phase 3: Fleet Management Dashboard (Frontend)
- Bootstrapped a Next.js 14 frontend in the `/frontend` directory.
- Configured a Shadcn UI preset with custom dark mode theming.
- Built a command-and-control dashboard featuring:
  - Global E-STOP dialog.
  - Live mock telemetry data (battery, CPU, GPS).
  - A mock multi-spectral camera feed.
  - Fleet manifest tables.

### Phase 4: GitHub Integration
- Initialized the `AGRO_AI_PROJECT` directory as a standalone Git repository to make it fully separable.
- Pushed the initial codebase (backend ROS2 + frontend Next.js) to `gugu-2/Autonomous-Farming-Tractors`.

## 5. Outstanding Tasks & Roadmap
1. **Fix Backend Codebase Bugs:** Apply the fixes identified by the testing agents to the JEPA and RL modules so the AI can execute without crashing.
2. **Connect Frontend to Backend:** Replace the frontend's mock telemetry with real data streamed from the ROS2 `mqtt_bridge_node.py`.
3. **Robotaxi Lite & Military Expansion:** Begin research and planning for the secondary initiatives involving high-speed vehicles and convoy modes.
