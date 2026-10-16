import math
import random

from PIL import Image
from ursina import *

from scripts.neblina import fogify, sprite
from scripts.supermercado import ROOT
from scripts.world import PRODUCT_PIXEL, distance_xz

SLEEP_COLOR = color.rgb(0.78, 0.78, 0.86)
HURT_COLOR = color.rgb(1, 0.35, 0.35)
PLAYER_RADIUS = 0.3

BASE_STATS = {"size": 0.5, "hp": 3, "speed": 2.2, "damage": 10, "ranged": False, "zigzag": False,
              "knockback": 0.15, "big": False, "fly": 0.0, "frames": 1, "weight": 1,
              "voice": "growl", "pitch": 1.0}
ENEMY_TYPES = {
    "Apple_Two": {"size": 0.55, "hp": 3, "speed": 2.6, "damage": 10, "frames": 2, "weight": 3,
                  "voice": "wobble", "pitch": 1.1},
    "Jalapeño": {"size": 0.45, "hp": 2, "speed": 1.8, "damage": 8, "ranged": True, "weight": 2,
                 "voice": "snort", "pitch": 1.3},
    "Pineapple": {"size": 0.6, "hp": 4, "speed": 2.0, "damage": 12, "fly": 0.3, "zigzag": True, "weight": 2,
                  "voice": "critter", "pitch": 1.0},
    "Pretzel_Bat": {"size": 0.5, "hp": 2, "speed": 3.2, "damage": 6, "fly": 1.1, "zigzag": True, "weight": 2,
                    "voice": "raven", "pitch": 1.2},
    "Waffles": {"size": 0.5, "hp": 3, "speed": 2.4, "damage": 10, "weight": 3, "voice": "wobble", "pitch": 0.8},
    "Watermelon_monster": {"size": 0.75, "hp": 8, "speed": 1.4, "damage": 25, "knockback": 0.6, "big": True,
                           "weight": 1, "voice": "snort", "pitch": 0.6},
}


def enemy_stats(kind):
    return {**BASE_STATS, **ENEMY_TYPES.get(kind, {})}


def load_enemy_assets():
    textures, colors = {}, {}
    for f in sorted((ROOT / "images" / "characters").glob("*.png")):
        textures[f.stem] = Texture(str(f), filtering=None)
        pixels = [p for p in Image.open(f).convert("RGBA").getdata() if p[3] > 128]
        r, g, b = (sum(p[i] for p in pixels) / len(pixels) / 255 for i in range(3))
        colors[f.stem] = (min(1, r * 1.2), min(1, g * 1.2), min(1, b * 1.2))
    return textures, colors


class Enemy:
    def __init__(self, game, kind, slot):
        self.game = game
        self.kind = kind
        self.stats = enemy_stats(kind)
        self.size = self.stats["size"]
        self.hp = self.stats["hp"]
        self.tint = game.enemy_colors[kind]
        self.slot = slot
        self.state = "dormant"
        self.vel = Vec3(0, 0, 0)
        self.timer = 0.0
        self.attack_cd = random.uniform(0.3, 1.0)
        self.flash = 0.0
        self.phase = random.uniform(0, 10)
        self.frame_timer = 0.0
        self.frame = 0
        self.los = False
        self.direct = False
        self.los_timer = random.uniform(0, 0.2)

        tex = game.enemy_textures[kind]
        frames = self.stats["frames"]
        self.aspect = tex.width / (tex.height / frames)
        sleep_h = tex.height / frames * PRODUCT_PIXEL
        self.e = sprite(tex, color=SLEEP_COLOR,
                        texture_scale=(1, 1 / frames), texture_offset=(0, 1 - 1 / frames),
                        scale=(sleep_h * self.aspect, sleep_h),
                        position=slot["pos"] + Vec3(0, sleep_h / 2, 0))

    @property
    def alive(self):
        return self.state != "dead"

    @property
    def awake(self):
        return self.state in ("falling", "stunned", "chase")

    @property
    def radius(self):
        return 0.08 if self.state in ("dormant", "falling") else self.size * 0.4

    @property
    def ground_y(self):
        return self.size / 2 + self.stats["fly"]

    @property
    def position(self):
        return self.e.position

    def awaken(self):
        if self.state != "dormant":
            return
        self.state = "falling"
        self.e.color = color.white
        self.e.scale = (self.size * self.aspect, self.size)
        self.vel = self.slot["dir"] * random.uniform(1.4, 2.0) + Vec3(random.uniform(-0.4, 0.4), 1.6, 0)
        self.cry(0.5)

    def cry(self, volume, pitch_var=0.1):
        self.game.sfx.play(self.stats["voice"], volume, pitch_var, pitch=self.stats["pitch"])

    def hurt(self, dmg, push_dir=None):
        if not self.alive:
            return False
        if self.state == "dormant":
            self.awaken()
        self.hp -= dmg
        self.flash = 0.1
        self.game.fx.burst(self.e.world_position, self.tint, count=4, speed=2.0, size=0.06, life=0.5)
        if push_dir is not None and self.state == "chase":
            self.e.x, self.e.z = self.game.level.slide_move(self.e.position, push_dir.x * 0.35, push_dir.z * 0.35, self.radius)
        if self.hp <= 0:
            self.die()
            return True
        self.game.sfx.play("hit", 0.6)
        return False

    def die(self):
        self.state = "dead"
        pos = self.e.world_position
        self.game.fx.burst(pos, self.tint, count=16, speed=3.5, size=0.09, life=1.0)
        self.game.fx.splat(pos, self.tint, size=self.size * 1.3)
        self.game.sfx.play("splat", 0.8, 0.2)
        destroy(self.e)

    def remove(self):
        if self.alive:
            destroy(self.e)
        self.state = "dead"

    def update(self, dt):
        if self.flash > 0:
            self.flash -= dt
            self.e.color = HURT_COLOR if self.flash > 0 else color.white
        if self.state == "falling":
            self._fall(dt)
        elif self.state == "stunned":
            self._stunned(dt)
        elif self.state == "chase":
            self._chase(dt)
        self._animate(dt)

    def _animate(self, dt):
        frames = self.stats["frames"]
        if frames < 2 or not self.awake:
            return
        self.frame_timer += dt
        if self.frame_timer >= 0.18:
            self.frame_timer = 0
            self.frame = (self.frame + 1) % frames
            self.e.texture_offset = (0, 1 - (self.frame + 1) / frames)

    def _fall(self, dt):
        self.vel.y -= 14 * dt
        self.e.x, self.e.z = self.game.level.slide_move(self.e.position, self.vel.x * dt, self.vel.z * dt, self.radius)
        self.e.y += self.vel.y * dt
        if self.e.y <= self.ground_y and self.vel.y < 0:
            self.e.y = self.ground_y
            self.state = "stunned"
            self.timer = 0.45
            self.e.x, self.e.z = self.game.level.unstick(self.e.position, self.slot["dir"], self.size * 0.4)
            self.e.scale_y = self.size * 0.6
            self.game.fx.burst(Vec3(self.e.x, 0.05, self.e.z), (0.6, 0.6, 0.6), count=5, speed=1.5, size=0.05, life=0.4)
            if distance_xz(self.e.position, self.game.player_pos) < 12:
                self.game.sfx.play("thump", 0.6, 0.2)

    def _stunned(self, dt):
        self.timer -= dt
        self.e.scale_y = lerp(self.e.scale_y, self.size, dt * 10)
        if self.timer <= 0:
            self.state = "chase"
            self.e.scale_y = self.size

    def _chase(self, dt):
        game, level, player_pos = self.game, self.game.level, self.game.player_pos
        to_player = Vec3(player_pos.x - self.e.x, 0, player_pos.z - self.e.z)
        dist = to_player.length()

        self.los_timer -= dt
        if self.los_timer <= 0:
            self.los_timer = 0.2
            self.los = level.line_of_sight(self.e.position, player_pos)
            self.direct = self.los and level.clear_path(self.e.position, player_pos, self.radius + 0.05)

        target = player_pos if self.direct else (game.pathfinder.next_step(self.e.position) or player_pos)
        move = Vec3(target.x - self.e.x, 0, target.z - self.e.z)
        if move.length() > 0.001:
            move = move.normalized()

        reach = self.size * 0.45 + PLAYER_RADIUS + 0.25
        speed = self.stats["speed"]
        if self.stats["zigzag"] and self.direct and dist > 1.5:
            side = Vec3(-move.z, 0, move.x)
            move = (move + side * math.sin(time.time() * 6 + self.phase) * 0.8).normalized()
        if self.stats["ranged"] and self.los and dist < 5.5:
            move = move * -0.4 if dist < 3.5 else Vec3(0, 0, 0)
        if dist > reach:
            self.e.x, self.e.z = level.slide_move(self.e.position, move.x * speed * dt, move.z * speed * dt, self.radius)

        self.phase += dt * speed * 4
        if self.stats["fly"]:
            self.e.y = self.ground_y + math.sin(self.phase * 0.5) * 0.12
        else:
            bounce = abs(math.sin(self.phase))
            self.e.y = self.ground_y + bounce * 0.06
            self.e.scale_y = self.size * (0.94 + 0.08 * bounce)

        self.attack_cd -= dt
        if self.attack_cd <= 0:
            if dist <= reach + 0.1:
                self.attack_cd = 1.2
                game.damage_player(self.stats["damage"], to_player.normalized() if dist > 0 else None,
                                   knockback=self.stats["knockback"])
                self.e.scale_x = self.size * self.aspect * 1.25
                self.cry(0.35, 0.15)
            elif self.stats["ranged"] and self.los and dist < 11:
                self.attack_cd = random.uniform(1.8, 2.6)
                game.projectiles.throw(self)
        self.e.scale_x = lerp(self.e.scale_x, self.size * self.aspect, dt * 8)


class EnemyManager:
    def __init__(self, game):
        self.game = game
        self.enemies = []
        self.kinds = list(game.enemy_textures)
        self.weights = [enemy_stats(k)["weight"] for k in self.kinds]

    def __iter__(self):
        return iter(self.enemies)

    def spawn(self, slot):
        kind = random.choices(self.kinds, weights=self.weights)[0]
        self.enemies.append(Enemy(self.game, kind, slot))

    def clear(self):
        for f in self.enemies:
            f.remove()
        self.enemies = []

    def dormant(self):
        return [f for f in self.enemies if f.state == "dormant"]

    def active_count(self):
        return sum(1 for f in self.enemies if f.awake)

    def update(self, dt):
        for f in self.enemies:
            if f.alive:
                f.update(dt)
        self._separate()
        self.enemies = [f for f in self.enemies if f.alive]

    def push_away_from(self, pos, radius):
        level = self.game.level
        for f in self.enemies:
            if f.state in ("chase", "stunned"):
                d = distance_xz(f.e.position, pos)
                min_d = f.radius + radius
                if 0.001 < d < min_d:
                    push = Vec3(f.e.x - pos.x, 0, f.e.z - pos.z).normalized() * (min_d - d)
                    f.e.x, f.e.z = level.slide_move(f.e.position, push.x, push.z, f.radius)

    def _separate(self):
        level = self.game.level
        awake = [f for f in self.enemies if f.state in ("chase", "stunned")]
        for i, a in enumerate(awake):
            for b in awake[i + 1:]:
                dx, dz = b.e.x - a.e.x, b.e.z - a.e.z
                d = math.hypot(dx, dz)
                min_d = a.radius + b.radius
                if 0.0001 < d < min_d:
                    push = (min_d - d) / 2
                    nx, nz = dx / d * push, dz / d * push
                    a.e.x, a.e.z = level.slide_move(a.e.position, -nx, -nz, a.radius)
                    b.e.x, b.e.z = level.slide_move(b.e.position, nx, nz, b.radius)


class Projectiles(Entity):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.items = []

    def throw(self, enemy):
        start = enemy.e.position + Vec3(0, enemy.size * 0.2, 0)
        target = self.game.player_pos + Vec3(0, 1.1, 0)
        direction = (target - start).normalized()
        e = fogify(Entity(model="sphere", color=color.rgb(*enemy.tint), position=start, scale=0.14))
        self.items.append([e, direction * 7, enemy.stats["damage"], enemy.tint])
        enemy.cry(0.3, 0.2)

    def clear(self):
        for e, *_ in self.items:
            destroy(e)
        self.items = []

    def update(self):
        dt = time.dt
        game, level = self.game, self.game.level
        keep = []
        for item in self.items:
            e, vel, dmg, tint = item
            vel.y -= 1.5 * dt
            e.position += vel * dt
            if distance_xz(e.position, game.player_pos) < PLAYER_RADIUS + 0.15 and 0 < e.y < 1.9:
                game.damage_player(dmg, Vec3(vel.x, 0, vel.z).normalized(), knockback=0.1)
                game.fx.burst(e.position, tint, count=8, speed=2, size=0.06, life=0.5)
                destroy(e)
                continue
            if e.y <= 0.05 or level.blocked(e.x, e.z, 0.05):
                game.fx.burst(e.position, tint, count=8, speed=2, size=0.06, life=0.5)
                game.fx.splat(e.position, tint, size=0.4)
                game.sfx.play("splat", 0.35, 0.3)
                destroy(e)
                continue
            keep.append(item)
        self.items = keep
