from ursina import *

FONDO = color.rgba(0, 0, 0, 0.85)
COLOR_BOTON = color.rgb32(40, 40, 46)
COLOR_BOTON_HOVER = color.rgb32(150, 35, 35)
FUENTE = "VeraMono.ttf"


class Menu(Entity):
    def __init__(self, titulo, botones, subtitulo="", col=color.white):
        super().__init__(parent=camera.ui, z=-2, enabled=False)
        Entity(parent=self, model="quad", scale=(3, 2), color=FONDO)
        self.titulo = Text(parent=self, text=titulo, origin=(0, 0), scale=3, y=0.25, z=-0.1,
                           color=col, font=FUENTE)
        self.subtitulo = Text(parent=self, text=subtitulo, origin=(0, 0), scale=1.2, y=0.15, z=-0.1,
                              color=color.light_gray, font=FUENTE)
        for i, (texto, accion) in enumerate(botones):
            Button(parent=self, text=texto, on_click=accion, scale=(0.36, 0.075), y=-0.02 - i * 0.1, z=-0.1,
                   color=COLOR_BOTON, highlight_color=COLOR_BOTON_HOVER, pressed_color=COLOR_BOTON_HOVER)

    def show(self, titulo=None, subtitulo=None, col=None):
        if titulo is not None:
            self.titulo.text = titulo
        if subtitulo is not None:
            self.subtitulo.text = subtitulo
        if col is not None:
            self.titulo.color = col
        mouse.locked = False
        self.enabled = True

    def hide(self):
        self.enabled = False


class MainMenu(Menu):
    def __init__(self, al_jugar):
        super().__init__("AFTER HOURS", [
            ("Jugar", al_jugar),
            ("Salir", application.quit),
        ], subtitulo="Sobrevive la noche en el supermercado", col=color.rgb32(255, 90, 70))
        self.al_jugar = al_jugar

    def input(self, key):
        if key == "escape":
            application.quit()
        elif key in ("enter", "return", "keypad enter"):
            self.al_jugar()

class GameOverMenu(Menu):
    def __init__(self, al_reintentar, al_menu):
        super().__init__("", [
            ("Reintentar", al_reintentar),
            ("Menu principal", al_menu),
            ("Salir", application.quit),
        ])
