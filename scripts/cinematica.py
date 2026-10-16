from ursina import *

FUENTE = "VeraMono.ttf"
PAUSA_LINEA = 1.4
ESPACIO_LINEA = 0.075
TECLAS_AVANZAR = ("left mouse down", "enter", "return", "keypad enter", "space")

INTRO = [
    "Tienes 9 anos. Tu mama te dejo un momento en SpookMart.",
    "\"Esperame aqui, ya vuelvo\". Te sentaste detras de los estantes...",
    "...y sin querer, te quedaste dormido.",
    "Cuando abriste los ojos todo estaba a oscuras. 23:50.",
    "Las puertas, cerradas. Nadie sabia que seguias adentro.",
    "Dicen que la comida que nadie compra... despierta a medianoche.",
    "Junto a la caja encontraste la pistola del guardia de seguridad.",
    "Las puertas se abren a las 06:00. Aguanta hasta entonces.",
]

EPILOGO = [
    "La luz del sol te pega en la cara.",
    "Tu mama corre hacia ti por el estacionamiento.",
    "Detras de ti, las puertas de SpookMart se cierran solas.",
    "Nunca mas vuelves a dormirte en el supermercado.",
]

COLOR_AMANECER = color.rgb32(255, 228, 190)
TAMANO_PIXEL_IMAGEN = 0.0045


class Cinematica(Entity):
    """Pantalla de texto que muestra frases una a una; clic o Enter para avanzar."""

    def __init__(self):
        super().__init__(parent=camera.ui, z=-3, enabled=False)
        self.fondo = Entity(parent=self, model="quad", scale=(3, 2), color=color.black)
        self.pista = Text(parent=self, text="Clic o Enter para continuar", origin=(0, 0), y=-0.4, z=-0.1,
                          scale=0.9, font=FUENTE)
        self.imagen = Entity(parent=self, model="quad", y=0.37, z=-0.1, enabled=False)
        self.lineas = []
        self.al_terminar = None

    def mostrar(self, lineas, al_terminar, fondo=color.black, color_texto=color.white, imagen=None):
        for linea in self.lineas:
            destroy(linea)
        self.imagen.enabled = imagen is not None
        if imagen is not None:
            self.imagen.texture = imagen
            self.imagen.scale = (imagen.width * TAMANO_PIXEL_IMAGEN, imagen.height * TAMANO_PIXEL_IMAGEN)
        centro = -0.05 if imagen is not None else 0.04
        alto = (len(lineas) - 1) * ESPACIO_LINEA
        self.lineas = [Text(parent=self, text=texto, origin=(0, 0), y=alto / 2 - i * ESPACIO_LINEA + centro,
                            z=-0.1, scale=1.1, font=FUENTE, color=color_texto, enabled=False)
                       for i, texto in enumerate(lineas)]
        self.fondo.color = fondo
        self.pista.color = color.rgba(color_texto.r, color_texto.g, color_texto.b, 0.5)
        self.pista.enabled = False
        self.al_terminar = al_terminar
        self.visibles = 0
        self.reloj = 0.5
        self.bloqueo = 0.3  # evita que el clic/Enter que abrio la escena la salte
        mouse.locked = False
        self.enabled = True

    def _revelar(self, cuantas):
        for linea in self.lineas[self.visibles:cuantas]:
            linea.enabled = True
            linea.alpha = 0
            linea.animate("alpha", 1, duration=0.6)
        self.visibles = cuantas
        self.pista.enabled = self.visibles >= len(self.lineas)

    def update(self):
        self.bloqueo -= time.dt
        if self.visibles >= len(self.lineas):
            return
        self.reloj -= time.dt
        if self.reloj <= 0:
            self.reloj = PAUSA_LINEA
            self._revelar(self.visibles + 1)

    def input(self, key):
        if key not in TECLAS_AVANZAR or self.bloqueo > 0:
            return
        if self.visibles < len(self.lineas):
            self._revelar(len(self.lineas))
            return
        self.enabled = False
        self.al_terminar()
