"""El "director" de la noche: reloj, historia y luces que parpadean."""
import random
from pathlib import Path

from ursina import *

from scripts.supermercado import asset_path

INICIO_MINUTOS = -10
MINUTOS_POR_SEGUNDO = 2
NIEBLA_INICIO = 6
NIEBLA_NORMAL = 26
NIEBLA_NOCHE = 14
LUZ_ENCENDIDA = color.rgb32(235, 245, 255)
LUZ_APAGADA = color.rgb32(60, 64, 70)


def sonido(*partes, **kwargs):
    return Audio(Path(asset_path(*partes)), autoplay=False, **kwargs)


class HudNoche:
    def __init__(self):
        self.oscuridad = Entity(parent=camera.ui, model="quad", color=color.rgba(0, 0, 0, 0),
                                scale=(3, 2), z=-0.5)
        self.reloj = Text(text="", parent=camera.ui, origin=(0.5, 0.5), scale=1.6, z=-1,
                          position=(window.top_right.x - 0.03, window.top_right.y - 0.03))
        self.titulo = Text(text="", parent=camera.ui, origin=(0, 0), scale=2.2, y=0.22, z=-1)
        self.subtitulo = Text(text="", parent=camera.ui, origin=(0, 0), scale=1.2, y=0.15, z=-1,
                              color=color.light_gray)
        self.tiempo_mensaje = 0

    def set_reloj(self, texto):
        self.reloj.text = texto

    def set_oscuridad(self, alpha):
        self.oscuridad.color = color.rgba(0, 0, 0, alpha)

    def show_message(self, titulo, subtitulo, duracion, col=color.white):
        self.titulo.text, self.subtitulo.text = titulo, subtitulo
        self.titulo.color = col
        self.titulo.alpha = self.subtitulo.alpha = 1
        self.tiempo_mensaje = duracion

    def update(self, dt):
        if self.tiempo_mensaje > 0:
            self.tiempo_mensaje -= dt
            alpha = clamp(self.tiempo_mensaje / 0.6, 0, 1)
            self.titulo.alpha = self.subtitulo.alpha = alpha


class NightDirector(Entity):
    def __init__(self, puertas, luces):
        super().__init__()
        self.puertas = puertas
        self.luces = luces
        self.hud = HudNoche()
        self.zumbido = sonido("audio", "buzz.wav", volume=0.5)
        self.ambiente = sonido("audio", "atmo-public-supermarket-calm-cooling-shelf-switching-distant-01.wav",
                               loop=True, volume=0.4)
        self.musica_noche = sonido("audio", "25. Dark Factory.wav", loop=True, volume=0.45)
        self.ambiente.play()
        self.reset()

    def reset(self):
        self.minutes = INICIO_MINUTOS
        self.story = 0
        self.last_hour = -1
        self.flicker = 0.0
        self.base_dark = 0.0
        self.doors_open = False
        scene.fog_density = (NIEBLA_INICIO, NIEBLA_NORMAL)

    @property
    def progress(self):
        """0 a medianoche, 1 a las 06:00."""
        return clamp(self.minutes / 360.0, 0, 1)

    def clock_text(self):
        m = int(self.minutes) % (24 * 60)
        return f"{m // 60:02d}:{m % 60:02d}"

    def update(self):
        dt = time.dt
        before = self.minutes
        self.minutes += dt * MINUTOS_POR_SEGUNDO
        self._story_events(before)
        self._lights(dt)
        self.hud.set_reloj(self.clock_text())
        self.hud.update(dt)

    def _buzz(self, volumen):
        self.zumbido.volume = volumen
        self.zumbido.play()

    def _story_events(self, before):
        hud = self.hud
        if self.story == 0 and self.minutes >= -4:
            self.story = 1
            hud.show_message("...algo se mueve en los estantes", "", 3, color.light_gray)
        if self.story == 1 and self.minutes >= 0:
            self.story = 2
            self.flicker = 2.5
            self._buzz(0.8)
            self.ambiente.fade_out(duration=2)
            self.musica_noche.play()
            hud.show_message("MEDIANOCHE: LA COMIDA COBRO VIDA", "Sobrevive hasta las 06:00", 4, color.rgb32(255, 90, 70))
            scene.fog_density = (NIEBLA_INICIO / 2, NIEBLA_NOCHE)
        if self.minutes >= 360 and not self.doors_open:
            self.story = 3
            self.doors_open = True
            for puerta in self.puertas:
                puerta.open()
            hud.show_message("06:00", "Las puertas se abrieron. ¡Sal de aqui!", 4, color.rgb32(90, 255, 120))

        hour = int(self.minutes // 60)
        if 0 < hour < 6 and hour != self.last_hour and int(before // 60) != hour:
            self.last_hour = hour
            left = 6 - hour
            hud.show_message(f"{hour:02d}:00", f"Faltan {left} hora{'s' if left > 1 else ''} para que abran", 2.5,
                             color.rgb32(255, 210, 90))
            self.flicker = 0.8
            self._buzz(0.5)

    def _lights(self, dt):
        """La tienda se oscurece con la noche y los fluorescentes parpadean."""
        if self.minutes >= 0:
            self.base_dark = 0.22 + 0.3 * self.progress
            if random.random() < dt * 0.08:
                self.flicker = random.uniform(0.3, 0.9)
                self._buzz(0.35)
        alpha = self.base_dark
        apagada = False
        if self.flicker > 0:
            self.flicker -= dt
            if random.random() < 0.45:
                alpha = 0.85
                apagada = True
        self.hud.set_oscuridad(alpha)
        for luz in self.luces:
            luz.color = LUZ_APAGADA if apagada else LUZ_ENCENDIDA
