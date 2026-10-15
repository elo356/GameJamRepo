from ursina import *

class Menu(Entity):
    def __init__(self, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True)

        self.main_menu = Entity(parent=self, enabled=True)

        self.background = Sprite('shore', color=color.black, z=1)


        self.title = Text('After Hours', parent=camera.ui, origin=(0, 0), color=color.white, scale=2, y=0.3)

        self.start_button = Button(text='Start Game', parent=camera.ui, origin=(0, 0), color=color.white, scale=0.1, y=0)

        self.quit_button = Button(text='Quit', parent=camera.ui, origin=(0, 0), color=color.white, scale=0.1, y=-0.2)

        self.controls_text = Text('Controls:\nWASD to move\nMouse to look around\nLeft Click to shoot\nP to pause/unpause\nEsc to quit', parent=camera.ui, origin=(0, 0), color=color.white, scale=0.05, y=-0.5)

        self.start_button.on_click = self.start_game
        self.quit_button.on_click = application.quit

        ButtonList(button_dict={
            "Start": Func(print_on_screen,"You clicked on Start button!", position=(0,.1), origin=(0,0)),
            "Exit": Func(lambda: application.quit())
        },y=0,parent=self.main_menu)

    def start_game(self):
        self.disable()
        application.paused = False

    def update(self):
        pass