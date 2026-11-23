"""
Polimento da arte (tudo menos o heroi): repinta por codigo as pecas que
destoavam do resto do jogo.

    ./.venv/bin/python ferramentas/geradores/polir_arte.py

  - emblemas do bosque, das ilhas e da cidadela no mesmo estilo de redoma das
    dunas e da geleira (antes os tres eram quase o mesmo desenho: coluna numa ilha)
  - portais de chegada proprios e animados para bosque, dunas e geleira (usavam
    o cinza generico tingido) e o miolo do portal da cidadela, que tinha um
    resto da arte gerada no meio (um sofazinho), virou um redemoinho em volta
    do eclipse
  - a seta de "pule aqui" limpa e com quadro aceso nos cinco mundos
  - no bosque, o totem de engrenagens (metal, fora da floresta) virou um menir
    com musgo e a runa dos ecos
  - as colunas cinzentas da cidadela recoloridas na pedra violeta dela

Usa a telinha de pixels logicos de ferramentas/pintar_arte.py (ampliada 2x).
"""

import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
sys.path.insert(0, os.path.dirname(os.path.dirname(AQUI)))

import pygame

import pintar_arte as pa
from pintar_arte import C, mist, salvar
from jogo.config import TEMAS

UI = os.path.join(pa.RAIZ, "assets", "art", "ui")


def rampa(cor, n=4, escuro=0.55, claro=0.45):
    """n tons de `cor`: do escuro (sombra) ao claro (luz)."""
    preto, branco = (12, 8, 24), (255, 255, 255)
    return tuple(mist(mist(cor, preto, escuro), mist(cor, branco, claro), k / (n - 1)) for k in range(n))


# ================================================================== EMBLEMAS
# Todos os emblemas: um disco de ceu (a redoma) sobre um chao em meia-lua, a
# cena do mundo no meio, contorno escuro. 48x48 logicos, ampliados 2x.
def _ceu(c, de, ate, faixas=True):
    for y in range(3, 40):
        for x in range(48):
            if (x - 23.5) ** 2 + (y - 21.5) ** 2 <= 19.5 ** 2:
                k = (y - 3) / 36.0
                if faixas:
                    k = ((y - 3) // 5) / 7.0
                c.p(x, y, mist(de, ate, min(1.0, k)))


def _chao(c, camadas, topo_luz, topo):
    """O chao em meia-lua: camadas de cima para baixo, a linha do topo acesa."""
    for x in range(3, 45):
        t = (x - 3) / 41.0
        fundo = 30 + int(round(math.sin(t * math.pi) ** 0.55 * 15))
        for y in range(29, fundo):
            prof = (y - 29) / 16.0
            cor = camadas[min(len(camadas) - 1, int(prof * len(camadas)))]
            if (y - 29) % 4 == 3:
                cor = mist(cor, (20, 12, 28), 0.3)
            c.p(x, y, cor)
    c.r(3, 28, 44, 28, topo_luz)
    c.r(4, 29, 43, 29, topo)


def _pinheiro(c, cx, pe, alto, larg, folha, tronco):
    c.r(cx - 1, pe - 2, cx, pe, tronco)
    andares = max(3, alto // 5)
    for n in range(andares):
        t = n / max(1, andares - 1)
        y0 = pe - 2 - int(n * (alto - 3) / andares)
        w = max(1, int(round(larg * (1 - t * 0.75))))
        for y in range(y0 - 4, y0 + 1):
            ww = int(round(w * (0.5 + 0.5 * (y - (y0 - 4)) / 4.0)))
            for x in range(-ww, ww + 1):
                c.p(cx + x, y, folha[0] if x < -ww * 0.3 else (folha[2] if x > ww * 0.3 else folha[1]))
    c.p(cx, pe - 2 - int((andares - 1) * (alto - 3) / andares) - 5, folha[3])


def emblema_bosque():
    """O bosque dos ecos: noite, lua cheia, o pinheiro, a lanterna de pedra acesa e o cristal rosa."""
    c = C(48, 48)
    _ceu(c, (12, 20, 44), (44, 78, 96))
    # a lua cheia com crateras, e as estrelas
    c.disco(32, 12, 5.5, (232, 216, 170)); c.disco(33, 11, 4.2, (246, 234, 196))
    for x, y, r in ((30, 13, 1.1), (34, 9, 0.8), (33, 15, 0.7)):
        c.disco(x, y, r, (212, 192, 146))
    for x, y in ((12, 10), (18, 6), (9, 18), (41, 20), (22, 13)):
        c.p(x, y, (220, 236, 255))
    # a mata do fundo, escura
    for x in range(5, 43):
        alto = 24 - int(3 * abs(math.sin(x * 0.55)) + 2 * abs(math.sin(x * 0.21)))
        for y in range(alto, 29):
            c.p(x, y, (20, 44, 46))
    _chao(c, ((72, 120, 80), (84, 64, 48), (66, 48, 40), (48, 34, 34), (32, 22, 28)),
          (150, 214, 120), (96, 160, 96))
    _pinheiro(c, 14, 28, 20, 6, ((20, 50, 46), (30, 74, 62), (50, 104, 80), (120, 170, 120)), (70, 50, 40))
    # a lanterna de pedra, acesa
    pedra = ((56, 66, 66), (84, 98, 92), (120, 134, 124))
    c.r(25, 26, 30, 27, pedra[1]); c.r(26, 21, 29, 25, pedra[1]); c.r(29, 21, 29, 25, pedra[2])
    c.r(24, 19, 31, 20, pedra[2]); c.r(25, 18, 30, 18, pedra[1]); c.r(27, 17, 28, 17, pedra[1])
    c.r(27, 22, 28, 24, (255, 222, 150)); c.p(27, 23, (255, 250, 220))
    c.halo(27.5, 23, 5, (255, 210, 130), 90)
    # o cristal rosa (o perigo do bosque) e um eco no ar
    for y in range(18, 28):
        w = min(2, (y - 18) // 2)
        c.r(37 - w, y, 37 + w, y, (226, 92, 150)); c.p(37 + w, y, (255, 170, 210))
    c.p(37, 17, (255, 220, 236))
    c.r(20, 12, 20, 12, (126, 244, 180)); c.p(19, 13, (126, 244, 180)); c.p(21, 13, (126, 244, 180))
    c.p(20, 14, (126, 244, 180)); c.p(20, 13, (230, 255, 240))
    c.contorno((10, 14, 24))
    return c


def emblema_ilhas():
    """As ilhas suspensas: por do sol, a ilha flutuando com o templo e a cascata, sobre o mar de nuvens."""
    c = C(48, 48)
    _ceu(c, (70, 40, 96), (250, 160, 120))
    c.disco(31, 14, 6.5, (255, 196, 120)); c.disco(31, 14, 5, (255, 228, 168))
    for x, y in ((10, 9), (16, 6), (40, 22)):
        c.p(x, y, (255, 230, 240))
    # o chao da redoma e o mar de nuvens, em ondas rosadas
    _chao(c, ((236, 176, 178), (214, 146, 160), (186, 116, 146), (150, 88, 130), (110, 60, 110)),
          (255, 220, 214), (244, 194, 192))
    for x in range(4, 44, 6):
        c.r(x, 27, x + 3, 27, (255, 220, 214))                 # os topos das nuvens
    # a ilha flutuante: pedra violeta em ponta para baixo, gramado por cima
    for x in range(11, 33):
        t = (x - 11) / 21.0
        fundo = 20 + int(round(math.sin(t * math.pi) ** 0.8 * 9))
        for y in range(17, fundo):
            prof = (y - 17) / 11.0
            cor = ((126, 92, 140), (100, 70, 118), (78, 52, 98), (56, 36, 76))[min(3, int(prof * 4))]
            if (x * 3 + y * 5) % 11 == 0:
                cor = mist(cor, (30, 18, 46), 0.35)
            c.p(x, y, cor)
    c.r(11, 16, 32, 16, (170, 220, 140)); c.r(12, 17, 31, 17, (110, 170, 110))
    # a cascata caindo da beira ate as nuvens
    for y in range(17, 28):
        c.p(31, y, (190, 236, 255)); c.p(32, y, (130, 200, 240) if y % 3 else (255, 255, 255))
    c.r(29, 27, 34, 27, (255, 255, 255))
    # o templo de colunas e o cristal coral (o perigo das ilhas)
    c.r(13, 8, 22, 9, (240, 220, 200)); c.r(14, 7, 21, 7, (255, 240, 220))
    for x in (14, 17, 21):
        c.r(x, 10, x, 15, (226, 206, 190)); c.p(x, 10, (255, 240, 222))
    c.r(13, 15, 22, 15, (210, 186, 172))
    for y in range(10, 16):
        w = min(2, (y - 10) // 2)
        c.r(27 - w, y, 27 + w, y, (255, 106, 118)); c.p(27 + w, y, (255, 180, 170))
    c.p(27, 9, (255, 230, 220))
    c.contorno((24, 12, 34))
    return c


def emblema_eclipse():
    """A cidadela do eclipse: o sol negro de coroa dourada sobre as torres, com as seteiras acesas."""
    c = C(48, 48)
    _ceu(c, (10, 4, 22), (78, 34, 92))
    # o eclipse: coroa dourada, disco negro
    for y in range(0, 26):
        for x in range(18, 44):
            d = math.hypot(x - 31, y - 13)
            if 6.2 < d <= 8.6 and (x - 23.5) ** 2 + (y - 21.5) ** 2 <= 19.5 ** 2:
                k = 1.0 - (d - 6.2) / 2.4
                c.p(x, y, mist((140, 70, 40), (255, 214, 130), k))
    c.disco(31, 13, 6.2, (8, 4, 14))
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        px, py = 31 + math.cos(a) * 9.6, 12 + math.sin(a) * 9.6
        if (px - 23.5) ** 2 + (py - 21.5) ** 2 <= 19.5 ** 2:
            c.p(px, py, (255, 230, 160))
    for x, y in ((9, 12), (15, 7), (12, 22), (40, 26)):
        c.p(x, y, (230, 200, 255))
    _chao(c, ((96, 70, 120), (70, 48, 96), (54, 34, 78), (40, 24, 60), (26, 14, 42)),
          (196, 170, 230), (130, 100, 168))
    # as torres da cidadela
    pedra = ((34, 20, 52), (56, 36, 82), (80, 58, 110))
    for x0, x1, topo in ((7, 14, 14), (15, 21, 19), (22, 30, 11), (31, 37, 18)):
        c.r(x0, topo, x1, 28, pedra[1])
        c.r(x1, topo, x1, 28, pedra[2])
        c.r(x0, topo, x0, 28, pedra[0])
        for x in range(x0, x1 + 1, 2):
            c.p(x, topo - 1, pedra[1])                      # as ameias
        for y in range(topo + 3, 27, 5):
            c.p((x0 + x1) // 2, y, (255, 190, 100))         # as seteiras acesas
    c.r(25, 5, 25, 10, pedra[2]); c.r(26, 6, 28, 8, (130, 70, 170))   # o estandarte
    # a chama do braseiro (o perigo da cidadela)
    for y in range(20, 28):
        w = min(2, (28 - y) // 2) if y > 23 else (y - 20) // 2
        c.r(41 - w, y, 41 + w, y, (255, 128, 96)); c.p(41, y, (255, 214, 150))
    c.contorno((8, 4, 16))
    return c


# =================================================================== PORTAIS
def faz_portal(aro, miolo, centro, deco=None, base=None):
    """
    O portal de chegada (48x96 logicos, 4 quadros): o aro com a luz da
    direita, o redemoinho girando por dentro e o pedestal. `deco(c)` enfeita o
    aro de cada mundo.
    """
    quadros = []
    cx, cy, rx, ry = 23.5, 46.0, 21.0, 41.0
    for k in range(4):
        c = C(48, 96)
        for y in range(96):
            for x in range(48):
                u, v = (x - cx) / rx, (y - cy) / ry
                r = math.hypot(u, v)
                if r > 1.0:
                    continue
                ui, vi = (x - cx) / (rx - 4.5), (y - cy) / (ry - 4.5)
                ri = math.hypot(ui, vi)
                if ri > 1.0:                                  # o aro
                    luz = (u * 0.6 - v * 0.8) / max(0.01, r)
                    n = int(round((luz + 1) * 1.5))
                    cor = aro[max(0, min(3, n))]
                    if ri < 1.07:
                        cor = mist(cor, aro[0], 0.5)          # a borda de dentro, funda
                    c.p(x, y, cor)
                    continue
                ang = math.atan2(vi, ui)
                braco = math.sin(ang * 2 + ri * 8.5 - k * math.pi / 2)
                prof = ri ** 1.4
                if braco > 0.45:
                    cor = mist(miolo[3], miolo[1], prof)
                elif braco > -0.1:
                    cor = mist(miolo[2], miolo[0], prof)
                else:
                    cor = mist(miolo[1], miolo[0], min(1.0, prof * 1.3))
                if ri < 0.22:
                    cor = mist(centro, miolo[3], ri / 0.22)
                c.p(x, y, cor)
        # o pedestal
        pedra = base or (aro[0], aro[1], aro[2])
        c.r(9, 86, 38, 89, pedra[1]); c.r(9, 86, 38, 86, pedra[2])
        c.r(5, 90, 42, 95, pedra[1]); c.r(5, 90, 42, 90, pedra[2]); c.r(5, 95, 42, 95, pedra[0])
        c.r(42, 90, 42, 95, pedra[2]); c.r(38, 86, 38, 89, pedra[2])
        if deco:
            deco(c, k)
        c.contorno((10, 8, 20))
        quadros.append(c)
    return quadros


def deco_bosque(c, k):
    """Musgo no alto do aro e as runas verdes dos ecos acendendo uma por vez."""
    musgo = ((44, 84, 66), (74, 120, 88), (110, 160, 100))
    for x in range(10, 38):
        alto = 7 - int(round(6 * math.sin((x - 10) / 27 * math.pi) ** 0.5))
        y = 5 + alto
        c.r(x, y - 1, x, y + (1 if x % 3 else 2), musgo[1 if x % 4 else 2])
        c.p(x, y - 1, musgo[2])
    for i, ang in enumerate((200, 240, 300, 340, 20, 160)):
        a = math.radians(ang)
        x, y = 23.5 + math.cos(a) * 18.8, 46 + math.sin(a) * 38.8
        cor = (230, 255, 240) if i % 4 == k else (126, 244, 180)
        c.p(x, y, cor); c.p(x, y + 1, cor)
    for x, h in ((7, 3), (9, 2), (39, 3), (41, 2)):                  # cogumelos no pe
        c.r(x, 89 - h, x, 89, (220, 230, 220)); c.r(x - 1, 88 - h, x + 1, 88 - h, (150, 255, 200))


def deco_dunas(c, k):
    """Os olhos turquesa da caravana no alto e dos lados, piscando devagar."""
    for x, y in ((23, 4), (2, 46), (44, 46)):
        aceso = (x + k) % 3 != 0
        c.r(x - 1, y, x + 1, y + 2, (40, 150, 140))
        c.p(x, y + 1, (190, 255, 240) if aceso else (72, 226, 208))
    for x in range(14, 34, 4):                                     # areia escorrendo no pedestal
        c.p(x, 85, (238, 196, 126)); c.p(x + 1, 85, (255, 232, 160))


def deco_geleira(c, k):
    """Cristais AZUIS de gelo no alto (violeta e so o perigo) e neve nos ombros do aro."""
    for cx, topo, larg in ((23, 0, 3), (16, 4, 2), (31, 4, 2)):
        for y in range(topo, topo + 9):
            w = min(larg, (y - topo + 1) // 2)
            for x in range(cx - w, cx + w + 1):
                c.p(x, y, (130, 190, 236) if x < cx else (200, 240, 255))
        c.p(cx, topo, (255, 255, 255))
    for x in range(6, 42):
        t = (x - 6) / 35.0
        y = 6 + int(round((1 - math.sin(t * math.pi) ** 0.5) * 28))
        if y < 30:
            c.r(x, y - 1, x, y, (232, 244, 255))
    c.r(5, 89, 42, 89, (232, 244, 255))
    brilho = (14 + k * 6, 20)
    c.p(*brilho, (255, 255, 255))


def miolo_eclipse():
    """
    O portal da cidadela: o aro dourado de runas do original, com o miolo
    repintado -- um redemoinho violeta girando em volta de um eclipse pequeno.
    """
    caminho = os.path.join(pa.OBJ, "jogo", "eclipse", "portal.png")
    if not os.path.exists(caminho):
        print("  jogo/eclipse/portal_4f.png ja repintado (o original portal.png nao esta mais la)")
        return
    velho = pygame.image.load(caminho).convert_alpha()
    w, h = velho.get_size()

    def ouro(p):
        return p.a > 200 and p.r > 150 and p.r - p.b > 60

    dentro = set()
    for y in range(h):
        xs = [x for x in range(w) if ouro(velho.get_at((x, y)))]
        if len(xs) < 2:
            continue
        # o vao entre o primeiro trecho de ouro e o ultimo
        esq = xs[0]
        while esq + 1 < w and ouro(velho.get_at((esq + 1, y))):
            esq += 1
        dir_ = xs[-1]
        while dir_ - 1 >= 0 and ouro(velho.get_at((dir_ - 1, y))):
            dir_ -= 1
        for x in range(esq + 1, dir_):
            p = velho.get_at((x, y))
            if p.a > 200 and not ouro(p):
                acima = any(ouro(velho.get_at((x, yy))) for yy in range(0, y))
                abaixo = any(ouro(velho.get_at((x, yy))) for yy in range(y + 1, h))
                if acima and abaixo:
                    dentro.add((x, y))
    xs = [x for x, _ in dentro]
    ys = [y for _, y in dentro]
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    rx, ry = (max(xs) - min(xs)) / 2.0 + 1, (max(ys) - min(ys)) / 2.0 + 1
    miolo = ((16, 6, 30), (48, 20, 80), (110, 60, 170), (196, 150, 255))
    tira = pygame.Surface((w * 4, h), pygame.SRCALPHA)
    for k in range(4):
        q = velho.copy()
        for x, y in dentro:
            bx, by = x // 2 * 2, y // 2 * 2                 # celulas de 2 px, como o resto
            ui, vi = (bx - cx) / rx, (by - cy) / ry
            ri = math.hypot(ui, vi)
            ang = math.atan2(vi, ui)
            braco = math.sin(ang * 2 + ri * 8.5 - k * math.pi / 2)
            prof = min(1.0, ri ** 1.3)
            if braco > 0.45:
                cor = mist(miolo[3], miolo[1], prof)
            elif braco > -0.1:
                cor = mist(miolo[2], miolo[0], prof)
            else:
                cor = mist(miolo[1], miolo[0], min(1.0, prof * 1.3))
            d = math.hypot(bx - cx, (by - cy) * rx / ry)
            if d < 7:
                cor = (6, 2, 12)                            # o sol negro
            elif d < 10:
                cor = mist((255, 230, 160), (200, 120, 60), (d - 7) / 3)   # a coroa
            q.set_at((x, y), (*cor, 255))
        tira.blit(q, (k * w, 0))
    os.remove(caminho)
    pygame.image.save(tira, os.path.join(pa.OBJ, "jogo", "eclipse", "portal_4f.png"))
    print(f"  jogo/eclipse/portal_4f.png  {tira.get_width()}x{h} ({len(dentro)} px do miolo repintados)")


# ==================================================================== SETAS
def chevron(cor):
    """A seta de "pule aqui": V largo, luz no alto; o 2o quadro e o aceso, na batida."""
    quadros = []
    for aceso in (False, True):
        tons = rampa(cor, 4, 0.5, 0.55 if aceso else 0.35)
        c = C(16, 16)
        for y in range(2, 14):
            # cada braco desce em diagonal ate a ponta, com 4 px de grossura
            for x in range(16):
                dx = abs(x - 7.5)
                topo = 2 + (7.5 - dx) * 1.25
                if topo - 0.5 <= y <= topo + 5.2 and dx <= 7.5:
                    perto = y - topo                         # 0 no alto do braco
                    cor_px = tons[3] if perto < 1.2 else (tons[2] if perto < 3.2 else tons[1])
                    if x < 8 and perto >= 3.2:
                        cor_px = tons[0]                     # o lado da sombra
                    c.p(x, y, cor_px)
        if aceso:
            c.p(7, 12, (255, 255, 255)); c.p(8, 12, (255, 255, 255))
        c.contorno((12, 8, 22))
        quadros.append(c)
    return quadros


# ================================================================== BOSQUE
def menir(k=0):
    """O menir dos ecos: pedra alta com musgo e a runa verde, cogumelos no pe."""
    pedra = ((46, 56, 58), (70, 84, 82), (100, 116, 108), (134, 150, 138))
    musgo = ((40, 78, 60), (70, 116, 84), (110, 160, 100))
    c = C(24, 24)
    for y in range(3, 23):
        t = (y - 3) / 19.0
        meia = 3.2 + t * 2.6 - (0.9 if y < 5 else 0)
        for x in range(24):
            d = x - 11.5
            if -meia <= d <= meia:
                cor = pedra[1] if d < -meia * 0.3 else (pedra[2] if d < meia * 0.55 else pedra[3])
                if (x * 7 + y * 3) % 13 == 0:
                    cor = pedra[0]
                c.p(x, y, cor)
    for x in range(8, 16):                                  # o musgo no alto, escorrendo
        c.p(x, 3, musgo[2] if x > 11 else musgo[1])
        c.p(x, 4, musgo[1])
        if x in (9, 12, 14):
            c.r(x, 5, x, 6 + x % 3, musgo[0])
    runa = (150, 255, 200) if k == 0 else (210, 255, 230)
    for dx, dy in ((0, 0), (1, 0), (2, 1), (2, 2), (1, 3), (0, 3), (-1, 2), (-1, 1), (0, 5), (1, 5), (0, 7)):
        c.p(11 + dx, 9 + dy, runa)
    c.r(5, 22, 18, 23, musgo[1]); c.r(6, 22, 17, 22, musgo[2])
    for x, h in ((5, 3), (18, 2)):                           # cogumelos
        c.r(x, 22 - h, x, 21, (220, 230, 220)); c.r(x - 1, 21 - h, x + 1, 21 - h, (150, 255, 200))
    c.contorno((10, 16, 18))
    c.halo(11.5, 12, 6, (126, 244, 180), 50 if k == 0 else 80)
    return c


# ================================================================= CIDADELA
VIOLETA_PEDRA = ((22, 14, 36), (44, 32, 64), (72, 58, 100), (106, 92, 138), (150, 136, 182), (206, 196, 232))


def recolorir_colunas():
    """As colunas cinzas da cidadela na pedra violeta: so o cinza muda (vitral, ouro e musgo ficam)."""
    pasta = os.path.join(pa.OBJ, "jogo", "eclipse")
    for nome in sorted(os.listdir(pasta)):
        if not nome.startswith("coluna_"):
            continue
        img = pygame.image.load(os.path.join(pasta, nome)).convert_alpha()
        mudou = 0
        for y in range(img.get_height()):
            for x in range(img.get_width()):
                p = img.get_at((x, y))
                if p.a == 0:
                    continue
                mx, mn = max(p.r, p.g, p.b), min(p.r, p.g, p.b)
                if mx == 0 or (mx - mn) / mx > 0.16:
                    continue                                 # tem cor: fica
                lum = (p.r * 0.3 + p.g * 0.55 + p.b * 0.15) / 255.0
                n = min(len(VIOLETA_PEDRA) - 1, int(lum * len(VIOLETA_PEDRA)))
                img.set_at((x, y), (*VIOLETA_PEDRA[n], p.a))
                mudou += 1
        if mudou:
            pygame.image.save(img, os.path.join(pasta, nome))
            print(f"  jogo/eclipse/{nome}  {mudou} px de cinza recoloridos")


BRASA = ((60, 16, 28), (120, 34, 36), (190, 70, 48), (240, 116, 72), (255, 168, 104), (255, 222, 160))


def recolorir_marfim():
    """
    Na cidadela, os dentes de marfim (caco*v3) eram creme e branco: o unico
    perigo do mundo fora da cor de brasa. Mesma forma (e mesma colisao), na brasa.
    """
    pasta = os.path.join(pa.OBJ, "jogo", "eclipse")
    for nome in sorted(os.listdir(pasta)):
        if not (nome.startswith("caco") and "v3" in nome):
            continue
        img = pygame.image.load(os.path.join(pasta, nome)).convert_alpha()
        for y in range(img.get_height()):
            for x in range(img.get_width()):
                p = img.get_at((x, y))
                if p.a == 0:
                    continue
                lum = (p.r * 0.3 + p.g * 0.55 + p.b * 0.15) / 255.0
                if lum < 0.12:
                    continue                                 # o contorno fica
                n = min(len(BRASA) - 1, int(lum * len(BRASA)))
                img.set_at((x, y), (*BRASA[n], p.a))
        pygame.image.save(img, os.path.join(pasta, nome))
        print(f"  jogo/eclipse/{nome}  marfim -> brasa")


def lua_bosque(k):
    """A lua cheia do bosque: esfera com a borda mais escura, crateras com aro aceso, respirando."""
    c = C(44, 44)
    raio = (12.0, 13.5, 12.8)[k]
    cx = cy = 21.5
    for y in range(44):
        for x in range(44):
            d = math.hypot(x - cx, y - cy)
            if d > raio:
                continue
            borda = (d / raio) ** 3                           # escurece na borda (o limbo)
            luz = max(0.0, ((cx - x) * -0.35 + (cy - y) * 0.45) / raio)   # do alto, a direita
            cor = mist((246, 236, 204), (196, 176, 136), borda * 0.8)
            cor = mist(cor, (255, 250, 228), luz * 0.35)
            c.p(x, y, cor)
    s = raio / 12.0
    for dx, dy, r in ((-4.5, -2.5, 2.6), (3.5, 4.0, 2.0), (4.0, -4.5, 1.4), (-2.0, 5.5, 1.2), (-6.5, 3.5, 1.0)):
        x0, y0, rr = cx + dx * s, cy + dy * s, r * s
        c.disco(x0, y0, rr, (206, 186, 146))
        c.disco(x0 + 0.5, y0 + 0.5, max(0.6, rr - 0.8), (220, 202, 164))
        c.p(x0 + rr * 0.7, y0 + rr * 0.7, (252, 244, 218))   # o aro aceso do lado da luz
    return c


def main():
    pygame.init()
    pygame.display.set_mode((8, 8))
    print("emblemas:")
    for nome, faz in (("bosque", emblema_bosque), ("ilhas", emblema_ilhas), ("eclipse", emblema_eclipse)):
        pygame.image.save(pygame.transform.scale_by(faz().s, 2), os.path.join(UI, f"emblema_{nome}.png"))
        print(f"  ui/emblema_{nome}.png  96x96")
    print("portais:")
    salvar("jogo/bosque", "portal", faz_portal(
        ((40, 50, 50), (70, 84, 82), (104, 120, 110), (140, 156, 140)),
        ((8, 24, 30), (20, 70, 70), (60, 170, 140), (170, 255, 210)), (240, 255, 246), deco_bosque))
    salvar("jogo/dunas", "portal", faz_portal(
        ((112, 62, 46), (160, 98, 66), (206, 140, 88), (246, 204, 140)),
        ((20, 30, 50), (24, 80, 96), (60, 180, 180), (190, 255, 240)), (255, 250, 220), deco_dunas,
        ((110, 60, 44), (174, 110, 72), (230, 180, 120))))
    salvar("jogo/geleira", "portal", faz_portal(
        ((44, 78, 132), (76, 128, 188), (130, 190, 236), (210, 244, 255)),
        ((8, 16, 40), (24, 60, 100), (50, 170, 160), (170, 255, 220)), (240, 255, 250), deco_geleira,
        ((40, 46, 70), (98, 108, 136), (200, 222, 248))))
    miolo_eclipse()
    print("setas:")
    for mundo in ("bosque", "dunas", "ilhas", "geleira", "eclipse"):
        tema = TEMAS[mundo]
        salvar(f"jogo/{mundo}", "chevron", chevron(tema.destaque))
    print("bosque:")
    salvar("jogo/bosque", "enfeite_4", [menir(0), menir(1)])
    print("cidadela:")
    recolorir_colunas()
    recolorir_marfim()
    print("bosque (lua):")
    salvar("cenario/bosque", "astro", [lua_bosque(k) for k in range(3)], 1)


if __name__ == "__main__":
    main()
