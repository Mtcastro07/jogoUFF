"""
Pinta, por codigo, o que paira no ar nos mundos depois das dunas: os
"nao pule" (o enxame de cada mundo) e os "so um toque" (o pingente de cada
mundo), que jogo/fases.py poe nas batidas vazias e nos saltos em sequencia
para que segurar o botao nao baste.

    ./.venv/bin/python ferramentas/geradores/pintar_ares.py

    ilhas     revoada: andorinhas de ruido   cristais: pendurados de uma laje de pedra
    geleira   morcegos de gelo               (o pingente e o de pintar_geleira.py)
    eclipse   morcegos de brasa              espetos: a grade levadica da muralha

A regra de leitura de sempre: o que fere e pontudo e na cor de perigo do mundo.
Os enxames tem o tamanho do das dunas (24x62 pixels logicos, 4 quadros) e os
pingentes o da geleira (48x64): a ponta de baixo e o pe da caixa de colisao.
"""

import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: F401  (o pintar_arte inicia o pygame)

from pintar_arte import C, mist, salvar

# as rampas de perigo de cada mundo (do escuro ao aceso), tiradas dos cacos
PERIGO = {
    "ilhas": ((148, 47, 75), (199, 75, 96), (228, 96, 112), (255, 200, 188)),
    "geleira": ((84, 22, 120), (156, 52, 214), (214, 110, 255), (246, 206, 255)),
    "eclipse": ((120, 40, 36), (230, 100, 50), (255, 140, 60), (255, 214, 140)),
}
CONTORNO = {"ilhas": (58, 26, 58), "geleira": (36, 10, 58), "eclipse": (14, 6, 20)}
# a pedra de onde pendem os pingentes
PEDRA = {
    "ilhas": ((70, 52, 84), (110, 84, 122), (150, 118, 160), (196, 168, 204)),
    "eclipse": ((40, 22, 46), (70, 42, 78), (104, 66, 112), (140, 98, 140)),
}
# onde ficam os tres bichos da coluna, e quanto cada um sobe ou desce por quadro
LUGARES = ((12, 10), (11, 31), (12, 52))
OSCILA = (0, 1, 0, -1)


# =================================================================== ENXAMES
def andorinha(c, cx, cy, k, mundo):
    """Uma andorinha de ruido: asas em foice, pontudas, e a cauda em forquilha."""
    e, m, cl, luz = PERIGO[mundo]
    abre = (-4, -1, 3, 0)[k % 4]                  # as asas: para cima, abertas, para baixo
    for lado in (-1, 1):
        for d in range(1, 11):
            t = d / 10.0
            y = cy + abre * t - 1.5 * math.sin(t * math.pi)
            esp = 2 if d < 5 else (1 if d < 9 else 0)
            for h in range(-esp, 1):
                c.p(cx + lado * d, y + h, cl if h == -esp else (m if h < 0 else e))
        c.p(cx + lado * 10, cy + abre, luz)       # a ponta da asa: o que fere
    # o corpo: um fuso, e a cauda aberta em forquilha
    for y in range(-3, 4):
        w = 2 if abs(y) < 2 else (1 if abs(y) < 3 else 0)
        c.r(cx - w, cy + y, cx + w, cy + y, m if y < 1 else e)
        c.p(cx + w, cy + y, cl)
    c.p(cx, cy - 2, luz)
    c.p(cx - 1, cy + 4, e); c.p(cx - 2, cy + 5, e); c.p(cx - 2, cy + 6, cl)
    c.p(cx + 1, cy + 4, e); c.p(cx + 2, cy + 5, e); c.p(cx + 2, cy + 6, cl)
    c.p(cx, cy - 4, e); c.p(cx, cy - 5, cl)       # o bico


def morcego(c, cx, cy, k, mundo):
    """Um morcego: asas de membrana com as pontas em garra, e duas orelhas."""
    e, m, cl, luz = PERIGO[mundo]
    abre = (-5, -2, 3, 0)[k % 4]
    for lado in (-1, 1):
        for d in range(2, 11):
            t = d / 10.0
            topo = cy - 1 + abre * t
            # a membrana recortada: tres dedos, um vale entre eles
            fundo = topo + 1 + int(round(3 * abs(math.sin(t * math.pi * 1.5))))
            for y in range(int(topo), int(fundo) + 1):
                c.p(cx + lado * d, y, e if y > topo + 1 else m)
            c.p(cx + lado * d, topo, cl)
        c.p(cx + lado * 11, cy - 1 + abre, luz)   # a garra da ponta
    # o corpo, as orelhas e os olhos acesos
    c.r(cx - 2, cy - 2, cx + 2, cy + 3, m)
    c.r(cx - 1, cy + 4, cx + 1, cy + 4, e)
    c.p(cx - 2, cy - 3, cl); c.p(cx - 2, cy - 4, luz)
    c.p(cx + 2, cy - 3, cl); c.p(cx + 2, cy - 4, luz)
    c.p(cx - 1, cy - 1, luz); c.p(cx + 1, cy - 1, luz)


def enxame(mundo, bicho):
    quadros = []
    e, m, cl, luz = PERIGO[mundo]
    for k in range(4):
        c = C(24, 62)
        for n, (x, y) in enumerate(LUGARES):
            bicho(c, x + (n % 2), y + OSCILA[(k + n) % 4], k + n, mundo)
        c.contorno(CONTORNO[mundo])
        # o ruido entre eles: liga os tres num bando so
        for n, (x, y) in enumerate(((16, 20), (7, 22), (15, 42), (8, 41))):
            if (n + k) % 2 == 0:
                c.p(x + (k % 2), y, (*cl, 200))
        quadros.append(c)
    salvar(f"jogo/{mundo}", "enxame", quadros)


# ================================================================= PINGENTES
def laje(c, mundo, fundo_de):
    """A pedra suspensa: o topo claro, o corpo e o fundo irregular de onde as pontas pendem."""
    e, m, cl, luz = PEDRA[mundo]
    for x in range(3, 45):
        fundo = fundo_de(x)
        for y in range(4, fundo):
            cor = cl if y < 7 else (m if x < 34 else cl)
            if y == fundo - 1:
                cor = e
            c.p(x, y, cor)
        c.p(x, 4, luz if x % 5 else cl)
    for x, y in ((10, 8), (21, 9), (30, 7), (38, 9)):
        c.p(x, y, e)                                # as fissuras da pedra


def ponta(c, mundo, cx, raiz, fim, larg):
    """Uma ponta pendurada, afinando ate o pe; a luz do lado direito."""
    e, m, cl, luz = PERIGO[mundo]
    for y in range(raiz, fim + 1):
        t = (y - raiz) / max(1, fim - raiz)
        w = max(0, int(round(larg * (1 - t) ** 0.9)))
        for x in range(-w, w + 1):
            c.p(cx + x, y, e if x < -w * 0.3 else (cl if x > w * 0.3 else m))
        if w >= 1:
            c.p(cx + w, y, luz if t < 0.6 else cl)
    c.p(cx, fim, luz)


def cristais(k):
    """Ilhas: uma laje de pedra flutuante com os cristais rubros pendurados por baixo."""
    c = C(48, 64)
    laje(c, "ilhas", lambda x: 13 + int(round(math.sin((x - 3) / 41.0 * math.pi) * 3)))
    ponta(c, "ilhas", 24, 13, 63, 5)
    ponta(c, "ilhas", 13, 13, 44, 4)
    ponta(c, "ilhas", 35, 13, 49, 4)
    ponta(c, "ilhas", 7, 12, 28, 2)
    ponta(c, "ilhas", 41, 12, 32, 2)
    y = 20 + k * 10                                    # o brilho escorrendo pelo cristal do meio
    c.p(25, y, (255, 255, 255)); c.p(25, y + 1, PERIGO["ilhas"][3])
    c.contorno(CONTORNO["ilhas"])
    c.halo(24, 60, 6, PERIGO["ilhas"][1], 80)
    return c


def espetos(k):
    """Cidadela: a grade levadica descida pela metade -- barras de ferro com as pontas em brasa."""
    e, m, cl, luz = PERIGO["eclipse"]
    ferro = ((30, 22, 40), (58, 46, 72), (92, 78, 108))
    c = C(48, 64)
    laje(c, "eclipse", lambda x: 12)
    # as barras: ferro escuro, a ponta aquecida ate a brasa (o que fere)
    for n, (cx, fim) in enumerate(((8, 40), (16, 52), (24, 63), (32, 52), (40, 40))):
        for y in range(12, fim + 1):
            t = (y - 12) / max(1, fim - 12)
            if t < 0.55:
                cores = ferro
            else:
                q = (t - 0.55) / 0.45
                cores = (mist(ferro[0], e, q), mist(ferro[1], m, q), mist(ferro[2], cl, q))
            w = 2 if t < 0.82 else (1 if t < 0.94 else 0)
            for x in range(-w, w + 1):
                c.p(cx + x, y, cores[0] if x < 0 else (cores[2] if x > 0 else cores[1]))
        c.p(cx, fim, luz)
        # a brasa pulsa: a ponta acende em quadros alternados
        if (k + n) % 2 == 0:
            c.p(cx, fim - 1, luz)
    # as travessas que prendem as barras
    for y in (18, 28):
        c.r(5, y, 43, y, ferro[1])
        c.r(5, y + 1, 43, y + 1, ferro[0])
    c.contorno(CONTORNO["eclipse"])
    c.halo(24, 60, 6, m, 80 + 30 * (k % 2))
    return c


if __name__ == "__main__":
    print("enxames:")
    enxame("ilhas", andorinha)
    enxame("geleira", morcego)
    enxame("eclipse", morcego)
    print("pingentes:")
    salvar("jogo/ilhas", "pingente", [cristais(k) for k in range(4)])
    salvar("jogo/eclipse", "pingente", [espetos(k) for k in range(4)])
