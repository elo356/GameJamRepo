import math
import random

from PIL import Image, ImageDraw
from ursina import Entity, Texture, Vec3, color, destroy

MAX_PARTICLES = 160
MAX_DECALS = 60
SPLAT_VARIANTS = 4


def make_splats():
    textures = []
    for _ in range(SPLAT_VARIANTS):
        img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((9, 9, 23, 23), fill=(255, 255, 255, 255))
        for _ in range(random.randint(5, 9)):
            ang = random.uniform(0, math.tau)
            dist = random.uniform(5, 13)
            r = random.uniform(1.5, 4)
            cx, cy = 16 + math.cos(ang) * dist, 16 + math.sin(ang) * dist
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 255))
        textures.append(Texture(img, filtering=None))
    return textures


class Effects:
    def __init__(self):
        self.splats = make_splats()
        self.particles = []
        self.decals = []

    def burst(self, pos, rgb, count=10, speed=3.0, size=0.08, life=0.8):
        for _ in range(count):
            if len(self.particles) >= MAX_PARTICLES:
                destroy(self.particles.pop(0)["e"])
            shade = random.uniform(0.75, 1.1)
            e = Entity(model="quad", position=pos, scale=size * random.uniform(0.7, 1.3), billboard=True,
                       color=color.rgb(*(min(1, c * shade) for c in rgb)))
            v = Vec3(random.uniform(-1, 1), random.uniform(0.3, 1.4), random.uniform(-1, 1)) * speed
            self.particles.append(dict(e=e, v=v, life=life * random.uniform(0.6, 1.2)))

    def splat(self, pos, rgb, size=0.9):
        if len(self.decals) >= MAX_DECALS:
            destroy(self.decals.pop(0))
        e = Entity(model="plane", texture=random.choice(self.splats),
                   position=(pos.x, 0.01 + len(self.decals) * 0.0004, pos.z),
                   scale=size * random.uniform(0.8, 1.3), rotation_y=random.choice((0, 90, 180, 270)),
                   color=color.rgb(*(c * 0.8 for c in rgb)))
        self.decals.append(e)

    def update(self, dt):
        for p in self.particles[:]:
            p["life"] -= dt
            if p["life"] <= 0:
                destroy(p["e"])
                self.particles.remove(p)
                continue
            p["v"].y -= 9.8 * dt
            e = p["e"]
            e.position += p["v"] * dt
            if e.y < 0.03:
                e.y = 0.03
                p["v"] = Vec3(p["v"].x * 0.5, 0, p["v"].z * 0.5)

    def clear(self):
        for p in self.particles:
            destroy(p["e"])
        for d in self.decals:
            destroy(d)
        self.particles.clear()
        self.decals.clear()
