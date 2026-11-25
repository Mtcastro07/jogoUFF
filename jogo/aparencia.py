import math

import pygame

from . import arte
from .animacao import Animadinho
from .config import QUADRADO

ja_feitos = {}

CORES_DO_LUGAR = {
    "bosque": ((24, 44, 48), 0.40, ((22, 44, 40), (66, 86, 82), (94, 114, 106))),
    "dunas": ((214, 190, 150), 0.38, ((92, 50, 44), (140, 84, 58), (190, 128, 82))),
    "ilhas": ((118, 78, 112), 0.42, ((46, 33, 61), (69, 50, 87), (86, 66, 106))),
    "geleira": ((30, 48, 90), 0.40, ((22, 36, 70), (48, 78, 124), (120, 168, 214))),
    "eclipse": ((26, 12, 44), 0.45, ((14, 6, 26), (28, 14, 46), (40, 24, 64))),
}
ENFEITES_DO_ATO = {
    "bosque": ((3, 7, 1), (1, 2, 7), (4, 5, 6), (6, 1, 5, 2, 3)),
    "dunas": ((1, 3), (1, 2, 4), (5, 2, 6), (4, 3, 6, 1)),
    "ilhas": ((6, 2), (6, 3), (2, 3, 5), (5, 3, 2)),
    "geleira": ((1, 2), (1, 2, 3), (4, 5, 6), (1, 3, 4, 6)),
    "eclipse": ((1, 2), (1, 2, 5), (7, 5, 6), (6, 7, 5, 2)),
}
RAIO_AURA = 4
AFUNDA_O_ENFEITE = 6
AFUNDA_A_ARVORE = 14


def sombra(larg, alto, alfa):
    chave = ("sombra", larg, alto, alfa)
    if chave not in ja_feitos:
        s = pygame.Surface((larg, alto), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, alfa), (0, 0, larg, alto))
        ja_feitos[chave] = s
    return ja_feitos[chave]


def desenha_com_brilho(tela, figurinha, cor):
    x, y = figurinha.cantinho()
    tela.blit(arte.aura(figurinha.imagem_dele(), cor, RAIO_AURA), (x - RAIO_AURA, y - RAIO_AURA))
    figurinha.draw(tela)


def setinha_pra_cima(cor):
    chave = ("seta", cor)
    if chave not in ja_feitos:
        u = 3
        img = pygame.Surface((7 * u, 4 * u), pygame.SRCALPHA)
        for y in range(4):
            for x in (3 - y, 3 + y):
                img.fill(cor, (x * u, y * u, u, u))
                if y:
                    img.fill(cor, (x * u, (y - 1) * u, u, u))
        ja_feitos[chave] = img
    return ja_feitos[chave]


def anel(cor, raio, grosso):
    chave = ("anel", cor, raio, grosso)
    if chave not in ja_feitos:
        u = 3
        n = raio * 2 + 3
        img = pygame.Surface((n * u, n * u), pygame.SRCALPHA)
        c = n // 2
        for y in range(n):
            for x in range(n):
                d = math.hypot(x - c, y - c)
                if raio - grosso < d <= raio + 0.3:
                    img.fill(cor, (x * u, y * u, u, u))
                elif d <= raio - grosso - 2 and d <= 1.5:
                    img.fill((255, 255, 255), (x * u, y * u, u, u))
                elif d <= raio - grosso - 2:
                    img.fill(arte.clareia(cor, 0.5), (x * u, y * u, u, u))
        ja_feitos[chave] = arte.aura(img, cor, 4)
    return ja_feitos[chave]


def brilho(cor, alto, n_quadro):
    chave = ("brilho", cor, alto, n_quadro)
    if chave not in ja_feitos:
        ja_feitos[chave] = arte.aura(pinta_brilho(cor, alto, n_quadro), cor, 4)
    return ja_feitos[chave]


def pinta_brilho(cor, alto, n_quadro):
    u = 3
    img = pygame.Surface((11 * u, 11 * u), pygame.SRCALPHA)

    def ponto(x, y, c):
        img.fill(c, ((5 + x) * u, (5 + y) * u, u, u))

    raio = 3
    if n_quadro == 1:
        raio = 2
    for y in range(-raio, raio + 1):
        for x in range(-raio, raio + 1):
            d = abs(x) + abs(y)
            if d <= raio - 2:
                ponto(x, y, (255, 255, 255))
            elif d < raio:
                ponto(x, y, cor)
            elif d == raio:
                ponto(x, y, arte.escurece_cor(cor, 0.45))
    if n_quadro == 2:
        for x, y in ((0, -5), (0, 5), (-5, 0), (5, 0)):
            ponto(x, y, (255, 255, 255))
    if alto:
        for x, y in ((-4, -2), (4, -2), (-4, 2), (4, 2), (-2, -4), (2, -4), (-2, 4), (2, 4)):
            ponto(x, y, arte.clareia(cor, 0.35))
    return img


def eco(cor, alto):
    chave = ("eco", cor, alto)
    if chave not in ja_feitos:
        ja_feitos[chave] = Animadinho.feito_de_quadros([brilho(cor, alto, q) for q in range(3)])
    return ja_feitos[chave]


def arvore(d, cores_da_fase):
    cor, forca, _ = CORES_DO_LUGAR[cores_da_fase.nome]
    return arte.recuar(arte.arvore(d.qual_desenho), cor, forca)


def enfeite(d, cores_da_fase):
    atos = ENFEITES_DO_ATO[cores_da_fase.nome]
    quais = atos[min(d.ato, len(atos) - 1)]
    figurinha = arte.peca(f"enfeite_{quais[d.qual_desenho % len(quais)]}", cores_da_fase.nome)
    cor, forca, _ = CORES_DO_LUGAR[cores_da_fase.nome]
    return arte.recuada(figurinha, cor, forca * 0.85)


QUANDO_ACORDA = 7 * QUADRADO


def poca(cor, larg):
    chave = ("poca", cor, larg)
    if chave not in ja_feitos:
        s = pygame.Surface((larg, 22))
        for i, k in enumerate((0.10, 0.18, 0.28)):
            tom = (int(cor[0] * k), int(cor[1] * k), int(cor[2] * k))
            pygame.draw.ellipse(s, tom, (i * larg // 8, i * 3, larg - i * larg // 4, 22 - i * 6))
        ja_feitos[chave] = s
    return ja_feitos[chave]
