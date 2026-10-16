from pathlib import Path

from ursina import *

ANCHO = 30
LARGO = 19
ALTO = 3
ALTO_CAJA = 0.9

INICIO_JUGADOR = (9.5, 0, 6.5)
ROOT = Path(__file__).resolve().parent.parent


def asset_path(*parts):
    filename = Path(*parts)
    candidates = [
        ROOT / "images" / filename,
        ROOT / filename,
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return str(ROOT / filename)


def textura(nombre):
    path = asset_path("environment", f"{nombre}.png")
    if not Path(path).exists():
        raise FileNotFoundError(f"Texture not found: {path}")
    return Texture(path, filtering=None)


def bloque(nombre_textura, x, z, ancho, alto, grosor=1, girado=False, **kwargs):
    return Entity(model="cube",
                  texture=textura(nombre_textura),
                  position=(x, alto / 2, z),
                  rotation_y=90 if girado else 0,
                  scale=(ancho, alto, grosor),
                  texture_scale=(ancho, alto),
                  collider="box",
                  **kwargs)


def construir_supermercado():
    Entity(model="plane", texture=textura("floor"),
           scale=(ANCHO, 1, LARGO), texture_scale=(ANCHO / 2, LARGO / 2),
           collider="box")
    Entity(model="plane", texture=textura("ceiling"),
           y=ALTO, rotation_x=180,
           scale=(ANCHO, 1, LARGO), texture_scale=(ANCHO / 2, LARGO / 2))

    bloque("wall_tiles", 0, 9, ANCHO, ALTO)
    bloque("wall", -14.5, 0, 17, ALTO, girado=True)
    bloque("wall", 14.5, 0, 17, ALTO, girado=True)
    bloque("wall", -8.5, -9, 13, ALTO)
    bloque("wall", 7.5, -9, 15, ALTO)

    bloque("metal_door", -1, -9, 2, ALTO, grosor=0.2, color=color.rgb32(150, 150, 160))

    for x in (-10, 0, 8):
        bloque("metal_door", x, -6, 2, ALTO_CAJA)
