"""
Particulas: a poeira do pulo e do pouso, as faiscas de um acerto, a morte do
Leo (ele vira ruido) e o ar de cada mundo (vaga-lumes no bosque, poeira de
luz nas ilhas, fagulhas do eclipse). Cada particula e um quadradinho de
pixel que nasce, anda e encolhe ate sumir -- sem imagem e sem transparencia,
como no resto do jogo.
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


class Faiscas:
    """
    O estouro de um acerto: pontinhos de luz que saem do Leo em roda e somem.
    Vivem no mundo, como a poeira; nao caem -- o ar so os freia.
    """

    def __init__(self):
        self.p = []           # [x, y, vx, vy, vida, vida_total, cor]
        self.rnd = random.Random(11)

    def soltar(self, x, y, cor, n):
        r = self.rnd
        for i in range(n):
            ang = math.tau * i / n + r.uniform(-0.25, 0.25)
            vel = r.uniform(110, 190)
            vida = r.uniform(0.26, 0.4)
            self.p.append([x, y, math.cos(ang) * vel, math.sin(ang) * vel - 40, vida, vida, cor])

    def atualizar(self, dt):
        vivas = []
        for q in self.p:
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[2] *= 1.0 - 7.0 * dt
            q[3] *= 1.0 - 7.0 * dt
            q[4] -= dt
            if q[4] > 0.0:
                vivas.append(q)
        self.p = vivas

    def desenhar(self, tela, cam_x, cam_y):
        for x, y, _, _, vida, total, cor in self.p:
            k = vida / total
            tam = 4 if k > 0.66 else 2                       # nasce grande, some pequena
            tela.fill((255, 255, 255) if k > 0.8 else cor,
                      (int(x - cam_x) - tam // 2, int(y - cam_y) - tam // 2, tam, tam))


def _tingido(img, cor):
    """Copia de `img` numa cor so, mantendo o recorte (o alfa) dela."""
    s = img.copy()
    s.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
    s.fill((*cor, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return s


class Desintegracao:
    """
    A morte do Leo: quem sai do compasso vira ruido e desaparece, como conta o
    enredo. Tres tempos, a partir do quadro em que ele estava:

        0,00 - 0,12 s   o estalo: o corpo inteiro fica branco
        0,12 - 0,50 s   a falha: o corpo se parte em faixas que escorregam de
                        lado, com as cores separadas (magenta e ciano)
        0,40 - 1,30 s   o ruido: pixel por pixel, da cabeca aos pes, o corpo
                        se solta e sobe piscando ate sumir
    """

    ESTALO, FALHA, FIM = 0.12, 0.50, 1.30
    CORES_RUIDO = ((255, 255, 255), (255, 70, 190), (80, 235, 255))

    def __init__(self, sprite, x, y):
        self.sprite, self.x, self.y = sprite, x, y      # o quadro e o canto dele no mundo
        self.t = 0.0
        self.branco = _tingido(sprite, (255, 255, 255))
        self.magenta = _tingido(sprite, (255, 70, 190))
        self.ciano = _tingido(sprite, (80, 235, 255))
        r = random.Random(11)
        w, h = sprite.get_size()
        self.faixas = [r.uniform(0.0, math.tau) for _ in range(h // 3 + 1)]
        # cada pixel (de 2 em 2) do desenho: [x, y, vx, vy, quando solta, cor, sorte]
        self.pixels = []
        topo = sprite.get_bounding_rect(min_alpha=128)
        for py in range(topo.top, topo.bottom, 2):
            desce = (py - topo.top) / max(1, topo.height)
            for px in range(topo.left, topo.right, 2):
                c = sprite.get_at((px, py))
                if c.a < 128:
                    continue
                solta = 0.40 + 0.40 * desce + r.uniform(0.0, 0.18)
                self.pixels.append([x + px, y + py, r.uniform(-55.0, 55.0), r.uniform(-150.0, -40.0),
                                    solta, (c.r, c.g, c.b), r.random()])

    def atualizar(self, dt):
        self.t += dt
        for q in self.pixels:
            if self.t >= q[4]:
                q[0] += q[2] * dt
                q[1] += q[3] * dt
                q[2] *= 1.0 - 1.5 * dt
                q[3] -= 90.0 * dt              # o ruido sobe cada vez mais depressa

    def desenhar(self, tela, cam_x, cam_y):
        t = self.t
        x, y = int(self.x - cam_x), int(self.y - cam_y)
        if t < self.ESTALO:
            tela.blit(self.branco, (x, y))
            return
        if t < self.FALHA:
            k = (t - self.ESTALO) / (self.FALHA - self.ESTALO)
            salto = int(t * 30)                # a falha muda de forma 30 vezes por segundo
            if salto % 2 == 0:
                abre = 3 + int(5 * k)
                tela.blit(self.magenta, (x - abre, y))
                tela.blit(self.ciano, (x + abre, y))
            w, h = self.sprite.get_size()
            amp = 2.0 + 9.0 * k
            for i, fase in enumerate(self.faixas):
                dx = int(math.sin(fase + salto * 1.7) * amp) if (i + salto) % 3 else 0
                tela.blit(self.sprite, (x + dx, y + i * 3), (0, i * 3, w, 3))
        for q in self.pixels:
            px, py = int(q[0] - cam_x), int(q[1] - cam_y)
            if t < q[4]:
                if t >= self.FALHA:            # ainda preso ao corpo que se desfaz
                    tela.fill(q[5], (px, py, 2, 2))
                continue
            vida = (t - q[4]) / (self.FIM - q[4])
            if vida >= 1.0 or (vida > 0.6 and (int(t * 40) + int(q[6] * 7)) % 2):
                continue                       # no fim, piscam antes de sumir
            tam = 3 if vida < 0.35 else (2 if vida < 0.75 else 1)
            cor = q[5] if vida < 0.3 else self.CORES_RUIDO[int(q[6] * 3 + t * 12) % 3]
            tela.fill(cor, (px, py, tam, tam))


class Vento:
    """
    Riscos de vento cruzando o ceu enquanto o Leo corre mais rapido que o
    normal (depois de um portal de velocidade). Aparecem e somem aos poucos.
    """

    def __init__(self):
        r = random.Random(3)
        self.riscos = [(r.uniform(0, LARGURA + 200), r.uniform(0, ALTURA * 0.8),
                        r.uniform(0.7, 1.3), r.randint(24, 70)) for _ in range(26)]
        self.forca = 0.0              # 0 sem vento, 1 em cheio

    def desenhar(self, tela, tempo, ventando, cor, dt):
        self.forca += ((1.0 if ventando else 0.0) - self.forca) * min(1.0, dt * 4.0)
        if self.forca < 0.05:
            return
        for x0, y, vel, comp in self.riscos:
            x = (x0 - tempo * 900 * vel) % (LARGURA + 200) - 100
            tela.fill(cor, (int(x), int(y), int(comp * self.forca), 2))


# o ar de cada mundo: (quantas, cor, cor clara, velocidade x, velocidade y, balanco)
AR = {
    # vaga-lumes: poucos, lentos, vagando entre as copas e o chao
    "bosque": (28, (120, 196, 104), (214, 255, 150), 5.0, -3.0, 26.0),
    # poeira de luz levada pelo vento do por do sol, da direita para a esquerda
    "ilhas": (46, (255, 206, 170), (255, 240, 220), -26.0, -6.0, 10.0),
    # brasas raras e apagadas, subindo devagar da coroa do eclipse
    "eclipse": (30, (190, 80, 60), (230, 130, 90), -5.0, -10.0, 8.0),
}
# so no bosque: a faixa da tela (fracao da altura) onde os vaga-lumes vivem, o
# quanto sobem e descem vagando, e o halo em cruz em volta dos que estao acesos
FAIXA_AR = {"bosque": (0.34, 0.9)}
VAGUEIA_AR = {"bosque": 13.0}
HALO_AR = {"bosque": (46, 92, 58)}


class Ar:
    """
    Particulas que enchem o ar de um mundo. Vivem na tela, com parallax leve
    (andam um pouco com a camera), e dao a volta nas bordas: nunca acabam.
    """

    def __init__(self, tema):
        self.cfg = AR.get(tema.nome)
        self.faixa = FAIXA_AR.get(tema.nome, (0.0, 1.0))
        self.vagueia = VAGUEIA_AR.get(tema.nome, 0.0)
        self.halo = HALO_AR.get(tema.nome)
        r = random.Random(tema.nome)
        n = self.cfg[0] if self.cfg else 0
        self.p = [(r.uniform(0, LARGURA), r.uniform(0, ALTURA), r.uniform(0, math.tau),
                   r.uniform(0.6, 1.4), r.random() < 0.3) for _ in range(n)]

    def desenhar(self, tela, cam_x, cam_y, tempo):
        if not self.cfg:
            return
        _, cor, clara, vx, vy, balanco = self.cfg
        topo, alto = ALTURA * self.faixa[0], ALTURA * (self.faixa[1] - self.faixa[0])
        halo = self.halo
        for x0, y0, fase, vel, grande in self.p:
            x = (x0 + vx * vel * tempo - cam_x * 0.35 + math.sin(tempo * 0.9 + fase) * balanco) % LARGURA
            y = topo + (y0 + vy * vel * tempo - cam_y * 0.35
                        + math.sin(tempo * 0.7 + fase * 2.0) * self.vagueia) % alto
            brilho = math.sin(tempo * 2.3 + fase * 3.0)
            if brilho < -0.55:
                continue                                   # piscam, como vaga-lumes
            tam = 3 if grande and brilho > 0.4 else 2
            if halo and brilho > 0.3:
                tela.fill(halo, (int(x) - 2, int(y), tam + 4, tam))
                tela.fill(halo, (int(x), int(y) - 2, tam, tam + 4))
            tela.fill(clara if brilho > 0.6 else cor, (int(x), int(y), tam, tam))
