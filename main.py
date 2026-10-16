import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ursina import *

from scripts.supermercado import INICIO_JUGADOR
from scripts.player import Player
from scripts.world import FOG_COLOR, build_world

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



def main():
    app = Ursina(title=" After Hours", size=(1280, 720))

    window.editor_ui.enabled = False
    window.color = FOG_COLOR

    build_world()

    scene.fog_color = FOG_COLOR
    scene.fog_density = (6, 26)

    player = Player(position=INICIO_JUGADOR, rotation_y=180)

    pause_handler = PauseHandler()

    window.update_aspect_ratio()

    # def start_game():
    #     print("Starting game...")
    #     main_menu.enabled = False

    # main_menu = ButtonList({
    # "Start Game": Func(start_game),
    # "Options": Func(print, "Options opened"),
    # "Quit": Func(application.quit)
    # }, width=0.5, button_height=1.5)

    app.run()


if __name__ == "__main__":
    main()
