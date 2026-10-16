from ursina import *

FONDO = color.rgba(0, 0, 0, 0.85)
COLOR_BOTON = color.rgb32(40, 40, 46)
COLOR_BOTON_HOVER = color.rgb32(150, 35, 35)
FUENTE = "VeraMono.ttf"
COLOR_ACENTO = color.rgb32(255, 90, 70)

CONTROLES = [
    [(["W", "A", "S", "D"], "Moverse"), (["Raton"], "Apuntar"), (["Clic"], "Disparar"), (["Espacio"], "Saltar")],
    [(["1", "2"], "Cambiar arma"), (["3", "4", "5"], "Curarte"), (["P"], "Pausa"), (["R"], "Reintentar")],
]
PANEL_Y, PANEL_ANCHO, PANEL_ALTO = -0.335, 0.92, 0.28
FILA_Y0, FILA_PASO = -0.27, 0.048
COLUMNAS_X = (-0.41, 0.03)
ACCION_DX = (0.215, 0.165)  # separacion entre teclas y accion en cada columna
TECLA_ALTO, TECLA_HUECO = 0.036, 0.006


def dibujar_tecla(padre, texto, x, y):
    """Dibuja una tecla de teclado con su sombra; devuelve su ancho."""
    ancho = max(0.045, 0.014 * len(texto) + 0.022)
    Entity(parent=padre, model="quad", origin=(-0.5, 0), position=(x, y - 0.005), z=-0.1,
           scale=(ancho, TECLA_ALTO), color=color.rgb32(15, 15, 18))
    Entity(parent=padre, model="quad", origin=(-0.5, 0), position=(x, y), z=-0.11,
           scale=(ancho, TECLA_ALTO), color=color.rgb32(150, 150, 162))
    Entity(parent=padre, model="quad", origin=(-0.5, 0), position=(x + 0.003, y + 0.001), z=-0.12,
           scale=(ancho - 0.006, TECLA_ALTO - 0.007), color=color.rgb32(50, 50, 60))
    Text(parent=padre, text=texto, origin=(0, 0), position=(x + ancho / 2, y + 0.001), z=-0.13,
         scale=0.8, font=FUENTE, color=color.white)
    return ancho


def dibujar_controles(padre):
    Entity(parent=padre, model="quad", y=PANEL_Y, z=-0.05, scale=(PANEL_ANCHO + 0.006, PANEL_ALTO + 0.006),
           color=color.rgb32(70, 22, 22))
    Entity(parent=padre, model="quad", y=PANEL_Y, z=-0.06, scale=(PANEL_ANCHO, PANEL_ALTO),
           color=color.rgba(0.07, 0.07, 0.09, 0.95))
    Entity(parent=padre, model="quad", y=PANEL_Y + PANEL_ALTO / 2 - 0.002, z=-0.07,
           scale=(PANEL_ANCHO, 0.004), color=COLOR_ACENTO)
    Text(parent=padre, text="CONTROLES", origin=(0, 0), y=PANEL_Y + PANEL_ALTO / 2 - 0.033, z=-0.1,
         scale=1.0, color=COLOR_ACENTO, font=FUENTE)
    for x0, dx, filas in zip(COLUMNAS_X, ACCION_DX, CONTROLES):
        for i, (teclas, accion) in enumerate(filas):
            y = FILA_Y0 - i * FILA_PASO
            x = x0
            for tecla in teclas:
                x += dibujar_tecla(padre, tecla, x, y) + TECLA_HUECO
            Text(parent=padre, text=accion, origin=(-0.5, 0), position=(x0 + dx, y), z=-0.1,
                 scale=0.9, font=FUENTE, color=color.light_gray)


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
        super().__init__("SpookMart", [
            ("Jugar", al_jugar),
            ("Salir", application.quit),
        ], subtitulo="Sobrevive la noche en el supermercado", col=COLOR_ACENTO)
        self.al_jugar = al_jugar
        dibujar_controles(self)

    def input(self, key):
        if key == "escape":
            application.quit()
        elif key in ("enter", "return", "keypad enter"):
            self.al_jugar()

class GameOverMenu(Menu):
    def __init__(self, al_reintentar, al_menu):
        super().__init__("", [
            ("Reintentar", al_reintentar),
            ("Salir", application.quit),
        ]) 
