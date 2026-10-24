# How we built the project, step by step

This guide describes the V1 project in student language. For the fastest reproduction, follow the root README and open a supplied scene. These steps explain how that working project was assembled.

## 1. Decide what we mean by room mapping

We chose a three-dimensional simulated room and a two-dimensional map. The drone operates near one flight height, and horizontal range readings describe a slice through the room. We did not try to reconstruct the ceiling, furniture height or a complete 3D mesh.

We separated the simulation from the physical aircraft. The simulation is implemented. ESP-Drone, electronics, real sensors and indoor localization are future integration work. The original team budget was approximately ₹2,000–₹4,000 in total; that was a planning constraint, not a verified bill of materials or a claim that hardware was purchased.

## 2. Choose a simulator that we can run

We considered Isaac Sim and then chose CoppeliaSim for a simpler room demonstration with an included drone. The selected laptop was an i5-12500H with 16 GB RAM and an RTX 3050. We kept the scene small and avoided ROS, a learning framework and downloaded drone assets.

## 3. Check the built-in drone first

We loaded CoppeliaSim's Quadcopter and checked that it could follow its target object. This established that the existing controller and dynamics worked before we introduced our mapper. The model's geometry, stabilization and thrust control remain Coppelia Robotics' contribution.

Our Python program controls a position target, not raw motor speeds. The aircraft can lag behind this target, so mapping uses measured pose rather than the requested position.

## 4. Build a simple room

`scene.py` creates the following geometry in a new scene:

| Wall | Size X, Y, Z (m) | Centre X, Y, Z (m) |
|---|---|---|
| North | 4.4, 0.2, 1.8 | 0, 2.1, 0.9 |
| South | 4.4, 0.2, 1.8 | 0, -2.1, 0.9 |
| East | 0.2, 4.4, 1.8 | 2.1, 0, 0.9 |
| West | 0.2, 4.4, 1.8 | -2.1, 0, 0.9 |

The inner wall surfaces define a 4 m square. The walls are static and respondable. The default floor remains, and there is no ceiling so that we can see the aircraft. The builder sets the initial target to 0.9 m height and the simulation time step to 0.05 s.

## 5. Add four short-range sensors

We attach front, left, back and right ray sensors to the drone's base. Each uses the shared one-metre range from `sensor_config.py`. Their origin is 0.04 m above the base reference, and their local +Z axes point horizontally.

The simulated bracket rotates the four rays at 0.65 rad/s, modulo a quarter turn. Four directions therefore sweep around the drone while its body heading stays stable. This is an ideal simulation arrangement; a real aircraft would need an equivalent sensor and mounting design.

## 6. Send synchronized observations to Python

The `SNAPSHOT_LUA` string in `scene.py` contains our Lua extension. It explicitly handles the proximity sensors and exposes `indoorMappingSnapshot` to the remote API. A packet contains simulation time, measured position/orientation and each ray's origin, endpoint, range and hit flag.

Python uses the official ZeroMQ remote client in stepping mode. It reads a packet, updates the map and target, then advances the simulator. The same packet also includes collision and surface-clearance measurements for monitoring. Obstacle geometry does not enter the exploration planner.

## 7. Convert observations into an occupancy map

`mapping.py` starts a 100 × 100 grid with every cell unknown. A cell is 5 cm wide, so the map spans 5 m square. World coordinates are converted into indices relative to an origin at (-2.5, -2.5).

Bresenham traversal lists the cells a ray crosses. We add free-space evidence before its endpoint. A detected endpoint adds occupied evidence; a no-return ray adds no artificial obstacle at its range limit. Observations accumulate, and an explicit observed flag preserves unknown cells.

The map window displays the grid and measured flight path. It is a display of observations, not a copy of the simulator's room geometry.

## 8. Handle walls and the size of the drone

A point-sized path can be clear while the rotors collide. We therefore use a 0.23 m body footprint and expand measured occupied cells by a nominal 0.52 m centre clearance. The full footprint must fit in observed free space, including near unknown boundaries.

Dijkstra search finds reachable cells with cardinal and diagonal moves. A diagonal move is forbidden when either adjacent side cell is unsafe. This prevents cutting corners through inflated obstacles.

## 9. Observe wall contours and interior gaps

After an initial eight-second scan, the planner samples candidate viewpoints on a 15 cm lattice. It estimates how many unknown interior cells a one-metre view could reveal, stopping predicted visibility at measured obstacles. A score balances information gain, travel distance and repeated visits. A preference for useful wall-adjacent views produces contour-following behaviour.

Following the outer wall alone can leave unknown space in the middle. The planner therefore considers interior viewpoints as well. It never fills a gray patch simply because it expects the room to be empty.

## 10. Move slowly and revise the route

The target moves at up to 0.12 m/s and leads measured position by at most 0.10 m. Python rechecks the immediate route as new observations arrive. A hit below 0.40 m cancels the old route and commands a fixed retreat target.

A viewpoint is counted as visited after arrival and a 2.8 s scan, not when it is first planned. Contact, excessive tilt or flight-limit violations stop a failed run. These checks do not prove that every possible environment is safe.

## 11. Test an added partition

The supplied partition is 0.20 m thick and 1.55 m long, centred at (-0.70, -1.225, 0.90), with height 1.8 m. It extends inward from the south wall to Y = -0.45 m.

Use the supplied obstacle scene to reproduce this case. To rebuild it manually, create a cuboid with these dimensions/position in the empty project scene, set it static/respondable and save a separate scene. The planner discovers it through ray hits. Its rectangle coordinates are used only by the separate evaluation.

## 12. Save and inspect evidence

Every run can save a PNG preview, PGM/YAML occupancy map, grid JSON, telemetry CSV and metrics JSON. The image helps explain the result; the raw files let us check it. Always inspect whether a run completed and whether it reported a failure.

The committed empty and partition flights recorded zero contacts and zero unknown cells in the defined evaluated open interior. The evaluation bands and exact simulator pose matter when interpreting those claims. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## 13. Prepare the student explanation

We divide the explanation into purpose/setup, sensing/mapping/software, testing/results, and outputs/limitations/hardware plans. Each student should run the program and understand at least one complete flow from sensor measurement to map update to motion decision.

The presentation and explanation concern V1. Later-version requests remain in the historical conversation but do not change the source included in this repository.

## 14. Package the public project

We copied only the V1 runtime into this repository, removed a computer-specific Python fallback and kept runtime output separate from committed examples. We added an environment checker, a read-only evidence validator, documentation, contribution instructions and automated tests. The two `.ttt` files make initial setup easy; the builder makes the scene inspectable and reproducible.

Use the MIT terms for our original contribution and retain upstream notices for the simulator and its assets. The published conversation is sanitized and explains how AI assistance was used.
