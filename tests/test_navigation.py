import math
import unittest
from mapping import OccupancyGrid
from navigation import Explorer, WALL_CLEARANCE
from run import analytic_packet


class NavigationTests(unittest.TestCase):
    def known_grid(self):
        g=OccupancyGrid()
        for y in range(g.size):
            for x in range(g.size):
                g.values[y][x]=-4
                g.observed[y][x]=True
        return g

    def test_paths_go_around_a_partition_with_body_clearance(self):
        g=self.known_grid()
        for y in range(g.cell(0,-1.9)[1],g.cell(0,.5)[1]+1):
            g.values[y][g.cell(0,0)[0]]=4
        nav=Explorer(g)
        safe,_=nav.build_safe_map()
        self.assertNotIn(g.cell(.3,0),safe)
        start=g.cell(-1,0); goal=g.cell(1,0)
        reachable,parents,root=nav.reachable(start,safe)
        self.assertIn(goal,reachable)
        route=[]; c=goal
        while c!=root: route.append(c); c=parents[c]
        self.assertGreater(max(nav.world(c)[1] for c in route),.9)

    def test_unknown_holes_generate_a_sensing_goal_without_fake_filling(self):
        g=self.known_grid()
        x,y=g.cell(.5,.5)
        for yy in range(y,y+3):
            for xx in range(x,x+3):
                g.values[yy][xx]=0; g.observed[yy][xx]=False
        nav=Explorer(g)
        self.assertTrue(nav.plan([0,0,.9]))
        self.assertGreater(nav.last_gain,0)
        self.assertEqual(g.state(x,y),-1)
        self.assertEqual(g.state(*nav.goal),0)
        self.assertNotIn(nav.goal,nav.visits)  # planned is not the same as visited

    def test_no_blind_motion_when_no_known_free_footprint_exists(self):
        nav=Explorer(OccupancyGrid())
        self.assertFalse(nav.plan([0,0,.9]))
        self.assertFalse(nav.done)
        self.assertEqual(nav.path,[])

    def test_unseen_space_blocks_a_corridor_narrower_than_the_body(self):
        g=OccupancyGrid()
        for y in range(47,53):
            for x in range(g.size):
                g.values[y][x]=-4; g.observed[y][x]=True
        safe,_=Explorer(g).build_safe_map()
        self.assertEqual(safe,set())

    def test_retreat_target_is_fixed_instead_of_chasing_drift(self):
        nav=Explorer(self.known_grid())
        packet={'time':10,'position':[1.6,0,.9],
                'rays':[{'hit':True,'distance':.3,'origin':[1.6,0,.9],'endpoint':[1.9,0,.9]}]}
        command,_=nav.update(packet)
        packet['time']=10.05; packet['position']=[1.63,0,.9]
        command2,_=nav.update(packet)
        self.assertEqual(command,command2)
        self.assertLess(command[0],1.6)

    def test_added_wall_is_detected_and_occludes_the_far_wall(self):
        p=analytic_packet([-.7,.15,.9],0,[(-.8,-.6,-2,-.45)])
        ray=next(r for r in p['rays'] if r['name']=='right')
        self.assertTrue(ray['hit'])
        self.assertAlmostEqual(ray['distance'],.6)
        self.assertAlmostEqual(ray['endpoint'][1],-.45)


if __name__=='__main__': unittest.main()
