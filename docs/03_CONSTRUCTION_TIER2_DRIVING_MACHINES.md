# AGRO-AI Project: Tier 2 Construction Equipment Architecture (Driving & Working Machines)

## Overview

Tier 2 construction machines are complex autonomous agents that must simultaneously **DRIVE** (navigate, path plan, avoid obstacles) and **WORK** (manipulate earth, material, or asphalt). The dual requirement makes their state and action spaces significantly larger than Tier 1 (driving-only) machines. 

The AGRO-AI architecture leverages a unified perception stack combined with specialized Reinforcement Learning (RL) agents for the working functions of each machine type. 

---

## A. BULLDOZER (CAT D6, CAT D9, Komatsu D475)

The autonomous bulldozer's primary task is bulk earthmoving and rough grading to match a digital terrain model (DTM).

### 1. The 3D Grade Control Problem
The AI must ingest a target Digital Terrain Model (DTM) in a format like LandXML or a georeferenced point cloud. It compares the current terrain scan against the DTM to compute the required cut and fill volumes in real-time. The goal is to push dirt efficiently to match the target grade with minimal passes.

### 2. Blade Control
The bulldozer features a 6-Degrees-of-Freedom (6DOF) blade:
- **Lift**: Automated (controlled by RL agent for cut depth).
- **Tilt**: Automated (controlled by RL agent for cross-slope).
- **Pitch**: Automated (adjusts blade attack angle for different soil types).
- **Angle**: Automated or Manual (angling blade left/right to windrow material).

### 3. State Space
- Current 6DOF blade position and hydraulic pressures (sensor feedback).
- Current terrain scan (LiDAR 3D point cloud of material immediately ahead of the blade).
- Target DTM slice (local window of the target grade).
- Machine heading, pitch, roll, and yaw rate (IMU + RTK-GPS).
- Machine speed, track slip, and engine load.

### 4. Action Space
- Blade lift rate (continuous, -1.0 to 1.0).
- Blade tilt rate (continuous, -1.0 to 1.0).
- Blade pitch rate (continuous, -1.0 to 1.0).
- Throttle/Engine RPM (continuous, 0.0 to 1.0).
- Steering (differential track speed, continuous, -1.0 to 1.0).

### 5. 3D Terrain Scanning & Compute
Forward-facing LiDAR point clouds are processed into a real-time 2.5D elevation map using a GPU-accelerated voxel grid. This map is subtracted from the DTM to compute delta-elevation (cut/fill required).

### 6. Path Planning
The high-level planner divides the site into longitudinal passes. The RL agent executes each pass, dynamically adjusting blade height to maximize material moved without stalling the engine (maintaining optimal track slip around 10-15%).

### 7. Competitor Comparison
**Komatsu Intelligent Machine Control (IMC)** uses traditional PID control algorithms based on track slip to raise the blade when the load is too high. AGRO-AI uses Deep RL (PPO) which learns predictive blade control based on LiDAR terrain scans before the load hits the tracks, resulting in smoother cuts and faster cycle times.

### 8. Hardware Extras
- **LiDAR**: Ouster OS0-32 (Forward-facing, ultra-wide 90° vertical FOV to see blade and dirt) (USD 3,000).
- **Compute**: NVIDIA Jetson AGX Orin 64GB (USD 1,999).
- **RTK-GPS**: Dual Swift Navigation Piksi Multi (heading + cm-accuracy) (USD 2,500).

### 9. Training Pipeline
- **Simulation**: PyBullet bulldozer simulation with a deformable terrain particle system.
- **Time**: 6-7 days on Google Colab T4.
- **Algorithm**: Proximal Policy Optimization (PPO).

### 10. ROS2 Architecture
```ascii
[RTK-GPS] ----> (State Estimator Node) <---- [IMU]
                       |
                       v
[LiDAR OS0] --> (Terrain Mapping Node) -----> (Cut/Fill Delta Node) <-- [Target DTM]
                       |                             |
                       +-----------------------------+
                                     |
                                     v
                        (RL Blade Control Agent Node)
                                     |
                                     v
                           (CANBus Translation Node)
                                     |
[Engine/Transmission CAN] <----------+----------> [Implement Valves CAN]
```

---

## B. MOTOR GRADER (CAT 14, Volvo G900, John Deere 872)

The motor grader is responsible for fine grading. It is the hardest Tier 2 machine to automate due to extreme precision requirements.

### 1. Why Hardest in Tier 2
While a bulldozer aims for ±10cm accuracy (rough grade), a motor grader must achieve **±1cm blade accuracy** for final road bases and drainage. Any error cascades into material costs (e.g., concrete/asphalt overages).

### 2. The 5DOF Blade Complexity
The grader has immense degrees of freedom:
- Main blade articulation.
- Lift Left cylinder.
- Lift Right cylinder.
- Circle rotation (turning the blade).
- Moldboard tilt (blade pitch).
- Wheel lean (front wheels).
- Articulation joint (chassis bending).

### 3. RTK-GPS Sub-cm Accuracy
Dual-mast RTK-GPS is mounted directly on the blade (or chassis with high-precision IMUs calculating blade tips). Corrections via NTRIP network provide 10Hz, <1cm positional accuracy.

### 4. Cross-Slope Control
The AI continuously monitors the cross-slope (e.g., 2% crown for road drainage). The RL agent outputs independent Left/Right lift rates to maintain this exact slope regardless of terrain unevenness under the tires.

### 5. Training Pipeline
- Requires higher precision reward shaping, heavily penalizing deviations > 1cm from target grade.
- **Time**: 9-10 days on Google Colab T4.

```ascii
      GRADER CYCLE:
      [Start Pass] -> [Drop Blade to Target Depth] -> [Maintain Cross Slope & Grade]
                                                             |
      [End Pass / Lift] <- [Detect Pass Completion] <--------+
```

---

## C. COMPACTOR / ROAD ROLLER (CAT CS-56, Dynapac CA6000D)

The compactor is the simplest Tier 2 machine. Its primary challenge is pure 2D coverage path planning.

### 1. Simplest Tier 2 Machine
No complex implements to control; just steering, speed, and vibration on/off.

### 2. Compaction Pattern
The AI generates a boustrophedon (lawnmower) path covering a GPS polygon. Passes must overlap by exactly 15% to ensure no uncompacted strips.

### 3. Density Sensing (Intelligent Compaction - IC)
An accelerometer mounted on the drum measures the amplitude and frequency of rebound vibrations. As the soil compacts, it becomes stiffer, altering the vibration signature. This creates a proxy metric for soil density.

### 4. Pass Count Map
The system builds a spatial 2D grid map logging:
- Pass count per cell.
- Latest IC stiffness value per cell.

### 5. Auto-Stop
The machine autonomously halts compaction on a specific strip when the target IC stiffness is achieved uniformly, preventing over-compaction.

### 6. Training Pipeline
- Mostly A* or D* Lite path planning algorithms. Minimal RL needed (mostly for obstacle avoidance).
- **Time**: 1-2 days on Google Colab T4.

---

## D. SKID-STEER LOADER (Bobcat S650, CAT 262D3)

Skid-steers operate in tight, confined environments (urban sites, indoors) and use tank-style steering.

### 1. Tank-Style Steering Challenge
No steering wheel. Steering is achieved by creating a speed differential between left and right wheels/tracks. This causes heavy skidding, making dead-reckoning odometry highly inaccurate.

### 2. Tight Space Operation
Requires 360° situational awareness for zero-radius turns in confined spaces.

### 3. LiDAR SLAM
Due to poor odometry and potential GPS-denial (indoors), the machine relies heavily on LiDAR SLAM (e.g., LOAM or FAST-LIO2).
- **Mapping Pass**: Driven manually once to build a 3D point cloud map.
- **Autonomous Ops**: Localizes against the prior map using AMCL/NDT.

### 4. Bucket Control
An RL agent controls the standard sequence: `Approach Pile -> Dig/Fill Bucket -> Lift & Tilt Back -> Reverse -> Approach Dump -> Dump`.

### 5. Training Pipeline
- Combined SLAM navigation and manipulation RL.
- **Time**: 7-10 days on Google Colab T4.

---

## E. COMPACT TRACK LOADER (CAT 259D3, John Deere 333G)

Virtually identical to the Skid-Steer Loader, but on tracks instead of wheels.

### 1. Architecture Reuse
We use the exact same ROS2 architecture, state space, and action space as the Skid-Steer Loader. Pre-trained weights are directly transferred.

### 2. Track Slip Compensation
The only physical difference is track dynamics on soft ground vs wheel dynamics on hard ground. The tracks provide better traction but different turning resistance.

### 3. Training Pipeline
- Transfer learning from Skid-Steer checkpoint.
- Fine-tuning for track physics.
- **Time**: Extra 2-3 days on Google Colab T4.

---

## F. WHEEL LOADER / FRONT-END LOADER (CAT 950, Volvo L120H)

The wheel loader specializes in cyclical material transfer, usually from a pile to a truck.

### 1. The V-Cycle
The standard operational pattern is the "V-pattern":
1. Approach pile forward.
2. Scoop material.
3. Reverse out (forming one leg of the V).
4. Drive forward to truck (forming the other leg).
5. Lift and dump.
6. Reverse back to start.

### 2. Pile Detection
LiDAR and stereoscopic cameras segment the environment to locate the material pile. Algorithms compute the centroid, height, and optimal attack angle to prevent tire spin.

### 3. Bucket Fill Optimization
An RL agent controls the bucket crowd (tilt) and lift cylinders during the scooping phase.
- **Reward Function**: Maximize payload weight (estimated via hydraulic pressure) while minimizing tire slip and cycle time.
- **Target**: 90%+ bucket fill factor.

### 4. Truck Positioning
Computer vision (YOLOv8) detects the haul truck's body/bed. The AI calculates the exact dump height and arc to distribute material evenly in the truck bed without spilling over the sides.

### 5. Autonomous Navigation
Operates at low speeds (<15 km/h) within a strictly geofenced work zone using RTK-GPS and LiDAR obstacle avoidance.

### 6. Training Pipeline
- Deep RL for the V-cycle execution.
- **Time**: 7-10 days on Google Colab T4.

```ascii
      WHEEL LOADER V-CYCLE:
             [Pile]
            /      
           / (Scoop)
          /         
   [Start]           [Dump into Truck]
          \         /
           \       /
            \     /
           [Reverse Point]
```

---

## G. ARTICULATED DUMP TRUCK (Volvo A40G, CAT 745)

Designed for hauling material over rough, muddy, unmarked off-road terrain.

### 1. Reuse OMNIDRIVE Robotaxi Lite Architecture
*Note: This architecture explicitly reuses the OMNIDRIVE Robotaxi Lite autonomous driving stack.*
Since ADTs primarily drive, we use the same perception (LiDAR + Camera) and planning stack as our on-road vehicles, but heavily tuned for off-road physics.

### 2. Differences from Robotaxi
- **No Lane Markings**: Relies purely on GPS waypoints and LiDAR drivable-space segmentation.
- **No Traffic Rules**: Follows site-specific rules (e.g., left-hand drive in some mines).
- **Terrain**: Deep mud, ruts, steep grades require specialized traction control and differential locking logic.

### 3. Haul Route Programming
A site surveyor inputs a looping series of GPS waypoints. The truck continuously loops between the excavator/loader (load zone) and the dump zone.

### 4. Load Detection & Dumping
- **Load Trigger**: Suspension strut pressure sensors detect when the truck is fully loaded, triggering the autonomous drive to the dump zone.
- **Dump Trigger**: Upon reaching the GPS dump polygon, the AI reverses into position, applies brakes, raises the bed, and pulls forward slightly to clear the pile.

### 5. Training Pipeline
- Reuse Robotaxi RL weights as a base. Train primarily on off-road terrain physics and the dumping sequence.
- **Time**: 5-7 days on Google Colab T4.

---

## H. RIGID OFF-HIGHWAY DUMP TRUCK (CAT 793, Komatsu 930E)

Massive mining trucks operating in highly controlled, structured open-pit mines.

### 1. Industry Context
*Note: Komatsu FrontRunner AHS and CAT Command have already deployed 500+ of these globally.*
AGRO-AI learns from these systems by focusing on centralized fleet management and predictable, deterministic routing rather than highly dynamic obstacle avoidance.

### 2. Fixed Haul Roads
Operates on well-maintained, wide haul roads. Navigation is simplified to strict GPS path following with cross-track error minimization.

### 3. Fleet Coordination (MQTT)
Multiple trucks on the same route must coordinate. AGRO-AI uses an MQTT-based central dispatcher to manage intersection right-of-way, queuing at the shovel, and queuing at the crusher to prevent congestion.

### 4. Training Pipeline
- Identical to Articulated Dump Truck.
- **Time**: 5-7 days on Colab T4.

---

## I. CRAWLER LOADER (CAT 963, Komatsu D61)

A hybrid between a bulldozer and a wheel loader (tracked loader).

### 1. Weight Reuse
We reuse the RL weights from the **Wheel Loader** (for the bucket kinematics and V-cycle logic) combined with the track physics model from the **Compact Track Loader**.

### 2. Training Pipeline
- Transfer learning. Fine-tune for the specific kinematics of the crawler loader lift arms and heavy track dynamics.
- **Time**: 2-3 extra days on Google Colab T4.

---

## J. COLD PLANER / MILLING MACHINE (Wirtgen W200i, CAT PM620)

Milling machines remove old asphalt prior to repaving.

### 1. The Job
Mill existing pavement at a highly precise depth (tolerance: ±3mm) and slope.

### 2. Depth Control Sensors
- 4x hydraulic leg sensors (measure machine height).
- Sonic/Ultrasonic grade sensors tracking the ground on either side of the milling drum.
- The AI aggregates these inputs to maintain the drum exactly at the target milling depth.

### 3. Speed-Depth Coupling
The RL agent controls advance speed. If the cut is deep or the asphalt is very hard (detected via engine load/drum pressure), the AI automatically slows the track speed to prevent stalling the milling drum or breaking cutting teeth.

### 4. GPS Line Following
The machine follows a pre-surveyed 2D polyline (the edge of the milling cut) using RTK-GPS to ensure perfectly straight cuts without leaving slivers of old asphalt.

### 5. Training Pipeline
- Focus on the feedback loop between engine load and track speed.
- **Time**: 3-4 days on Google Colab T4.

---

## K. ASPHALT PAVER (Vogele SUPER 1800-3i, CAT AP1055F)

Lays new asphalt. Continuous movement is critical; stopping creates bumps in the final road.

### 1. The Job
Lay hot mix asphalt at a precise thickness, slope, and width.

### 2. Screed Control
The AI controls the electro-hydraulic tow points of the screed. Using sonic sensors or laser trackers, it continuously adjusts the tow points to lay asphalt at the target thickness (e.g., 50mm).

### 3. Infrared Temperature Monitoring
Thermal cameras (e.g., FLIR) monitor the asphalt mat immediately behind the screed. If the temperature drops below the compaction threshold (e.g., 120°C), the AI alerts the trailing compactor fleet via MQTT.

### 4. GPS Line Following
Follows 3D stringlines from a LandXML road design file. Auto-steers the tractor unit to match the road curvature perfectly.

### 5. Training Pipeline
- Mostly PID control for the screed, combined with A* for steering.
- **Time**: 3-4 days on Google Colab T4.

---

## L. WHEEL TRACTOR-SCRAPER (CAT 623K)

The most complex Tier 2 machine. It loads itself, hauls the material, and spreads it.

### 1. The 3-Phase Complexity
Requires distinct RL models for three completely different phases of operation: Loading, Hauling, and Dumping.

### 2. Loading Phase (The Cut)
- Machine lowers the bowl and drives forward.
- The cutting edge scrapes the top layer of dirt into the bowl.
- **AI Task**: Manage engine RPM, transmission gear, and bowl height to maximize material intake without spinning tires. Often requires coordination with a push-dozer.

### 3. Haul Phase
- Bowl is raised, apron closed.
- Operates identically to an Articulated Dump Truck, following GPS waypoints at high speeds (up to 50 km/h).

### 4. Dump Phase (The Fill)
- Arrives at fill zone.
- **AI Task**: Open apron and push ejector forward while driving at a constant speed to spread the material evenly in a thin lift (e.g., 15cm thick), ready for compaction.

### 5. Training Pipeline
- Highly complex multi-agent/multi-phase RL.
- **Time**: 10-14 days on Google Colab T4.

```ascii
      SCRAPER CYCLE:
      [Lower Bowl & Scrape] ---> [Fill Bowl] ---> [Raise Bowl & Close Apron]
             ^ (Load Phase)                              | (Haul Phase)
             |                                           v
      [Return via GPS] <--- [Eject & Spread] <--- [Navigate to Dump Zone]
                               (Dump Phase)
```
