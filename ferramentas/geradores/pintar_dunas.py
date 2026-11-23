"""
Pinta, por codigo, TODA a arte das Dunas do Chocalho (o mundo entre o bosque e
as ilhas): perigos, enxame, blocos, enfeites, paisagem, sol, emblema e moldura.

    ./.venv/bin/python ferramentas/geradores/pintar_dunas.py

Usa a telinha de pixels logicos de ferramentas/pintar_arte.py. A regra do
mundo: so o perigo e CARMIM e pontudo; o resto e areia, barro e turquesa, e
redondo. A luz vem sempre do sol, a direita.
"""

import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

import pintar_arte as pa
from pintar_arte import C, L, mist, salvar

FASE = "dunas"
UI = os.path.join(pa.RAIZ, "assets", "art", "ui")

# o carmim do perigo, do escuro ao aceso
RUBI = ((110, 20, 54), (190, 38, 80), (236, 78, 106), (255, 176, 172))
ESPINHO = (255, 232, 206)
CONT_PERIGO = (58, 12, 34)
# areia, barro e pedra
AREIA = ((176, 118, 76), (220, 170, 106), (246, 210, 140), (255, 236, 176))
BARRO = ((112, 58, 44), (168, 96, 62), (206, 136, 86), (236, 178, 120))
PEDRA = ((120, 84, 70), (170, 126, 96), (212, 170, 126), (240, 208, 160))
TURQ = ((24, 110, 116), (48, 176, 168), (96, 232, 212), (206, 255, 244))
VERDE = ((30, 84, 72), (52, 128, 92), (104, 176, 110), (170, 216, 130))
CONT = (60, 34, 34)


# ================================================================== PERIGOS
def dentro_do_molde(c, quantidade):
    """Apaga o que passar do triangulo padrao (menos 1 px, a folga do contorno)."""
    uw = L // quantidade
    for y in range(L):
        for x in range(L):
            cx = (x // uw) * uw + uw / 2.0 - 0.5
            meia = (y - 2) / 21.0 * (uw / 2.0 - 1.2)
            if x >= uw * quantidade or abs(x - cx) > meia + 0.01:
                c.s.set_at((x, y), (0, 0, 0, 0))


def cacto(c, cx, uw, topo=2):
    """
    O cacto-rubi: coluna em lanca, com os GOMOS em faixas verticais (sulco
    escuro, crista clara), bracos baixos e os espinhos so na beira -- tufos
    claros e curtos, como pelos contra a luz.
    """
    e, m, cl, luz = RUBI
    a = {24: 4, 12: 2, 8: 1}[uw]
    sulco = mist(e, m, 0.35)
    for y in range(topo, 24):
        larg = min(a, int((y - topo) * 0.8))
        for x in range(-larg, larg + 1):
            if larg == 0:
                cor = luz
            elif x == -larg:
                cor = e                                      # a beira na sombra
            elif x == larg:
                cor = cl                                     # a beira no sol
            elif larg >= 3 and x in (-2, 2):
                cor = sulco if x < 0 else m                  # os sulcos entre os gomos
            elif larg >= 3 and x in (-1, 1):
                cor = m if x < 0 else cl                     # o gomo do meio, inchado
            elif x == 0:
                cor = cl if larg >= 2 else m
            else:
                cor = m
            c.p(cx + x, y, cor)
        # a crista do gomo do meio pega o sol de cima, mais forte no alto
        if larg >= 2 and y < topo + 9:
            c.p(cx + (1 if larg >= 3 else 0), y, luz)
    c.p(cx, topo, luz); c.p(cx, topo + 1, luz)
    if uw >= 12:
        # os bracos: saem baixo e sobem, cada um na sua altura, com a ponta acesa
        for lado, sai, sobe, longe in ((-1, 20, 16 if uw == 24 else 18, 7 if uw == 24 else 4),
                                       (1, 21, 17 if uw == 24 else 19, 7 if uw == 24 else 4)):
            for x in range(a, longe + 1):
                c.p(cx + lado * x, sai, m if lado < 0 else cl); c.p(cx + lado * x, sai + 1, e)
            for y in range(sobe, sai + 1):
                c.p(cx + lado * longe, y, cl if lado > 0 else m)
                if uw == 24:
                    c.p(cx + lado * (longe - 1), y, m if lado > 0 else e)
            c.p(cx + lado * longe, sobe, luz)
    # os espinhos: tufos curtos na beira, so a cada 5 linhas, alternando o lado
    if uw >= 12:
        for n, y in enumerate(range(topo + 5, 21, 5)):
            larg = min(a, int((y - topo) * 0.8))
            lado = 1 if n % 2 else -1
            c.p(cx + lado * larg, y, ESPINHO)
            c.p(cx + lado * larg, y - 1, mist(ESPINHO, cl, 0.5))
    # a areia amontoada no pe
    m_ = min(uw // 2 - 1, a + 2)
    c.r(cx - m_, 23, cx + m_, 23, AREIA[1])


def espinheiro(c, cx, uw, topo, k, i):
    """Galho seco de espinhos: sobe torto ate a ponta, com farpas para os lados."""
    e, m, cl, luz = RUBI
    h = 23 - topo
    amp = {24: 2.2, 12: 1.0, 8: 0.5}[uw]
    grosso = uw >= 12
    for y in range(int(topo), 24):
        t = (y - topo) / max(1, h)
        x = cx + amp * math.sin(t * 5.2 + i) * t
        c.p(x, y, m)
        if grosso and t > 0.25:
            c.p(x - 1, y, e)
        if grosso and t > 0.6 and uw == 24:
            c.p(x + 1, y, cl)
        # as farpas: curtas, para cima e para fora, alternando o lado
        if y > topo + 3 and (y + i) % 3 == 0:
            lado = 1 if ((y + i) // 3) % 2 else -1
            comp = max(1, int(t * (4 if uw == 24 else 2 if uw == 12 else 1)))
            for d in range(1, comp + 1):
                c.p(x + lado * (d + (1 if grosso else 0)), y - d, cl if lado > 0 else m)
            c.p(x + lado * (comp + (1 if grosso else 0)), y - comp, luz)
    c.p(cx, topo, luz); c.p(cx, topo + 1, cl)
    m_ = {24: 5, 12: 3, 8: 2}[uw]
    c.r(cx - m_, 23, cx + m_, 23, AREIA[1])
    c.p(cx - m_ + 1, 22, AREIA[2])


def cascavel(c, cx, uw, topo, k, i):
    """A cascavel de pe: o corpo em S, a cabeca em seta no alto e o chocalho tremendo no pe."""
    e, m, cl, luz = RUBI
    amp = {24: 2.6, 12: 1.2, 8: 0.5}[uw]
    g = {24: 1, 12: 1, 8: 0}[uw]
    h = 22 - topo
    for y in range(int(topo) + 3, 23):
        t = (y - topo - 3) / max(1, h - 3)
        x = cx + amp * math.sin(t * 6.0 + 0.4) * min(1.0, t * 2.2)
        for d in range(-g, g + 1):
            c.p(x + d, y, e if d < 0 else (cl if d > 0 else m))
        if g == 0:
            c.p(x, y, m if y % 2 else e)
        if g and y % 4 == 0:
            for d in range(-g, g + 1):
                c.p(x + d, y, mist(ESPINHO, cl, 0.45))               # as faixas do couro
            c.p(x + g, y, ESPINHO)
    # a cabeca: uma seta para cima
    c.p(cx, topo, luz)
    c.r(cx - (1 if uw >= 12 else 0), topo + 1, cx + (1 if uw >= 12 else 0), topo + 2, cl)
    if uw == 24:
        c.r(cx - 2, topo + 2, cx + 2, topo + 3, m)
        c.p(cx - 1, topo + 2, (255, 240, 120)); c.p(cx + 1, topo + 2, (255, 240, 120))   # os olhos
        c.p(cx - 2, topo + 3, e)
    # o chocalho: gomos claros no pe, tremendo de quadro em quadro
    tx = cx + {24: 5, 12: 3, 8: 2}[uw] * (1 if i % 2 == 0 else -1)
    tremor = (0, 1, 0, -1)[k % 4] if uw >= 12 else 0
    for n in range(3 if uw == 24 else 2):
        c.p(tx + tremor * (n % 2), 21 - n * (2 if uw == 24 else 1), ESPINHO if n % 2 == 0 else AREIA[2])
        if uw == 24:
            c.p(tx + tremor * (n % 2), 22 - n * 2, AREIA[1])
    m_ = {24: 6, 12: 3, 8: 2}[uw]
    c.r(cx - m_, 23, cx + m_, 23, AREIA[1])


def _lingua(c, cx, uw, topo, k, i):
    if uw == 24 and k % 4 in (1, 2):
        c.p(cx, topo - 1, (255, 150, 170, 255))


cascavel.brilho = _lingua


def pintar_perigos():
    print("perigos:")
    for q in (1, 2, 3):
        c = C(L, L)
        uw = L // q
        for i in range(q):
            cacto(c, i * uw + uw // 2, uw)
        dentro_do_molde(c, q)
        # a areia do pe e reposta depois do corte: o cacto nao flutua
        for i in range(q):
            cx = i * uw + uw // 2
            m_ = min(uw // 2 - 2, {24: 6, 12: 3, 8: 2}[uw])
            c.r(cx - m_, 23, cx + m_, 23, AREIA[1])
        c.contorno(CONT_PERIGO)
        salvar(f"jogo/{FASE}", f"caco{q}", c)
    pa.perigo(FASE, 2, espinheiro, cont=CONT_PERIGO)
    # o vidro de raio: a areia que o relampago fundiu em cristal
    pa.perigo(FASE, 3, pa.faz_cristal(RUBI, (AREIA[0], AREIA[1], AREIA[2])), cont=CONT_PERIGO)
    pa.perigo(FASE, 4, cascavel, quadros=4, cont=CONT_PERIGO)
    # nenhuma variante pode passar da silhueta do cacto: corta o que sobrar
    for q in (1, 2, 3):
        base = pygame.image.load(os.path.join(pa.OBJ, "jogo", FASE, f"caco{q}.png")).convert_alpha()
        topo = [next((y for y in range(48) if base.get_at((x, y)).a > 128), 48) for x in range(48)]
        # o molde e o TRIANGULO do cacto (os bracos dele nao contam para as outras)
        uw = 48 // q
        for nome in sorted(os.listdir(os.path.join(pa.OBJ, "jogo", FASE))):
            if not nome.startswith(f"caco{q}v"):
                continue
            caminho = os.path.join(pa.OBJ, "jogo", FASE, nome)
            img = pygame.image.load(caminho).convert_alpha()
            for x in range(img.get_width()):
                xx = x % 48
                cx = (xx // uw) * uw + uw / 2.0 - 0.5
                limite = 4 + abs(xx - cx) / (uw / 2.0 - 2.0) * 42
                for y in range(48):
                    if y < min(limite, 47) - 0.5 and y < 44 and img.get_at((x, y)).a > 128:
                        img.set_at((x, y), (0, 0, 0, 0))
            pygame.image.save(img, caminho)


# =================================================================== ENXAME
def escaravelho(c, cx, cy, k, virado):
    """
    Um escaravelho de ruido: casco carmim aberto em duas carapacas e as asas de
    vidro batendo -- grandes e claras, com o contorno proprio, para o enxame se
    ler como coisa que VOA (e que mora no alto).
    """
    e, m, cl, luz = RUBI
    # as asas: dois leques claros que sobem e descem a cada quadro
    batida = (-6, -3, 2, -2)[k % 4]
    for lado in (-1, 1):
        for d in range(2, 10):
            t = (d - 2) / 7.0
            y = cy - 1 + batida * t
            meio = 2 if d < 8 else 1
            for h in range(-meio, meio + 1):
                borda = abs(h) == meio or d == 9
                c.p(cx + lado * d, y + h, (178, 212, 224) if borda else
                    ((255, 255, 255) if d > 6 and h <= 0 else (226, 242, 244)))
        c.p(cx + lado * 9, y, (255, 255, 255))
    # o casco: oval, as duas carapacas entreabertas
    for y in range(-4, 5):
        larg = int(round(math.sqrt(max(0.0, 1 - (y / 4.6) ** 2)) * 4.2))
        for x in range(-larg, larg + 1):
            cor = e if x < -1 else (cl if x > 1 else m)
            c.p(cx + x, cy + y, cor)
    c.r(cx, cy - 3, cx, cy + 4, e)
    c.p(cx + 2, cy - 2, luz); c.p(cx + 3, cy - 1, luz); c.p(cx - 2, cy - 2, cl)
    # a cabeca e as pincas
    d = -1 if virado else 1
    c.r(cx - 2, cy - 6, cx + 2, cy - 5, CONT_PERIGO)
    c.p(cx - 3, cy - 7, cl); c.p(cx + 3, cy - 7, cl)
    c.p(cx - 3, cy - 8, luz); c.p(cx + 3, cy - 8, luz)
    c.p(cx + d, cy - 5, (255, 240, 120))
    # as patas: tracos curtos para baixo
    for x in (-4, 4):
        c.p(cx + x, cy + 3, CONT_PERIGO); c.p(cx + x + (1 if x > 0 else -1), cy + 4, CONT_PERIGO)


def pintar_enxame():
    print("enxame:")
    quadros = []
    for k in range(4):
        c = C(24, 62)
        for n, (x, y) in enumerate(((11, 10), (13, 31), (10, 52))):
            escaravelho(c, x, y + (0, 1, 0, -1)[(k + n) % 4], k + n, n % 2)
        c.contorno(CONT_PERIGO)
        # a poeira de ruido entre um e outro: liga os tres num enxame so
        for n, (x, y) in enumerate(((15, 20), (8, 22), (14, 42), (9, 41), (12, 58), (6, 4))):
            if (n + k) % 2 == 0:
                c.p(x + (k % 2), y, (*RUBI[2], 200))
        quadros.append(c)
    salvar(f"jogo/{FASE}", "enxame", quadros)


# =================================================================== BLOCOS
def bloco_arenito():
    """Arenito lavrado, com a espiral turquesa da caravana: da para pisar."""
    e, m, cl, luz = PEDRA
    c = C(24, 24)
    c.r(0, 0, 23, 23, m)
    c.r(0, 0, 23, 1, luz); c.r(22, 0, 23, 23, cl)                # o sol: em cima e a direita
    c.r(0, 2, 1, 23, e); c.r(0, 22, 23, 23, e)
    c.r(3, 4, 20, 20, mist(m, e, 0.35)); c.r(4, 5, 20, 20, mist(m, cl, 0.25))
    for x, y in ((6, 3), (15, 21), (2, 12), (21, 9), (10, 2)):
        c.p(x, y, e)
    # a espiral
    for x, y in ((8, 8), (9, 7), (10, 7), (11, 7), (12, 7), (13, 7), (14, 8), (15, 9), (15, 10),
                 (15, 11), (15, 12), (15, 13), (14, 14), (13, 15), (12, 15), (11, 15), (10, 15),
                 (9, 14), (8, 13), (8, 12), (8, 11), (9, 10), (10, 10), (11, 10), (12, 11), (12, 12),
                 (11, 12)):
        c.p(x, y, TURQ[1])
        c.p(x, y + 1, mist(TURQ[0], e, 0.5)) if not c.cheio(x, y + 1) or True else None
    for x, y in ((9, 7), (13, 7), (15, 10), (10, 10)):
        c.p(x, y, TURQ[2])
    c.r(0, 0, 23, 0, AREIA[3])
    return c


def bloco_anfora():
    """Um caixote de vime com a anfora dentro: o que a caravana carrega."""
    e, m, cl, luz = BARRO
    c = C(24, 24)
    c.r(0, 0, 23, 23, m)
    for y in range(1, 23, 3):
        for x in range(0, 24):
            c.p(x, y + ((x // 3) % 2), e if (x // 3 + y) % 2 else cl)   # a trama do vime
    c.r(0, 0, 23, 1, luz); c.r(22, 0, 23, 23, cl); c.r(0, 2, 1, 23, e); c.r(0, 22, 23, 23, e)
    # a janela com a anfora
    c.r(6, 5, 17, 19, (70, 36, 36))
    for y in range(7, 19):
        larg = (2, 2, 3, 4, 4, 5, 5, 5, 4, 4, 3, 2)[y - 7]
        for x in range(-larg, larg + 1):
            c.p(11.5 + x, y, PEDRA[1] if x < 0 else PEDRA[2])
        c.p(11 + larg, y, PEDRA[3])
    c.r(9, 12, 14, 12, TURQ[1]); c.r(9, 13, 14, 13, TURQ[0])
    c.r(10, 6, 13, 6, PEDRA[3])
    for x0, y0 in ((0, 0), (21, 0), (0, 21), (21, 21)):
        c.r(x0, y0, x0 + 2, y0 + 2, PEDRA[0]); c.p(x0 + 1, y0 + 1, PEDRA[3])
    c.r(0, 0, 23, 0, AREIA[3])
    return c


def pintar_blocos():
    print("blocos:")
    salvar(f"jogo/{FASE}", "bloco", bloco_arenito())
    salvar(f"jogo/{FASE}", "bloco_v2", bloco_anfora())
    salvar(f"jogo/{FASE}", "bloco_v3", pa.bloco_emblema((PEDRA[0], PEDRA[1], PEDRA[2]),
                                                       (TURQ[0], TURQ[1], TURQ[3]), TURQ[2]))


# ================================================================= ENFEITES
def _vaso(c, cx, pe, alt, bojo, faixa=True):
    """Uma anfora: boca, pescoco, bojo redondo, pe estreito. Luz a direita."""
    e, m, cl, luz = BARRO
    for y in range(pe - alt, pe + 1):
        t = (y - (pe - alt)) / max(1, alt)
        if t < 0.12:
            larg = bojo * 0.55
        elif t < 0.28:
            larg = bojo * 0.36
        else:
            larg = bojo * math.sin(min(1.0, (t - 0.28) / 0.72 * 0.92 + 0.08) * math.pi) ** 0.6
        larg = max(1, int(round(larg)))
        for x in range(-larg, larg + 1):
            cor = e if x < -larg * 0.4 else (cl if x > larg * 0.35 else m)
            c.p(cx + x, y, cor)
        if larg >= 3:
            c.p(cx + larg - 1, y, luz)
    if faixa:
        y = pe - int(alt * 0.45)
        larg = int(bojo)
        for x in range(-larg, larg + 1):
            if c.cheio(cx + x, y):
                c.p(cx + x, y, TURQ[1] if x < larg * 0.4 else TURQ[2])
                c.p(cx + x, y + 1, TURQ[0])
    c.r(cx - 1, pe - alt, cx + 1, pe - alt, (70, 36, 36))            # a boca escura


def anforas():
    c = C(26, 22)
    _vaso(c, 8, 21, 17, 6)
    _vaso(c, 19, 21, 11, 4, faixa=False)
    c.r(16, 16, 22, 16, TURQ[1])
    c.contorno(CONT)
    return c


def _palmeira(c, cx, pe, alt, verde=VERDE, tronco=BARRO, fino=False):
    """Palmeira de tronco curvo; as folhas caem em arco, redondas na ponta."""
    topo_x = cx
    for y in range(pe, pe - alt, -1):
        t = (pe - y) / alt
        x = cx + 4 * math.sin(t * 1.6) * (0 if fino else 1) + (2 * t if fino else 0)
        c.p(x, y, tronco[1]); c.p(x + 1, y, tronco[2])
        if not fino:
            c.p(x - 1, y, tronco[0])
        if y % 3 == 0:
            c.p(x, y, tronco[0])
        topo_x = x
    ty = pe - alt
    for ang, comp in ((-150, 11), (-175, 12), (-30, 12), (-5, 12), (-90, 6), (-125, 9), (-55, 9)):
        comp = comp * (0.62 if fino else 1.0)
        for d in range(1, int(comp) + 1):
            t = d / comp
            x = topo_x + math.cos(math.radians(ang)) * d
            y = ty + math.sin(math.radians(ang)) * d * 0.55 + t * t * comp * 0.62   # a folha pesa e cai
            cor = verde[1] if ang < -90 else verde[2]
            c.p(x, y, cor); c.p(x, y + 1, verde[0])
            if d % 3 == 0 and not fino:
                c.p(x, y + 2, verde[1])
            if d == int(comp):
                c.p(x, y, verde[3])
    c.disco(topo_x, ty, 1.6, verde[1])
    if not fino:
        c.p(topo_x - 1, ty + 2, (120, 70, 50)); c.p(topo_x + 2, ty + 2, (150, 92, 60))   # os cocos
    return topo_x


def palmeira():
    c = C(34, 40)
    _palmeira(c, 14, 39, 28)
    c.contorno(CONT)
    return c


def estandarte(k):
    """O estandarte da caravana: pano turquesa com o sol, balancando no vento."""
    c = C(18, 36)
    c.r(3, 3, 4, 35, PEDRA[1]); c.r(4, 3, 4, 35, PEDRA[3])
    c.disco(3.5, 2, 1.6, AREIA[3])
    for y in range(6, 24):
        onda = int(round(math.sin((y * 0.5) + k * math.pi) * 1.2 * (y - 6) / 18.0))
        larg = 10 - (1 if y > 20 else 0) - (2 if y > 22 else 0)
        for x in range(5, 5 + larg):
            c.p(x + onda, y, TURQ[1] if x < 11 else TURQ[2])
        c.p(5 + onda, y, TURQ[0])
        if y in (7, 21):
            for x in range(5, 5 + larg):
                c.p(x + onda, y, AREIA[3])
    c.disco(10, 14, 2.3, AREIA[3]); c.disco(10, 14, 1.2, (255, 190, 110))
    c.contorno(CONT)
    return c


def tenda():
    """A tenda da caravana: listras creme e turquesa, a porta escura, redonda no alto."""
    c = C(38, 26)
    for x in range(2, 36):
        t = (x - 2) / 33.0
        topo = 25 - int(round(math.sin(t * math.pi) ** 0.75 * 20))
        for y in range(topo, 26):
            listra = ((x - 2) // 4) % 2
            cor = (AREIA[3] if x > 20 else AREIA[2]) if listra else (TURQ[2] if x > 20 else TURQ[1])
            c.p(x, y, cor)
        c.p(x, topo, AREIA[3])
    for y in range(13, 26):
        larg = min(4, (y - 12))
        c.r(19 - larg, y, 19 + larg, y, (64, 34, 44))
    c.r(18, 2, 19, 6, PEDRA[1]); c.disco(18.5, 2, 1.5, (255, 190, 110))
    c.r(2, 25, 35, 25, AREIA[0])
    c.contorno(CONT)
    return c


def coluna_caida():
    """Uma coluna de arenito quebrada, com glifos, e o tambor dela tombado ao lado."""
    e, m, cl, luz = PEDRA
    c = C(26, 30)
    for y in range(6, 30):
        quebra = (0, 1, 3, 2, 4)[(y - 6)] if y < 11 else 9
        for x in range(4, 4 + min(9, quebra + 3 if y < 11 else 9)):
            c.p(x, y, e if x < 6 else (cl if x > 10 else m))
        if y >= 11:
            c.p(12, y, luz)
            if y % 2:
                c.p(8, y, mist(m, e, 0.5))                           # as caneluras
    for x, y in ((6, 14), (7, 14), (8, 15), (7, 16), (6, 17), (8, 17), (9, 20), (7, 21), (8, 21),
                 (6, 22), (9, 23)):
        c.p(x, y, TURQ[1])
    c.r(2, 27, 14, 29, m); c.r(2, 27, 14, 27, luz); c.r(2, 29, 14, 29, e)        # a base
    # o tambor tombado
    c.disco(20, 25, 4.2, m); c.disco(20.6, 24.6, 2.6, cl); c.disco(20.4, 24.8, 1.2, e)
    c.r(16, 29, 24, 29, AREIA[1])
    c.contorno(CONT)
    return c


def lamparina(k):
    """A lamparina do oasis: tigela de pedra e a chama turquesa, redonda (chama carmim seria perigo)."""
    c = C(16, 24)
    c.r(7, 14, 8, 22, PEDRA[1]); c.r(8, 14, 8, 22, PEDRA[3])
    c.r(4, 22, 11, 23, PEDRA[1]); c.r(4, 22, 11, 22, PEDRA[3])
    for y, larg in ((11, 5), (12, 5), (13, 4), (14, 2)):
        c.r(7.5 - larg, y, 7.5 + larg, y, PEDRA[2] if y == 11 else PEDRA[1])
    c.r(12, 11, 12, 13, PEDRA[3])
    alto = (5, 6, 5, 4)[k % 4]
    desvio = (0, 1, 0, -1)[k % 4]
    for y in range(10 - alto, 11):
        t = (10 - y) / alto
        larg = max(0, int(round(math.sin((1 - t) * math.pi * 0.85 + 0.25) * 3)))
        for x in range(-larg, larg + 1):
            c.p(7.5 + x + desvio * t, y, TURQ[1] if abs(x) == larg else TURQ[2])
    c.disco(7.5, 8.5, 1.2, TURQ[3])
    c.contorno(CONT)
    c.halo(7.5 + desvio, 7, 6, TURQ[2], 90)
    return c


def pintar_enfeites():
    print("enfeites:")
    salvar(f"jogo/{FASE}", "enfeite_1", anforas())
    salvar(f"jogo/{FASE}", "enfeite_2", palmeira())
    salvar(f"jogo/{FASE}", "enfeite_3", [estandarte(k) for k in range(2)])
    salvar(f"jogo/{FASE}", "enfeite_4", tenda())
    salvar(f"jogo/{FASE}", "enfeite_5", coluna_caida())
    salvar(f"jogo/{FASE}", "enfeite_6", [lamparina(k) for k in range(4)])


# ================================================================= PAISAGEM
# pecas do fundo, ja na escala do buffer (320x180). Tons de areia mais apagados
# que os do jogo: sao longe. A face da direita pega o sol.
LONGE = ((176, 132, 116), (206, 164, 130), (234, 200, 156), (250, 228, 186))
PERTO = ((128, 78, 64), (176, 112, 76), (216, 154, 98), (248, 206, 140))
# a esfinge e de pedra lavrada, mais clara que o arenito cru das mesas
PEDRA_PERTO = ((140, 96, 78), (196, 148, 104), (230, 190, 136), (252, 226, 176))


def piramide(w, h, pal, degraus=5, topo=None):
    """Piramide em degraus: a metade direita acesa, a esquerda na sombra."""
    e, m, cl, luz = pal
    c = C(w, h)
    alto = h / degraus
    for d in range(degraus):
        y0 = int(h - (d + 1) * alto)
        meia = (w / 2.0) * (1 - d / (degraus + 0.6))
        cx = w / 2.0
        for y in range(y0, int(h - d * alto)):
            for x in range(int(cx - meia), int(cx + meia)):
                c.p(x, y, m if x < cx - meia * 0.12 else cl)
        c.r(int(cx - meia), y0, int(cx + meia) - 1, y0, luz)
        c.r(int(cx - meia), y0 + 1, int(cx - meia * 0.12), y0 + 1, e) if alto >= 4 else None
    # a escadaria no meio e a porta
    c.r(w // 2 - 1, int(h - (degraus - 1) * alto), w // 2, h - 1, e)
    if topo:
        c.r(w // 2 - 2, int(h - degraus * alto) - 2, w // 2 + 1, int(h - degraus * alto) - 1, topo[1])
        c.p(w // 2, int(h - degraus * alto) - 3, topo[2])
    return c


def mesa(w, h, pal):
    """
    Uma mesa de arenito: o topo chato com a borda de pedra mais dura (que
    passa um pouco da parede), as camadas que o vento comeu em reentrancias,
    fendas verticais, a face da esquerda na sombra e o entulho no pe.
    """
    e, m, cl, luz = pal
    c = C(w, h)
    sol = int(w * 0.62)
    camadas = [(y, (y * 2654435761 >> 5) % 3) for y in range(4, h, 5)]
    for y in range(h):
        t = y / (h - 1)
        # as camadas mais moles recuam: a parede nao e uma linha reta
        recuo = 0
        for y0, mole in camadas:
            if y0 <= y < y0 + 5 and mole == 0:
                recuo = 1
        x0 = 2 + recuo - (1 if t > 0.8 else 0)
        x1 = w - 3 - recuo + (1 if t > 0.8 else 0)
        for x in range(x0, x1 + 1):
            cor = m if x < sol else cl
            if x < x0 + 3:
                cor = e                                         # a face de tras
            if y % 5 == 4:
                cor = mist(cor, e, 0.55)                        # a junta da camada
            c.p(x, y, cor)
    # o topo de pedra dura, um pouco mais largo
    c.r(0, 0, w - 1, 2, cl); c.r(0, 0, w - 1, 0, luz); c.r(0, 2, sol, 2, m)
    # fendas verticais e um nicho escuro
    for fx in (int(w * 0.24), int(w * 0.71)):
        for y in range(3, h - 4):
            c.p(fx + (1 if (y // 6) % 2 else 0), y, e)
    nx, ny = int(w * 0.42), int(h * 0.38)
    c.r(nx, ny, nx + 3, ny + 4, e); c.r(nx + 1, ny - 1, nx + 2, ny - 1, e)
    # o entulho no pe: pedras redondas, acesas a direita
    for px, r in ((1, 2.2), (w - 3, 2.6), (w * 0.5, 1.6), (w * 0.8, 1.8)):
        c.disco(px, h - 1.5, r, m)
        c.p(px + r * 0.5, h - 2.5, luz)
    return c


def obelisco(pal):
    e, m, cl, luz = pal
    c = C(16, 28)
    for y in range(3, 26):
        larg = 1 + (y - 3) // 9
        c.r(6 - larg, y, 6, y, m); c.r(7, y, 7 + larg, y, cl)
    c.p(6, 1, luz); c.p(7, 1, luz); c.r(6, 2, 7, 2, cl)
    c.r(3, 26, 10, 27, m); c.r(3, 26, 10, 26, luz)
    for y in (8, 12, 16, 20):
        c.p(7, y, e)
    c.r(11, 24, 14, 27, m); c.r(11, 24, 14, 24, luz); c.p(12, 22, m); c.p(12, 23, m)
    return c


def oasis(pal_verde, pal):
    c = C(34, 22)
    for cx, alt in ((7, 14), (16, 18), (25, 12)):
        _palmeira(c, cx, 20, alt, pal_verde, (pal[0], pal[1], pal[2]), fino=True)
    c.r(2, 20, 31, 21, pal_verde[1]); c.r(8, 21, 26, 21, (120, 196, 196))
    return c


def arco(pal):
    """Um arco natural de arenito: duas pernas e a ponte de pedra por cima."""
    e, m, cl, luz = pal
    c = C(48, 32)
    for x in range(48):
        t = x / 47.0
        topo = int(round(8 - math.sin(t * math.pi) ** 0.6 * 7 + (2 if (x * 5) % 7 == 0 else 0)))
        vao_topo = int(round(30 - math.sin(min(1.0, max(0.0, (t - 0.24) / 0.5)) * math.pi) ** 0.7 * 20))
        dentro_do_vao = 0.24 < t < 0.74
        for y in range(topo, 32):
            if dentro_do_vao and y > vao_topo:
                continue
            cor = m if t < 0.5 else cl
            if y % 6 == 5:
                cor = e if t < 0.5 else m
            c.p(x, y, cor)
        c.p(x, topo, luz)
        if dentro_do_vao:
            c.p(x, vao_topo, e)
    return c


def esfinge(pal):
    """
    A guardia das dunas: uma leoa de pedra deitada sobre o pedestal, de cabeca
    erguida para o sol, com o toucado em listras e o colar turquesa. Meio
    enterrada: a areia ja cobre o pe do pedestal.
    """
    e, m, cl, luz = pal
    c = C(56, 34)
    # o pedestal
    c.r(2, 27, 53, 33, m); c.r(2, 27, 53, 27, luz); c.r(2, 28, 4, 33, e)
    for x in range(8, 52, 9):
        c.r(x, 29, x, 33, e)                                    # os blocos
    # o corpo: o lombo comprido, a anca redonda atras
    for x in range(6, 40):
        t = (x - 6) / 33.0
        topo = int(round(26 - 7.5 * math.sin(min(1.0, 0.15 + t * 0.95) * math.pi) ** 0.45))
        if x < 13:
            topo = int(round(26 - 9 * math.sqrt(max(0.0, 1 - ((x - 13) / 7.0) ** 2))))
        for y in range(topo, 27):
            c.p(x, y, e if y > 24 else (m if y > topo + 2 else cl))
        c.p(x, topo, luz)
    for x, y in ((12, 22), (18, 23), (24, 22), (30, 23)):
        c.p(x, y, mist(m, e, 0.6))                              # as costelas na pedra
    # as patas da frente, esticadas
    c.r(36, 23, 50, 26, cl); c.r(36, 23, 50, 23, luz); c.r(36, 26, 50, 26, m)
    for x in (44, 47, 50):
        c.p(x, 25, e)                                           # os dedos
    # o peito e a cabeca erguida
    for y in range(12, 24):                                     # o peito, largo
        larg = 4 + (y - 12) // 3
        c.r(38 - larg, y, 38 + 2, y, m)
        c.r(39, y, 41, y, cl)
        c.p(38 - larg, y, e)
    c.r(33, 4, 42, 12, m); c.r(40, 4, 42, 12, cl); c.r(33, 4, 42, 4, luz)
    # o toucado: cai pelos dois lados da cabeca, em listras
    for y in range(5, 16):
        cor = TURQ[1] if y % 3 else TURQ[0]
        c.p(32, y, cor); c.p(31, y + 1, cor)
        c.p(43, y, cor if y < 14 else m); c.p(44, y + 1, cor if y < 13 else m)
    c.r(34, 3, 41, 3, TURQ[1]); c.r(35, 2, 40, 2, AREIA[3])
    # o rosto: olho, nariz, a boca serena
    c.p(39, 7, e); c.p(40, 7, (40, 26, 30)); c.p(42, 9, e); c.p(41, 10, e)
    # o colar
    c.r(34, 13, 41, 13, TURQ[2]); c.r(35, 14, 40, 14, TURQ[0])
    # o rabo enrolado na anca
    for x, y in ((5, 25), (4, 24), (4, 23), (5, 22), (6, 22)):
        c.p(x, y, m)
    # a areia que ja subiu pelo pedestal
    for x in range(0, 56):
        alto = int(2 + 1.5 * math.sin(x * 0.3) + (2 if x < 10 or x > 47 else 0))
        c.r(x, 34 - alto, x, 33, AREIA[2] if x % 3 else AREIA[1])
    return c


def nuvem(w, semente):
    """
    Cumulo de dia: bolhas redondas por cima de uma base reta, o lado do sol (a
    direita) mais claro e a barriga azulada. Varia de nuvem para nuvem.
    """
    import random
    rnd = random.Random(semente)
    h = 14
    c = C(w, h)
    base = h - 3
    x = 3
    bolhas = []
    while x < w - 3:
        t = x / float(w)
        r = (2.0 + 4.2 * math.sin(t * math.pi) ** 0.8) * rnd.uniform(0.75, 1.1)
        bolhas.append((x, base - r * 0.55, r))
        x += max(2, int(r * rnd.uniform(0.9, 1.4)))
    for bx, by, r in bolhas:
        c.disco(bx, by, r, (248, 252, 250))
    for bx, by, r in bolhas:
        c.disco(bx + r * 0.3, by - r * 0.25, max(1.0, r * 0.55), (255, 255, 255))
    for xx in range(w):
        for yy in range(int(base) - 1, h):
            if c.cheio(xx, yy) or (yy <= base and any(abs(xx - bx) <= r for bx, _, r in bolhas)):
                c.p(xx, yy, (214, 232, 236) if yy >= base else (236, 244, 244))
    c.r(2, base + 1, w - 3, base + 1, (190, 214, 222))
    return c


def sol(k):
    """O sol do deserto: disco branco-ouro e o anel quente; na batida ele incha."""
    c = C(44, 44)
    raio = (12, 14, 13)[k]
    for r, cor in ((raio + 6, (255, 226, 150, 40)), (raio + 4, (255, 232, 160, 80)),
                   (raio + 2, (255, 222, 140, 150))):
        for y in range(44):
            for x in range(44):
                if (x - 21.5) ** 2 + (y - 21.5) ** 2 <= r * r:
                    c.s.set_at((x, y), cor)
    c.disco(21.5, 21.5, raio, (255, 214, 120))
    c.disco(21.5, 21.5, raio - 1.2, (255, 240, 176))
    c.disco(22.5, 20.5, raio - 3.2, (255, 252, 226))
    return c


def pintar_paisagem():
    print("paisagem:")
    p = f"cenario/{FASE}"
    salvar(p, "longe_1", piramide(38, 24, LONGE, 5), 1)
    salvar(p, "longe_2", mesa(34, 17, LONGE), 1)
    salvar(p, "longe_3", obelisco(LONGE), 1)
    salvar(p, "longe_4", oasis(((70, 110, 100), (96, 140, 112), (130, 170, 124), (176, 206, 150)), LONGE), 1)
    salvar(p, "longe_5", piramide(26, 16, LONGE, 4), 1)
    salvar(p, "perto_1", piramide(58, 38, PERTO, 6, topo=TURQ), 1)
    salvar(p, "perto_2", arco(PERTO), 1)
    c = C(44, 46)
    verde_longe = ((44, 96, 84), (68, 132, 100), (112, 170, 112), (176, 210, 140))
    _palmeira(c, 26, 44, 22, verde_longe, (PERTO[0], PERTO[1], PERTO[2]))
    _palmeira(c, 13, 44, 31, VERDE, (PERTO[0], PERTO[1], PERTO[2]))
    for x in range(4, 40):                                      # o capim do oasis no pe
        alto = 1 + (x * 7) % 3
        c.r(x, 45 - alto, x, 45, (96, 150, 96) if x % 2 else (70, 120, 84))
    c.r(8, 45, 34, 45, (88, 170, 176))
    salvar(p, "perto_3", c, 1)
    salvar(p, "perto_4", esfinge(PEDRA_PERTO), 1)
    salvar(p, "perto_5", mesa(52, 30, PERTO), 1)
    for i, (w, sem) in enumerate(((52, 3), (38, 7), (64, 11), (30, 17)), 1):
        salvar(p, f"nuvem_{i}", nuvem(w, sem), 1)
    salvar(p, "astro", [sol(k) for k in range(3)], 1)


# ======================================================================= UI
def emblema():
    """O emblema da carta: a ilha de areia com a piramide e o cacto-rubi, contra o sol."""
    c = C(48, 48)
    for y in range(3, 40):                                           # o disco do ceu, em faixas
        for x in range(48):
            if (x - 23.5) ** 2 + (y - 21.5) ** 2 <= 19.5 ** 2:
                faixa = (y - 3) // 5
                c.p(x, y, mist((30, 86, 130), (150, 204, 190), min(1.0, faixa / 6.0)))
    c.disco(30, 17, 7, (255, 226, 150)); c.disco(30, 17, 5.6, (255, 246, 206))
    # a ilha de arenito
    for x in range(3, 45):
        t = (x - 3) / 41.0
        fundo = 30 + int(round(math.sin(t * math.pi) ** 0.55 * 15))
        for y in range(29, fundo):
            prof = (y - 29) / 16.0
            cor = (AREIA[2], BARRO[2], BARRO[1], BARRO[0], (84, 44, 44))[min(4, int(prof * 5))]
            if (y - 29) % 4 == 3:
                cor = mist(cor, (60, 30, 36), 0.35)
            c.p(x, y, cor)
    c.r(3, 28, 44, 28, AREIA[3]); c.r(4, 29, 43, 29, AREIA[2])
    # a piramide
    for d in range(5):
        meia = 11 - d * 2.2
        y0 = 27 - (d + 1) * 3
        for y in range(y0, y0 + 3):
            for x in range(int(18 - meia), int(18 + meia)):
                c.p(x, y, PEDRA[1] if x < 17 else PEDRA[2])
        c.r(int(18 - meia), y0, int(18 + meia) - 1, y0, PEDRA[3])
    c.r(17, 10, 18, 11, TURQ[2]); c.p(18, 9, TURQ[3])
    c.r(17, 18, 18, 27, PEDRA[0])
    # o cacto-rubi
    for y in range(15, 28):
        larg = min(2, (y - 15))
        c.r(36 - larg, y, 36 + larg, y, RUBI[1])
        c.p(36 + larg, y, RUBI[2]); c.p(36 - larg, y, RUBI[0]) if larg else None
    c.p(36, 14, RUBI[3]); c.r(32, 22, 34, 22, RUBI[1]); c.r(32, 19, 32, 22, RUBI[1])
    c.r(38, 24, 40, 24, RUBI[1]); c.r(40, 21, 40, 24, RUBI[2]); c.p(32, 18, RUBI[3]); c.p(40, 20, RUBI[3])
    c.contorno((20, 12, 28))
    return c


def moldura():
    """A moldura 9-slice das dunas: a do bosque, repintada em arenito com cravos turquesa."""
    base = pygame.image.load(os.path.join(UI, "moldura_bosque.png")).convert_alpha()
    w, h = base.get_size()
    miolo = base.get_at((w // 2, h // 2))
    rampa = ((70, 40, 44), (120, 72, 58), (170, 112, 76), (212, 160, 104), (246, 214, 150))
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
        s.fill((*TURQ[1], 255), (x, y, 2, 2)); s.set_at((x + 1, y), (*TURQ[3], 255))
    pygame.image.save(s, os.path.join(UI, "moldura_dunas.png"))
    print(f"  ui/moldura_dunas.png  {w}x{h}")


def pintar_ui():
    print("ui:")
    tira = pygame.transform.scale_by(emblema().s, 2)
    pygame.image.save(tira, os.path.join(UI, "emblema_dunas.png"))
    print("  ui/emblema_dunas.png  96x96")
    moldura()


def main():
    pygame.init()
    pygame.display.set_mode((8, 8))
    for pasta in (f"jogo/{FASE}", f"cenario/{FASE}"):
        os.makedirs(os.path.join(pa.OBJ, pasta), exist_ok=True)
    pintar_perigos()
    pintar_enxame()
    pintar_blocos()
    pintar_enfeites()
    pintar_paisagem()
    pintar_ui()


if __name__ == "__main__":
    main()
