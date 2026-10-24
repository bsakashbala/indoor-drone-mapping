"""Sensor-map navigation with body clearance and active coverage viewpoints.

Only the occupancy grid and measured drone pose are inputs. Scene geometry is
never supplied to this planner. A short-range sensor sweep supplies the map.
"""
from collections import deque
import heapq
import math

HEIGHT = 0.9
CRUISE_SPEED = 0.12
BODY_RADIUS = 0.23
WALL_CLEARANCE = 0.52  # includes controller braking margin and drone body
UNKNOWN_CLEARANCE = BODY_RADIUS
SCAN_SECONDS = 2.8
ROOM_HALF_EXTENT = 2.0  # known test-room work area, not an obstacle map


def disk_offsets(radius, resolution):
    n=math.ceil(radius/resolution)
    return [(x,y) for y in range(-n,n+1) for x in range(-n,n+1)
            if math.hypot(x,y)*resolution <= radius+1e-9]


class Explorer:
    def __init__(self, grid):
        self.grid=grid
        self.path=[]
        self.phase='Initial sensor sweep'
        self.done=False
        self.goal=None
        self.scan_until=8.0
        self.last_time=0.0
        self.command=None
        self.visits={}
        self.plans=0
        self.failed_goals={}
        self.last_gain=None
        self.stalled_since=None
        self.last_safety_check=-1
        self.emergency_target=None
        self.scan_goal=None

    def world(self, cell):
        g=self.grid
        return ((cell[0]+.5)*g.resolution-g.half_extent,
                (cell[1]+.5)*g.resolution-g.half_extent)

    def build_safe_map(self):
        g=self.grid
        free=set(); occupied=[]; unknown=[]
        for y in range(g.size):
            for x in range(g.size):
                state=g.state(x,y)
                if state==0: free.add((x,y))
                elif state==1: occupied.append((x,y))
                else: unknown.append((x,y))
        blocked=set()
        for x,y in occupied:
            for dx,dy in disk_offsets(WALL_CLEARANCE,g.resolution):
                blocked.add((x+dx,y+dy))
        offsets=disk_offsets(UNKNOWN_CLEARANCE,g.resolution)
        # Unknown-edge clearance is checked lazily below, avoiding expansion
        # of the entire unexplored exterior on every planning pass.
        def known_footprint(c):
            return all((c[0]+dx,c[1]+dy) in free for dx,dy in offsets)
        safe={c for c in free if c not in blocked and known_footprint(c)}
        return safe,occupied

    def reachable(self,start,safe):
        if start not in safe:
            candidates=[c for c in safe if math.dist(c,start)*self.grid.resolution<.18]
            if not candidates: return {},{},None
            start=min(candidates,key=lambda c:math.dist(c,start))
        distances={start:0.0}; parents={}; queue=[(0.0,start)]
        while queue:
            d,c=heapq.heappop(queue)
            if d>distances[c]+1e-9: continue
            x,y=c
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                n=x+dx,y+dy
                if n not in safe: continue
                if dx and dy and ((x+dx,y) not in safe or (x,y+dy) not in safe): continue
                nd=d+math.hypot(dx,dy)
                if nd<distances.get(n,math.inf):
                    distances[n]=nd; parents[n]=c; heapq.heappush(queue,(nd,n))
        return distances,parents,start

    def gain(self,cell):
        """Count unknown cells visible within the one-metre sensing limit."""
        from mapping import line_cells
        from sensor_config import MAX_RANGE_M
        g=self.grid
        seen=set()
        radius=(MAX_RANGE_M-.03)/g.resolution
        for i in range(48):
            a=i*math.tau/48
            end=(round(cell[0]+radius*math.cos(a)),round(cell[1]+radius*math.sin(a)))
            for x,y in line_cells(*cell,*end):
                if not g.inside(x,y): break
                state=g.state(x,y)
                if state==1: break
                if state==-1:
                    wx,wy=self.world((x,y))
                    # Do not chase unseen exterior through pixel-size gaps in
                    # a sensed boundary. The configured work area is 4 x 4 m.
                    if abs(wx)<ROOM_HALF_EXTENT-.08 and abs(wy)<ROOM_HALF_EXTENT-.08:
                        seen.add((x,y))
        return len(seen)

    def plan(self,pos):
        g=self.grid
        safe,occupied=self.build_safe_map()
        distances,parents,start=self.reachable(g.cell(*pos[:2]),safe)
        if start is None:
            self.phase='Scanning for a safe passage'
            return False
        # Sample candidate viewpoints on a 15 cm lattice. Include the current
        # viewpoint to revisit small holes without forcing an unsafe movement.
        candidates=[c for c in distances if c[0]%3==0 and c[1]%3==0]
        candidates.append(start)
        best=None; best_score=-math.inf
        for c in candidates:
            gain=self.gain(c)
            if gain<1: continue
            d=distances[c]*g.resolution
            nearest=min((math.dist(c,o)*g.resolution for o in occupied),default=2)
            # Prefer measured wall contours first, then views of interior holes.
            wall_bonus=1.8 if .40<=nearest<=.62 else 1.0
            repeats=self.visits.get(c,0)
            if repeats>=2: continue
            score=(gain*wall_bonus)/(0.65+d)/(1+2*repeats)
            if self.failed_goals.get(c,0)>1: continue
            if score>best_score:
                best,best_score=c,score
                self.last_gain=gain
        if best is None:
            self.done=True; self.phase='Coverage complete for reachable viewpoints'
            self.path=[]; return False
        route=[]; c=best
        while c!=start:
            route.append(c); c=parents[c]
        route.reverse()
        # Only simplify along cells already certified clear for the drone.
        from mapping import line_cells
        simplified=[]; anchor=start
        while route:
            furthest=0
            for i,c in enumerate(route):
                if all(q in safe for q in line_cells(*anchor,*c)):
                    furthest=i
                else: break
            anchor=route[furthest]; simplified.append(self.world(anchor))
            route=route[furthest+1:]
        self.path=simplified
        self.goal=best
        self.plans+=1
        nearest=min((math.dist(best,o)*g.resolution for o in occupied),default=2)
        self.phase='Following wall contour' if nearest<=.7 else 'Scanning uncovered interior'
        return True

    def update(self,packet):
        t=packet['time']; pos=packet['position']; dt=min(.15,max(.01,t-self.last_time))
        self.last_time=t
        if self.command is None: self.command=[pos[0],pos[1],HEIGHT]
        if t<8:
            return [pos[0],pos[1],HEIGHT],0.0
        # A near obstacle cancels accumulated target lead immediately. Continue
        # sweeping at rest rather than pushing the old command into the wall.
        close=[r for r in packet['rays'] if r['hit'] and r['distance']<.40]
        if close:
            if self.emergency_target is None:
                nearest=min(close,key=lambda r:r['distance'])
                dx=nearest['endpoint'][0]-nearest['origin'][0]
                dy=nearest['endpoint'][1]-nearest['origin'][1]
                n=max(math.hypot(dx,dy),1e-6)
                self.emergency_target=[pos[0]-.18*dx/n,pos[1]-.18*dy/n,HEIGHT]
            self.command=self.emergency_target[:]
            self.path=[]; self.scan_until=t+SCAN_SECONDS
            self.phase='Holding clear of obstacle'
            return self.command[:],0.0
        self.emergency_target=None
        if self.done:
            return [pos[0],pos[1],HEIGHT],0.0
        if t<self.scan_until:
            return self.command[:],0.0
        if self.scan_goal is not None:
            self.visits[self.scan_goal]=self.visits.get(self.scan_goal,0)+1
            self.scan_goal=None
        if not self.path:
            if math.dist(self.command[:2],pos[:2])>.045:
                return self.command[:],0.0
            if not self.plan(pos):
                self.scan_until=t+SCAN_SECONDS
                return self.command[:],0.0
            if not self.path:
                self.command=[pos[0],pos[1],HEIGHT]
                self.scan_until=t+SCAN_SECONDS
                self.scan_goal=self.goal
                return self.command[:],0.0
        goal=self.path[0]
        # Check the immediate path against freshly observed occupancy; a newly
        # added obstacle invalidates the old route instead of being ignored.
        from mapping import line_cells
        if t-self.last_safety_check>.25:
            self.last_safety_check=t
            a=self.grid.cell(*pos[:2]); b=self.grid.cell(*goal)
            offsets=disk_offsets(WALL_CLEARANCE,self.grid.resolution)
            for x,y in line_cells(*a,*b):
                for dx,dy in offsets:
                    xx,yy=x+dx,y+dy
                    if self.grid.inside(xx,yy) and self.grid.state(xx,yy)==1:
                        self.path=[]
                        self.scan_until=t+SCAN_SECONDS; self.phase='Replanning around obstacle'
                        return self.command[:],0.0
        distance=math.dist(self.command[:2],goal)
        if distance<.01:
            if math.dist(pos[:2],goal)<.06:
                self.path.pop(0)
                if not self.path:
                    self.scan_until=t+SCAN_SECONDS
                    self.scan_goal=self.goal
            return self.command[:],0.0
        step=min(CRUISE_SPEED*dt,distance)
        proposal=[self.command[0]+step*(goal[0]-self.command[0])/distance,
                  self.command[1]+step*(goal[1]-self.command[1])/distance,HEIGHT]
        if math.dist(proposal[:2],pos[:2])<=.10:
            self.command=proposal
        return self.command[:],0.0
