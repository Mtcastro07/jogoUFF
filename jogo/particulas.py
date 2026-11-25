import random

from PPlay.camera import Camera
from PPlay.particles import Particle, ParticleEmitter


class Grao(Particle):
    freio_x = 0.0
    freio_y = 0.0
    peso = 0.0

    def update(self, dt):
        super().update(dt)
        self.vx *= 1.0 - self.freio_x * dt
        self.vy = self.vy * (1.0 - self.freio_y * dt) + self.peso * dt


class SoltaParticula(ParticleEmitter):
    def __init__(self, semente=0):
        super().__init__(0, 0)
        self.numero_sorteado = random.Random(semente)

    def emitir(self):
        for i in range(self.intensidade):
            self.particulas.append(self.nova(i))

    def update(self, dt):
        for p in self.particulas:
            p.update(dt)
        self.particulas = [p for p in self.particulas if p.esta_viva()]

    def draw(self, tela):
        cam = Camera.get_instance()
        for p in self.particulas:
            x, y = p.x, p.y
            if cam is not None:
                x, y = cam.transform_x(x), cam.transform_y(y)
            p.draw(tela, x, y)
