"""
A musica escrita no mundo: os sinais da partitura em pixel art.

    Revoada     as notas que sobem do Leo a cada acerto: no PERFEITO uma
                colcheia, um par ligado ou um acorde, na cor do mundo; no BOM
                uma seminima; no marco da sequencia, uma clave de sol.
    Partitura   o que esta escrito no proprio mapa: na largada, a pauta com a
                clave de sol, o compasso 4/4 e o andamento (seminima = BPM);
                em cada parte da musica, a letra de ensaio (A, B, A') sobre a
                barra dupla; antes do portal, a barra final. E, no ceu, notas
                soltas flutuando devagar, longe, atras de tudo.

Nada disso e obstaculo nem colide: os sinais ficam altos, acima de qualquer
pulo comum, translucidos e nunca na cor de perigo -- a regra de leitura do
jogo (o que fere e pontudo e na cor de perigo) continua valendo.

Cada sinal e um desenho de pixels logicos (abaixo, '#' e pixel aceso),
ampliado sem suavizar e com o contorno escuro do HUD.
"""

import math
import random

import pygame

from . import arte, ui
from .config import TILE, BRANCO, AMARELO, CONTORNO, LARGURA, ALTURA

# as cabecas de nota: cheia (seminima, colcheia) e vazada (minima), inclinadas
CHEIA = ("..####", ".#####", "######", "#####.", ".###..")
VAZIA = ("..####", ".##..#", "#...##", "#..##.", ".###..")


def _grade(w, h):
    return [["."] * w for _ in range(h)]


def _por(g, x, y, desenho):
    for dy, linha in enumerate(desenho):
        for dx, ch in enumerate(linha):
            if ch == "#" and 0 <= y + dy < len(g) and 0 <= x + dx < len(g[0]):
                g[y + dy][x + dx] = "#"


def _haste(g, x, y0, y1):
    for y in range(y0, y1 + 1):
        g[y][x] = "#"


def _nota(cheia=True, bandeira=False):
    g = _grade(9 if bandeira else 6, 12)
    _por(g, 0, 7, CHEIA if cheia else VAZIA)
    _haste(g, 5, 0, 8)
    if bandeira:
        _por(g, 6, 1, ("#..", ".#.", "..#", "..#", ".#."))
    return g


def _colcheias():
    g = _grade(13, 12)
    _por(g, 0, 7, CHEIA)
    _por(g, 7, 7, CHEIA)
    _haste(g, 5, 0, 8)
    _haste(g, 12, 0, 8)
    for x in range(5, 13):
        g[0][x] = g[1][x] = "#"
    return g


def _acorde():
    g = _grade(6, 17)
    for y in (4, 8, 12):
        _por(g, 0, y, CHEIA)
    _haste(g, 5, 0, 13)
    return g


DESENHOS = {
    "seminima": _nota(),
    "minima": _nota(cheia=False),
    "colcheia": _nota(bandeira=True),
    "colcheias": _colcheias(),
    "acorde": _acorde(),
    "semibreve": [list(s) for s in (".####.", "##..##", "#....#", "##..##", ".####.")],
    "sustenido": [list(s) for s in ("..#..#.", "..#..#.", "#######", "..#..#.", "..#..#.",
                                    "#######", "..#..#.", "..#..#.")],
    "bemol": [list(s) for s in ("#....", "#....", "#....", "#....", "#.##.", "##..#",
                                "#...#", "#..#.", "#.#..", "##...")],
    "clave": [list(s) for s in (
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
    )],
}

_cache = {}


def glifo(nome, cor, escala=3):
    """O sinal `nome` na cor `cor`, ampliado `escala` vezes, com o contorno do HUD (em cache)."""
    chave = (nome, cor, escala)
    if chave not in _cache:
        g = DESENHOS[nome]
        s = pygame.Surface((len(g[0]), len(g)), pygame.SRCALPHA)
        for y, linha in enumerate(g):
            for x, ch in enumerate(linha):
                if ch == "#":
                    s.set_at((x, y), (*cor, 255))
        s = pygame.transform.scale_by(s, escala)
        _cache[chave] = arte.contornar(s, CONTORNO, max(2, escala - 1))
    return _cache[chave]


def _translucido(img, alfa):
    return arte.fantasma(img, max(16, int(alfa) // 16 * 16)) if alfa < 250 else img


# ------------------------------------------------------------------ acertos
class Revoada:
    """As notas que sobem do Leo a cada acerto e somem em menos de um segundo."""

    VIDA = 0.9

    def __init__(self, cor):
        self.cor = cor
        self.notas = []        # [x, y, vx, idade, img, fase da onda]
        self.rnd = random.Random(3)
        # monta os sinais ja na largada: o primeiro acerto nao monta nada na hora
        for nome in ("colcheia", "colcheias", "acorde"):
            glifo(nome, cor, 3)
        glifo("seminima", AMARELO, 3)
        glifo("clave", AMARELO, 4)

    def soltar(self, x, y, perfeito, marco=False):
        if marco:
            img = glifo("clave", AMARELO, 4)
        elif perfeito:
            img = glifo(self.rnd.choice(("colcheia", "colcheias", "acorde", "colcheia")), self.cor, 3)
        else:
            img = glifo("seminima", AMARELO, 3)
        vx = self.rnd.uniform(-26, 26)
        self.notas.append([x, y, vx, 0.0, img, self.rnd.uniform(0, 6.28)])
        del self.notas[:-8]

    def atualizar(self, dt):
        for n in self.notas:
            n[3] += dt
            n[0] += n[2] * dt
            n[1] -= (90 - 50 * n[3]) * dt          # sobe e vai perdendo o folego
        self.notas = [n for n in self.notas if n[3] < self.VIDA]

    def desenhar(self, tela, cam_x, cam_y):
        for x, y, _, idade, img, onda in self.notas:
            entra = min(1.0, idade / 0.08)
            sai = max(0.0, 1 - max(0.0, idade - 0.5) / (self.VIDA - 0.5))
            balanco = math.sin(idade * 9 + onda) * 5
            r = img.get_rect(center=(int(x - cam_x + balanco), int(y - cam_y - 18 * entra)))
            tela.blit(_translucido(img, 255 * sai), r)


# ------------------------------------------------------------------- o mapa
ESPACO_PAUTA = 9            # px entre as linhas da pauta
ALTURA_SINAIS = 6.4         # tiles acima do chao: acima do alto de qualquer pulo comum
ALFA_SINAIS = 176


class Partitura:
    """Os sinais escritos no mapa e as notas soltas no ceu de uma fase."""

    def __init__(self, fase):
        self.fase = fase
        tema = fase.tema
        self.cor = tema.destaque
        self.cor_pauta = tuple(int(c * 0.75 + 255 * 0.25) for c in tema.destaque)
        self.placas = []          # [(x do mundo, y do mundo, superficie)]
        self._largada()
        nomes = {"A": "A", "B": "B", "A'": "A'"}
        for (nome, _), x in zip(fase.secoes, fase.secoes_x):
            if nome in nomes:
                self._ensaio(x, nomes[nome])
        portal = [d for d in fase.decos if d.tipo == "portal"]
        if portal:
            self._final(portal[0].x)
        # o ceu: sinais soltos, longe (andam a metade do que anda o mundo)
        self.ceu = [glifo(n, tuple(int(c * 0.55) for c in self.cor), 3)
                    for n in ("seminima", "colcheia", "colcheias", "minima", "sustenido", "bemol", "semibreve")]

    # o chao na coluna de x, para os sinais ficarem a mesma altura acima dele
    def _chao(self, x):
        c = int(x // TILE)
        return self.fase.chao_col.get(c, self.fase.nivel_chao(c)) * TILE

    def _pauta(self, largura, barras=(), final=False):
        """Um trecho de pauta: 5 linhas, e barras verticais nos x pedidos."""
        h = ESPACO_PAUTA * 4
        s = pygame.Surface((largura + 8, h + 8), pygame.SRCALPHA)
        for k in range(5):
            y = 4 + k * ESPACO_PAUTA
            s.fill((*CONTORNO, 255), (0, y - 1, largura + 8, 4))
            s.fill((*self.cor_pauta, 255), (2, y, largura + 4, 2))
        for x, grossa in barras:
            w = 7 if grossa else 3
            s.fill((*CONTORNO, 255), (x - 2, 2, w + 4, h + 4))
            s.fill((*self.cor_pauta, 255), (x, 4, w, h))
        return s

    def _largada(self):
        """
        A pauta da largada: clave de sol, 4/4, tres notas e o andamento em cima.
        Fica atras do Leo, a esquerda: no meio do alto da tela, na espera, esta
        o letreiro com o nome da fase.
        """
        largura = int(5.5 * TILE)
        s = pygame.Surface((largura + 8, 150), pygame.SRCALPHA)
        pauta = self._pauta(largura)
        topo = 70
        s.blit(pauta, (0, topo))
        clave = glifo("clave", self.cor, 3)
        s.blit(clave, clave.get_rect(midleft=(10, topo + 4 + ESPACO_PAUTA * 2 + 4)))
        for k, y in enumerate((topo + 4 + ESPACO_PAUTA, topo + 4 + ESPACO_PAUTA * 3)):
            n = ui.texto("4", 20, self.cor, CONTORNO)
            s.blit(n, n.get_rect(center=(66, y)))
        for x, nome, linha in ((112, "seminima", 3), (160, "colcheia", 2), (208, "colcheias", 1)):
            img = glifo(nome, self.cor, 3)
            # o pe da cabeca na linha (ou no espaco) pedido da pauta
            s.blit(img, img.get_rect(bottomleft=(x, topo + 4 + ESPACO_PAUTA * linha + 10)))
        marca = glifo("seminima", BRANCO, 2)
        s.blit(marca, (12, 8))
        bpm = ui.texto(f"= {self.fase.bpm:.0f}", 20, BRANCO, CONTORNO)
        s.blit(bpm, bpm.get_rect(midleft=(12 + marca.get_width() + 8, 8 + marca.get_height() // 2 + 4)))
        # atras de onde o Leo comeca (ele so corre para a frente): pode ficar
        # mais baixa que os outros sinais, abaixo do HUD e ao lado do letreiro
        self.placas.append((-7.4 * TILE, self._chao(0) - 4.4 * TILE - topo, s))

    def _ensaio(self, x, letra):
        """A letra de ensaio de uma parte da musica, numa caixa, sobre a barra dupla."""
        largura = 4 * TILE
        meio = largura // 2
        s = pygame.Surface((largura + 8, 110), pygame.SRCALPHA)
        topo = 60
        s.blit(self._pauta(largura, barras=((meio - 6, False), (meio + 2, False))), (0, topo))
        txt = ui.texto(letra, 26, BRANCO, CONTORNO)
        caixa = pygame.Rect(0, 0, max(42, txt.get_width() + 18), 42)
        caixa.midbottom = (meio, topo - 8)
        pygame.draw.rect(s, CONTORNO, caixa.inflate(6, 6))
        pygame.draw.rect(s, self.cor, caixa.inflate(2, 2))
        pygame.draw.rect(s, (24, 22, 40), caixa.inflate(-4, -4))
        s.blit(txt, txt.get_rect(center=caixa.center))
        self.placas.append((x - meio, self._chao(x) - ALTURA_SINAIS * TILE - topo, s))

    def _final(self, x):
        """A barra final antes do portal: uma fina e uma grossa, fechando a pauta."""
        largura = 4 * TILE
        s = self._pauta(largura, barras=((largura - 14, False), (largura - 4, True)))
        self.placas.append((x - largura - TILE, self._chao(x) - ALTURA_SINAIS * TILE, s))

    def desenhar(self, tela, cam_x, cam_y, t):
        # no ceu: um sinal a cada 420 px, em alturas e desenhos sorteados por posicao
        longe = cam_x * 0.5
        espaco = 420
        for k in range(int(longe // espaco) - 1, int((longe + LARGURA) // espaco) + 2):
            rnd = random.Random(k * 7919)
            img = self.ceu[rnd.randrange(len(self.ceu))]
            x = k * espaco + rnd.uniform(0, 200) - longe
            y = 90 + rnd.uniform(0, 170) + math.sin(t * 0.9 + k) * 8
            tela.blit(_translucido(img, 120), (int(x), int(y)))
        for x, y, s in self.placas:
            sx, sy = x - cam_x, y - cam_y
            if -s.get_width() < sx < LARGURA and -s.get_height() < sy < ALTURA:
                tela.blit(_translucido(s, ALFA_SINAIS), (int(sx), int(sy)))
