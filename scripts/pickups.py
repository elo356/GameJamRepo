import math
import random

from ursina import *

from scripts.neblina import sprite
from scripts.supermercado import asset_path
from scripts.world import distance_xz

TAMANO_PIXEL = 0.022
RADIO_RECOGER = 0.8
FLOTACION = 0.06

# tipo: (carpeta, textura, escala extra, celdas (col, fila) del mapa donde aparece)
TIPOS = {
    "escopeta": ("icons", "escopeta", 2.6, [(1, 2)]),
    "botiquin": ("props", "botiquin", 1.0, [(2, 12), (23, 9), (12, 6), (5, 3)]),
    "frasco": ("props", "frasco", 1.4, [(20, 12), (8, 9), (17, 5), (24, 1)]),
    "cartuchos": ("props", "cartuchos", 1.0, [(12, 12), (3, 6), (22, 3), (18, 9)]),
}


class Pickup:
    def __init__(self, tipo, posicion, textura, escala):
        self.tipo = tipo
        ancho, alto = textura.width * TAMANO_PIXEL * escala, textura.height * TAMANO_PIXEL * escala
        self.base_y = alto / 2 + 0.1
        self.fase = random.uniform(0, math.tau)
        self.e = sprite(textura, position=(posicion.x, self.base_y, posicion.z), scale=(ancho, alto))

    @property
    def activo(self):
        return self.e.enabled


class Pickups(Entity):
    """Escopeta, botiquines, frascos y cajas de cartuchos repartidos por el supermercado."""

    def __init__(self, game):
        super().__init__()
        self.game = game
        self.items = []
        for tipo, (carpeta, nombre, escala, celdas) in TIPOS.items():
            textura = Texture(asset_path(carpeta, f"{nombre}.png"), filtering=None)
            for celda in celdas:
                self.items.append(Pickup(tipo, game.level.cell_center(*celda), textura, escala))

    def reset(self):
        for item in self.items:
            item.e.enabled = True

    def update(self):
        if self.game.state != "playing":
            return
        pos = self.game.player_pos
        for item in self.items:
            if not item.activo:
                continue
            item.e.y = item.base_y + math.sin(time.time() * 2.5 + item.fase) * FLOTACION
            if distance_xz(pos, item.e.position) < RADIO_RECOGER and self.game.recoger(item.tipo):
                item.e.enabled = False
