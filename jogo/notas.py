import math
import random

import pygame
from PPlay.particles import Particle

from . import arte, ui
from .config import QUADRADO, BRANCO, AMARELO, CONTORNO, LARG_TELA, ALT_TELA
from .particulas import SoltaParticula

CHEIA = ("..####", ".#####", "######", "#####.", ".###..")
VAZIA = ("..####", ".##..#", "#...##", "#..##.", ".###..")


def faz_grade(w, h):
    return [["."] * w for _ in range(h)]


def poe_no_fundo(g, x, y, desenho):
    for dy, linha in enumerate(desenho):
        for dx, ch in enumerate(linha):
            if ch == "#" and 0 <= y + dy < len(g) and 0 <= x + dx < len(g[0]):
                g[y + dy][x + dx] = "#"


def faz_haste(g, x, y0, y1):
    for y in range(y0, y1 + 1):
        g[y][x] = "#"


def faz_nota(ta_cheia=True, bandeira=False):
    g = faz_grade(9 if bandeira else 6, 12)
    poe_no_fundo(g, 0, 7, CHEIA if ta_cheia else VAZIA)
    faz_haste(g, 5, 0, 8)
    if bandeira:
        poe_no_fundo(g, 6, 1, ("#..", ".#.", "..#", "..#", ".#."))
    return g


def faz_colcheias():
    g = faz_grade(13, 12)
    poe_no_fundo(g, 0, 7, CHEIA)
    poe_no_fundo(g, 7, 7, CHEIA)
    faz_haste(g, 5, 0, 8)
    faz_haste(g, 12, 0, 8)
    for x in range(5, 13):
        g[0][x] = g[1][x] = "#"
    return g


def faz_acorde():
    g = faz_grade(6, 17)
    for y in (4, 8, 12):
        poe_no_fundo(g, 0, y, CHEIA)
    faz_haste(g, 5, 0, 13)
    return g


DESENHO_DAS_NOTAS = {
    "seminima": faz_nota(),
    "minima": faz_nota(ta_cheia=False),
    "colcheia": faz_nota(bandeira=True),
    "colcheias": faz_colcheias(),
    "acorde": faz_acorde(),
    "semibreve": (".####.", "##..##", "#....#", "##..##", ".####."),
    "sustenido": ("..#..#.", "..#..#.", "#######", "..#..#.", "..#..#.",
                  "#######", "..#..#.", "..#..#."),
    "bemol": ("#....", "#....", "#....", "#....", "#.##.", "##..#",
              "#...#", "#..#.", "#.#..", "##..."),
    "clave": (
        "....##...",
        "...#..#..",
        "...#..#..",
        "...#.#...",
        "...##....",
        "..##.....",
        ".#.#.....",
        "#..####..",
        "#.##...#.",
        "#.#.#...#",
        "#.#..#..#",
        ".#...#.#.",
        "..####...",
        ".....#...",
        ".....#...",
        ".##..#...",
        "#..#.#...",
        ".##.#....",
    ),
}

fases_prontas = {}


def simbolo(nome, cor, escala=3):
    chave = (nome, cor, escala)
    if chave not in fases_prontas:
        g = DESENHO_DAS_NOTAS[nome]
        s = pygame.Surface((len(g[0]), len(g)), pygame.SRCALPHA)
        for y, linha in enumerate(g):
            for x, ch in enumerate(linha):
                if ch == "#":
                    s.set_at((x, y), (*cor, 255))
        s = pygame.transform.scale_by(s, escala)
        fases_prontas[chave] = arte.faz_contorno(s, CONTORNO, max(2, escala - 1))
    return fases_prontas[chave]


def meio_transparente(img, alfa):
    if alfa >= 250:
        return img
    return arte.fantasma(img, max(16, int(alfa) // 16 * 16))


class Nota(Particle):
    idade = 0.0

    def __init__(self, x, y, vx, img, onda):
        super().__init__(x, y, vx, 0.0, NotasVoando.VIDA, None, img.get_width())
        self.img, self.onda = img, onda

    def update(self, dt):
        self.idade += dt
        self.vy = -(90 - 50 * self.idade)
        super().update(dt)

    def esta_viva(self):
        return self.idade < self.vida_max

    def draw(self, tela, x, y):
        entra = min(1.0, self.idade / 0.08)
        sai = max(0.0, 1 - max(0.0, self.idade - 0.5) / (self.vida_max - 0.5))
        balanco = math.sin(self.idade * 9 + self.onda) * 5
        r = self.img.get_rect(center=(int(x + balanco), int(y - 18 * entra)))
        tela.blit(meio_transparente(self.img, 255 * sai), r)


class NotasVoando(SoltaParticula):
    VIDA = 0.9

    def __init__(self, cor):
        super().__init__(3)
        self.cor = cor
        for nome in ("colcheia", "colcheias", "acorde"):
            simbolo(nome, cor, 3)
        simbolo("seminima", AMARELO, 3)
        simbolo("clave", AMARELO, 4)
        self.img = None

    def solta_aqui(self, x, y, perfeito, marco=False):
        if marco:
            self.img = simbolo("clave", AMARELO, 4)
        elif perfeito:
            nome = self.numero_sorteado.choice(("colcheia", "colcheias", "acorde", "colcheia"))
            self.img = simbolo(nome, self.cor, 3)
        else:
            self.img = simbolo("seminima", AMARELO, 3)
        self.set_pos(x, y)
        self.explodir(1)
        del self.particulas[:-8]

    def nova(self, i):
        r = self.numero_sorteado
        return Nota(self.x, self.y, r.uniform(-26, 26), self.img, r.uniform(0, 6.28))


ESPACO_PAUTA = 9
ALTURA_SINAIS = 6.4
ALFA_SINAIS = 176


class Partitura:
    def __init__(self, fase):
        self.fase = fase
        cores_da_fase = fase.cores_da_fase
        self.cor = cores_da_fase.destaque
        self.cor_da_pauta = tuple(int(c * 0.75 + 255 * 0.25) for c in cores_da_fase.destaque)
        self.placas = []
        self.na_largada()
        for (nome, _), x in zip(fase.partes_da_musica, fase.x_das_partes):
            if nome != "introducao":
                self.letra_da_parte(x, nome)
        for d in fase.enfeites:
            if d.tipo == "portal":
                self.barra_final(d.x)
        cor = tuple(int(c * 0.55) for c in self.cor)
        self.ceu = []
        for nome in ("seminima", "colcheia", "colcheias", "minima", "sustenido", "bemol", "semibreve"):
            self.ceu.append(simbolo(nome, cor, 3))

    def risca_chao(self, x):
        c = int(x // QUADRADO)
        return self.fase.chao_por_coluna.get(c, self.fase.altura_do_chao(c)) * QUADRADO

    def faz_pauta(self, largura, barras=(), final=False):
        h = ESPACO_PAUTA * 4
        s = pygame.Surface((largura + 8, h + 8), pygame.SRCALPHA)
        for k in range(5):
            y = 4 + k * ESPACO_PAUTA
            s.fill((*CONTORNO, 255), (0, y - 1, largura + 8, 4))
            s.fill((*self.cor_da_pauta, 255), (2, y, largura + 4, 2))
        for x, grossa in barras:
            w = 7 if grossa else 3
            s.fill((*CONTORNO, 255), (x - 2, 2, w + 4, h + 4))
            s.fill((*self.cor_da_pauta, 255), (x, 4, w, h))
        return s

    def na_largada(self):
        largura = int(5.5 * QUADRADO)
        s = pygame.Surface((largura + 8, 150), pygame.SRCALPHA)
        pauta = self.faz_pauta(largura)
        topo = 70
        s.blit(pauta, (0, topo))
        clave = simbolo("clave", self.cor, 3)
        s.blit(clave, clave.get_rect(midleft=(10, topo + 4 + ESPACO_PAUTA * 2 + 4)))
        for k, y in enumerate((topo + 4 + ESPACO_PAUTA, topo + 4 + ESPACO_PAUTA * 3)):
            n = ui.texto("4", 20, self.cor, CONTORNO)
            s.blit(n, n.get_rect(center=(66, y)))
        for x, nome, linha in ((112, "seminima", 3), (160, "colcheia", 2), (208, "colcheias", 1)):
            img = simbolo(nome, self.cor, 3)
            s.blit(img, img.get_rect(bottomleft=(x, topo + 4 + ESPACO_PAUTA * linha + 10)))
        notinha = simbolo("seminima", BRANCO, 2)
        s.blit(notinha, (12, 8))
        texto_bpm = ui.texto(f"= {self.fase.bpm_da_musica:.0f}", 20, BRANCO, CONTORNO)
        s.blit(texto_bpm, texto_bpm.get_rect(midleft=(12 + notinha.get_width() + 8,
                                                      8 + notinha.get_height() // 2 + 4)))
        self.placas.append((-7.4 * QUADRADO, self.risca_chao(0) - 4.4 * QUADRADO - topo, s))

    def letra_da_parte(self, x, letra):
        largura = 4 * QUADRADO
        meio = largura // 2
        s = pygame.Surface((largura + 8, 110), pygame.SRCALPHA)
        topo = 60
        s.blit(self.faz_pauta(largura, barras=((meio - 6, False), (meio + 2, False))), (0, topo))
        txt = ui.texto(letra, 26, BRANCO, CONTORNO)
        caixa = pygame.Rect(0, 0, max(42, txt.get_width() + 18), 42)
        caixa.midbottom = (meio, topo - 8)
        pygame.draw.rect(s, CONTORNO, caixa.inflate(6, 6))
        pygame.draw.rect(s, self.cor, caixa.inflate(2, 2))
        pygame.draw.rect(s, (24, 22, 40), caixa.inflate(-4, -4))
        s.blit(txt, txt.get_rect(center=caixa.center))
        self.placas.append((x - meio, self.risca_chao(x) - ALTURA_SINAIS * QUADRADO - topo, s))

    def barra_final(self, x):
        largura = 4 * QUADRADO
        s = self.faz_pauta(largura, barras=((largura - 14, False), (largura - 4, True)))
        self.placas.append((x - largura - QUADRADO, self.risca_chao(x) - ALTURA_SINAIS * QUADRADO, s))

    def mostra_na_tela(self, tela, cam, t):
        longe = cam.x * 0.5
        espaco = 420
        for k in range(int(longe // espaco) - 1, int((longe + LARG_TELA) // espaco) + 2):
            dado = random.Random(k * 7919)
            img = self.ceu[dado.randrange(len(self.ceu))]
            x = k * espaco + dado.uniform(0, 200) - longe
            y = 90 + dado.uniform(0, 170) + math.sin(t * 0.9 + k) * 8
            tela.blit(meio_transparente(img, 120), (int(x), int(y)))
        for x, y, s in self.placas:
            sx, sy = cam.transform_x(x), cam.transform_y(y)
            if -s.get_width() < sx < LARG_TELA and -s.get_height() < sy < ALT_TELA:
                tela.blit(meio_transparente(s, ALFA_SINAIS), (int(sx), int(sy)))
