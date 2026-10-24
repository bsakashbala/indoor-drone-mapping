"""Small, simulator-independent occupancy grid. Coordinates are in metres."""
import math
from pathlib import Path


def line_cells(x0, y0, x1, y1):
    """Bresenham traversal, including both endpoints."""
    dx, sx = abs(x1-x0), 1 if x0 < x1 else -1
    dy, sy = -abs(y1-y0), 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        yield x0, y0
        if x0 == x1 and y0 == y1:
            return
        e = 2*err
        if e >= dy:
            err += dy
            x0 += sx
        if e <= dx:
            err += dx
            y0 += sy


class OccupancyGrid:
    def __init__(self, half_extent=2.5, resolution=0.05):
        self.half_extent, self.resolution = half_extent, resolution
        self.size = round(2*half_extent/resolution)
        self.values = [[0.0]*self.size for _ in range(self.size)]
        self.observed = [[False]*self.size for _ in range(self.size)]
        self.rays = 0

    def cell(self, x, y):
        return (math.floor((x+self.half_extent)/self.resolution),
                math.floor((y+self.half_extent)/self.resolution))

    def inside(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def update(self, origin, endpoint, hit):
        if not all(math.isfinite(v) for v in (*origin[:2], *endpoint[:2])):
            return
        a, b = self.cell(*origin[:2]), self.cell(*endpoint[:2])
        cells = list(line_cells(*a, *b))
        for i, (x,y) in enumerate(cells):
            if self.inside(x,y):
                occupied = hit and i == len(cells)-1
                self.values[y][x] = max(-4.0, min(4.0, self.values[y][x] + (0.85 if occupied else -0.4)))
                self.observed[y][x] = True
        self.rays += 1

    def state(self, x, y):
        if not self.observed[y][x]:
            return -1
        if self.values[y][x] > 0.6:
            return 1
        if self.values[y][x] < -0.2:
            return 0
        return -1

    def image(self, trajectory=()):
        from PIL import Image, ImageDraw
        im = Image.new('RGB', (self.size,self.size), '#b8bec6')
        pix = im.load()
        for y in range(self.size):
            for x in range(self.size):
                pix[x,self.size-1-y] = {1:(25,35,48), 0:(246,248,250), -1:(184,190,198)}[self.state(x,y)]
        draw = ImageDraw.Draw(im)
        points = [(self.cell(p[0],p[1])[0], self.size-1-self.cell(p[0],p[1])[1]) for p in trajectory]
        if len(points)>1:
            draw.line(points,fill='#0b8f83',width=1)
        if points:
            x,y=points[-1]
            draw.ellipse((x-1,y-1,x+1,y+1),fill='#d65b32')
        return im

    def save(self, directory, trajectory=()):
        import json
        directory = Path(directory)
        directory.mkdir(parents=True,exist_ok=True)
        self.image(trajectory).resize((700,700),resample=0).save(directory/'map.png')
        # ROS-style grayscale values: occupied 0, free 254, unknown 205.
        rows = bytearray()
        for y in reversed(range(self.size)):
            rows.extend({1:0,0:254,-1:205}[self.state(x,y)] for x in range(self.size))
        (directory/'map.pgm').write_bytes(f'P5\n{self.size} {self.size}\n255\n'.encode()+rows)
        (directory/'map.yaml').write_text(
            f'image: map.pgm\nresolution: {self.resolution}\norigin: [-{self.half_extent}, -{self.half_extent}, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n',encoding='utf-8')
        (directory/'grid.json').write_text(json.dumps({'resolution_m':self.resolution,
            'origin_m':[-self.half_extent,-self.half_extent], 'row_order':'increasing world Y',
            'states':[[self.state(x,y) for x in range(self.size)] for y in range(self.size)]}),encoding='utf-8')

    def metrics(self):
        counts = {-1:0,0:0,1:0}
        for y in range(self.size):
            for x in range(self.size):
                counts[self.state(x,y)] += 1
        # Room geometry is used ONLY to evaluate the output, never to create it.
        detected,expected = 0,0
        for y in range(self.size):
            for x in range(self.size):
                wx = -self.half_extent+(x+0.5)*self.resolution
                wy = -self.half_extent+(y+0.5)*self.resolution
                if (abs(abs(wx)-2.0)<self.resolution*0.51 and abs(wy)<=2.0 or
                    abs(abs(wy)-2.0)<self.resolution*0.51 and abs(wx)<=2.0):
                    expected += 1
                    if any(self.inside(xx,yy) and self.state(xx,yy)==1
                           for xx in range(x-1,x+2) for yy in range(y-1,y+2)):
                        detected += 1
        return {'rays':self.rays,'occupied_cells':counts[1],'free_cells':counts[0],
                'unknown_cells':counts[-1], 'evaluated_wall_cells':expected,
                'wall_recall_with_one_cell_tolerance':detected/expected if expected else 0}
