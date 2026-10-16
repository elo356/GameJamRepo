import random
from pathlib import Path

from ursina import *

from scripts.effects import Effects
from scripts.enemy import PLAYER_RADIUS, EnemyManager, Projectiles, load_enemy_assets
from scripts.night import NightDirector
from scripts.player import Player
from scripts.supermercado import INICIO_JUGADOR, asset_path
from scripts.world import Pathfinder, build_world

ROTACION_INICIAL = 180
ALCANCE_DISPARO = 30


class Sfx:
    def __init__(self, names):
        self.clips = {name: Path(asset_path("audio", f"{name}.wav")) for name in names}

    def play(self, name, volume=1.0, pitch_var=0.0):
        Audio(self.clips[name], volume=volume, pitch=1 + random.uniform(-pitch_var, pitch_var), auto_destroy=True)


class PauseHandler(Entity):
    def __init__(self, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.pause_text = Text('PAUSED', origin=(0, -1), scale=3, enabled=False, color = color.red, font='VeraMono.ttf')
        self.instrucctions_text = Text("Press 'P' to unpause", origin = (0,2), scale =2, enabled = False, color=color.red, font = 'VeraMono.ttf')
        
def input(self, key):
    if key == "p" or key == "P":
        application.paused = not application.paused
        self.pause_text.enabled = application.paused
        self.instrucctions_text.enabled = application.paused
        self.state = "playing" if not application.paused else "paused"
    elif key == "escape":
        if application.paused:
            application.quit()
    else:
        application.paused = True
        self.pause_text.enabled = True
        self.instrucctions_text.enabled = True


class Game(Entity):
    def __init__(self):
        super().__init__()
        self.level, self.doors, self.lights = build_world()
        self.enemy_textures, self.enemy_colors = load_enemy_assets()
        self.sfx = Sfx(["buzz", "growl", "growl_big", "hit", "splat", "thump", "hurt"])
        self.fx = Effects()
        self.pathfinder = Pathfinder(self.level)
        self.enemies = EnemyManager(self)
        self.projectiles = Projectiles(self)
        self.player = Player(al_disparar=self.shoot, nivel=self.level, position=INICIO_JUGADOR, rotation_y=ROTACION_INICIAL)
        self.night = NightDirector(self)
        self.state = "playing"
        self.kills = 0
        self.spawn_all()

    @property
    def player_pos(self):
        return self.player.pos

    def spawn_all(self):
        for slot in self.level.shelf_slots:
            self.enemies.spawn(slot)

    def shoot(self, origin, direction):
        hit = raycast(origin, direction, distance=ALCANCE_DISPARO, ignore=[self.player.controller, self.player])
        max_d = hit.distance if hit.hit else ALCANCE_DISPARO
        best = None
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            to = enemy.e.world_position - origin
            t = to.dot(direction)
            if t <= 0 or t >= max_d:
                continue
            closest = origin + direction * t
            r = max(enemy.e.scale_x, enemy.e.scale_y) * 0.5
            if (enemy.e.world_position - closest).length() < r and (best is None or t < best[0]):
                best = (t, enemy)
        if best is None:
            return max_d
        t, enemy = best
        if enemy.hurt(1, Vec3(direction.x, 0, direction.z).normalized()):
            self.kills += 1
        return t

    def damage_player(self, dmg, direction=None, knockback=0.0):
        if self.state != "playing":
            return
        self.player.recibir_dano(dmg, direction, knockback, self.level)
        self.sfx.play("hurt", 0.7, 0.15)
        if not self.player.vivo:
            self.end("TE COMIERON", color.rgb32(255, 70, 60))

    def end(self, titulo, col):
        self.state = "over"
        self.night.enabled = False
        self.projectiles.enabled = False
        self.player.congelar(True)
        self.night.hud.show_message(titulo, f"Eliminaste {self.kills} enemigos  -  Pulsa R para reintentar", 99999, col)

    def restart(self):
        self.enemies.clear()
        self.projectiles.clear()
        self.fx.clear()
        for door in self.doors:
            door.close()
        self.kills = 0
        self.spawn_all()
        self.player.reiniciar(INICIO_JUGADOR, ROTACION_INICIAL)
        self.night.reset()
        self.night.enabled = True
        self.projectiles.enabled = True
        self.state = "playing"

    def input(self, key):
        if key == "r" and self.state == "over":
            self.restart()

    def update(self):
        dt = time.dt
        self.fx.update(dt)
        if self.state != "playing":
            return
        self.level.exits_open = self.night.doors_open
        pos = self.player_pos
        self.pathfinder.update(pos)
        self.enemies.update(dt)
        self.enemies.push_away_from(pos, PLAYER_RADIUS)
        if self.night.doors_open and pos.z < self.level.cell_center(0, 0).z - 0.1:
            self.end("¡SOBREVIVISTE!", color.rgb32(90, 255, 120))
