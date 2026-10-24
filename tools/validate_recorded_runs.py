"""Recheck committed V1 evidence without editing it or requiring CoppeliaSim."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'examples' / 'recorded_runs'


def evaluate(name):
    folder = EVIDENCE / name
    metrics = json.loads((folder / 'metrics.json').read_text(encoding='utf-8'))
    grid = json.loads((folder / 'grid.json').read_text(encoding='utf-8'))
    states = grid['states']
    resolution = grid['resolution_m']
    ox, oy = grid['origin_m']
    total = unknown = 0
    for row_index, row in enumerate(states):
        for column, state in enumerate(row):
            assert state in (-1, 0, 1), 'Invalid occupancy state'
            x = ox + (column + 0.5) * resolution
            y = oy + (row_index + 0.5) * resolution
            open_interior = abs(x) < 1.9 and abs(y) < 1.9
            if name == 'partition' and -0.85 < x < -0.55 and y < -0.4:
                open_interior = False
            if open_interior:
                total += 1
                unknown += state == -1
    count, max_range = 0, 0.0
    with (folder / 'telemetry.csv').open(newline='', encoding='utf-8') as handle:
        for ray in csv.DictReader(handle):
            distance = float(ray['range_m'])
            assert math.isfinite(distance) and 0 <= distance <= 1.000001, 'Out-of-range reading'
            origin = [float(ray[f'origin_{axis}_m']) for axis in 'xyz']
            endpoint = [float(ray[f'end_{axis}_m']) for axis in 'xyz']
            assert math.dist(origin, endpoint) <= 1.00001, 'Ray endpoint exceeds sensor range'
            max_range = max(max_range, distance)
            count += 1
    result = {
        'completed': metrics['completed'],
        'collision_events': metrics['collision_events'],
        'minimum_surface_clearance_m': metrics['minimum_surface_clearance_m'],
        'simulation_seconds': metrics['simulation_seconds'],
        'measurements': count,
        'evaluated_open_interior_cells': total,
        'unknown_open_interior_cells': unknown,
        'maximum_recorded_range_m': max_range,
    }
    assert count == metrics['telemetry_rows'], 'CSV row count differs from metrics'
    assert result['completed'], 'Recorded baseline did not complete'
    assert result['collision_events'] == 0, 'Recorded baseline has contact'
    assert result['minimum_surface_clearance_m'] > 0.2, 'Recorded clearance is too small'
    assert unknown == 0, 'Recorded open interior contains unknown cells'
    return result


def main():
    expected = json.loads((EVIDENCE / 'summary.json').read_text(encoding='utf-8'))
    for name in ['empty', 'partition']:
        actual = evaluate(name)
        for key, value in actual.items():
            target = expected[name][key]
            if isinstance(value, float):
                assert math.isclose(value, target, abs_tol=1e-7), f'{name}: {key} mismatch'
            else:
                assert value == target, f'{name}: {key} mismatch'
        print(name + ': evidence matches committed summary')
        print(json.dumps(actual, indent=2))
    print('Evidence checks passed. No new physics or hardware experiment was performed.')


if __name__ == '__main__':
    main()
