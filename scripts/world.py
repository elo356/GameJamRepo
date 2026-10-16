from ursina import *

from scripts.supermercado import ROOT, asset_path, textura

WALL_HEIGHT = 6
SHELF_HEIGHT = 2.2
COUNTER_HEIGHT = 1.1
SHELF_BOARDS = (0.15, 0.65, 1.15, 1.65)
PRODUCT_PIXEL = 0.011
PRODUCT_MAX_SIZE = 0.3
ENEMY_SLOT_CHANCE = 0.06
JAR_CHANCE = 0.12
AISLES = ("A", "B", "C", "D")
FOG_COLOR = color.rgb32(14, 16, 24)


def cargar_productos():
    carpeta = ROOT / "images" / "products"
    return [Texture(str(f), filtering=None) for f in sorted(carpeta.rglob("*.png"))]


def product_size(tex):
    pixel = min(PRODUCT_PIXEL, PRODUCT_MAX_SIZE / max(tex.width, tex.height))
    return tex.width * pixel, tex.height * pixel


def distance_xz(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


class MeshBuilder:
    def __init__(self):
        self.verts, self.tris, self.uvs, self.cols = [], [], [], []

    def quad(self, corners, shade=1.0, uv=(1, 1)):
        i = len(self.verts)
        self.verts.extend(corners)
        self.uvs.extend([(0, 0), (uv[0], 0), (uv[0], uv[1]), (0, uv[1])])
        c = color.rgb(shade, shade, shade)
        self.cols.extend([c, c, c, c])
        self.tris.extend([i, i + 1, i + 2, i, i + 2, i + 3])

    def build(self, texture, tint=color.white, collider="mesh"):
        if not self.verts:
            return None
        return Entity(model=Mesh(vertices=self.verts, triangles=self.tris, uvs=self.uvs, colors=self.cols),
                      texture=texture,
                      color=tint,
                      double_sided=True,
                      collider=collider)


class Door:
    CLOSED_COLOR = color.rgb32(255, 60, 50)
    OPEN_COLOR = color.rgb32(90, 255, 120)

    def __init__(self, pos, texture):
        self.entity = Entity(model="cube", texture=texture, position=(pos.x, WALL_HEIGHT / 2, pos.z),
                             scale=(1, WALL_HEIGHT, 0.2), color=color.rgb32(150, 150, 160), collider="box")
        self.label = Text(text="", parent=scene, origin=(0, 0), scale=9,
                          position=(pos.x, 2.4, pos.z + 0.12), rotation_y=180)
        Entity(model="quad", color=color.rgb32(255, 170, 90), position=(pos.x, WALL_HEIGHT / 2, pos.z - 0.3),
               scale=(0.98, WALL_HEIGHT), rotation_y=180, double_sided=True)
        self.close()

    def close(self):
        self.entity.enabled = self.label.enabled = True
        self.entity.collision = True
        self.entity.scale_x = 1
        self.label.text, self.label.color = "CERRADO", self.CLOSED_COLOR

    def open(self):
        self.label.text, self.label.color = "SALIDA", self.OPEN_COLOR
        self.entity.collision = False
        self.entity.animate_scale_x(0.05, duration=1.0)

    def hide(self):
        self.entity.enabled = self.label.enabled = False


class Level:
    def __init__(self, grid, exit_cells=None):
        self.grid = [list(row) for row in grid]
        self.rows = len(self.grid)
        self.cols = max(len(row) for row in self.grid)
        self.grid = [row + ['.'] * (self.cols - len(row)) for row in self.grid]
        self.exit_cells = exit_cells or []
        self.shelf_rows = [r for r, row in enumerate(self.grid) if "S" in row]
        self.shelf_slots = []

    def cell_center(self, col, row):
        return Vec3(col + 0.5 - self.cols / 2, 0, row + 0.5 - self.rows / 2)

    def cell_type(self, col, row):
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return "#"
        return self.grid[row][col]

    def solid(self, cell):
        return cell in "#FSCE"

    def cell_at(self, x, z):
        return math.floor(x + self.cols / 2), math.floor(z + self.rows / 2)

    def blocked(self, x, z, r):
        for cx, cz in ((x - r, z - r), (x + r, z - r), (x - r, z + r), (x + r, z + r)):
            if self.solid(self.cell_type(*self.cell_at(cx, cz))):
                return True
        return False

    def slide_move(self, pos, dx, dz, r):
        x, z = pos[0], pos[2]
        if not self.blocked(x + dx, z, r):
            x += dx
        if not self.blocked(x, z + dz, r):
            z += dz
        return x, z

    def unstick(self, pos, direction, r):
        x, z = pos[0], pos[2]
        for _ in range(20):
            if not self.blocked(x, z, r):
                break
            x, z = x + direction[0] * 0.05, z + direction[2] * 0.05
        return x, z

    def _walk_line(self, a, b, test):
        dist = distance_xz(a, b)
        steps = max(1, int(dist / 0.2))
        for i in range(1, steps):
            t = i / steps
            if test(a[0] + (b[0] - a[0]) * t, a[2] + (b[2] - a[2]) * t):
                return False
        return True

    def line_of_sight(self, a, b):
        return self._walk_line(a, b, lambda x, z: self.cell_type(*self.cell_at(x, z)) in "#SE")

    def clear_path(self, a, b, r):
        return self._walk_line(a, b, lambda x, z: self.blocked(x, z, r))


class Pathfinder:
    def __init__(self, level):
        self.level = level
        self.target = None
        self.dist = {}

    def update(self, pos):
        cell = self.level.cell_at(pos[0], pos[2])
        if cell == self.target:
            return
        self.target = cell
        lv = self.level
        self.dist = {cell: 0}
        frontier = [cell]
        while frontier:
            nxt = []
            for c, r in frontier:
                for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (c + dc, r + dr)
                    if n not in self.dist and not lv.solid(lv.cell_type(*n)):
                        self.dist[n] = self.dist[(c, r)] + 1
                        nxt.append(n)
            frontier = nxt

    def next_step(self, pos):
        c, r = self.level.cell_at(pos[0], pos[2])
        here = self.dist.get((c, r))
        if here is None:
            return None
        best = None
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c + dc, r + dr)
            d = self.dist.get(n)
            if d is not None and d < here and (best is None or d < best[0]):
                best = (d, n)
        return self.level.cell_center(*best[1]) if best else None


class StoreBuilder:
    def __init__(self, level):
        self.level = level
        self.product_textures = cargar_productos()
        self.jar_texture = Texture(asset_path("environment", "OGASGJ2018_Logo_Draft3_jar.png"), filtering="mipmap")

    def build(self):
        lv = self.level
        walls, tiles, shelves, counters, boards = (MeshBuilder() for _ in range(5))
        products = {}

        for row in range(lv.rows):
            for col in range(lv.cols):
                ch = lv.grid[row][col]
                if ch == "#":
                    self._block(walls, col, row, WALL_HEIGHT, set("#FE"))
                elif ch == "F":
                    self._block(tiles, col, row, WALL_HEIGHT, set("#F"))
                elif ch == "S":
                    self._block(shelves, col, row, SHELF_HEIGHT, set("#FSE"))
                    for d_row, dz in ((-1, -1), (1, 1)):
                        if not lv.solid(lv.cell_type(col, row + d_row)):
                            self._stock_shelf(boards, products, col, row, dz)
                elif ch == "C":
                    self._block(counters, col, row, COUNTER_HEIGHT, set("#FSCE"))

        tex = {
            "wall": textura("wall"),
            "wall_tiles": textura("wall_tiles"),
            "metal_shelf": textura("metal_shelf"),
            "metal_door": textura("metal_door"),
            "floor": textura("floor"),
            "ceiling": textura("ceiling"),
        }

        walls.build(tex["wall"])
        tiles.build(tex["wall_tiles"])
        shelves.build(tex["metal_shelf"], tint=color.rgb32(120, 130, 145))
        boards.build(tex["metal_shelf"], collider=None)
        counters.build(tex["metal_door"], tint=color.rgb32(170, 175, 185))

        for product_tex, mb in products.items():
            mb.build(product_tex, collider=None)

        Entity(model="cube", position=(0, -0.1, 0), scale=(lv.cols, 0.2, lv.rows),
               texture=tex["floor"], texture_scale=(lv.cols / 2, lv.rows / 2), collider="box")
        Entity(model="plane", scale=(lv.cols, 1, lv.rows), y=WALL_HEIGHT, rotation_x=180,
               texture=tex["ceiling"], texture_scale=(lv.cols / 2, lv.rows / 2), color=color.rgb32(150, 150, 150))

        lights = self._lights(lv)
        self._signs(lv)
        doors = [Door(lv.cell_center(c, r), tex["metal_door"]) for c, r in lv.exit_cells]
        return doors, lights

    def _block(self, mb, col, row, height, joins):
        lv = self.level
        c = lv.cell_center(col, row)
        x0, x1 = c.x - 0.5, c.x + 0.5
        z0, z1 = c.z - 0.5, c.z + 0.5
        faces = (
            (lv.cell_type(col, row + 1), [(x1, 0, z1), (x0, 0, z1), (x0, height, z1), (x1, height, z1)], 0.95),
            (lv.cell_type(col, row - 1), [(x0, 0, z0), (x1, 0, z0), (x1, height, z0), (x0, height, z0)], 0.9),
            (lv.cell_type(col + 1, row), [(x1, 0, z0), (x1, 0, z1), (x1, height, z1), (x1, height, z0)], 0.75),
            (lv.cell_type(col - 1, row), [(x0, 0, z1), (x0, 0, z0), (x0, height, z0), (x0, height, z1)], 0.8),
        )
        for neighbor, corners, shade in faces:
            if neighbor not in joins:
                mb.quad(corners, shade, uv=(1, height))
        if height < WALL_HEIGHT:
            mb.quad([(x0, height, z0), (x1, height, z0), (x1, height, z1), (x0, height, z1)], 0.55)

    def _stock_shelf(self, boards, products, col, row, dz):
        lv = self.level
        c = lv.cell_center(col, row)
        face = c.z + dz * 0.5
        lip = face + dz * 0.2
        x0, x1 = c.x - 0.5, c.x + 0.5
        for y in SHELF_BOARDS:
            boards.quad([(x0, y, face), (x1, y, face), (x1, y, lip), (x0, y, lip)], 0.9, uv=(1, 0.2))
            boards.quad([(x0, y - 0.05, lip), (x1, y - 0.05, lip), (x1, y, lip), (x0, y, lip)], 0.7, uv=(1, 0.05))
            tex = self.jar_texture if random.random() < JAR_CHANCE else random.choice(self.product_textures)
            w, h = product_size(tex)
            z = face + dz * 0.1
            for i in range(3):
                px = x0 + (i + 0.5) / 3
                if random.random() < ENEMY_SLOT_CHANCE:
                    lv.shelf_slots.append({"pos": Vec3(px, y, z), "dir": Vec3(0, 0, dz),
                                           "aisle": lv.shelf_rows.index(row)})
                    continue
                products.setdefault(tex, MeshBuilder()).quad(
                    [(px - w / 2, y, z), (px + w / 2, y, z), (px + w / 2, y + h, z), (px - w / 2, y + h, z)])

    def _lights(self, lv):
        lights = []
        for row in range(1, lv.rows - 1, 4):
            for col in range(2, lv.cols - 2, 3):
                c = lv.cell_center(col, row)
                lights.append(Entity(model="quad", color=color.rgb32(235, 245, 255), position=(c.x, WALL_HEIGHT - 0.02, c.z),
                                     rotation_x=-90, scale=(1.6, 0.22), double_sided=True))
        return lights

    def _signs(self, lv):
        for aisle_index, row in enumerate(lv.shelf_rows):
            label = AISLES[aisle_index % len(AISLES)]
            cols = [c for c in range(lv.cols) if lv.grid[row][c] == "S"]
            runs, start = [], cols[0] if cols else None
            if start is not None:
                for a, b in zip(cols, cols[1:] + [None]):
                    if b != a + 1:
                        runs.append((start, a))
                        start = b
                for c0, c1 in runs:
                    mid = (lv.cell_center(c0, row) + lv.cell_center(c1, row)) / 2
                    for rot in (0, 180):
                        pos = Vec3(mid.x, 2.62, mid.z)
                        Entity(model="quad", color=color.rgb32(240, 240, 240), position=pos, scale=(2.7, 0.56), rotation_y=rot)
                        sign = Entity(model="quad", color=color.rgb32(190, 35, 30), position=pos, scale=(2.6, 0.48), rotation_y=rot)
                        sign.z += -0.005 if rot == 0 else 0.005
                        text = Text(text=f"PASILLO {label}", parent=scene, origin=(0, 0), scale=10, color=color.white,
                                    position=pos, rotation_y=rot)
                        text.z += -0.02 if rot == 0 else 0.02


MAPA_SUPERMERCADO = [
    "###E####################E#",
    "#S....C......C....S......#",
    "#S.......................#",
    "#S..SSSSSSSSSSSSS..S.....#",
    "#........................#",
    "#..C..............C......#",
    "#........................#",
    "#..SSSSSSSSSSSSSSS.......#",
    "#........................#",
    "#....C..............C....#",
    "#........................#",
    "#..SSSSSSSSSSSSSSS.......#",
    "#........................#",
    "#....C......C............#",
    "#........................#",
    "##########################",
]


def build_world():
    level = Level(MAPA_SUPERMERCADO,
                  exit_cells=[(c, r) for r, fila in enumerate(MAPA_SUPERMERCADO) for c, ch in enumerate(fila) if ch == "E"])
    doors, lights = StoreBuilder(level).build()
    return level, doors, lights
