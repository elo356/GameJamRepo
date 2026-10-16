from ursina import *


class Bullet(Entity):
    def __init__(self, position=Vec3(0, 0, 0), direction=Vec3(0, 0, 0), speed=10, alcance=30, **kwargs):
        super().__init__(
            model='sphere',
            color=color.rgb32(255, 230, 120),
            scale=0.06,
            position=position,
            **kwargs
        )
        self.direction = direction.normalized()
        self.speed = speed
        self.restante = alcance

    def update(self):
        paso = self.speed * time.dt
        self.position += self.direction * paso
        self.restante -= paso
        if self.restante <= 0 or self.position.y < 0 or self.position.y > 10 or abs(self.position.x) > 15 or abs(self.position.z) > 15:
            destroy(self)

    def destroy_bullet(self):
        destroy(self)
