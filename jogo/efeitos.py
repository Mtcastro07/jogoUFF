import math
import random

import pygame
from PPlay.camera import Camera
from PPlay.particles import Particle

from . import arte
from .config import LARG_TELA, ALT_TELA
from .particulas import SoltaParticula, Grao


class PoeirinhaDoPe(Grao):
    freio_x = 4.0
    peso = 90.0

    def draw(self, tela, x, y):
        tam = 1 + int(3 * self.vida_restante / self.vida_max)
        tela.fill(self.cor, (int(x) - tam // 2, int(y) - tam // 2, tam, tam))


class Poeira(SoltaParticula):
    def __init__(self):
        super().__init__(7)
        self.espalha, self.joga_pra_tras = 1.0, 0.0

    def solta_aqui(self, x, y, cor, n, espalha=1.0, joga_pra_tras=0.0):
        self.set_pos(x, y)
        self.cor, self.espalha, self.joga_pra_tras = cor, espalha, joga_pra_tras
        self.explodir(n)

    def nova(self, i):
        r = self.numero_sorteado
        vida = r.uniform(0.22, 0.38)
        x = self.x + r.uniform(-8, 8)
        y = self.y - r.uniform(0, 3)
        vx = r.uniform(-70, 70) * self.espalha - self.joga_pra_tras * r.uniform(30, 70)
        vy = -r.uniform(20, 70)
        cor = self.cor
        if r.random() >= 0.6:
            cor = arte.clareia(cor, 0.4)
        return PoeirinhaDoPe(x, y, vx, vy, vida, cor, 4)


class UmaFaisca(Grao):
    freio_x = freio_y = 7.0

    def draw(self, tela, x, y):
        k = self.vida_restante / self.vida_max
        tam, cor = 2, self.cor
        if k > 0.66:
            tam = self.tamanho
        if k > 0.8:
            cor = (255, 255, 255)
        tela.fill(cor, (int(x) - tam // 2, int(y) - tam // 2, tam, tam))


class UmMonteDeFaisca(SoltaParticula):
    def __init__(self):
        super().__init__(11)

    def solta_aqui(self, x, y, cor, n):
        self.set_pos(x, y)
        self.cor = cor
        self.explodir(n)

    def nova(self, i):
        r = self.numero_sorteado
        ang = math.tau * i / self.intensidade + r.uniform(-0.25, 0.25)
        vel = r.uniform(110, 190)
        vida = r.uniform(0.26, 0.4)
        return UmaFaisca(self.x, self.y, math.cos(ang) * vel, math.sin(ang) * vel - 40, vida, self.cor, 4)


def tingido(img, cor):
    s = img.copy()
    s.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
    s.fill((*cor, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return s


class Chuvisco(Grao):
    freio_x = 1.5
    peso = -90.0

    def __init__(self, x, y, vx, vy, solta, cor, sorte):
        super().__init__(x, y, vx, vy, LeoSumindo.FIM - solta, cor, 3)
        self.solta, self.sorte = solta, sorte


class LeoSumindo(SoltaParticula):
    ESTALO, FALHA, FIM = 0.12, 0.50, 1.30
    CORES_RUIDO = ((255, 255, 255), (255, 70, 190), (80, 235, 255))

    def __init__(self, sprite, x, y):
        super().__init__(11)
        self.set_pos(x, y)
        self.sprite = sprite
        self.t = 0.0
        self.branco = tingido(sprite, (255, 255, 255))
        self.magenta = tingido(sprite, (255, 70, 190))
        self.ciano = tingido(sprite, (80, 235, 255))
        r = self.numero_sorteado
        h = sprite.get_height()
        self.faixas = [r.uniform(0.0, math.tau) for _ in range(h // 3 + 1)]
        topo = sprite.get_bounding_rect(min_alpha=128)
        for py in range(topo.top, topo.bottom, 2):
            desce = (py - topo.top) / max(1, topo.height)
            for px in range(topo.left, topo.right, 2):
                c = sprite.get_at((px, py))
                if c.a < 128:
                    continue
                solta = 0.40 + 0.40 * desce + r.uniform(0.0, 0.18)
                self.particulas.append(Chuvisco(x + px, y + py, r.uniform(-55.0, 55.0),
                                                r.uniform(-150.0, -40.0), solta, (c.r, c.g, c.b),
                                                r.random()))

    def update(self, dt):
        self.t += dt
        for p in self.particulas:
            if self.t >= p.solta:
                p.update(dt)

    def draw(self, tela):
        t = self.t
        cam = Camera.get_instance()
        x, y = int(cam.transform_x(self.x)), int(cam.transform_y(self.y))
        if t < self.ESTALO:
            tela.blit(self.branco, (x, y))
            return
        if t < self.FALHA:
            k = (t - self.ESTALO) / (self.FALHA - self.ESTALO)
            salto = int(t * 30)
            if salto % 2 == 0:
                abre = 3 + int(5 * k)
                tela.blit(self.magenta, (x - abre, y))
                tela.blit(self.ciano, (x + abre, y))
            w, h = self.sprite.get_size()
            sobe_quanto = 2.0 + 9.0 * k
            for i, fase in enumerate(self.faixas):
                dx = int(math.sin(fase + salto * 1.7) * sobe_quanto) if (i + salto) % 3 else 0
                tela.blit(self.sprite, (x + dx, y + i * 3), (0, i * 3, w, 3))
        for p in self.particulas:
            px, py = int(cam.transform_x(p.x)), int(cam.transform_y(p.y))
            if t < p.solta:
                if t >= self.FALHA:
                    tela.fill(p.cor, (px, py, 2, 2))
                continue
            vida = (t - p.solta) / p.vida_max
            if vida >= 1.0 or (vida > 0.6 and (int(t * 40) + int(p.sorte * 7)) % 2):
                continue
            tam = 1
            if vida < 0.35:
                tam = 3
            elif vida < 0.75:
                tam = 2
            cor = p.cor
            if vida >= 0.3:
                cor = self.CORES_RUIDO[int(p.sorte * 3 + t * 12) % 3]
            tela.fill(cor, (px, py, tam, tam))


class Vento:
    def __init__(self):
        r = random.Random(3)
        self.riscos = [(r.uniform(0, LARG_TELA + 200), r.uniform(0, ALT_TELA * 0.8),
                        r.uniform(0.7, 1.3), r.randint(24, 70)) for _ in range(26)]
        self.forca = 0.0

    def mostra_na_tela(self, tela, tempo, ta_ventando, cor, dt):
        alvo = 1.0 if ta_ventando else 0.0
        self.forca += (alvo - self.forca) * min(1.0, dt * 4.0)
        if self.forca < 0.05:
            return
        for x0, y, vel, comp in self.riscos:
            x = (x0 - tempo * 900 * vel) % (LARG_TELA + 200) - 100
            tela.fill(cor, (int(x), int(y), int(comp * self.forca), 2))


AR = {
    "bosque": (28, (120, 196, 104), (214, 255, 150), 5.0, -3.0, 26.0),
    "dunas": (40, (236, 204, 150), (255, 244, 214), -46.0, 6.0, 8.0),
    "ilhas": (46, (255, 206, 170), (255, 240, 220), -26.0, -6.0, 10.0),
    "geleira": (48, (196, 216, 255), (255, 255, 255), -16.0, 34.0, 18.0),
    "eclipse": (30, (190, 80, 60), (230, 130, 90), -5.0, -10.0, 8.0),
}
FAIXA_AR = {"bosque": (0.34, 0.9), "dunas": (0.48, 0.97)}
FAIXA_AR_DO_ATO = {"dunas": (0.40, 1.0)}
VAGUEIA_AR = {"bosque": 13.0}
HALO_AR = {"bosque": (46, 92, 58)}


AR_DO_ATO = {
    "bosque": {2: (34, (74, 120, 88), (150, 200, 120), -34.0, 44.0, 30.0),
               3: (30, (150, 255, 200), (226, 255, 240), 6.0, -16.0, 26.0)},
    "dunas": {2: (70, (226, 180, 120), (250, 224, 170), -130.0, 12.0, 10.0),
              3: (30, (120, 232, 214), (226, 255, 248), -10.0, -16.0, 22.0)},
    "ilhas": {2: (34, (150, 226, 255), (240, 250, 255), -12.0, -8.0, 18.0),
              3: (40, (255, 214, 150), (255, 244, 214), -60.0, 14.0, 14.0)},
    "geleira": {2: (90, (206, 222, 255), (255, 255, 255), -170.0, 60.0, 8.0),
                3: (34, (110, 255, 214), (226, 255, 246), -6.0, -20.0, 22.0)},
    "eclipse": {2: (60, (255, 128, 96), (255, 220, 150), -16.0, -64.0, 12.0),
                3: (40, (150, 160, 220), (226, 230, 255), -8.0, 26.0, 16.0)},
}


class Argola(Particle):
    idade = 0.0

    def update(self, dt):
        self.idade += dt

    def esta_viva(self):
        return self.idade < self.vida_max

    def draw(self, tela, x, y):
        k = self.idade / self.vida_max
        raio = int(14 + 86 * (1.0 - (1.0 - k) ** 2))
        alto = max(6, raio // 3)
        esp = 2
        if k < 0.35:
            esp = 4
        elif k < 0.7:
            esp = 3
        r = pygame.Rect(int(x) - raio, int(y) - alto // 2, raio * 2, alto)
        cor = self.cor
        if k < 0.2:
            cor = (255, 255, 255)
        pygame.draw.ellipse(tela, cor, r, esp)
        if k < 0.6:
            pygame.draw.ellipse(tela, self.cor, r.inflate(-raio, -alto // 2), 2)


class ArgolasDoEco(SoltaParticula):
    QUANTO_DURA = 0.42

    def solta_aqui(self, x, y, cor):
        self.set_pos(x, y)
        self.cor = cor
        self.explodir(1)

    def nova(self, i):
        return Argola(self.x, self.y, 0.0, 0.0, self.QUANTO_DURA, self.cor, 100)


class Ar(SoltaParticula):
    def __init__(self, cores_da_fase, jeito_do_ar=None):
        super().__init__(cores_da_fase.nome + str(jeito_do_ar))
        if jeito_do_ar:
            self.jeito_do_ar = jeito_do_ar
            self.faixa = FAIXA_AR_DO_ATO.get(cores_da_fase.nome, (0.0, 1.0))
            self.quanto_vagueia = 0.0
            self.halo = None
        else:
            self.jeito_do_ar = AR[cores_da_fase.nome]
            self.faixa = FAIXA_AR.get(cores_da_fase.nome, (0.0, 1.0))
            self.quanto_vagueia = VAGUEIA_AR.get(cores_da_fase.nome, 0.0)
            self.halo = HALO_AR.get(cores_da_fase.nome)
        self.explodir(self.jeito_do_ar[0])

    def nova(self, i):
        r = self.numero_sorteado
        _, cor, _, vx, vy, _ = self.jeito_do_ar
        x, y = r.uniform(0, LARG_TELA), r.uniform(0, ALT_TELA)
        fase, vel = r.uniform(0, math.tau), r.uniform(0.6, 1.4)
        tam = 3 if r.random() < 0.3 else 2
        p = Particle(x, y, vx * vel, vy * vel, math.inf, cor, tam)
        p.fase = fase
        return p

    def draw(self, tela, cam, tempo):
        _, cor, cor_clara, _, _, balanco = self.jeito_do_ar
        topo, alto = ALT_TELA * self.faixa[0], ALT_TELA * (self.faixa[1] - self.faixa[0])
        halo = self.halo
        for p in self.particulas:
            x = (p.x + p.vx * tempo - cam.x * 0.35 + math.sin(tempo * 0.9 + p.fase) * balanco) % LARG_TELA
            y = topo + (p.y + p.vy * tempo - cam.y * 0.35
                        + math.sin(tempo * 0.7 + p.fase * 2.0) * self.quanto_vagueia) % alto
            brilho = math.sin(tempo * 2.3 + p.fase * 3.0)
            if brilho < -0.55:
                continue
            tam, tom = 2, cor
            if brilho > 0.4:
                tam = p.tamanho
            if brilho > 0.6:
                tom = cor_clara
            if halo and brilho > 0.3:
                tela.fill(halo, (int(x) - 2, int(y), tam + 4, tam))
                tela.fill(halo, (int(x), int(y) - 2, tam, tam + 4))
            tela.fill(tom, (int(x), int(y), tam, tam))
