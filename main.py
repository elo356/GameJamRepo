from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

from supermercado import INICIO_JUGADOR, asset_path, construir_supermercado
from bullets import Bullet
# from menu import Menu


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
        elif key == "escape":
            if application.paused:
                application.quit()
            else:
                application.paused = True
                self.pause_text.enabled = True
                self.instrucctions_text.enabled = True

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
            sound = Audio( "shot_sound.wav", autoplay=False, loop=False, volume=0.5)
            sound.play()

            
      
        elif key == "escape":
            application.quit()
        # elif Menu.enabled and (key == "Enter" or key == "return"):
        #     Menu.start_game()


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
    app = Ursina(title=" After Hours", size=(1280, 720), origin=(0, 0))

   

    construir_supermercado()

    caja = Entity(model="cube", color=color.red, position=(0, 0.5, 5), collider="box")

    player = Player(position=INICIO_JUGADOR)

    window.update_aspect_ratio()

    pause_handler = PauseHandler()

    # menu = Menu()
  
    app.run()


if __name__ == "__main__":
    main()
