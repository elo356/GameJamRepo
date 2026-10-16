# Punto de entrada del ejecutable de escritorio (PyInstaller).
# Con --selftest solo comprueba que estan todos los modulos y assets, sin abrir ventana.

import sys


def selftest():
    from pathlib import Path

    import panda3d.core  # noqa: F401
    import ursina  # noqa: F401
    from scripts import game, main  # noqa: F401
    from scripts.supermercado import ROOT

    faltan = [p for p in ("images/weapons/pist_0.png", "images/story/nino.png", "audio/tension_intro.wav",
                          "audio/shot_sound.wav") if not (ROOT / p).is_file()]
    fuentes = Path(ursina.__file__).parent / "fonts" / "VeraMono.ttf"
    if not fuentes.is_file():
        faltan.append(str(fuentes))
    resultado = "FALTAN: " + ", ".join(faltan) if faltan else "OK"
    (Path(sys.executable).parent / "selftest.txt").write_text(resultado)
    sys.exit(1 if faltan else 0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    from scripts.main import main

    main()
