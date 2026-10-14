from ursina import *


class Bullet(Entity):
    def __init__(self, position=Vec3(0, 0, 0), direction=Vec3(0, 0, 0), speed=10, **kwargs):
        super().__init__(
            model='sphere',
            color=color.yellow,
            scale=0.1,
            position=position,
            **kwargs
        )
        self.direction = direction.normalized()
        self.speed = speed

    def update(self):
        self.position += self.direction * self.speed * time.dt
        if self.position.y < 0 or self.position.y > 10 or self.position.x < -15 or self.position.x > 15 or self.position.z < -15 or self.position.z > 15:
            destroy(self)
        return

    def destroy_bullet(self):
        destroy(self)
        return