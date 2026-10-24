# Indoor Drone Mapping: professional project conversation

This document rewrites our project discussion as clear student prompts and professional answers. It covers the project decisions, implementation requests, presentation preparation and public packaging. It is an **edited reconstruction**, not a claim that every answer below was spoken verbatim. The [public transcript](CONVERSATION_TRANSCRIPT.md) preserves the available original prompts and final responses, with publication redactions.

The current deliverable is the V1 simulation. References to later versions describe historical requests only. For installation and current behaviour, use the root README and source code.

## 1. Project idea

**Student prompt:** We are developing an indoor drone that can map a room. We would like help creating a simulation and exploring a physical prototype.

**Professional answer:** Separate the project into simulation, stable physical flight and eventual integration. First demonstrate a small drone observing a room and creating a map. Then evaluate the sensing, localization and firmware required for a real aircraft. A successful simulation is useful evidence, but it does not establish that an autonomous hardware drone has been completed.

## 2. Team, budget and proposed hardware

**Student prompt:** We are four students with approximately ₹500–₹1,000 each. Our target is a 2D map, and we have some Python and electronics experience. We are considering Espressif ESP-Drone as the hardware base.

**Professional answer:** The total proposed budget is approximately ₹2,000–₹4,000. Prioritize a reproducible simulation and bench sensing work before committing to purchases. ESP-Drone is a hardware reference that requires compatible components, reliable flight, real measurements and an indoor pose estimate. A simulator-to-firmware interface remains a separate implementation task. Divide the learning work across programming, simulation, electronics and validation without claiming unverified hardware results.

## 3. A 3D simulation with a 2D map

**Student prompt:** We want the simulation to be three-dimensional, and we are considering Isaac Sim.

**Professional answer:** A 3D world and a 2D output are compatible. The simulator can model aircraft motion and collisions in three dimensions while horizontal measurements build an occupancy slice near flight height. Choose the simulator around the project's required physics, model availability and available computer, rather than adding complexity unrelated to the demonstration.

## 4. Available computer

**Student prompt:** Our laptop has an Intel i5-12500H, 16 GB RAM and an NVIDIA RTX 3050.

**Professional answer:** Record those details as the development environment. For this project, a simple room and an included drone model are sufficient. The eventual choice was CoppeliaSim, avoiding the need to depend on a heavier rendering or learning stack. This conversation does not establish minimum hardware specifications or a benchmark comparison between simulators.

## 5. Alternative simulators

**Student prompt:** What else can we use for a simple 3D drone simulation?

**Professional answer:** Evaluate a simulator that already supports a multirotor, range sensing and an external Python interface. For this implementation, the useful result was to choose one tool and establish target-following before writing a mapper. CoppeliaSim provides the model, physics, sensors and a remote API needed for that workflow.

## 6. Selecting CoppeliaSim

**Student prompt:** Can we use CoppeliaSim?

**Professional answer:** Yes. Use the supplied Quadcopter as the flight baseline and build a small room around it. Retain its original flight controller and attribute it to Coppelia Robotics. Python can communicate through the official ZeroMQ API. Our recorded experiments used CoppeliaSim Edu 4.10.0; readers must install an edition they are eligible to use.

## 7. Initial simulator steps

**Student prompt:** We have CoppeliaSim open. What should we do first?

**Professional answer:** Start with a fresh scene, load the built-in Quadcopter, identify its target and verify that the controller follows target changes. Add a simple enclosure with static, respondable walls. Establish a stable flight height before adding sensing. This prevents a controller or geometry issue from being mistaken for a mapping problem.

## 8. Target following works

**Student prompt:** The initial steps are complete and the drone follows its target.

**Professional answer:** Keep that working baseline. Add sensors next and confirm their detection direction, maximum range and response to a nearby wall. Map observations from the measured aircraft position, because a target command is not the same as the aircraft's actual location. Continue testing one component at a time.

## 9. Scene setup completed

**Student prompt:** The next scene setup step is complete.

**Professional answer:** Save a recoverable scene and proceed to the sensing-to-Python interface. Keep the simulator stopped when configuring the project. The completed package automates the room and sensor setup in `scene.py`, so another student does not have to reproduce every manual scene edit.

## 10. Request for a complete project and report

**Student prompt:** Please build the project, keep the simulation simple, reuse a built-in drone where possible and provide a detailed project report.

**Professional answer:** Use the existing Quadcopter, a 4 m square room and four distance rays. Implement a Python occupancy grid, safe viewpoint navigation, a live display and saved telemetry. Include ready-to-open scenes, setup scripts, tests and an editable report. Distinguish our mapping/navigation application from the upstream drone geometry and stabilization controller.

## 11. Realistic short sensing distance

**Student prompt:** The sensor should have a short range and should not detect a distant opposite wall.

**Professional answer:** Set each ray's maximum range to one metre and share that constant between scene construction and Python. The ray only clears measured space up to its valid endpoint. With no detection, do not add an occupied cell at the range limit or label distant space free. If the range changes, rebuild the saved scene so both sides agree.

## 12. Added-wall failure and missing interior coverage

**Student prompt:** The drone does not handle an added wall correctly. It should stay near walls, avoid collisions and observe unknown areas in the middle of the room.

**Professional answer:** Include added shapes in the sensing collection while excluding the drone, floor and reference objects. Plan from observed occupancy with body clearance rather than following a fixed path. Prefer useful wall-adjacent viewpoints, then consider views that can reveal interior gaps. Preserve unknown cells until measured, and count a viewpoint as visited only after arrival and a scan. The recorded partition experiment supports this behaviour for that scene; it is not a guarantee for every obstacle arrangement.

## 13. Historical request for another version

**Student prompt:** Can you make another version of the project?

**Professional answer:** A separate version can explore improvements without overwriting the baseline. The later clarification prioritized navigation and coverage. That discussion remains part of the history, but the current public package contains V1 only, following the final submission decision.

## 14. Clarifying the improvement priority

**Student prompt:** Better navigation and coverage should be the main focus.

**Professional answer:** Useful areas to investigate include reachable observation goals, handling narrow passages, recognizing remaining occlusions and reporting honest completion conditions. Such extensions should be evaluated as separate experiments. They should not be silently attributed to the V1 submission or mixed into its baseline evidence.


## Closing project statement

“We developed a reproducible student simulation around an attributed existing flight model. Our contribution joins short-range sensing, occupancy mapping, viewpoint navigation, visualization and evidence export. The two committed physics experiments help us explain the result, while exact pose, ideal sensors and a configured work area define its limits. Physical sensing, localization and ESP-Drone integration remain future work.”
