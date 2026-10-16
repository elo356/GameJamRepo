#!/usr/bin/env python3

import sys
from pathlib import Path
import asyncio

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ursina import *

from scripts.game import Game
from scripts.neblina import setup_rendering

class PauseHandler(Entity):
    def __init__(self, game, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.game = game
        self.pause_text = Text('PAUSED', origin=(0, -1), scale=3, enabled=False, color = color.red, font='VeraMono.ttf')
        self.instrucctions_text = Text("Press 'P' to unpause", origin = (0,2), scale =2, enabled = False, color=color.red, font = 'VeraMono.ttf')

    def set_paused(self, paused):
        application.paused = paused
        self.pause_text.enabled = paused
        self.instrucctions_text.enabled = paused
        mouse.locked = not paused

    def input(self, key):
        if key == "p":
            if application.paused:
                self.set_paused(False)
            elif self.game.state == "playing":
                self.set_paused(True)
        elif key == "escape" and application.paused:
            application.quit()


def main():
    app = Ursina(title=" After Hours", size=(1280, 720))

    window.editor_ui.enabled = False

    game = Game()
    PauseHandler(game)
    setup_rendering()

    window.update_aspect_ratio()

    app.run()


if __name__ == "__main__":
    main()
