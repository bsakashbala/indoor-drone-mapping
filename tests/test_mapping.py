import math
import unittest
from mapping import OccupancyGrid, line_cells
from mission import reference, duration, ROUTE_OFFSET, HOVER_SECONDS, SPEED
from sensor_config import MAX_RANGE_M
from run import ideal_packet


class MappingTests(unittest.TestCase):
    def test_hit_marks_endpoint_and_clears_path(self):
        g=OccupancyGrid()
        g.update([0,0],[1,0],True)
        self.assertEqual(g.state(*g.cell(1,0)),1)
        self.assertEqual(g.state(*g.cell(.5,0)),0)
        self.assertEqual(g.state(*g.cell(.5,.5)),-1)

    def test_no_return_does_not_invent_wall(self):
        g=OccupancyGrid()
        g.update([0,0],[4,0],False)
        self.assertEqual(g.metrics()['occupied_cells'],0)

    def test_negative_coordinates_and_outside_grid(self):
        g=OccupancyGrid()
        g.update([0,0],[-4,-4],True)
        self.assertEqual(g.metrics()['occupied_cells'],0)
        self.assertEqual(g.state(*g.cell(-1,-1)),0)

    def test_nonfinite_input_is_rejected(self):
        g=OccupancyGrid(); g.update([0,0],[math.nan,0],True)
        self.assertEqual(g.rays,0)

    def test_saturation_and_line_endpoints(self):
        g=OccupancyGrid()
        for _ in range(100): g.update([0,0],[1,0],True)
        x,y=g.cell(1,0); self.assertEqual(g.values[y][x],4)
        self.assertEqual(list(line_cells(0,0,0,0)),[(0,0)])

    def test_mission_stays_within_room_and_ends(self):
        for t in range(math.ceil(duration())):
            ref=reference(t)
            if ref:
                p,yaw=ref
                self.assertLessEqual(max(abs(p[0]),abs(p[1])),ROUTE_OFFSET+1e-9)
                self.assertEqual(p[2],.9)
        self.assertIsNone(reference(duration()+1))

    def test_centre_cannot_detect_distant_walls(self):
        packet=ideal_packet(0)
        self.assertTrue(all(not r['hit'] for r in packet['rays']))
        for r in packet['rays']:
            self.assertAlmostEqual(math.dist(r['origin'],r['endpoint']),MAX_RANGE_M)

    def test_range_limit_does_not_clear_unseen_space(self):
        grid=OccupancyGrid()
        for r in ideal_packet(0)['rays']:
            grid.update(r['origin'],r['endpoint'],r['hit'])
        self.assertEqual(grid.state(*grid.cell(1.5,0)),-1)
        self.assertEqual(grid.state(*grid.cell(2,0)),-1)
        self.assertEqual(grid.state(*grid.cell(.5,0)),0)

    def test_nearby_wall_is_detected_within_range(self):
        t=HOVER_SECONDS+math.hypot(ROUTE_OFFSET,ROUTE_OFFSET)/SPEED
        rays=ideal_packet(t)['rays']
        self.assertTrue(any(r['hit'] for r in rays))
        self.assertTrue(any(not r['hit'] for r in rays))
        self.assertTrue(all(0<r['distance']<=MAX_RANGE_M for r in rays))


if __name__=='__main__': unittest.main()
