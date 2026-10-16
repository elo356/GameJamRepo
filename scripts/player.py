from pathlib import Path

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

from scripts.supermercado import asset_path
from scripts.bullets import Bullet

ALTURA_OJOS = 1.65
POSICION_ARMA = Vec2(0.32, -0.3)


class Player(Entity):
    def __init__(self, **kwargs):
        self.controller = FirstPersonController(height=ALTURA_OJOS, **kwargs)
        self.controller.cursor.color = color.white
        self.controller.cursor.scale = 0.006
        super().__init__(parent=self.controller)

        self.frames_pistola = [Texture(asset_path("weapons", f"pist_{i}.png"), filtering=None)
                               for i in range(4)]
        self.disparando = False
        self.balanceo = 0

        self.gun = Entity(parent=camera.ui,
                          model="quad",
                          texture=self.frames_pistola[0],
                          scale=(0.6, 0.6 * 150 / 170),
                          position=POSICION_ARMA,
                          )
        self.sonido_disparo = Audio(Path(asset_path("audio", "shot_sound.wav")), autoplay=False, loop=False, volume=0.5)

    def update(self):
        moviendo = self.controller.grounded and (held_keys["w"] or held_keys["a"] or held_keys["s"] or held_keys["d"])
        if moviendo:
            self.balanceo += time.dt * 9
        objetivo = POSICION_ARMA + Vec2(math.sin(self.balanceo) * 0.012, -abs(math.cos(self.balanceo)) * 0.015 * moviendo)
        self.gun.position = lerp(self.gun.position, Vec3(objetivo.x, objetivo.y, 0), min(time.dt * 12, 1))

    def input(self, key):
        if key == "left mouse down":
            self.disparar()
            Bullet(position=camera.world_position + camera.forward * 0.5,
                   direction=camera.forward,
                   speed=20)
            self.sonido_disparo.play()

        elif key == "escape":
            application.quit()

    def disparar(self):
        if self.disparando:
            return
        self.disparando = True

        self.gun.texture = self.frames_pistola[1]
        invoke(setattr, self.gun, "texture", self.frames_pistola[2], delay=0.08)
        invoke(setattr, self.gun, "texture", self.frames_pistola[3], delay=0.16)
        invoke(self.terminar_disparo, delay=0.24)

    def terminar_disparo(self):
        self.gun.texture = self.frames_pistola[0]
        self.disparando = False
