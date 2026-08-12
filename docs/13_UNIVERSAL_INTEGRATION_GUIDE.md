# AGRO-AI: Universal Integration Guide

The core thesis of AGRO-AI is that our physical hardware box is **Universal**. We do not build different hardware for a John Deere tractor vs. a Komatsu excavator. We use a single, ruggedized compute module and rely on integration adapters to interface with the chaotic world of OEM manufacturing.

This document details how we physically and digitally integrate our universal brain into any machine.

## 1. The Vehicle Abstraction Layer (VAL)

At the software level, the AGRO-AI Brain is completely agnostic to the vehicle it is sitting on. 
*   **The AI Output:** The neural networks output normalized commands: `[Steering: +15°], [Throttle: 40%], [Implement: DOWN]`.
*   **The Translation (VAL):** The VAL is a middleware layer. When the technician installs the box, they select the vehicle profile (e.g., `"CAT_320_Excavator_2019"`). The VAL translates the generic `[Throttle: 40%]` command into the specific hex-coded CAN bus message that Caterpillar uses for that specific model year.

By building a massive library of translation profiles, we support thousands of vehicle types with one codebase.

## 2. Integration Method A: Modern Drive-by-Wire (Digital)

Most heavy machinery built after 2010 uses "Drive-by-Wire" systems (ISOBUS, J1939 CAN bus). The steering wheel and pedals are just electronic joysticks sending digital signals to the engine and hydraulics.

*   **How we integrate:** We plug our universal wiring harness directly into the machine's diagnostic port or splice into the main CAN bus line.
*   **How it drives:** Our hardware injects CAN packets onto the network, "spoofing" the steering wheel. The vehicle's engine computer thinks the human is turning the wheel, but it is actually the AGRO-AI brain.
*   **The Challenge:** OEMs often encrypt or obfuscate their CAN signals to prevent third-party modifications. Our engineering team must reverse-engineer (packet sniff) the CAN networks of target vehicles to build the translation profiles.

## 3. Integration Method B: Legacy Actuator Retrofits (Physical)

For older machines (pre-2010) with mechanical steering columns, steel throttle cables, and analog hydraulic levers, digital integration is impossible.

*   **How we integrate:** We provide physical hardware add-ons alongside the Universal Brain.
    *   *Steering:* A motorized friction ring that bolts onto the existing steering wheel (similar to early auto-steer kits).
    *   *Pedals:* Linear actuators (robotic arms) bolted to the floorboard that physically press the brake and gas pedals.
*   **How it drives:** The AGRO-AI brain sends PWM (Pulse Width Modulation) electrical signals to these external motors. The motors physically turn the wheel and push the pedals, acting as a "ghost driver" in the cabin.

## 4. The Sensor Array Standardization

To ensure the AI models work consistently across all machines, the sensor placement must be relatively standardized.
*   **The Roof Rack:** We provide a magnetic or bolt-on aluminum roof rack. This rack holds the primary 360° cameras, the LiDAR dome, and the RTK-GPS dual-antennas.
*   **Calibration:** During installation, the technician drives the machine in a figure-8 pattern. The AGRO-AI software automatically calibrates the extrinsic parameters (calculating exactly how high the roof rack is off the ground, and exactly where the wheels are relative to the camera).
