from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

from scripts.hud import Hotbar
from scripts.supermercado import asset_path, audio_path
from scripts.bullets import Bullet

ALTURA_OJOS = 1.65
VIDA_MAXIMA = 150
VELOCIDAD = 5
RADIO = 0.3
PERDIGONES = 6
DISPERSION = 0.07
MAX_MEDICINAS = 3
CURAS = {"botiquin": 40, "frasco": 15}
CASILLA_ARMA = {"pistola": 0, "escopeta": 1}

# frames: [reposo, disparo...]; secuencia: (frame, segundo) tras disparar; fin: cuando se puede volver a disparar
ARMAS = {
    "pistola": dict(frames=["pist_0", "pist_1", "pist_2", "pist_3"],
                    escala=(0.6, 0.6 * 150 / 170), posicion=Vec2(0.32, -0.3),
                    secuencia=[(1, 0), (2, 0.08), (3, 0.16)], fin=0.24, tono=1.0, volumen=0.5),
    "escopeta": dict(frames=["escopeta_5", "escopeta_4", "escopeta_3", "escopeta_1"],
                     escala=(1.0, 1.0 * 180 / 320), posicion=Vec2(0.12, -0.22),
                     secuencia=[(1, 0), (2, 0.08), (3, 0.2)], fin=0.75, tono=0.6, volumen=0.8),
}


def textura(*partes):
    return Texture(asset_path(*partes), filtering=None)


class Player(Entity):
    def __init__(self, al_disparar=None, nivel=None, **kwargs):
        self.controller = FirstPersonController(height=ALTURA_OJOS, **kwargs)

        self.controller.speed = 0 if nivel else 5
        self.controller.cursor.color = color.white
        self.controller.cursor.scale = 0.006
        super().__init__(parent=self.controller)

        self.al_disparar = al_disparar
        self.nivel = nivel
        self.frames = {arma: [textura("weapons", f"{f}.png") for f in datos["frames"]] for arma, datos in ARMAS.items()}
        self.iconos = {"pistola": textura("icons", "pistola.png"), "escopeta": textura("icons", "escopeta.png"),
                       "botiquin": textura("props", "botiquin.png"), "frasco": textura("props", "frasco.png")}
        self.disparando = False
        self.balanceo = 0
        self.vida = VIDA_MAXIMA
        self.vivo = True
        self.arma = "pistola"
        self.tiene_escopeta = False
        self.cartuchos = 0
        self.medicinas = []

        self.gun = Entity(parent=camera.ui, model="quad")
        self.sonido_disparo = audio_path("shot_sound.wav")

        self.flash_dano = Entity(parent=camera.ui, model="quad", scale=(3, 2), z=-0.6,
                                 color=color.rgba(0.8, 0, 0, 0))
        self.hud = Hotbar()
        self.actualizar_vida()
        self.equipar("pistola")

    @property
    def pos(self):
        return self.controller.position

    def actualizar_vida(self):
        self.hud.set_vida(self.vida, VIDA_MAXIMA)

    def actualizar_hud(self):
        casillas = self.hud.casillas
        casillas[0].mostrar(self.iconos["pistola"])
        if self.tiene_escopeta:
            casillas[1].mostrar(self.iconos["escopeta"], str(self.cartuchos),
                                "normal" if self.cartuchos > 0 else "apagado")
        else:
            casillas[1].mostrar(self.iconos["escopeta"], str(self.cartuchos) if self.cartuchos else "", "silueta")
        for i, casilla in enumerate(casillas[2:]):
            casilla.mostrar(self.iconos[self.medicinas[i]] if i < len(self.medicinas) else None)
        self.hud.seleccionar(CASILLA_ARMA[self.arma])

    def equipar(self, arma):
        if self.disparando:
            return
        datos = ARMAS[arma]
        self.arma = arma
        self.gun.texture = self.frames[arma][0]
        self.gun.scale = datos["escala"]
        self.gun.position = datos["posicion"] + Vec2(0, -0.15)  # entra desde abajo
        self.actualizar_hud()

    def curar(self, cantidad):
        if not self.vivo or self.vida >= VIDA_MAXIMA:
            return False
        self.vida = min(VIDA_MAXIMA, self.vida + cantidad)
        self.actualizar_vida()
        self.flash_dano.color = color.rgba(0.2, 0.9, 0.3, 0.3)
        self.flash_dano.animate_color(color.rgba(0.2, 0.9, 0.3, 0), duration=0.5)
        return True

    def dar_escopeta(self):
        self.tiene_escopeta = True
        if self.cartuchos > 0:
            self.equipar("escopeta")
        self.actualizar_hud()

    def dar_cartuchos(self, cantidad):
        self.cartuchos += cantidad
        self.actualizar_hud()

    def guardar_medicina(self, tipo):
        if len(self.medicinas) >= MAX_MEDICINAS:
            return False
        self.medicinas.append(tipo)
        self.actualizar_hud()
        return True

    def usar_medicina(self, indice):
        if indice >= len(self.medicinas):
            self.hud.avisar("Casilla vacia", indice + 2)
            return
        if not self.curar(CURAS[self.medicinas[indice]]):
            self.hud.avisar("Tu vida ya esta llena")
            return
        self.medicinas.pop(indice)
        self.hud.destello(indice + 2)
        self.actualizar_hud()

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
        self.tiene_escopeta = False
        self.cartuchos = 0
        self.medicinas = []
        self.disparando = False
        self.equipar("pistola")
        self.gun.enabled = True
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
        objetivo = ARMAS[self.arma]["posicion"] + Vec2(math.sin(self.balanceo) * 0.012,
                                                       -abs(math.cos(self.balanceo)) * 0.015 * moviendo)
        self.gun.position = lerp(self.gun.position, Vec3(objetivo.x, objetivo.y, 0), min(time.dt * 12, 1))

    def puede_escopeta(self):
        return self.tiene_escopeta and self.cartuchos > 0

    def input(self, key):
        if not (self.vivo and self.controller.enabled):
            if key == "escape":
                application.quit()
            return

        if key == "left mouse down":
            self.disparar()
        elif key == "1" and self.arma != "pistola":
            self.equipar("pistola")
        elif key == "2" and self.arma != "escopeta":
            if self.puede_escopeta():
                self.equipar("escopeta")
            else:
                self.hud.avisar("Aun no tienes la escopeta" if not self.tiene_escopeta else "Sin cartuchos", 1)
        elif key in ("3", "4", "5"):
            self.usar_medicina(int(key) - 3)
        elif key in ("scroll up", "scroll down"):
            if self.arma == "escopeta":
                self.equipar("pistola")
            elif self.puede_escopeta():
                self.equipar("escopeta")
        elif key == "escape":
            application.quit()

    def disparar(self):
        if self.disparando:
            return
        datos = ARMAS[self.arma]
        self.disparando = True

        direcciones = [camera.forward]
        if self.arma == "escopeta":
            self.cartuchos -= 1
            direcciones = [(camera.forward + camera.right * random.uniform(-DISPERSION, DISPERSION)
                            + camera.up * random.uniform(-DISPERSION, DISPERSION)).normalized()
                           for _ in range(PERDIGONES)]
            self.actualizar_hud()

        for i, direccion in enumerate(direcciones):
            alcance = self.al_disparar(camera.world_position, direccion) if self.al_disparar else 30
            if i < 3:  # pocas balas visibles bastan para el efecto
                Bullet(position=camera.world_position + direccion * 0.5, direction=direccion, speed=20, alcance=alcance)
        Audio(self.sonido_disparo, volume=datos["volumen"], pitch=datos["tono"], auto_destroy=True)

        frames = self.frames[self.arma]
        for frame, segundo in datos["secuencia"]:
            invoke(setattr, self.gun, "texture", frames[frame], delay=segundo)
        invoke(self.terminar_disparo, delay=datos["fin"])

    def terminar_disparo(self):
        self.gun.texture = self.frames[self.arma][0]
        self.disparando = False
        if self.arma == "escopeta" and self.cartuchos <= 0:
            self.equipar("pistola")
