from ursina import *

FUENTE = "VeraMono.ttf"
CASILLAS = 5
LADO = 0.085
SEPARACION = 0.008
Y_BARRA = -0.44
ICONO = 0.75  # fraccion de la casilla que ocupa el icono

COLOR_MARCO = color.rgba(0.45, 0.45, 0.5, 0.9)
COLOR_MARCO_ACTIVO = color.rgba(1, 1, 1, 1)
COLOR_FONDO = color.rgba(0.06, 0.06, 0.08, 0.75)
COLOR_RECHAZO = color.rgb32(230, 50, 50)
COLOR_SILUETA = color.rgba(0, 0, 0, 0.6)


class Casilla:
    def __init__(self, padre, numero, x):
        self.marco = Entity(parent=padre, model="quad", position=(x, Y_BARRA), scale=LADO + 0.008, color=COLOR_MARCO)
        Entity(parent=padre, model="quad", position=(x, Y_BARRA), z=-0.01, scale=LADO, color=COLOR_FONDO)
        self.icono = Entity(parent=padre, model="quad", position=(x, Y_BARRA), z=-0.02, enabled=False)
        Text(parent=padre, text=str(numero), origin=(-0.5, 0.5), scale=0.7, z=-0.03, font=FUENTE,
             position=(x - LADO / 2 + 0.005, Y_BARRA + LADO / 2 - 0.004), color=color.rgba(1, 1, 1, 0.55))
        self.cantidad = Text(parent=padre, text="", origin=(0.5, -0.5), scale=0.8, z=-0.03, font=FUENTE,
                             position=(x + LADO / 2 - 0.004, Y_BARRA - LADO / 2 + 0.004))
        self.interrogacion = Text(parent=padre, text="?", origin=(0, 0), scale=1.6, z=-0.03, font=FUENTE,
                                  position=(x, Y_BARRA), color=color.rgba(1, 1, 1, 0.8), enabled=False)

    def mostrar(self, textura=None, cantidad="", modo="normal"):
        """modo: "normal", "apagado" (sin municion) o "silueta" (aun no lo tienes)."""
        self.icono.enabled = textura is not None
        if textura is not None:
            k = LADO * ICONO / max(textura.width, textura.height)
            self.icono.texture = textura
            self.icono.scale = (textura.width * k, textura.height * k)
            self.icono.color = {"normal": color.white, "apagado": color.rgba(1, 1, 1, 0.35),
                                "silueta": COLOR_SILUETA}[modo]
        self.interrogacion.enabled = modo == "silueta"
        self.cantidad.text = cantidad
        self.cantidad.color = COLOR_RECHAZO if modo == "apagado" else color.white

    def activa(self, valor):
        self.marco.color = COLOR_MARCO_ACTIVO if valor else COLOR_MARCO
        self.marco.scale = LADO + (0.014 if valor else 0.008)

    def rechazo(self):
        self.marco.color = COLOR_RECHAZO
        self.marco.scale = LADO + 0.014
        invoke(self.activa, False, delay=0.3)


class Hotbar(Entity):
    """Barra de 5 casillas: 1 pistola, 2 escopeta, 3-5 medicinas; con la barra de vida encima."""

    def __init__(self):
        super().__init__(parent=camera.ui, z=-1)
        ancho = CASILLAS * LADO + (CASILLAS - 1) * SEPARACION
        x0 = -ancho / 2 + LADO / 2
        self.casillas = [Casilla(self, i + 1, x0 + i * (LADO + SEPARACION)) for i in range(CASILLAS)]

        y_vida = Y_BARRA + LADO / 2 + 0.03
        izquierda = -ancho / 2
        Entity(parent=self, model="quad", origin=(-0.5, 0), position=(izquierda - 0.003, y_vida), z=0.01,
               scale=(ancho + 0.006, 0.028), color=COLOR_MARCO)
        Entity(parent=self, model="quad", origin=(-0.5, 0), position=(izquierda, y_vida),
               scale=(ancho, 0.022), color=COLOR_FONDO)
        self.vida = Entity(parent=self, model="quad", origin=(-0.5, 0), position=(izquierda, y_vida), z=-0.01,
                           scale=(ancho, 0.022), color=color.rgb32(210, 45, 45))
        self.texto_vida = Text(parent=self, text="", origin=(-0.5, 0), scale=0.75, z=-0.02, font=FUENTE,
                               position=(izquierda + 0.006, y_vida))
        self.aviso = Text(parent=self, text="", origin=(0, 0), scale=1.0, z=-0.02, font=FUENTE,
                          position=(0, y_vida + 0.045))
        self.ancho = ancho

    def set_vida(self, vida, maxima):
        self.vida.scale_x = self.ancho * max(0, vida) / maxima
        self.texto_vida.text = f"{max(0, int(vida))}"

    def seleccionar(self, indice):
        for i, casilla in enumerate(self.casillas):
            casilla.activa(i == indice)

    def avisar(self, texto, casilla=None):
        """Mensaje corto encima de la barra; si se indica casilla, su marco destella en rojo."""
        self.aviso.text = texto
        self.aviso.color = COLOR_RECHAZO
        self.aviso.animate("alpha", 0, duration=0.6, delay=1.4)
        if casilla is not None:
            self.casillas[casilla].rechazo()

    def destello(self, indice):
        casilla = self.casillas[indice]
        casilla.activa(True)
        invoke(casilla.activa, False, delay=0.2)
