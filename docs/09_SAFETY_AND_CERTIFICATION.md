# AGRO-AI: Safety and Certification Architecture (09_SAFETY_AND_CERTIFICATION)

## 1. Why Safety Certification Matters

Autonomous heavy machinery inherently poses a massive risk to human life and property. A 20-ton excavator or a fast-moving combine harvester operating without a human in the cabin introduces severe legal, ethical, and financial liabilities. 

If an AGRO-AI powered machine injures a person, the liability falls on the manufacturer and the AI software provider unless stringent, documented safety standards are met and proven to be actively mitigating risks.

### Regulatory Landscape
*   **USA:** OSHA (Occupational Safety and Health Administration) regulates workplace safety. Autonomous construction equipment must comply with general duty clauses and specific standards. UL (Underwriters Laboratories) certification is often required for the electronic hardware.
*   **EU:** The Machinery Directive 2006/42/EC (currently transitioning to the new Machinery Regulation 2023/1230/EU which explicitly addresses AI).
*   **CE Marking:** Mandatory for selling any machinery in the European Economic Area. It requires a comprehensive Technical File and Risk Assessment.

---

## 2. Safety Standards Reference

Our architecture is designed to comply with (or exceed) the following international standards:

1.  **ISO 13849-1 (Safety of machinery — Safety-related parts of control systems):**
    *   This is the cornerstone standard. It defines the required Performance Level (PL).
    *   For heavy autonomous machinery, the emergency stop and obstacle detection systems must meet **Performance Level d (PL d)** or PL e. PL d requires dual-channel architectures and continuous self-monitoring.
    *   Mean Time to Dangerous Failure (MTTFd) calculations are heavily scrutinized.
2.  **IEC 62061 (Functional safety of electrical/electronic/programmable electronic control systems):** Similar to ISO 13849, dealing with Safety Integrity Levels (SIL). We target SIL 2/3.
3.  **ISO 11688:** The upcoming standard specifically for Autonomous Mobile Machinery safety (2024).
4.  **ANSI/ITSDF B56.5:** Safety Standard for Driverless, Automatic Guided Industrial Vehicles (applicable in USA).
5.  **ISO 18497 (2018):** Agricultural machinery and tractors — Safety of highly automated agricultural machines.

---

## 3. The 7 Safety Layers (Defense in Depth)

We employ a "Defense in Depth" strategy. We do not trust the AI. The AI is a convenience feature; the safety layers are independent, robust systems that act as an infallible safety net.

*   **Layer 1: AI Perception (Software)**
    *   YOLOv8 running on the main compute node actively identifies humans and vehicles, pausing operations intelligently.
*   **Layer 2: LiDAR Field (Hardware/Firmware)**
    *   A 360-degree LiDAR (e.g., Ouster or Velodyne) scans a geofenced volume around the machine. A simple, non-AI firmware layer detects *any* object taller than 20cm in the path and commands a stop.
*   **Layer 3: Ultrasonic Ring (Hardware)**
    *   6x ultrasonic sensors provide a 1-meter close-range backup. If dirt blinds the LiDAR or cameras, ultrasonic waves still detect imminent physical proximity.
*   **Layer 4: Watchdog Timer (Hardware)**
    *   A dedicated microcontroller expects a heartbeat signal from the AI (Jetson) every 100ms. If the AI crashes, hangs, or kernel panics, the watchdog hardware resets the system and drops the safety relay.
*   **Layer 5: Emergency Stop Relay (Hardware)**
    *   Physical safety relays cut power to the hydraulic pilot valves. **Software cannot override this.** If the e-stop is triggered, the machine physically cannot move.
*   **Layer 6: Remote Kill Switch (Hardware)**
    *   A 900MHz LoRa radio module held by the site supervisor. Pressing the red button instantly drops the Layer 5 safety relay from up to 500 meters away.
*   **Layer 7: Geofencing (Firmware/Hardware)**
    *   RTK GPS boundaries are loaded into a separate microcontroller. If the machine's coordinate leaves the polygon boundary by even 1 cm, hydraulic power is cut.

---

## 4. E-Stop Circuit Design

The Emergency Stop circuit is the ultimate fail-safe. It must be designed to Category 3, Performance Level d (PL d) standards.

### Schematic Description

```text
[+24V Supply]
      |
      +---> [Remote LoRa Rx Relay (Normally Open, held Closed by heartbeat)]
      |
      +---> [Local Mushroom E-Stop Button (Dual Channel NC)]
      |
      +---> [Watchdog Relay (Normally Open, held Closed by heartbeat)]
      |
[Pilz PNOZ X Safety Relay (Dual Channel Evaluation)]
      |
      +---> [Hydraulic Solenoid Valve Power (Pilot Cutoff)]
      |
[GND]
```

*   **Dual-Channel:** The E-stop button has two independent internal switches (contacts). Both must close to allow operation. The Pilz safety relay checks for discrepancies (e.g., if one switch fails closed, the relay detects the fault and prevents restarting).
*   **Hardware Isolation:** The Pilz relay directly powers the solenoids that control the hydraulic pilot pressure. When power drops, spring-return valves immediately center, stopping all actuators.
*   **Response Time:** The time from pressing the button (or losing LoRa heartbeat) to the hydraulic pressure dropping is **<100ms**.

---

## 5. Human Detection System

Operating around humans requires robust perception, as humans move unpredictably.

### Hardware & Models
*   **Primary RGB:** High-dynamic-range industrial cameras feeding into a Jetson Orin.
*   **Model:** **YOLOv8-pose** (tracking human skeletons) running at 20fps via TensorRT. Pose estimation is more reliable than simple bounding boxes for distinguishing humans from oddly shaped obstacles.
*   **Night/Dust Operation:** A **FLIR Lepton 3.5 thermal camera** is fused with the RGB stream. Thermal is critical for agriculture where dust clouds from tractors can blind optical cameras.

### Safety Zones and Reactions

We define dynamic radii around the machine:

| Zone | Distance | AI Reaction | Hardware Reaction |
| :--- | :--- | :--- | :--- |
| **Green** | > 20m | Normal Operation | None |
| **Yellow** | 10m - 20m | ALERT: Sound external buzzer, notify supervisor dashboard. | None |
| **Orange** | 5m - 10m | SLOW DOWN: Restrict max velocity/hydraulic flow to 30%. | None |
| **Red (HARD STOP)**| 0m - 5m | COMMAND STOP. | (If AI fails, Layer 2/3 triggers E-stop) |

### False Positive Mitigation
To prevent the machine from stopping due to a single noisy frame, we implement a temporal buffer. The AI must detect a human in **3 consecutive frames** (approx. 150ms) to trigger a zone change. However, once triggered, the human must be completely absent from the zone for 20 frames (1 second) before resuming.

---

## 6. Product Liability Insurance Requirements

A strong technical architecture must be backed by financial protection.

*   **USA Markets:** Commercial General Liability (CGL) paired with a specific Product Liability policy. Startups deploying autonomous equipment typically require coverage between **USD 2 million to 5 million per year** depending on fleet size.
*   **EU Markets:** Governed by the Product Liability Directive (85/374/EEC). 
*   **Risk Mitigation Strategy for Insurance:** Insurers will not underwrite a fully autonomous machine without a track record. We mandate a "Trained Operator in Proximity" clause for the first 12 months of deployment. The operator holds the LoRa kill switch at all times.

---

## 7. Testing and Validation Protocol

Achieving CE marking and passing safety audits requires documented empirical proof. We follow a 4-phase rollout:

1.  **Phase 1: Lab Testing (Simulated Hydraulics)**
    *   HIL (Hardware-in-the-Loop) testing. The physical compute node and safety relays are wired to a simulation PC. We run 10,000 automated test cases (e.g., injecting fault codes, simulating human intrusions) and verify relay drop times.
2.  **Phase 2: Outdoor Proving Grounds**
    *   Controlled test site. No humans within 100m. Machine operates real tasks. Crash test dummies are thrown into the path to verify YOLOv8 and LiDAR response.
3.  **Phase 3: Beta Customer Deployment**
    *   Deployed to 3 partner farms/construction sites.
    *   **Requirement:** A trained human supervisor must actively monitor the machine with a LoRa kill switch.
4.  **Phase 4: Full Autonomous Operations**
    *   Achieved only after logging **500 hours of incident-free operation** per machine class in Phase 3.
    *   Compilation of the **Technical File, Risk Assessment, and Declaration of Conformity** for CE marking.

---

## 8. Data Privacy (GDPR Compliance)

Because our machines have numerous cameras operating in public or semi-public spaces, data privacy is a serious concern, especially in Europe.

*   **Local Processing:** Camera footage is processed directly on the Jetson Orin and **is not uploaded to the cloud**. 
*   **Blackbox Storage:** A rolling 24-hour video buffer is saved to an encrypted local SD card for incident investigation (like an airplane flight recorder). It overwrites itself automatically.
*   **Anonymized Telemetry:** GPS traces, error logs, and efficiency metrics sent to the AGRO-AI cloud are anonymized. Precise GPS coordinates are offset if they relate to private farm locations without explicit consent.
*   **GDPR:** We enforce Data Processing Agreements with European clients and support "Right to Deletion" for any telemetry tied to individual operators.

*(Document concludes here)*
