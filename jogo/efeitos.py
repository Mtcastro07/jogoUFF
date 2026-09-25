"""
Particulas: a poeira do pulo e do pouso, e o ar de cada mundo (poeira de luz
nas ilhas, fagulhas do eclipse). Cada particula e um quadradinho de pixel que
nasce, anda e encolhe ate sumir -- sem imagem e sem transparencia, como no
resto do jogo.
"""

import math
import random

import pygame

from . import arte
from .config import LARGURA, ALTURA


class Poeira:
    """A poeira que o pe levanta. Vive no mundo: fica para tras quando Leo corre."""

    def __init__(self):
        self.p = []           # [x, y, vx, vy, vida, vida_total, cor]
        self.rnd = random.Random(7)

    def soltar(self, x, y, cor, n, espalha=1.0, para_tras=0.0):
        r = self.rnd
        for _ in range(n):
            vida = r.uniform(0.22, 0.38)
            self.p.append([x + r.uniform(-8, 8), y - r.uniform(0, 3),
                           r.uniform(-70, 70) * espalha - para_tras * r.uniform(30, 70),
                           -r.uniform(20, 70), vida, vida,
                           cor if r.random() < 0.6 else arte.clarear(cor, 0.4)])

    def atualizar(self, dt):
        vivas = []
        for q in self.p:
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[2] *= 1.0 - 4.0 * dt            # o ar freia a poeira
            q[3] += 90.0 * dt                  # e ela assenta
            q[4] -= dt
            if q[4] > 0.0:
                vivas.append(q)
        self.p = vivas

    def desenhar(self, tela, cam_x, cam_y):
        for x, y, _, _, vida, total, cor in self.p:
            tam = 1 + int(3 * vida / total)    # 4 px ao nascer, 1 px antes de sumir
            tela.fill(cor, (int(x - cam_x) - tam // 2, int(y - cam_y) - tam // 2, tam, tam))


# o ar de cada mundo: (quantas, cor, cor clara, velocidade x, velocidade y, balanco)
AR = {
    # poeira de luz levada pelo vento do por do sol, da direita para a esquerda
    "ilhas": (46, (255, 206, 170), (255, 240, 220), -26.0, -6.0, 10.0),
    # fagulhas que sobem da coroa do eclipse
    "eclipse": (54, (255, 150, 80), (255, 214, 130), -8.0, -22.0, 14.0),
}


class Ar:
    """
    Particulas que enchem o ar de um mundo. Vivem na tela, com parallax leve
    (andam um pouco com a camera), e dao a volta nas bordas: nunca acabam.
    """

    def __init__(self, tema):
        self.cfg = AR.get(tema.nome)
        r = random.Random(tema.nome)
        n = self.cfg[0] if self.cfg else 0
        self.p = [(r.uniform(0, LARGURA), r.uniform(0, ALTURA), r.uniform(0, math.tau),
                   r.uniform(0.6, 1.4), r.random() < 0.3) for _ in range(n)]

    def desenhar(self, tela, cam_x, cam_y, tempo):
        if not self.cfg:
            return
        _, cor, clara, vx, vy, balanco = self.cfg
        for x0, y0, fase, vel, grande in self.p:
            x = (x0 + vx * vel * tempo - cam_x * 0.35 + math.sin(tempo * 0.9 + fase) * balanco) % LARGURA
            y = (y0 + vy * vel * tempo - cam_y * 0.35) % ALTURA
            brilho = math.sin(tempo * 2.3 + fase * 3.0)
            if brilho < -0.55:
                continue                                   # piscam, como vaga-lumes
            tam = 3 if grande and brilho > 0.4 else 2
            tela.fill(clara if brilho > 0.6 else cor, (int(x), int(y), tam, tam))
