# Convierte los shaders GLSL de escritorio de Ursina a GLSL ES 3.00 (WebGL2).
# build.py redirige las llamadas a Shader.make de ursina/shader.py hacia make_shader.

import re

from panda3d.core import Shader

ES_HEADER = "#version 300 es\nprecision highp float;\nprecision highp int;\n"


def glsl_es(source, fragment=False):
    if not source:
        return source
    source = re.sub(r"^\s*#version[^\n]*\n", "", source.lstrip())
    source = source.replace("texture2D(", "texture(")
    if "gl_FragColor" in source:
        source = "out vec4 _frag_color;\n" + source.replace("gl_FragColor", "_frag_color")
    if fragment:
        # WebGL no tiene alpha test: los pixeles transparentes se descartan aqui
        salida = re.search(r"\bout\s+vec4\s+(\w+)\s*;", source)
        fin = source.rfind("}")
        if salida and fin != -1:
            source = f"{source[:fin]}    if ({salida.group(1)}.a < 0.004) discard;\n{source[fin:]}"
    return ES_HEADER + source


def make_shader(language, vertex, fragment, geometry=""):
    return Shader.make(language, glsl_es(vertex), glsl_es(fragment, fragment=True), geometry)
