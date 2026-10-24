# Architecture and implementation

## Responsibilities

| File | Responsibility |
|---|---|
| `launch.py` | Check the local server, locate the Windows simulator and call the runner. |
| `scene.py` | Build the room, load the upstream model, attach sensors and define the Lua extension. `configure` refreshes sensing logic without replacing an open project scene. |
| `run.py` | Parse options, coordinate stepping, receive telemetry, update map/navigation, draw the display and save evidence. |
| `mapping.py` | Simulator-independent occupancy grid, ray traversal, classification, image export and boundary-recall evaluation. |
| `navigation.py` | Footprint clearance, safe-cell search, visibility gain, goal selection, target motion and close-obstacle response. |
| `sensor_config.py` | Shared maximum ray range. |
| `mission.py` | Legacy reference trajectory used by original sensor tests. It does not fly the live exploration mission. |

## One iteration

1. Read a Lua snapshot from the drone controller script.
2. Check stop-monitor conditions and record measured pose.
3. Update the occupancy grid for the four measured rays.
4. Write four telemetry rows, including the current target and phase.
5. Ask the explorer for the next position/yaw target.
6. If exploration is finished, exit and export. Otherwise set the target and advance one physics step.
7. Refresh the live display periodically, if enabled.

The default physics step is 0.05 s. The code processes four rays each step, giving a nominal 80 readings per simulated second. The live display refreshes less frequently than sensing. A fixed hardware sampling rate is not implied by those values.

## Coordinates and mapping

Coordinates use metres in the simulator's world frame. The grid origin is (-2.5, -2.5), with 0.05 m cells. For horizontal position `(x, y)`:

```text
column = floor((x + 2.5) / 0.05)
row    = floor((y + 2.5) / 0.05)
```

Raw JSON row index increases with world Y. The preview and PGM reverse row order so that positive Y appears upward. `map.yaml` supplies the origin and resolution.

The snapshot uses the sensor's measured transform to convert its local hit point into world coordinates. With no hit, the endpoint is the transformed local maximum-range point. Mapping uses the horizontal components, so this is a horizontal projection of sensor observations rather than a full 3D map.

### Bresenham traversal

`line_cells` enumerates integer cells along the ray, including both endpoints. For a hit, cells before the endpoint receive free evidence and the final cell receives occupied evidence. For no return, the entire measured segment receives free evidence. Space beyond the segment remains unobserved.

### Evidence accumulation

Each observation applies:

```text
evidence_new = clip(evidence_old + increment, -4.0, 4.0)
occupied endpoint increment = +0.85
free ray-path increment    = -0.40
occupied if observed and evidence > +0.60
free     if observed and evidence < -0.20
unknown  otherwise
```

This is a simplified log-odds-style inverse sensor model. The increments and thresholds are demonstration settings, not a calibrated probability model for a real sensor. Repeated free evidence can eventually clear a previously occupied cell. An unobserved zero is never automatically classified as free.

## Navigation algorithms

### Occupied-cell inflation and known-free footprint

`disk_offsets` enumerates grid offsets within a radius. Occupied cells block possible drone centres within 0.52 m. A candidate centre must also have its full 0.23 m footprint inside observed free cells. This represents body size and a conservative planning margin; it is not the actual full 3D drone geometry.

### Dijkstra shortest-path search

`reachable` expands eight-connected safe neighbours using a heap. Straight moves cost one cell and diagonals cost √2 cells. Side-cell checks prohibit diagonal corner cutting. Parent pointers reconstruct a route to a selected viewpoint. Route simplification only connects points through cells already classified safe.

### Visibility gain and viewpoint scoring

Candidate positions lie on a 0.15 m lattice plus the current reachable position. `gain` casts 48 predicted map rays over a conservative range just under one metre. These prediction rays are planning computations, distinct from the four physical simulated sensors. They stop at occupied cells and count unique unknown cells inside the configured room area.

The score is:

```text
score = gain × wall_bonus / (0.65 + route_distance_m) / (1 + 2 × previous_visits)
```

The code sets `wall_bonus = 1.8` when the nearest occupied cell is 0.40–0.62 m away, otherwise 1.0. The 0.52 m safe-map inflation still governs legal positions, so the preference does not override clearance. Viewpoints with at least two completed visits or sufficient recorded failures are skipped.

This is an information-seeking viewpoint heuristic with a wall-contour preference. It is not a strict left-hand/right-hand wall follower, optimal coverage planner or proof that every visible cell will eventually be observed.

### Motion control and replanning

The low-level Quadcopter controller remains upstream. Our explorer advances its target at up to 0.12 m/s, limits target lead and holds while scanning. The immediate route is checked periodically against updated occupancy. A hit closer than 0.40 m triggers a fixed retreat target about 0.18 m away from that hit direction. A fixed target avoids moving the retreat destination along with drone drift.

### Completion

When no eligible sampled reachable viewpoint predicts new unknown cells, the explorer sets `done`. This is a practical stopping criterion within the configured area and visit limits. Sealed regions, narrow passages, map discretization and occlusion can leave unknown space. Independently inspect final coverage; `completed=true` is not a mathematical coverage certificate.

## Monitoring versus navigation

The Lua snapshot includes true scene collision and surface-distance measurements. The runner uses contact as a stop condition and records minimum surface clearance for evaluation. The explorer itself receives pose and sensed rays, and uses the occupancy grid for paths; it does not query those true distances for planning.

Bounds, altitude and tilt monitors also stop a failed run after the initial settling period. Output is saved in the `finally` block. These monitors and exact pose simplify a simulated experiment and are not a substitute for a physical aircraft's estimator or flight safety systems.

## Data files

- `grid.json`: resolution, origin, row order and integer cell states.
- `telemetry.csv`: timestamp, position, roll/pitch/yaw, sensor name, hit flag, range, ray origin, endpoint, commanded position, surface clearance and phase. One row per ray.
- `metrics.json`: mode, simulator version, completion/failure, simulated duration, wall-clock duration, reading count, cell counts, tracking error, altitude range, contact count and planner information.
- `map.pgm`: grayscale occupancy only: occupied 0, free 254, unknown 205.
- `map.yaml`: resolution, origin and ROS-style thresholds.
- `map.png`: display image with trajectory overlay. Do not interpret its coloured path as occupancy.

## Extending the code

Keep sensor range consistent between scene and Python. Introduce noise/dropout handling as a separate experiment, retain an unchanged baseline, and report the effect on map quality. A real sensor timeout must not automatically mean valid free space. Replacing exact pose requires a separate localization implementation. Hardware requires a firmware interface, measured mass/dynamics and a tested indoor estimator before autonomous flight can be claimed.
