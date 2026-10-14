from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

from supermercado import INICIO_JUGADOR, asset_path, construir_supermercado
from bullets import Bullet


class Player(Entity):
    def __init__(self, **kwargs):
        self.controller = FirstPersonController(**kwargs)
        super().__init__(parent=self.controller)

        self.frames_pistola = [Texture(asset_path("weapons", f"pist_{i}.png"), filtering=None)
                               for i in range(4)]
        self.disparando = False

        self.gun = Entity(parent=camera.ui,
                          model="quad",
                          texture=self.frames_pistola[0],
                          scale=(0.68, 0.6),
                          position=(0.1, -0.2),
                          )

    def input(self, key):
        if key == "left mouse down":
            self.disparar()
            bullet = Bullet(position=self.controller.position + self.controller.forward + Vec3(0, 1, 0),
                            direction=camera.forward + Vec3(0, 0.1, 0),
                            speed=20)


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


def main():
    app = Ursina(title=" After Hours", size=(1280, 720))

    construir_supermercado()

    caja = Entity(model="cube", color=color.red, position=(0, 0.5, 5), collider="box")

    player = Player(position=INICIO_JUGADOR)

    window.update_aspect_ratio()
  
    app.run()


if __name__ == "__main__":
    main()
