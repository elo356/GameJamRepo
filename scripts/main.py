#!/home/elo/Documents/GameJamRepo/.venv/bin/python

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ursina import *

from scripts.game import Game
from scripts.world import FOG_COLOR


def main():
    app = Ursina(title=" After Hours", size=(1280, 720))

    window.editor_ui.enabled = False
    window.color = FOG_COLOR

    scene.fog_color = FOG_COLOR

    Game()

    window.update_aspect_ratio()

    app.run()


if __name__ == "__main__":
    main()
