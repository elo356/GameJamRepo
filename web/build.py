#!/usr/bin/env python3
"""Genera la version web del juego con pygbag.

Uso (desde la raiz del repo, con el .venv que tiene ursina y pygbag):
    .venv/bin/python web/build.py           # build en build/web_src/build/web
    .venv/bin/python web/build.py --serve   # build y servidor en http://localhost:8000
"""

import audioop
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import ursina

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
OUT = ROOT / "build" / "web_src"

AUDIO_RATE = 22050
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def audio_usado(sources):
    """Solo los .wav nombrados en el codigo; el resto de pistas no se empaqueta."""
    usados = []
    for wav in (ROOT / "audio").rglob("*.wav"):
        nombre = wav.relative_to(ROOT / "audio").with_suffix("").as_posix()
        if re.search(rf'["/]{re.escape(nombre)}(\.wav)?"', sources):
            usados.append(wav)
    return usados


def comprimir_wav(src, dst):
    """Pasa a mono 16-bit 22 kHz para que la descarga en el navegador sea ligera."""
    with wave.open(str(src)) as w:
        channels, width, rate = w.getnchannels(), w.getsampwidth(), w.getframerate()
        frames = w.readframes(w.getnframes())

    if width != 2:
        frames = audioop.lin2lin(frames, width, 2)
    if channels == 2:
        frames = audioop.tomono(frames, 2, 0.5, 0.5)
    if rate != AUDIO_RATE:
        frames, _ = audioop.ratecv(frames, 2, 1, rate, AUDIO_RATE, None)

    dst.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(AUDIO_RATE)
        w.writeframes(frames)


def preparar():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    shutil.copy(WEB / "main.py", OUT / "main.py")
    for stub in (WEB / "stubs").glob("*.py"):
        shutil.copy(stub, OUT / stub.name)
    shutil.copytree(ROOT / "scripts", OUT / "scripts", ignore=IGNORE)
    shutil.copytree(ROOT / "images", OUT / "images", ignore=IGNORE)
    # ursina no esta en el repositorio de paquetes de pygbag: va dentro del build
    shutil.copytree(Path(ursina.__file__).parent, OUT / "ursina", ignore=IGNORE)
    # WebGL2 solo acepta GLSL ES: todos los shaders pasan por stubs/glsl_es.py
    shader_py = OUT / "ursina" / "shader.py"
    codigo = shader_py.read_text().replace("Panda3dShader.make(", "make_shader(")
    shader_py.write_text(codigo + "\n\nfrom glsl_es import make_shader\n")
    # M_dual depende del alpha test, que WebGL no tiene: se usa mezcla normal
    entity_py = OUT / "ursina" / "entity.py"
    entity_py.write_text(entity_py.read_text().replace("TransparencyAttrib.M_dual", "TransparencyAttrib.M_alpha"))

    sources = "\n".join(p.read_text() for p in (ROOT / "scripts").glob("*.py"))
    for wav in audio_usado(sources):
        comprimir_wav(wav, OUT / wav.relative_to(ROOT))
        print("audio:", wav.relative_to(ROOT))


def main():
    preparar()
    cmd = [sys.executable, "-m", "pygbag", "--no_opt", "--disable-sound-format-error", "--title", "After Hours"]
    if "--serve" not in sys.argv:
        cmd += ["--build", "--archive"]
    subprocess.run(cmd + [str(OUT)], check=True)
    print("\nBuild listo en", OUT / "build" / "web")


if __name__ == "__main__":
    main()
