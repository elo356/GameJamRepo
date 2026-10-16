from panda3d.core import TransparencyAttrib
from ursina import Entity, camera, color, scene, window

from scripts.world import FOG_COLOR


def setup_rendering():
    window.color = color.rgb32(8, 8, 12)
    camera.fov = 85
    camera.clip_plane_near = 0.05


def set_fog(start, end):
    scene.fog_color = FOG_COLOR
    scene.fog_density = (start, end)


def fogify(entity):
    entity.set_shader_input("fog_color", scene.fog_color)
    entity.set_shader_input("fog_start", scene.fog_density[0])
    entity.set_shader_input("fog_end", scene.fog_density[1])
    return entity


def cutout(entity):
    entity.setTransparency(TransparencyAttrib.M_binary)
    return entity


def sprite(texture, billboard=True, **kwargs):
    e = Entity(model="quad", texture=texture, **kwargs)
    cutout(e)
    fogify(e)
    if billboard:
        e.setBillboardAxis()
    return e
