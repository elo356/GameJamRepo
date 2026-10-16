from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

from scripts.supermercado import asset_path, audio_path
from scripts.bullets import Bullet

ALTURA_OJOS = 1.65
POSICION_ARMA = Vec2(0.32, -0.3)
VIDA_MAXIMA = 150
VELOCIDAD = 5
RADIO = 0.3


class Player(Entity):
    def __init__(self, al_disparar=None, nivel=None, **kwargs):
        self.controller = FirstPersonController(height=ALTURA_OJOS, **kwargs)
     
        self.controller.speed = 0 if nivel else 5
        self.controller.cursor.color = color.white
        self.controller.cursor.scale = 0.006
        super().__init__(parent=self.controller)

        self.al_disparar = al_disparar
        self.nivel = nivel
        self.frames_pistola = [Texture(asset_path("weapons", f"pist_{i}.png"), filtering=None)
                               for i in range(4)]
        self.disparando = False
        self.balanceo = 0
        self.vida = VIDA_MAXIMA
        self.vivo = True

        self.gun = Entity(parent=camera.ui,
                          model="quad",
                          texture=self.frames_pistola[0],
                          scale=(0.6, 0.6 * 150 / 170),
                          position=POSICION_ARMA,
                          )
        self.sonido_disparo = Audio(audio_path("shot_sound.ogg"), autoplay=False, loop=False, volume=0.5)

        self.flash_dano = Entity(parent=camera.ui, model="quad", scale=(3, 2), z=-0.6,
                                 color=color.rgba(0.8, 0, 0, 0))
        izquierda = window.bottom_left + Vec2(0.04, 0.05)
        Entity(parent=camera.ui, model="quad", origin=(-0.5, 0), position=izquierda, z=-0.9,
               scale=(0.42, 0.035), color=color.rgba(0, 0, 0, 0.6))
        self.barra_vida = Entity(parent=camera.ui, model="quad", origin=(-0.5, 0), position=izquierda, z=-1,
                                 scale=(0.42, 0.035), color=color.rgb32(220, 50, 50))
        self.texto_vida = Text(parent=camera.ui, text="", origin=(-0.5, 0), scale=0.9, z=-1.1,
                               position=izquierda + Vec2(0.01, 0))
        self.actualizar_vida()

    @property
    def pos(self):
        return self.controller.position

    def actualizar_vida(self):
        self.barra_vida.scale_x = 0.42 * max(0, self.vida) / VIDA_MAXIMA
        self.texto_vida.text = f"{max(0, int(self.vida))}"

    def recibir_dano(self, dano, direccion=None, empuje=0.0, nivel=None):
        if not self.vivo:
            return
        self.vida -= dano
        self.actualizar_vida()
        self.flash_dano.color = color.rgba(0.8, 0, 0, 0.45)
        self.flash_dano.animate_color(color.rgba(0.8, 0, 0, 0), duration=0.5)
        if direccion is not None and nivel is not None and empuje > 0:
            self.controller.x, self.controller.z = nivel.slide_move(self.pos, direccion.x * empuje, direccion.z * empuje, RADIO,
                                                                    nivel.blocks_player)
        if self.vida <= 0:
            self.vivo = False

    def congelar(self, congelado):
        self.controller.enabled = not congelado
        mouse.locked = not congelado

    def reiniciar(self, posicion, rotacion_y):
        self.vida = VIDA_MAXIMA
        self.vivo = True
        self.actualizar_vida()
        self.controller.position = posicion
        self.controller.rotation_y = rotacion_y
        self.controller.camera_pivot.rotation_x = 0
        self.congelar(False)

    def mover(self):
        c = self.controller
        if not self.nivel or not c.enabled:
            return
        direccion = (c.forward * (held_keys["w"] - held_keys["s"]) + c.right * (held_keys["d"] - held_keys["a"])).normalized()
        paso = VELOCIDAD * time.dt
        c.x, c.z = self.nivel.slide_move(c.position, direccion.x * paso, direccion.z * paso, RADIO, self.nivel.blocks_player)

    def update(self):
        self.mover()
        moviendo = self.controller.grounded and (held_keys["w"] or held_keys["a"] or held_keys["s"] or held_keys["d"])
        if moviendo:
            self.balanceo += time.dt * 9
        objetivo = POSICION_ARMA + Vec2(math.sin(self.balanceo) * 0.012, -abs(math.cos(self.balanceo)) * 0.015 * moviendo)
        self.gun.position = lerp(self.gun.position, Vec3(objetivo.x, objetivo.y, 0), min(time.dt * 12, 1))

    def input(self, key):
        if key == "left mouse down" and self.vivo and self.controller.enabled:
            if self.disparando:
                return
            self.disparar()
            alcance = self.al_disparar(camera.world_position, camera.forward) if self.al_disparar else 30
            Bullet(position=camera.world_position + camera.forward * 0.5,
                   direction=camera.forward,
                   speed=20,
                   alcance=alcance)
            self.sonido_disparo.play()

        elif key == "escape":
            application.quit()

    def disparar(self):
        if self.disparando:
            return
        self.disparando = True

        self.gun.texture = self.frames_pistola[1]
        invoke(setattr, self.gun, "texture", self.frames_pistola[2], delay=0.08)
        invoke(setattr, self.gun, "texture", self.frames_pistola[3], delay=0.16)
        invoke(self.terminar_disparo, delay=0.24)

    def terminar_disparo(self):
        self.gun.texture = self.frames_pistola[0]
        self.disparando = False
