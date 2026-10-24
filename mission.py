"""Predetermined demonstration route; this is not autonomous exploration."""
import math

HEIGHT = 0.9
SPEED = 0.18
HOVER_SECONDS = 8.0
ROUTE_OFFSET = 1.35
WAYPOINTS = [(0,0),(-ROUTE_OFFSET,-ROUTE_OFFSET),(ROUTE_OFFSET,-ROUTE_OFFSET),
             (ROUTE_OFFSET,ROUTE_OFFSET),(-ROUTE_OFFSET,ROUTE_OFFSET),
             (-ROUTE_OFFSET,-ROUTE_OFFSET),(0,0)]


def reference(t):
    """Continuous target position and heading. None means the mission ended."""
    if t < HOVER_SECONDS:
        return [0,0,HEIGHT], 0.0
    elapsed = t-HOVER_SECONDS
    for a,b in zip(WAYPOINTS,WAYPOINTS[1:]):
        duration = math.dist(a,b)/SPEED
        if elapsed <= duration:
            u = elapsed/duration
            return [a[0]+u*(b[0]-a[0]), a[1]+u*(b[1]-a[1]), HEIGHT], 0.16*(t-HOVER_SECONDS)
        elapsed -= duration
    if elapsed < 8:
        return [0,0,HEIGHT], 0.16*(t-HOVER_SECONDS)
    return None


def duration():
    return HOVER_SECONDS+sum(math.dist(a,b)/SPEED for a,b in zip(WAYPOINTS,WAYPOINTS[1:]))+8
