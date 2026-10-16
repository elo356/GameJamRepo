#!/home/elo/Documents/GameJamRepo/.venv/bin/python

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ursina import *

from scripts.supermercado import INICIO_JUGADOR
from scripts.night import NightDirector
from scripts.player import Player
from scripts.world import FOG_COLOR, build_world


def main():
    app = Ursina(title=" After Hours", size=(1280, 720))

    window.editor_ui.enabled = False
    window.color = FOG_COLOR

    doors, lights = build_world()

    scene.fog_color = FOG_COLOR

    player = Player(position=INICIO_JUGADOR, rotation_y=180)
    night = NightDirector(doors, lights)

    window.update_aspect_ratio()

    app.run()


if __name__ == "__main__":
    main()
