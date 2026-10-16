# /// script
# dependencies = [
#     "panda3d",
#     "pillow",
# ]
# ///

# Entrada para la version web (pygbag). El navegador no permite un bucle
# bloqueante como app.run(), asi que avanzamos un frame y cedemos el control.

import asyncio
import platform

from ursina import Vec3, application, mouse

from scripts.main import setup

# En escritorio Ursina recentra el puntero cada frame para mirar con el raton;
# el navegador no deja mover el puntero, asi que usamos Pointer Lock y el
# movimiento relativo (movementX/Y) del evento mousemove.
POINTER_LOCK_JS = """
(() => {
    const canvas = document.getElementById("canvas");
    let dx = 0, dy = 0, quiereBloqueo = false;
    document.addEventListener("mousemove", (e) => {
        if (document.pointerLockElement === canvas) {
            dx += e.movementX;
            dy += e.movementY;
        }
    });
    canvas.addEventListener("mousedown", () => {
        if (quiereBloqueo && document.pointerLockElement !== canvas) {
            canvas.requestPointerLock();
        }
    });
    window.ursina_mouse = (bloquear) => {
        quiereBloqueo = bloquear;
        if (!bloquear && document.pointerLockElement === canvas) {
            document.exitPointerLock();
        }
        const delta = dx + "," + dy;
        dx = 0;
        dy = 0;
        return delta;
    };
})();
"""

_mouse_update = type(mouse).update


def mouse_update(self):
    dx, dy = (float(v) for v in str(platform.window.ursina_mouse(bool(self.locked))).split(","))
    if not self.locked:
        _mouse_update(self)
        return
    alto = application.base.win.getYSize() or 1
    self.velocity = Vec3(dx / alto, -dy / alto, 0)


async def main():
    app = setup()
    platform.window.eval(POINTER_LOCK_JS)
    type(mouse).update = mouse_update
    while True:
        app.step()
        await asyncio.sleep(0)


asyncio.run(main())
