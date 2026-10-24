# Four-student explanation

These are suggested speaking roles, not a verified attribution of individual code commits. Everyone should be able to reproduce the setup and distinguish completed simulation work from planned hardware.

| Presenter | Explain |
|---|---|
| Bhavesh Sharma | Problem, why 3D simulation produces a 2D map, tool choice and room setup. |
| Priyanshu Yadav | Sensors, mapping, Python/Lua communication, navigation and libraries. |
| Atharva Joshi | Added-wall experiment, tests, measured results and live demonstration. |
| Akash Bala | Saved outputs, limitations, upstream credits and proposed ESP-Drone work. |

## A short opening

“Good morning, Sir. Our project explores an indoor room in CoppeliaSim and builds a two-dimensional occupancy map using one-metre range measurements. We kept the simulator's built-in drone and stabilization controller. Our work connects sensing, map updates, viewpoint selection, movement commands and saved evaluation data.”

## Questions we should answer

**Why a 2D map in a 3D simulator?** The simulator models flight and collisions in three dimensions, but the sensors observe a slice near flight height. That slice is sufficient for this bounded mapping demonstration.

**Why is this not SLAM?** The simulator gives the drone's exact pose. We map from known positions; we do not jointly estimate position and map.

**Can the sensor see the opposite wall?** Only if the first detected surface lies within one metre. A nearer partition occludes surfaces behind it.

**How does it hug a wall?** It prefers useful wall-adjacent viewpoints while maintaining a clearance margin. It is not a rigid contact follower or a strict hand-rule controller.

**How do we avoid unknown patches in the middle?** We score viewpoints by the unknown interior cells they could reveal and move to reachable safe observation positions. We do not erase unknown areas without sensing them.

**How do we account for the drone's size?** Occupied cells are inflated, and its complete circular footprint must fit in known free space. Narrow passages can therefore remain inaccessible.

**Who controls the motors?** CoppeliaSim's original Quadcopter controller. Our program changes the target position and receives measured sensor/pose data.

**What proves the result?** Committed telemetry, grids, metrics and a separate evaluator support the two recorded experiments. Unit tests cover mapping and planner behaviour. A screenshot alone does not establish successful coverage.

**What does zero unknown mean?** Zero unknown cells in the specifically defined evaluated open interior, excluding boundary/surface bands. It does not include exterior regions or the solid wall interior.

**What did we build ourselves?** The room/sensor setup, telemetry extension, Python mapper, navigation, display, export and tests around an attributed existing model/controller. We used AI assistance and should explain and verify that work ourselves.

**Is the physical drone ready?** No. ESP-Drone is a future hardware reference. Real sensing, pose estimation, firmware commands and flight validation remain necessary.

## Live demonstration order

Open the empty scene, leave it stopped, launch Python and explain the map legend. Show the one-metre range and growing observations. Open the separate partition scene for a second run and explain occlusion and route changes. Show saved metrics and the committed examples if a full flight cannot fit into the presentation time.
