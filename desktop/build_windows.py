#!/usr/bin/env python3
"""Genera el .exe de Windows con PyInstaller dentro de Docker (Wine + Python para Windows).

Uso (desde la raiz del repo, necesita Docker):
    .venv/bin/python desktop/build_windows.py
Resultado: build/SpookMart-windows.zip (carpeta SpookMart/ con SpookMart.exe)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "web"))
from build import audio_usado  # noqa: E402  (mismo filtro de audio que la version web)

OUT = ROOT / "build" / "win_src"
IMAGEN = "tobix/pywine:3.12"
DEPENDENCIAS = "pyinstaller ursina==8.3.0 panda3d==1.10.16 panda3d-gltf pillow screeninfo pyperclip"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*-pygbag.py")

PYINSTALLER = [
    "pyinstaller", "--noconfirm", "--clean", "--windowed", "--noupx", "--name", "SpookMart",
    "--add-data=images:images", "--add-data=audio:audio",
    "--collect-all", "ursina", "--collect-all", "panda3d", "--collect-all", "direct",
    "--collect-all", "gltf", "--collect-submodules", "scripts",
    "SpookMart.py",
]


def preparar():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copy(ROOT / "desktop" / "SpookMart.py", OUT / "SpookMart.py")
    shutil.copytree(ROOT / "scripts", OUT / "scripts", ignore=IGNORE)
    shutil.copytree(ROOT / "images", OUT / "images", ignore=IGNORE)
    sources = "\n".join(p.read_text() for p in (ROOT / "scripts").glob("*.py"))
    for wav in audio_usado(sources):
        destino = OUT / wav.relative_to(ROOT)
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(wav, destino)


def docker(comando):
    subprocess.run(["docker", "run", "--rm", "-v", f"{OUT}:/src", "-w", "/src", IMAGEN,
                    "bash", "-c", comando], check=True)


def main():
    preparar()
    usuario = f"{os.getuid()}:{os.getgid()}"
    docker(f"(wine python -m pip install --quiet {DEPENDENCIAS} && wine {' '.join(PYINSTALLER)} "
           f"&& timeout 300 wine dist/SpookMart/SpookMart.exe --selftest); rc=$?; chown -R {usuario} /src; exit $rc")
    resultado = OUT / "dist" / "SpookMart" / "selftest.txt"
    print("selftest:", resultado.read_text() if resultado.exists() else "sin resultado")
    if resultado.exists():
        resultado.unlink()
    zip_base = ROOT / "build" / "SpookMart-windows"
    shutil.make_archive(str(zip_base), "zip", OUT / "dist", "SpookMart")
    print("\nListo:", zip_base.with_suffix(".zip"))


if __name__ == "__main__":
    main()
