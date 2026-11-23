"""
Pinta, por codigo, TODA a arte da Geleira da Aurora (o mundo entre as ilhas e
a cidadela): perigos, pingente, blocos, enfeites, paisagem, lua, emblema e moldura.

    ./.venv/bin/python ferramentas/geradores/pintar_geleira.py

Usa a telinha de pixels logicos de ferramentas/pintar_arte.py. A regra do
mundo: so o perigo e VIOLETA (o cristal de ruido) e pontudo para cima ou para
baixo; o gelo de verdade e azul e branco, e o que brilha sem ferir e o verde da
aurora. A luz vem da lua, a direita.
"""

import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
sys.path.insert(0, AQUI)

import pygame

import pintar_arte as pa
import pintar_dunas as pd
from pintar_arte import C, L, mist, salvar

FASE = "geleira"
UI = os.path.join(pa.RAIZ, "assets", "art", "ui")

# o violeta do perigo, do escuro ao aceso
VIOLETA = ((84, 22, 120), (156, 52, 214), (214, 110, 255), (246, 206, 255))
CONT_PERIGO = (36, 10, 58)
# neve, gelo e pedra
NEVE = ((150, 180, 224), (200, 222, 248), (232, 244, 255), (255, 255, 255))
GELO = ((44, 78, 132), (76, 128, 188), (130, 190, 236), (200, 240, 255))
PEDRA = ((40, 46, 70), (66, 74, 100), (98, 108, 136), (140, 152, 180))
MADEIRA = ((54, 38, 44), (90, 62, 58), (126, 90, 74), (160, 120, 92))
AURORA = ((30, 120, 110), (60, 200, 170), (110, 255, 214), (220, 255, 246))
PINHO = ((16, 40, 52), (24, 60, 70), (40, 86, 92), (70, 120, 120))
CONT = (14, 18, 38)


# ================================================================== PERIGOS
def cristal_de_ruido(c, cx, uw):
    """O cristal de ruido: uma lasca alta e duas baixas, brotando de um monte de neve."""
    e, m, cl, luz = VIOLETA
    a = {24: 4, 12: 2, 8: 1}[uw]
    if uw >= 12:
        lado = uw * 0.28
        pa._lasca(c, cx - lado, 13 if uw == 24 else 15, max(1, a - 2), 21, e, m, cl, luz, -1)
        pa._lasca(c, cx + lado, 11 if uw == 24 else 14, max(1, a - 2), 21, e, m, cl, luz, 1)
    pa._lasca(c, cx, 2, a, 21, e, m, cl, luz)
    # o monte de neve no pe
    mm = min(uw // 2 - 1, a + (5 if uw == 24 else 2 if uw == 12 else 1))
    for x in range(int(cx - mm), int(cx + mm) + 1):
        alto = 2 if abs(x - cx) < mm * 0.6 else 1
        c.r(x, 23 - alto, x, 23, NEVE[1] if x < cx else NEVE[2])
        c.p(x, 23 - alto, NEVE[3])


def aparar():
    """Nenhuma variante passa do triangulo do cristal base (folga de 2 px de cada lado)."""
    for q in (1, 2, 3):
        uw = 48 // q
        pasta = os.path.join(pa.OBJ, "jogo", FASE)
        for nome in sorted(os.listdir(pasta)):
            if not nome.startswith(f"caco{q}v"):
                continue
            caminho = os.path.join(pasta, nome)
            img = pygame.image.load(caminho).convert_alpha()
            for x in range(img.get_width()):
                xx = x % 48
                cx = (xx // uw) * uw + uw / 2.0 - 0.5
                limite = 4 + abs(xx - cx) / (uw / 2.0 - 2.0) * 42
                for y in range(48):
                    if y < min(limite, 47) - 0.5 and y < 44 and img.get_at((x, y)).a > 128:
                        img.set_at((x, y), (0, 0, 0, 0))
            pygame.image.save(img, caminho)


def pintar_perigos():
    print("perigos:")
    for q in (1, 2, 3):
        c = C(L, L)
        uw = L // q
        for i in range(q):
            cristal_de_ruido(c, i * uw + uw // 2, uw)
        pd.dentro_do_molde(c, q)
        for i in range(q):                                   # a neve do pe volta depois do corte
            cx = i * uw + uw // 2
            mm = min(uw // 2 - 2, {24: 6, 12: 3, 8: 2}[uw])
            c.r(cx - mm, 23, cx + mm, 23, NEVE[2])
        c.contorno(CONT_PERIGO)
        salvar(f"jogo/{FASE}", f"caco{q}", c)
    # as lancas de gelo: haste de gelo, ponta de cristal de ruido, amarra de neve
    pa.perigo(FASE, 2, pa.faz_lancas((GELO[0], GELO[1], GELO[2]), (VIOLETA[0], VIOLETA[2], VIOLETA[3]),
                                     NEVE[2]), cont=CONT_PERIGO)
    # o espinheiro congelado: o mesmo galho das dunas, em violeta e neve
    pd.RUBI, pd.AREIA, pd.ESPINHO = VIOLETA, (NEVE[0], NEVE[2], NEVE[2], NEVE[3]), NEVE[3]
    pa.perigo(FASE, 3, pd.espinheiro, cont=CONT_PERIGO)
    aparar()
    # a chama fria: fogo-fatuo violeta num braseiro de gelo (anda fora da batida)
    pa.perigo(FASE, 4, pa.faz_chama(VIOLETA[1], VIOLETA[2], VIOLETA[3], (GELO[0], GELO[1], GELO[3]),
                                    NEVE[3]), quadros=4, cont=CONT_PERIGO, caber=True)
    aparar()


# ================================================================= PINGENTE
def pingente(k):
    """
    A laje de gelo flutuando com os cristais de ruido pendurados: o do meio
    desce ate o pe da caixa de colisao. Uma gota de luz escorre por eles.
    """
    e, m, cl, luz = VIOLETA
    c = C(48, 64)
    # a laje: neve por cima, gelo azul por baixo, o fundo irregular
    for x in range(3, 45):
        t = (x - 3) / 41.0
        fundo = 13 + int(round(math.sin(t * math.pi) * 3 + (1 if (x * 7) % 5 == 0 else 0)))
        for y in range(3, fundo):
            cor = GELO[1] if y > 7 else GELO[2]
            if x > 34:
                cor = GELO[2] if y > 7 else GELO[3]
            c.p(x, y, cor)
        c.p(x, fundo - 1, GELO[0])
        alto = 2 + int(1.2 * math.sin(x * 0.7))
        c.r(x, 4 - alto, x, 5, NEVE[2] if x < 34 else NEVE[3])
        c.p(x, 4 - alto, NEVE[3])
    for x, y in ((9, 9), (20, 10), (31, 8), (14, 7)):
        c.p(x, y, GELO[3])                                   # bolhas no gelo
    c.r(2, 4, 2, 9, NEVE[1]); c.r(45, 4, 45, 10, GELO[3])

    def gelo_ponta(cx, raiz, ponta, larg):
        for y in range(raiz, ponta + 1):
            t = (y - raiz) / max(1, ponta - raiz)
            w = max(0, int(round(larg * (1 - t) ** 0.9)))
            for x in range(-w, w + 1):
                cor = e if x < -w * 0.3 else (cl if x > w * 0.3 else m)
                c.p(cx + x, y, cor)
            if w >= 1:
                c.p(cx + w, y, luz if y < raiz + (ponta - raiz) * 0.6 else cl)
        c.p(cx, ponta, luz)

    gelo_ponta(24, 13, 63, 5)
    gelo_ponta(13, 13, 46, 4)
    gelo_ponta(35, 13, 50, 4)
    gelo_ponta(7, 12, 30, 2)
    gelo_ponta(41, 12, 34, 2)
    # a gota de luz escorrendo pelo cristal do meio
    y = 20 + k * 10
    c.p(25, y, (255, 255, 255)); c.p(25, y + 1, luz)
    c.contorno(CONT_PERIGO)
    c.halo(24, 60, 6, m, 80)
    return c


# =================================================================== BLOCOS
def bloco_gelo():
    """Um cubo de gelo: facetas azuis, a quina da lua acesa e a neve por cima."""
    e, m, cl, luz = GELO
    c = C(24, 24)
    c.r(0, 0, 23, 23, m)
    c.r(0, 2, 1, 23, e); c.r(0, 22, 23, 23, e); c.r(22, 0, 23, 23, cl)
    for i in range(3, 21):                                   # as facetas em diagonal
        c.p(i, 23 - i, cl); c.p(i + 1, 23 - i, mist(m, cl, 0.4))
    c.r(3, 3, 9, 3, luz); c.r(3, 3, 3, 8, luz)
    for x, y in ((15, 14), (6, 17), (18, 6), (11, 9)):
        c.p(x, y, GELO[3]); c.p(x + 1, y, mist(GELO[3], m, 0.5))
    for x in range(24):                                      # a neve por cima
        alto = 2 + (1 if (x * 5) % 7 < 3 else 0)
        c.r(x, 0, x, alto - 1, NEVE[2] if x < 16 else NEVE[3])
        c.p(x, alto, NEVE[0])
    return c


def pintar_blocos():
    print("blocos:")
    salvar(f"jogo/{FASE}", "bloco", bloco_gelo())
    salvar(f"jogo/{FASE}", "bloco_v2", pa.bloco_caixote((MADEIRA[0], MADEIRA[1], MADEIRA[2]),
                                                         (PEDRA[0], PEDRA[2], PEDRA[3]),
                                                         musgo=(NEVE[0], NEVE[2], NEVE[3])))
    salvar(f"jogo/{FASE}", "bloco_v3", pa.bloco_emblema((PEDRA[0], PEDRA[1], PEDRA[2]),
                                                       (AURORA[0], AURORA[1], AURORA[3]), AURORA[2]))


# ================================================================= ENFEITES
def lanterna(k):
    """A lanterna de gelo: um globo de gelo com a chama verde da aurora dentro."""
    c = C(16, 26)
    c.r(7, 15, 8, 25, PEDRA[1]); c.r(8, 15, 8, 25, PEDRA[3])
    c.r(4, 24, 11, 25, PEDRA[1]); c.r(4, 24, 11, 24, PEDRA[3])
    c.disco(7.5, 9, 5.6, GELO[2])
    c.disco(7.5, 9, 4.6, mist(GELO[1], AURORA[1], 0.35))
    alto = (4, 5, 4, 3)[k % 4]
    desvio = (0, 1, 0, -1)[k % 4]
    for y in range(11 - alto, 12):
        t = (11 - y) / alto
        larg = max(0, int(round(math.sin((1 - t) * math.pi * 0.85 + 0.25) * 2.2)))
        for x in range(-larg, larg + 1):
            c.p(7.5 + x + desvio * t, y, AURORA[2] if abs(x) < larg else AURORA[1])
    c.disco(7.5, 10, 1.0, AURORA[3])
    c.p(10, 6, NEVE[3]); c.p(10, 7, GELO[3])                  # o brilho do globo
    c.r(4, 3, 11, 3, NEVE[2]); c.r(5, 2, 10, 2, NEVE[3])      # a neve no alto
    c.contorno(CONT)
    c.halo(7.5, 9, 8, AURORA[2], 80)
    return c


def _pinheiro(c, cx, pe, alto, larg, pal=PINHO, neve=NEVE, tronco=MADEIRA):
    """Pinheiro em andares arredondados, cada andar com a neve por cima (redondo: pontudo e o perigo)."""
    c.r(cx - 1, pe - 3, cx + 1, pe, tronco[1]); c.p(cx + 1, pe - 1, tronco[2])
    andares = max(3, alto // 6)
    for n in range(andares):
        t = n / max(1, andares - 1)                          # 0 = o de baixo
        y0 = pe - 3 - int(n * (alto - 4) / andares)
        w = max(2, int(round(larg * (1 - t * 0.78))))
        for y in range(y0 - 5, y0 + 1):
            ww = int(round(w * (0.55 + 0.45 * (y - (y0 - 5)) / 5.0)))
            for x in range(-ww, ww + 1):
                cor = pal[0] if x < -ww * 0.4 else (pal[2] if x > ww * 0.35 else pal[1])
                c.p(cx + x, y, cor)
        for x in range(-w + 1, w):                           # a neve do andar
            yy = y0 - 5 + (1 if abs(x) > w * 0.6 else 0)
            c.p(cx + x, yy, neve[2] if x < w * 0.3 else neve[3])
            if abs(x) < w * 0.5:
                c.p(cx + x, yy + 1, neve[1])
    topo = pe - 3 - int((andares - 1) * (alto - 4) / andares) - 6
    c.disco(cx, topo, 1.2, neve[3])


def pinheirinho():
    c = C(22, 30)
    _pinheiro(c, 11, 29, 26, 9)
    c.r(3, 29, 19, 29, NEVE[2])
    c.contorno(CONT)
    return c


def boneco():
    """O boneco de neve da caravana: cachecol verde-aurora, galhos por bracos."""
    c = C(22, 28)
    c.disco(11, 21, 6.2, NEVE[2]); c.disco(12, 20, 4.5, NEVE[3])
    c.disco(11, 11, 4.4, NEVE[2]); c.disco(12, 10, 3.2, NEVE[3])
    c.disco(11, 4.5, 3.4, NEVE[2]); c.disco(11.8, 4, 2.2, NEVE[3])
    for x in range(7, 16):
        c.p(x, 22 + (1 if x < 9 or x > 13 else 0), NEVE[0])  # a sombra em baixo de cada bola
    c.p(10, 4, CONT); c.p(13, 4, CONT); c.r(14, 5, 16, 5, (240, 140, 80))   # olhos e nariz
    c.r(7, 8, 15, 8, AURORA[1]); c.r(13, 9, 14, 12, AURORA[1]); c.p(14, 12, AURORA[2])  # o cachecol
    c.p(11, 11, CONT); c.p(11, 13, CONT)
    for x, y in ((6, 10), (5, 9), (4, 8), (4, 7), (16, 10), (17, 9), (18, 9), (19, 8)):
        c.p(x, y, MADEIRA[1])
    c.contorno(CONT)
    return c


def marco(k):
    """Um marco de pedra com a runa da aurora acesa: respira devagar."""
    c = C(16, 28)
    for y in range(4, 27):
        w = 5 if y > 6 else 5 - (6 - y)
        c.r(8 - w, y, 7, y, PEDRA[1]); c.r(8, y, 8 + w - 1, y, PEDRA[2])
        c.p(8 - w, y, PEDRA[0])
    c.r(3, 3, 12, 4, NEVE[2]); c.r(4, 2, 11, 2, NEVE[3])
    luz = AURORA[2] if k else AURORA[1]
    for dx, dy in ((0, 0), (2, 0), (-1, 2), (3, 2), (-1, 4), (3, 4), (0, 6), (2, 6), (1, 3)):
        c.p(7 + dx, 11 + dy, luz)
    c.r(2, 26, 13, 27, NEVE[1]); c.r(3, 26, 12, 26, NEVE[2])
    c.contorno(CONT)
    if k:
        c.halo(8, 14, 7, AURORA[2], 70)
    return c


def treno():
    """Um treno de madeira esquecido, com a carga coberta de neve."""
    c = C(30, 16)
    c.r(3, 12, 27, 12, PEDRA[3]); c.r(25, 9, 25, 12, PEDRA[3]); c.p(26, 9, PEDRA[3]); c.p(27, 10, PEDRA[3])
    for x in (6, 13, 20):
        c.r(x, 10, x, 11, MADEIRA[1])
    c.r(4, 8, 24, 9, MADEIRA[2]); c.r(4, 9, 24, 9, MADEIRA[1])
    c.r(6, 4, 20, 7, MADEIRA[1]); c.r(6, 4, 20, 4, MADEIRA[3])          # a carga
    c.r(8, 5, 8, 7, MADEIRA[0]); c.r(14, 5, 14, 7, MADEIRA[0])
    for x in range(5, 22):
        alto = 1 + (1 if 8 < x < 18 else 0)
        c.r(x, 4 - alto, x, 3, NEVE[2] if x < 15 else NEVE[3])
    c.r(2, 13, 28, 15, NEVE[1]); c.r(2, 13, 28, 13, NEVE[2])
    c.contorno(CONT)
    return c


def iglu():
    c = C(30, 20)
    for x in range(2, 28):
        t = (x - 2) / 25.0
        topo = 19 - int(round(math.sin(t * math.pi) ** 0.7 * 17))
        for y in range(topo, 20):
            cor = NEVE[1] if x < 15 else NEVE[2]
            if (y - topo) % 4 == 3:
                cor = NEVE[0]                                # as fiadas de blocos
            elif ((x + (y // 4) * 3) % 6) == 0:
                cor = NEVE[0]
            c.p(x, y, cor)
        c.p(x, topo, NEVE[3])
    for y in range(12, 20):                                  # a porta, acesa por dentro
        w = min(3, y - 11)
        c.r(9 - w, y, 9 + w, y, (60, 50, 70))
    c.r(8, 16, 10, 19, (250, 200, 120)); c.p(9, 15, (255, 230, 170))
    c.contorno(CONT)
    c.halo(9, 17, 6, (255, 200, 120), 60)
    return c


def pintar_enfeites():
    print("enfeites:")
    salvar(f"jogo/{FASE}", "enfeite_1", [lanterna(k) for k in range(4)])
    salvar(f"jogo/{FASE}", "enfeite_2", pinheirinho())
    salvar(f"jogo/{FASE}", "enfeite_3", boneco())
    salvar(f"jogo/{FASE}", "enfeite_4", [marco(k) for k in range(2)])
    salvar(f"jogo/{FASE}", "enfeite_5", treno())
    salvar(f"jogo/{FASE}", "enfeite_6", iglu())


# ================================================================= PAISAGEM
# pecas do fundo, ja na escala do buffer (320x180): azuis da noite, mais
# apagadas quanto mais longe; a neve pega a lua pela direita
PINHO_LONGE = ((22, 36, 70), (30, 48, 86), (42, 62, 104), (60, 84, 126))
NEVE_LONGE = ((80, 104, 150), (120, 146, 190), (156, 180, 220), (190, 210, 240))
PINHO_PERTO = ((12, 26, 44), (18, 38, 58), (28, 54, 74), (46, 78, 96))
NEVE_PERTO = ((120, 150, 200), (170, 196, 232), (210, 228, 250), (240, 248, 255))


def pinheiros(w, h, lista, pal, neve):
    c = C(w, h)
    for cx, alto, larg in lista:
        _pinheiro(c, cx, h - 1, alto, larg, pal, neve, (pal[0], pal[1], pal[2]))
    return c


def agulha(pal):
    """Uma agulha de gelo distante, com a face da lua acesa."""
    e, m, cl, luz = pal
    c = C(14, 34)
    for y in range(34):
        t = y / 33.0
        w = 1 + int(round(t ** 0.8 * 6))
        c.r(7 - w, y, 6, y, m); c.r(7, y, 7 + w - 1, y, cl)
    c.r(7, 0, 7, 20, luz)
    return c


def cristal_gigante():
    """Um cristal de gelo enorme, de AZUL (nao violeta: ele nao fere), com a aurora refletida."""
    c = C(34, 46)
    for cx, topo, a, inc in ((10, 16, 4, -2), (24, 20, 3, 2), (17, 2, 6, 0)):
        pa._lasca(c, cx, topo, a, 45, GELO[0], GELO[1], GELO[2], GELO[3], inc)
    for y in range(8, 40, 3):
        c.p(18, y, AURORA[2])                                # o reflexo da aurora
    c.r(4, 44, 30, 45, NEVE_PERTO[1]); c.r(6, 43, 28, 43, NEVE_PERTO[2])
    return c


def cascata():
    """Um rochedo com a cachoeira congelada descendo em colunas de gelo."""
    c = C(48, 40)
    for x in range(48):
        t = x / 47.0
        topo = int(round(4 + 10 * abs(t - 0.45) ** 1.3 * 2 + (1 if (x * 3) % 5 == 0 else 0)))
        for y in range(topo, 40):
            c.p(x, y, PEDRA[1] if x < 24 else PEDRA[2])
            if (y + x // 3) % 7 == 0:
                c.p(x, y, PEDRA[0])
        c.r(x, topo, x, topo + 1, NEVE_PERTO[2] if x < 30 else NEVE_PERTO[3])
    for x in range(17, 31):                                   # a cachoeira de gelo
        topo = 8 + (x % 3)
        for y in range(topo, 38):
            c.p(x, y, GELO[2] if (x % 3) else GELO[3])
        c.p(x, 38, GELO[1]); c.p(x, 39, NEVE_PERTO[2])
    c.r(12, 37, 36, 39, NEVE_PERTO[1])
    return c


def arco_de_gelo():
    c = C(46, 30)
    for x in range(46):
        t = x / 45.0
        topo = int(round(9 - math.sin(t * math.pi) ** 0.6 * 8))
        vao = int(round(29 - math.sin(min(1.0, max(0.0, (t - 0.22) / 0.56)) * math.pi) ** 0.7 * 19))
        dentro = 0.22 < t < 0.78
        for y in range(topo, 30):
            if dentro and y > vao:
                continue
            c.p(x, y, GELO[1] if x < 23 else GELO[2])
            if (x * 7 + y * 13) % 41 == 0:
                c.p(x, y, GELO[3])                               # uma bolha aqui e ali
            if dentro and y == vao and x > 23:
                c.p(x, y, GELO[3])                               # a lua na borda de dentro
        c.r(x, topo, x, topo + 1, NEVE_PERTO[2] if x < 30 else NEVE_PERTO[3])
    return c


def lua(k):
    """A lua minguante: o disco claro mordido pela sombra; na batida ela incha um pouco."""
    c = C(44, 44)
    raio = (12, 13.5, 12.8)[k]
    for r, cor in ((raio + 5, (120, 160, 230, 40)), (raio + 3, (160, 200, 250, 70))):
        for y in range(44):
            for x in range(44):
                if (x - 21.5) ** 2 + (y - 21.5) ** 2 <= r * r:
                    c.s.set_at((x, y), cor)
    c.disco(21.5, 21.5, raio, (214, 232, 255))
    c.disco(22.5, 20.5, raio - 2, (236, 246, 255))
    for x, y, r in ((17, 18, 2.2), (24, 26, 1.6), (26, 15, 1.2)):
        c.disco(x, y, r, (196, 214, 244))
    # a parte apagada: o ceu aparece (transparente), e a lua vira um crescente
    # largo, virado para a direita -- nada a ver com o disco escuro do eclipse
    for y in range(44):
        for x in range(44):
            if (x - 12.0) ** 2 + (y - 19.0) ** 2 <= (raio - 0.5) ** 2:
                c.s.set_at((x, y), (0, 0, 0, 0))
    return c


def pintar_paisagem():
    print("paisagem:")
    p = f"cenario/{FASE}"
    salvar(p, "longe_1", pinheiros(16, 26, ((8, 24, 6),), PINHO_LONGE, NEVE_LONGE), 1)
    salvar(p, "longe_2", pinheiros(30, 22, ((7, 18, 5), (17, 21, 6), (25, 14, 4)), PINHO_LONGE, NEVE_LONGE), 1)
    salvar(p, "longe_3", agulha(((40, 70, 120), (70, 110, 160), (110, 156, 206), (180, 216, 246))), 1)
    salvar(p, "longe_4", pinheiros(22, 18, ((6, 15, 4), (15, 17, 5)), PINHO_LONGE, NEVE_LONGE), 1)
    salvar(p, "perto_1", pinheiros(26, 44, ((13, 42, 11),), PINHO_PERTO, NEVE_PERTO), 1)
    salvar(p, "perto_2", pinheiros(40, 40, ((12, 38, 10), (29, 28, 8)), PINHO_PERTO, NEVE_PERTO), 1)
    salvar(p, "perto_3", cristal_gigante(), 1)
    salvar(p, "perto_4", cascata(), 1)
    salvar(p, "perto_5", arco_de_gelo(), 1)
    salvar(p, "astro", [lua(k) for k in range(3)], 1)


# ======================================================================= UI
def emblema():
    """O emblema da carta: a ilha de gelo com o pinheiro e o cristal violeta, sob a aurora."""
    c = C(48, 48)
    for y in range(3, 40):
        for x in range(48):
            if (x - 23.5) ** 2 + (y - 21.5) ** 2 <= 19.5 ** 2:
                c.p(x, y, mist((8, 14, 40), (40, 70, 120), min(1.0, (y - 3) / 34.0)))
    for x in range(6, 42):                                   # a aurora no disco
        y = int(12 + 3 * math.sin(x * 0.3))
        for k in range(5):
            if (x - 23.5) ** 2 + (y - k - 21.5) ** 2 <= 19 ** 2:
                c.p(x, y - k, mist(AURORA[2], (60, 120, 220), k / 5.0))
    c.disco(34, 9, 3.2, (226, 240, 255)); c.disco(32.6, 8.4, 2.6, (40, 70, 120))
    for x in range(3, 45):                                   # a ilha de gelo
        t = (x - 3) / 41.0
        fundo = 30 + int(round(math.sin(t * math.pi) ** 0.55 * 15))
        for y in range(29, fundo):
            prof = (y - 29) / 16.0
            cor = (NEVE[1], GELO[2], GELO[1], GELO[0], (20, 34, 74))[min(4, int(prof * 5))]
            c.p(x, y, cor)
    c.r(3, 28, 44, 28, NEVE[3]); c.r(4, 29, 43, 29, NEVE[2])
    _pinheiro(c, 15, 28, 22, 7)
    for y in range(16, 28):                                  # o cristal violeta
        w = min(3, (y - 16) // 3)
        c.r(33 - w, y, 33 + w, y, VIOLETA[1]); c.p(33 + w, y, VIOLETA[2])
    c.p(33, 15, VIOLETA[3])
    c.contorno((8, 10, 28))
    return c


def moldura():
    """A moldura 9-slice da geleira: a do bosque repintada em gelo, com cravos verde-aurora."""
    base = pygame.image.load(os.path.join(UI, "moldura_bosque.png")).convert_alpha()
    w, h = base.get_size()
    miolo = base.get_at((w // 2, h // 2))
    rampa = ((24, 36, 70), (50, 80, 130), (90, 140, 196), (150, 200, 240), (226, 244, 255))
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            p = base.get_at((x, y))
            if p.a == 0 or (p.r, p.g, p.b) == (miolo.r, miolo.g, miolo.b):
                s.set_at((x, y), p)
                continue
            lum = (p.r * 0.3 + p.g * 0.55 + p.b * 0.15) / 255.0
            s.set_at((x, y), (*rampa[min(4, int(lum * 2.2 * 5))], p.a))
    for x, y in ((4, 4), (w - 6, 4), (4, h - 6), (w - 6, h - 6)):
        s.fill((*AURORA[1], 255), (x, y, 2, 2)); s.set_at((x + 1, y), (*AURORA[3], 255))
    pygame.image.save(s, os.path.join(UI, "moldura_geleira.png"))
    print(f"  ui/moldura_geleira.png  {w}x{h}")


def pintar_ui():
    print("ui:")
    pygame.image.save(pygame.transform.scale_by(emblema().s, 2), os.path.join(UI, "emblema_geleira.png"))
    print("  ui/emblema_geleira.png  96x96")
    moldura()


def main():
    pygame.init()
    pygame.display.set_mode((8, 8))
    for pasta in (f"jogo/{FASE}", f"cenario/{FASE}"):
        os.makedirs(os.path.join(pa.OBJ, pasta), exist_ok=True)
    pintar_perigos()
    salvar(f"jogo/{FASE}", "pingente", [pingente(k) for k in range(4)])
    pintar_blocos()
    pintar_enfeites()
    pintar_paisagem()
    pintar_ui()


if __name__ == "__main__":
    main()
