import bisect
import math
import random

import pygame

from .cenario import clima
from .config import QUADRADO

UNID = 4
GROSSURA_DA_ILHA = 128
AFINA = 120
BURACAO = 4
QUINA = 36

BRILHO = (212, 244, 255)
CRISTAL = (148, 219, 250)
TOPO = (128, 100, 139)
ROCHA_CLARA = (105, 79, 120)
ROCHA = (86, 66, 106)
ROCHA_ESCURA = (69, 50, 87)
SOMBRA = (57, 42, 74)
FUNDO = (46, 33, 61)

ACIMA = 12
PENDE = 30

contornos_prontos = {}
pontas_prontas = {}
colunas_prontas = {}
QUANTAS_GUARDA = 180


def barulhinho(dado, n, passo):
    pontos = [dado.uniform(-1.0, 1.0) for _ in range(n // passo + 3)]
    ta_de_saida = []
    for i in range(n):
        k, r = divmod(i, passo)
        t = (1.0 - math.cos(math.pi * r / passo)) * 0.5
        ta_de_saida.append(pontos[k] * (1.0 - t) + pontos[k + 1] * t)
    return ta_de_saida


def contorno_da_ilha(fase):
    if fase.qual_fase in contornos_prontos:
        return contornos_prontos[fase.qual_fase]
    chao = fase.chao_por_coluna
    col0, col1 = min(chao), max(chao) + 1
    x0 = col0 * QUADRADO
    n = (col1 - col0) * QUADRADO // UNID
    dado = random.Random(f"ilhas/{fase.semente}")
    barriga = barulhinho(dado, n, 26)
    pedras = barulhinho(dado, n, 5)

    topo = []
    for i in range(n):
        tx = (x0 + i * UNID) // QUADRADO
        if tx in chao:
            topo.append(chao[tx] * QUADRADO)
        else:
            topo.append(None)
    ta_vazio = [t is None for t in topo]
    buraquinho = so_buracao(ta_vazio)
    dist = distancia_ate_o_vazio(buraquinho)
    dist_fenda = distancia_ate_o_vazio(ta_vazio)
    raio = 2 * QUADRADO // UNID

    fundo = {}
    for i in range(n):
        if ta_vazio[i]:
            continue
        viz = []
        for k in range(max(0, i - raio), min(n, i + raio + 1)):
            if not ta_vazio[k]:
                viz.append(topo[k])
        d = GROSSURA_DA_ILHA + barriga[i] * 24 + pedras[i] * 8
        t = min(1.0, dist[i] / AFINA)
        d *= 0.2 + 0.8 * t * t * (3.0 - 2.0 * t)
        q = min(1.0, dist_fenda[i] / QUINA)
        d *= 0.55 + 0.45 * math.sqrt(q)
        y = max(topo[i] + 36, sum(viz) / len(viz) + d)
        fundo[x0 // UNID + i] = int(y) // UNID * UNID

    pontinhas_da_ilha = []
    for i in range(n):
        if ta_vazio[i]:
            continue
        if (i + 1 >= n or buraquinho[i + 1]) and i - 4 >= 0:
            pontinhas_da_ilha.append(i - 4)
        if (i == 0 or buraquinho[i - 1]) and i + 4 < n:
            pontinhas_da_ilha.append(i + 4)
    pontas_prontas[fase.qual_fase] = []
    for i in pontinhas_da_ilha:
        u = x0 // UNID + i
        if u in fundo:
            pontas_prontas[fase.qual_fase].append((u * UNID, fundo[u] - 6))
    contornos_prontos[fase.qual_fase] = fundo
    return fundo


def so_buracao(ta_vazio):
    n = len(ta_vazio)
    fendinha = BURACAO * QUADRADO // UNID
    buraquinho = list(ta_vazio)
    i = 0
    while i < n:
        j = i
        while j < n and ta_vazio[j]:
            j += 1
        if 0 < j - i < fendinha and i > 0 and j < n:
            for k in range(i, j):
                buraquinho[k] = False
        i = j + 1
    return buraquinho


def distancia_ate_o_vazio(ta_vazio):
    n = len(ta_vazio)
    d = [0] * n
    ultimo = -1
    for i in range(n):
        if ta_vazio[i]:
            ultimo = i
        d[i] = (i - ultimo) * UNID
    ultimo = n
    for i in range(n - 1, -1, -1):
        if ta_vazio[i]:
            ultimo = i
        d[i] = min(d[i], (ultimo - i) * UNID)
    return d


def chao_das_ilhas(fase, tx):
    chao = fase.chao_por_coluna
    topo = chao[tx] * QUADRADO
    perfil = contorno_da_ilha(fase)
    faixas = [perfil[(tx * QUADRADO) // UNID + k] - topo for k in range(QUADRADO // UNID)]
    s = pygame.Surface((QUADRADO, ACIMA + max(faixas) + UNID + PENDE), pygame.SRCALPHA)
    alto = ACIMA
    dado = random.Random(tx * 7919)
    for k, fim in enumerate(faixas):
        x = k * UNID
        linhas = fim // UNID
        cor_escura = int(linhas * 0.62)
        onda = (tx * 3 + k // 3) % 7
        passo = 7 + (tx % 3)
        for j in range(linhas):
            if j == 0:
                cor = CRISTAL
            elif j <= 3:
                cor = TOPO
            elif j == 4:
                cor = ROCHA_CLARA
            elif j == linhas - 1:
                cor = FUNDO
            elif j >= linhas - 3:
                cor = SOMBRA
            elif j >= cor_escura:
                cor = SOMBRA if (j + onda) % passo == 0 else ROCHA_ESCURA
            else:
                cor = ROCHA_ESCURA if (j + onda) % passo == 0 else ROCHA
            if 5 < j < cor_escura:
                sorte = dado.random()
                if sorte < 0.03:
                    cor = ROCHA_CLARA
                elif sorte < 0.034:
                    cor = CRISTAL
            s.fill(cor, (x, alto + j * UNID, UNID, UNID))
    detalhe_da_ilha(s, fase, tx, faixas, alto)
    s.fill(BRILHO, (0, alto, QUADRADO, 2))

    for lado, x in ((-1, 0), (1, QUADRADO - UNID)):
        viz = chao.get(tx + lado)
        if viz is None or viz > chao[tx]:
            fim = faixas[0 if lado < 0 else -1]
            ate = fim if viz is None else min(fim, (viz - chao[tx]) * QUADRADO)
            s.fill(ROCHA_CLARA, (x, alto + UNID * 5, UNID, max(0, ate - UNID * 6)))
            s.fill(CRISTAL, (x, alto, UNID, UNID * 2))
            s.fill(BRILHO, (x + (0 if lado < 0 else UNID - 2), alto, 2, UNID * 2))

    tem_caco_perto = any(len(fase.perigos_por_coluna.em(tx + d)) for d in (-1, 0, 1))
    if not tem_caco_perto and dado.random() < 0.34:
        k = dado.randrange(1, QUADRADO // UNID - 2) * UNID
        if dado.random() < 0.5:
            s.fill(TOPO, (k, alto - UNID, UNID * 2, UNID))
            s.fill(CRISTAL, (k + UNID, alto - UNID, UNID, UNID // 2))
        else:
            s.fill(CRISTAL, (k, alto - UNID * 2, UNID, UNID * 2))
            s.fill(BRILHO, (k, alto - UNID * 2, 2, UNID))
    for _ in range(2):
        if dado.random() < 0.3:
            k = dado.randrange(2, QUADRADO // UNID - 2)
            fim = alto + faixas[k] - 2
            comp = dado.randrange(3, PENDE // UNID - 1) * UNID
            s.fill(SOMBRA, (k * UNID + 1, fim, 2, comp))
            s.fill(CRISTAL, (k * UNID, fim + comp, UNID, UNID))
    return s


def detalhe_da_ilha(s, fase, tx, faixas, alto):
    dado = random.Random(tx * 104723 + 5)
    n = QUADRADO // UNID
    for k in range(n):
        if faixas[k] // UNID > 8:
            sorte = dado.random()
            if sorte < 0.4:
                s.fill(TOPO, (k * UNID, alto + 4 * UNID, UNID, UNID * (2 if sorte < 0.12 else 1)))
    s.fill(mistura(TOPO, BRILHO, 0.25), (0, alto + UNID, QUADRADO, UNID // 2))
    fundo = min(faixas) // UNID
    if fundo > 14 and dado.random() < 0.3:
        passo = dado.choice((-1, 1))
        k = dado.randrange(3, n - 3)
        j = dado.randrange(7, max(8, int(fundo * 0.55)))
        for _ in range(dado.randrange(3, 6)):
            if not 0 <= k < n:
                break
            s.fill(CRISTAL, (k * UNID, alto + j * UNID, UNID, UNID))
            s.fill(BRILHO, (k * UNID, alto + j * UNID, 2, 2))
            s.fill(ROCHA_ESCURA, (k * UNID, alto + (j + 1) * UNID, UNID, UNID // 2))
            k += passo
            j += 1
    if fundo > 12 and dado.random() < 0.35:
        k = dado.randrange(1, n - 4)
        j = dado.randrange(6, max(7, int(fundo * 0.5)))
        x, y = k * UNID, alto + j * UNID
        s.fill(ROCHA_CLARA, (x + UNID, y, UNID * 2, UNID * 2))
        s.fill(ROCHA_CLARA, (x, y + UNID, UNID * 4, UNID))
        s.fill(TOPO, (x + UNID, y, UNID * 2, UNID // 2))
        s.fill(SOMBRA, (x + UNID, y + UNID * 2, UNID * 3, UNID // 2))
    if not any(len(fase.perigos_por_coluna.em(tx + d)) for d in (-1, 0, 1)) and dado.random() < 0.28:
        k = dado.randrange(1, n - 3)
        s.fill(TOPO, (k * UNID, alto - UNID // 2, UNID * 3, UNID // 2))
        s.fill(mistura(TOPO, BRILHO, 0.35), (k * UNID + UNID // 2, alto - UNID, UNID * 2, UNID // 2))


FIADA = 16
FUNDO_CIDADELA = 6 * QUADRADO
LAVANDA = (206, 168, 255)
COROA_CLARA = (99, 61, 122)
COROA = (89, 50, 113)
TIJOLO = (51, 32, 74)
TIJOLO_ESCURO = (38, 22, 58)
JUNTA = (24, 11, 40)
PROFUNDO = (18, 8, 32)
RUNA = (206, 168, 255)
SETEIRA = (255, 176, 90)
PANO = (92, 40, 118)
PANO_ESCURO = (58, 22, 80)
OURO = (255, 206, 120)


def mistura(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def chao_da_cidadela(fase, tx):
    chao = fase.chao_por_coluna
    topo = chao[tx] * QUADRADO
    s = pygame.Surface((QUADRADO, ACIMA + FUNDO_CIDADELA), pygame.SRCALPHA)
    alto = ACIMA
    x0 = tx * QUADRADO
    dado = random.Random(tx * 104729)
    for y in range(topo + 14, topo + FUNDO_CIDADELA, FIADA):
        fiada = y // FIADA
        larg = 32 if fiada % 3 else 24
        desloc = (fiada * 13) % larg
        escurece = min(0.9, max(0.0, (y - topo - 30) / 170.0))
        sy = alto + (y - topo)
        bx = x0 - (x0 - desloc) % larg
        while bx < x0 + QUADRADO:
            cor = TIJOLO if ((bx // larg) * 7 + fiada) % 5 else TIJOLO_ESCURO
            cor = mistura(cor, PROFUNDO, escurece)
            a, b = max(bx, x0), min(bx + larg, x0 + QUADRADO)
            s.fill(cor, (a - x0, sy, b - a, FIADA))
            junta = mistura(mistura(JUNTA, TIJOLO, 0.35), PROFUNDO, escurece)
            if bx > x0 - larg:
                s.fill(junta, (max(0, bx - x0), sy, 2, FIADA))
            bx += larg
        s.fill(mistura(mistura(JUNTA, TIJOLO, 0.35), PROFUNDO, escurece), (0, sy, QUADRADO, 2))
    if dado.random() < 0.3:
        cx, cy = dado.randrange(8, QUADRADO - 12), alto + dado.randrange(24, 90)
        for k in range(5):
            s.fill(JUNTA, (cx + k * 2, cy + k * 3 + (k % 2), 2, 3))
    if dado.random() < 0.12:
        cx, cy = dado.randrange(10, QUADRADO - 16), alto + 30
        for dx, dy in ((2, 0), (4, 0), (0, 2), (6, 2), (0, 4), (6, 4), (2, 6), (4, 6)):
            s.fill(RUNA, (cx + dx, cy + dy, 2, 2))
        s.fill(mistura(RUNA, TIJOLO, 0.55), (cx + 2, cy + 2, 4, 4))
    sorte = (tx * 2654435761 >> 9) % 100
    if sorte < 9:
        x = 20 + (tx % 2) * 4
        s.fill(JUNTA, (x - 2, alto + 30, 8, 26))
        s.fill(SETEIRA, (x, alto + 34, 4, 18))
        s.fill(mistura(SETEIRA, (255, 255, 255), 0.4), (x, alto + 34, 2, 6))
    elif sorte < 16:
        x = 14
        s.fill(JUNTA, (x - 2, alto + 14, 24, 4))
        s.fill(PANO_ESCURO, (x, alto + 18, 20, 40))
        s.fill(PANO, (x + 2, alto + 18, 16, 38))
        s.fill(LAVANDA, (x, alto + 18, 2, 40))
        s.fill(LAVANDA, (x + 18, alto + 18, 2, 40))
        s.fill(PANO, (x + 4, alto + 58, 12, 2))
        s.fill(PANO_ESCURO, (x + 6, alto + 60, 8, 2))
        for dx, dy in ((6, 0), (8, 0), (4, 2), (10, 2), (4, 4), (10, 4), (6, 6), (8, 6)):
            s.fill(OURO, (x + dx, alto + 32 + dy, 2, 2))
    s.fill(COROA, (0, alto, QUADRADO, 14))
    s.fill(COROA_CLARA, (0, alto + 2, QUADRADO, 2))
    s.fill(JUNTA, (0, alto + 12, QUADRADO, 2))
    junta = (x0 // 48) % 2 * 24 + 12
    s.fill(JUNTA, (junta, alto + 4, 2, 8))
    s.fill(LAVANDA, (0, alto, QUADRADO, 2))
    for lado, x in ((-1, 0), (1, QUADRADO - 2)):
        viz = chao.get(tx + lado)
        if viz is None or viz > chao[tx]:
            ate = FUNDO_CIDADELA if viz is None else (viz - chao[tx]) * QUADRADO
            s.fill(COROA_CLARA, (x, alto + 2, 2, min(ate, FUNDO_CIDADELA) - 2))
            s.fill(LAVANDA, (x, alto, 2, 12))
    return s


PX = 2
LAJE_ALTA = 12 * PX
FUNDO_BOSQUE = 6 * QUADRADO
CAMADA = 24
LAJE_LUZ = (138, 152, 126)
LAJE_TONS = ((106, 116, 100), (114, 126, 106), (98, 108, 94))
LAJE_MEIA = (86, 98, 88)
LAJE_SOMBRA = (64, 78, 72)
JUNTA_LAJE = (30, 40, 38)
MUSGO_CLARO = (122, 176, 86)
MUSGO = (92, 140, 70)
MUSGO_ESCURO = (58, 94, 60)
TERRA_TONS = ((34, 62, 54), (28, 53, 48), (40, 70, 60))
TERRA_VEIO = (21, 42, 39)
TERRA_LUZ = (52, 88, 72)
SOMBRA_LAJE = (18, 36, 34)
PROFUNDO_BOSQUE = (12, 26, 28)
PEDRA_LUZ = (94, 114, 106)
PEDRA_CORPO = (66, 86, 82)
PEDRA_SOMBRA = (42, 60, 58)
PASTA_DO_JOGO = (46, 50, 42)
RAIZ_NO = (74, 80, 62)
FLORES = ((236, 226, 150), (176, 214, 255), (228, 236, 240))
AMARELO_MIOLO = (250, 196, 90)
COGUMELO = (150, 255, 200)
CAULE = (196, 206, 196)

juntas_prontas = {}


def _h(*valores):
    x = 0x9E3779B1
    for v in valores:
        x = ((x ^ (v & 0xFFFFFFFF)) * 0x85EBCA6B) & 0xFFFFFFFF
        x ^= x >> 13
    return x


def la_no_fundo(cor, prof):
    return mistura(cor, PROFUNDO_BOSQUE, min(1.0, max(0.0, (prof - 36) / (FUNDO_BOSQUE - 84))))


def faz_lajes(fase):
    if fase.qual_fase not in juntas_prontas:
        chao = fase.chao_por_coluna
        x, fim = min(chao) * QUADRADO, (max(chao) + 1) * QUADRADO
        dado = random.Random(f"bosque/{fase.semente}")
        lista = []
        x += dado.randrange(8, 40, PX)
        while x < fim:
            lista.append(x)
            x += dado.randrange(26, 64, PX)
        juntas_prontas[fase.qual_fase] = lista
    return juntas_prontas[fase.qual_fase]


def faz_divisa(xw, k):
    return k * CAMADA + PX * round(1.3 * math.sin(xw * 0.045 + k * 2.3) +
                                   0.6 * math.sin(xw * 0.11 + k))


def faz_pedra(s, x, y, w, h, prof):
    corpo, luz, sombra = (la_no_fundo(c, prof) for c in (PEDRA_CORPO, PEDRA_LUZ, PEDRA_SOMBRA))
    s.fill(corpo, (x + PX, y, w - 2 * PX, h))
    s.fill(corpo, (x, y + PX, w, h - 2 * PX))
    s.fill(luz, (x + PX, y, w - 2 * PX, PX))
    s.fill(luz, (x + w - PX, y + PX, PX, max(0, h - 3 * PX)))
    s.fill(sombra, (x + PX, y + h - PX, w - 2 * PX, PX))
    s.fill(la_no_fundo(TERRA_VEIO, prof), (x + 2 * PX, y + h, w - 3 * PX, PX))


def chao_do_bosque(fase, tx):
    chao = fase.chao_por_coluna
    n = chao[tx]
    topo = n * QUADRADO
    x0 = tx * QUADRADO
    s = pygame.Surface((QUADRADO, ACIMA + FUNDO_BOSQUE), pygame.SRCALPHA)
    a = ACIMA
    dado = random.Random(tx * 7727 + n)
    ini, fim = topo + LAJE_ALTA, topo + FUNDO_BOSQUE

    for xs in range(0, QUADRADO, PX):
        xw = x0 + xs
        k = ini // CAMADA - 1
        de = faz_divisa(xw, k)
        while de < fim:
            ate = faz_divisa(xw, k + 1)
            y0, y1 = max(ini, de), min(fim, ate)
            if y1 > y0:
                cor = TERRA_TONS[k % 3]
                s.fill(la_no_fundo(cor, (y0 + y1) // 2 - topo), (xs, a + y0 - topo, PX, y1 - y0))
                if y1 < fim:
                    s.fill(la_no_fundo(TERRA_VEIO, y1 - topo), (xs, a + y1 - topo, PX, PX))
                    if _h(xw // 6, k, 3) % 5 == 0:
                        s.fill(la_no_fundo(TERRA_LUZ, y1 - topo), (xs, a + y1 - topo + PX, PX, PX))
            k, de = k + 1, ate

    s.fill(SOMBRA_LAJE, (0, a + LAJE_ALTA, QUADRADO, PX))
    s.fill(mistura(SOMBRA_LAJE, TERRA_TONS[0], 0.5), (0, a + LAJE_ALTA + PX, QUADRADO, PX))

    for cy in range(ini // 34, fim // 34 + 1):
        for cx in range((x0 - 30) // 44, (x0 + QUADRADO + 30) // 44 + 1):
            h = _h(cx, cy, 5)
            if h % 100 >= 24:
                continue
            grande = (h >> 24) % 4 == 0
            w = (8 if grande else 4) + (h >> 7) % 4 * PX
            alto = (6 if grande else 4) + (h >> 10) % 2 * PX
            px = cx * 44 + (h >> 13) % (44 - w) // PX * PX
            py = cy * 34 + (h >> 18) % (34 - alto) // PX * PX
            if ini + 8 <= py and py + alto <= fim - 40:
                faz_pedra(s, px - x0, a + py - topo, w, alto, py - topo)

    for _ in range(2):
        if dado.random() < 0.45:
            x = dado.randrange(4, QUADRADO - 8, PX)
            comp = dado.randrange(14, 46, PX)
            for i in range(0, comp, PX):
                if i > 4 and dado.random() < 0.3:
                    x = min(QUADRADO - 4, max(2, x + dado.choice((-PX, PX))))
                prof = LAJE_ALTA + i
                grossa = i < comp // 3
                s.fill(la_no_fundo(PASTA_DO_JOGO, prof), (x, a + prof, 2 * PX if grossa else PX, PX))
                if grossa or i % 6 == 0:
                    s.fill(la_no_fundo(RAIZ_NO, prof), (x + (PX if grossa else 0), a + prof, PX, PX))

    juntas = faz_lajes(fase)
    i0 = bisect.bisect_right(juntas, x0)
    i1 = bisect.bisect_left(juntas, x0 + QUADRADO)
    cortes = [x0] + juntas[i0:i1] + [x0 + QUADRADO]
    for xa, xb in zip(cortes, cortes[1:]):
        tom = LAJE_TONS[_h(bisect.bisect_right(juntas, xa), 1) % 3]
        s.fill(LAJE_LUZ, (xa - x0, a + PX, xb - xa, PX))
        s.fill(tom, (xa - x0, a + 2 * PX, xb - xa, 7 * PX))
        s.fill(LAJE_MEIA, (xa - x0, a + 9 * PX, xb - xa, PX))
        s.fill(LAJE_SOMBRA, (xa - x0, a + 10 * PX, xb - xa, PX))
    s.fill(JUNTA_LAJE, (0, a + 11 * PX, QUADRADO, PX))
    for laje in range(i0 - 1, i1):
        la = juntas[laje] if laje >= 0 else juntas[0] - 60
        lb = juntas[laje + 1] if laje + 1 < len(juntas) else la + 60
        h = _h(laje, 7)
        for k in range(3):
            hk = _h(laje, 11, k)
            s.fill(LAJE_MEIA, (la + PX + hk % max(PX, lb - la - 3 * PX) // PX * PX - x0,
                               a + (3 + (hk >> 8) % 5) * PX, PX, PX))
        if h % 10 < 3:
            px = la + (6 + (h >> 4) % max(1, lb - la - 14)) // PX * PX
            for d in range(2 + (h >> 20) % 4):
                s.fill(LAJE_SOMBRA if d else JUNTA_LAJE, (px - x0, a + (2 + d) * PX, PX, PX))
                px += PX * ((_h(laje, 13, d) % 3) - 1)
        if (h >> 8) % 10 < 5:
            w = (3 + (h >> 12) % 4) * PX
            s.fill(MUSGO, (la - x0, a + PX, w, 2 * PX))
            s.fill(MUSGO_CLARO, (la - x0 + PX, a + PX, w - 2 * PX, PX))
            s.fill(MUSGO, (la - x0, a + 3 * PX, w // 2 // PX * PX, 2 * PX))
            s.fill(MUSGO_ESCURO, (la - x0, a + 5 * PX, PX, PX))
    for j in juntas[max(0, i0 - 1):i1 + 1]:
        s.fill(JUNTA_LAJE, (j - x0, a + PX, PX, 10 * PX))
        s.fill(LAJE_MEIA, (j - x0 - PX, a + PX, PX, PX))
        s.fill(LAJE_MEIA, (j - x0 + PX, a + PX, PX, PX))
    for _ in range(dado.randrange(1, 4)):
        s.fill(MUSGO_ESCURO, (dado.randrange(0, QUADRADO - PX, PX), a + LAJE_ALTA,
                              PX, dado.randrange(1, 4) * PX))
    s.fill(fase.cores_da_fase.chao_topo, (0, a, QUADRADO, PX))

    for lado, x in ((-1, 0), (1, QUADRADO - PX)):
        viz = chao.get(tx + lado)
        if viz is None or viz > n:
            ate = FUNDO_BOSQUE if viz is None else min(FUNDO_BOSQUE, (viz - n) * QUADRADO)
            s.fill((0, 0, 0, 0), (x, a, PX, PX))
            s.fill(fase.cores_da_fase.chao_topo, (x, a + PX, PX, 10 * PX))
            face = TERRA_LUZ if lado > 0 else TERRA_VEIO
            for y in range(LAJE_ALTA, ate, 16):
                s.fill(la_no_fundo(face, y), (x, a + y, PX, min(16, ate - y)))
            for _ in range(3):
                if dado.random() < 0.7:
                    dx = x - lado * dado.randrange(0, 4) * PX
                    s.fill(MUSGO, (dx, a + LAJE_ALTA - PX, PX, dado.randrange(2, 8) * PX))
                    s.fill(MUSGO_CLARO, (dx, a + LAJE_ALTA - PX, PX, PX))

    perto = any(len(fase.perigos_por_coluna.em(tx + d)) for d in (-1, 0, 1)) or \
        any(bx in (tx - 1, tx, tx + 1) for bx, _ in fase.blocos)
    sorte = dado.random()
    if not perto and sorte < 0.55:
        x = dado.randrange(6, QUADRADO - 14, PX)
        if sorte < 0.32:
            w = dado.randrange(4, 8) * PX
            s.fill(MUSGO_ESCURO, (x, a - PX, w, PX))
            s.fill(MUSGO, (x + PX, a - 2 * PX, w - 2 * PX, PX))
            s.fill(MUSGO, (x + 2 * PX, a - 3 * PX, w - 4 * PX, PX))
            s.fill(MUSGO_CLARO, (x + 2 * PX, a - 3 * PX, PX, PX))
            s.fill(MUSGO_CLARO, (x + PX, a - 2 * PX, PX, PX))
        elif sorte < 0.46:
            s.fill(MUSGO, (x, a - 3 * PX, PX, 3 * PX))
            s.fill(MUSGO_CLARO, (x + PX, a - 2 * PX, PX, PX))
            flor = FLORES[dado.randrange(len(FLORES))]
            s.fill(flor, (x - PX, a - 4 * PX, 3 * PX, PX))
            s.fill(flor, (x, a - 5 * PX, PX, 3 * PX))
            s.fill(AMARELO_MIOLO, (x, a - 4 * PX, PX, PX))
        else:
            s.fill(CAULE, (x + PX, a - 2 * PX, PX, 2 * PX))
            s.fill(mistura(COGUMELO, (0, 0, 0), 0.35), (x, a - 3 * PX, 3 * PX, PX))
            s.fill(COGUMELO, (x, a - 4 * PX, 3 * PX, PX))
            s.fill(mistura(COGUMELO, (255, 255, 255), 0.6), (x + PX, a - 4 * PX, PX, PX))
    return s


def fosso(tela, col0, col1, y, cam):
    alto = tela.get_height()
    x, w, sy = cam.transform_x(col0 * QUADRADO), (col1 - col0) * QUADRADO, cam.transform_y(y)
    if sy >= alto:
        return
    faixas = ((PX, MUSGO_ESCURO), (3 * PX, TERRA_TONS[2]), (4 * PX, TERRA_TONS[0]),
              (4 * PX, mistura(TERRA_VEIO, PROFUNDO_BOSQUE, 0.4)))
    for grossura, cor in faixas:
        tela.fill(cor, (x, sy, w, grossura))
        sy += grossura
    tela.fill(PROFUNDO_BOSQUE, (x, sy, w, alto - sy))
    for k in range(0, w, 12):
        h = _h(col0 * QUADRADO + k, 9)
        if h % 3 == 0:
            tela.fill(PEDRA_CORPO, (x + k + h % 8 // PX * PX, cam.transform_y(y) + 2 * PX, 3 * PX, PX))

FUNDO_DUNAS = 6 * QUADRADO
AREIA_LUZ = (255, 232, 160)
AREIA = (238, 196, 126)
AREIA_MEIA = (220, 170, 106)
AREIA_SOMBRA = (190, 134, 86)
ARENITO = ((198, 124, 78), (174, 100, 66), (212, 146, 92), (156, 86, 60), (186, 112, 72))
VEIO_DUNAS = (126, 66, 52)
CREME = (232, 190, 132)
PROFUNDO_DUNAS = (64, 32, 38)
GLIFO = (72, 226, 208)
FOSSIL = (240, 214, 170)


texturas_prontas = {}
sombras_prontas = {}
quinas_prontas = {}


def faz_textura(nome, cor_do_lugar, u0, u1):
    chave = (nome, u0, u1)
    if chave not in texturas_prontas:
        cores = {u: cor_do_lugar(u) for u in range(u0, u1 + 2 * PX)}
        faixas = {}
        for p in (0, 1):
            f = pygame.Surface((PX, u1 - u0 + 2 * PX)).convert()
            for r in range(0, u1 - u0, 2):
                f.fill(cores[u0 + p + r][0], (0, r, PX, 2))
            faixas[p] = f
        texturas_prontas[chave] = (faixas, cores)
    return texturas_prontas[chave]


def qual_faixa(fase, folga):
    alturas = [c * QUADRADO for c in fase.chao_por_coluna.values()]
    return min(alturas) - folga, max(alturas) + 6 * QUADRADO + folga


def recorta(s, textura, u0, x, b, y, alto):
    p = (b - u0) % 2
    s.blit(textura[p], (x, y), (0, b - u0 - p, PX, alto))


def faz_sombra(cor, inicio, largura, alto, fim, curva):
    chave = (cor, inicio, largura, alto, fim, curva)
    if chave not in sombras_prontas:
        f = pygame.Surface((largura, alto), pygame.SRCALPHA)
        for y in range(0, alto, PX):
            k = min(1.0, max(0.0, (y - fim[0]) / fim[1])) ** curva
            f.fill((*cor, int(round(255 * k))), (0, y, largura, PX))
        sombras_prontas[chave] = f
    return sombras_prontas[chave]


def faz_quina(cor, fundo, de, ate, fim, curva=1.0):
    chave = (cor, fundo, de, ate, fim, curva)
    if chave not in quinas_prontas:
        f = pygame.Surface((2, max(1, ate - de))).convert()
        for y in range(de, ate, PX):
            k = min(1.0, max(0.0, (y - fim[0]) / fim[1])) ** curva
            f.fill(mistura(cor, fundo, k), (0, y - de, 2, PX))
        quinas_prontas[chave] = f
    return quinas_prontas[chave]


def cor_da_areia(u):
    k = u // 26
    cor = ARENITO[_h(k, 3) % len(ARENITO)]
    if (u - PX) // 26 != k:
        return mistura(cor, VEIO_DUNAS, 0.55), False
    if (u - 2 * PX) // 26 != k and _h(k, 5) % 4 == 0:
        return mistura(cor, CREME, 0.5), False
    desce = 0.0
    for d in (4, 8, 12):
        if (u + d * PX) // 26 != k:
            desce = (13 - d) / 26.0
            break
    return mistura(cor, VEIO_DUNAS, desce * 0.5), True


def chao_das_dunas(fase, tx):
    chao = fase.chao_por_coluna
    topo = chao[tx] * QUADRADO
    s = pygame.Surface((QUADRADO, ACIMA + FUNDO_DUNAS), pygame.SRCALPHA)
    alto = ACIMA
    x0 = tx * QUADRADO
    u0, u1 = qual_faixa(fase, 16)
    textura, cores = faz_textura("dunas", cor_da_areia, u0, u1)
    for px in range(0, QUADRADO, PX):
        xw = x0 + px
        onda = 6.0 * math.sin(xw * 0.017) + 2.5 * math.sin(xw * 0.049 + 1.3)
        b = topo + 10 + int(math.floor(onda + 0.5))
        recorta(s, textura, u0, px, b, alto + 10, FUNDO_DUNAS - 10)
        xc = xw // PX
        passo = 31
        yc = _h(xc, 7) % passo
        while yc < (FUNDO_DUNAS - 10) // PX:
            cor, pedra = cores[b + yc * PX]
            if pedra:
                s.fill(mistura(cor, VEIO_DUNAS, 0.3), (px, alto + 10 + yc * PX, PX, PX))
            yc += 20 + _h(xc, yc, 8) % 23
    s.blit(faz_sombra(PROFUNDO_DUNAS, 10, QUADRADO, FUNDO_DUNAS + alto, (alto + 30, FUNDO_DUNAS - 90.0), 0.8),
           (0, 0))
    sorte = _h(tx, 11) % 100
    if sorte < 9:
        cx, cy = 10 + _h(tx, 12) % 20, alto + 34 + _h(tx, 13) % 50
        for dx, dy in ((2, 0), (4, 0), (6, 2), (6, 4), (4, 6), (2, 6), (0, 4), (0, 2), (2, 2), (3, 3)):
            s.fill(FOSSIL if (dx + dy) % 4 else mistura(FOSSIL, VEIO_DUNAS, 0.4), (cx + dx, cy + dy, PX, PX))
    elif sorte < 15:
        cx, cy = 16 + _h(tx, 14) % 14, alto + 34
        tinta = mistura(GLIFO, ARENITO[3], 0.35)
        sulco = mistura(VEIO_DUNAS, ARENITO[3], 0.3)
        for dx, dy in ((-2, -6), (0, -6), (2, -6), (-6, -2), (-6, 0), (-6, 2), (6, -2), (6, 0),
                       (6, 2), (-2, 6), (0, 6), (2, 6), (-4, -4), (4, -4), (-4, 4), (4, 4)):
            s.fill(sulco, (cx + dx, cy + dy + PX, PX, PX))
            s.fill(tinta, (cx + dx, cy + dy, PX, PX))
        for dx, dy in ((0, -10), (0, 10), (-10, 0), (10, 0)):
            s.fill(tinta, (cx + dx, cy + dy, PX, PX))
    elif sorte < 21:
        cx, cy = 8 + _h(tx, 15) % 24, alto + 60 + _h(tx, 16) % 60
        s.fill(ARENITO[3], (cx, cy, 10, 4))
        s.fill(CREME, (cx + 2, cy - 2, 6, 2))
        s.fill(VEIO_DUNAS, (cx + 2, cy + 4, 6, 2))
    s.fill(AREIA_SOMBRA, (0, alto + 8, QUADRADO, 4))
    s.fill(AREIA_MEIA, (0, alto + 4, QUADRADO, 6))
    s.fill(AREIA, (0, alto + 2, QUADRADO, 4))
    s.fill(AREIA_LUZ, (0, alto, QUADRADO, 2))
    for px in range(0, QUADRADO, PX):
        xw = x0 + px
        onda = int(2.0 + 1.6 * math.sin(xw * 0.19) + 1.2 * math.sin(xw * 0.071 + 2.0))
        s.fill(AREIA_MEIA, (px, alto + 4 + onda // 2 * PX, PX, PX))
        if _h(xw // PX, 21) % 9 == 0:
            s.fill(AREIA_LUZ, (px, alto + 4, PX, PX))
        dente = _h(xw // (2 * PX), 23) % 4
        s.fill(AREIA_SOMBRA, (px, alto + 12, PX, dente * PX))
    if _h(tx, 31) % 5 == 0:
        gx = 6 + _h(tx, 32) % 30
        for k, (dx, h) in enumerate(((0, 6), (2, 9), (4, 7), (6, 5))):
            s.fill((214, 176, 92) if k % 2 else (176, 140, 70), (gx + dx, alto - h + 2, PX, h))
        s.fill((236, 206, 120), (gx + 2, alto - 9 + 2, PX, PX))
    for lado, x in ((-1, 0), (1, QUADRADO - 2)):
        viz = chao.get(tx + lado)
        if viz is None or viz > chao[tx]:
            ate = FUNDO_DUNAS if viz is None else (viz - chao[tx]) * QUADRADO
            cor = CREME if lado > 0 else VEIO_DUNAS
            s.blit(faz_quina(cor, PROFUNDO_DUNAS, 12, min(ate, FUNDO_DUNAS), (40, FUNDO_DUNAS - 70.0)),
                   (x, alto + 12))
            s.fill(AREIA_LUZ, (x, alto, 2, 12))
    return s


def buraco_das_dunas(tela, col0, col1, y, cam):
    alto = tela.get_height()
    x, w, sy = cam.transform_x(col0 * QUADRADO), (col1 - col0) * QUADRADO, cam.transform_y(y)
    if sy >= alto:
        return
    for grossura, cor in ((PX, AREIA_SOMBRA), (3 * PX, ARENITO[3]),
                          (4 * PX, mistura(ARENITO[3], PROFUNDO_DUNAS, 0.45)),
                          (4 * PX, mistura(VEIO_DUNAS, PROFUNDO_DUNAS, 0.6))):
        tela.fill(cor, (x, sy, w, grossura))
        sy += grossura
    tela.fill(PROFUNDO_DUNAS, (x, sy, w, alto - sy))
    for k in range(0, w, 10):
        h = _h(col0 * QUADRADO + k, 9)
        if h % 3 == 0:
            tela.fill(AREIA_MEIA, (x + k + h % 6, cam.transform_y(y), 2 * PX, PX))


FUNDO_GELEIRA = 6 * QUADRADO
NEVE_LUZ = (244, 252, 255)
NEVE = (216, 236, 252)
NEVE_SOMBRA = (162, 196, 236)
NEVE_FUNDA = (120, 160, 214)
GELO = ((76, 128, 188), (64, 112, 172), (90, 146, 204), (58, 100, 160))
GELO_VEIO = (44, 78, 132)
GELO_LUZ = (150, 214, 250)
BOLHA = (206, 238, 255)
PROFUNDO_GELO = (12, 20, 46)
AURORA_GELO = (110, 255, 214)


def cor_do_gelo(u):
    k = u // 22
    cor = GELO[_h(k, 4) % len(GELO)]
    if (u - PX) // 22 != k:
        return mistura(cor, GELO_VEIO, 0.6), False
    if (u - 2 * PX) // 22 != k:
        return mistura(cor, GELO_LUZ, 0.35), False
    return cor, True


def chao_da_geleira(fase, tx):
    chao = fase.chao_por_coluna
    topo = chao[tx] * QUADRADO
    s = pygame.Surface((QUADRADO, ACIMA + FUNDO_GELEIRA), pygame.SRCALPHA)
    alto = ACIMA
    x0 = tx * QUADRADO
    u0, u1 = qual_faixa(fase, 8)
    u1 += int(max(fase.chao_por_coluna) * QUADRADO * 0.18) + QUADRADO
    textura, _ = faz_textura("geleira", cor_do_gelo, u0, u1)
    for px in range(0, QUADRADO, PX):
        xw = x0 + px
        b = topo + 12 + int(math.floor(xw * 0.18 + 4.0 * math.sin(xw * 0.023) + 0.5))
        recorta(s, textura, u0, px, b, alto + 12, FUNDO_GELEIRA - 12)
    s.blit(faz_sombra(PROFUNDO_GELO, 12, QUADRADO, FUNDO_GELEIRA + alto, (alto + 26, FUNDO_GELEIRA - 80.0), 0.75),
           (0, 0))
    for n in range(3):
        if _h(tx, 40 + n) % 3 == 0:
            bx = 4 + _h(tx, 50 + n) % 38
            by = 22 + _h(tx, 60 + n) % 110
            luz = mistura(BOLHA, PROFUNDO_GELO, min(0.8, by / 160.0))
            s.fill(luz, (bx, alto + by, PX * 2, PX))
            s.fill(luz, (bx - PX, alto + by + PX, PX * 4, PX))
            s.fill(luz, (bx, alto + by + 2 * PX, PX * 2, PX))
            s.fill(mistura(luz, (255, 255, 255), 0.6), (bx, alto + by, PX, PX))
    if _h(tx, 71) % 4 == 0:
        fx = 8 + _h(tx, 72) % 30
        for y in range(16, 120, PX):
            fx += (1 if (y // 6) % 2 else -1) * (PX if _h(tx, y) % 3 == 0 else 0)
            prof = min(1.0, y / 140.0)
            s.fill(mistura(GELO_VEIO, PROFUNDO_GELO, prof * 0.6), (fx, alto + y, PX, PX))
            if y < 60:
                s.fill(mistura(GELO_LUZ, GELO[0], 0.4), (fx + PX, alto + y, PX, PX))
    if _h(tx, 81) % 17 == 0:
        cx, cy = 18 + _h(tx, 82) % 10, alto + 44
        for dx, dy in ((2, 0), (4, 0), (0, 2), (6, 2), (0, 4), (6, 4), (2, 6), (4, 6), (3, 3)):
            s.fill(mistura(AURORA_GELO, GELO[1], 0.3), (cx + dx, cy + dy, PX, PX))
    for px in range(0, QUADRADO, PX):
        xw = x0 + px
        monte = 2.0 + 1.6 * math.sin(xw * 0.09) + 1.2 * math.sin(xw * 0.031 + 1.7)
        y0 = alto - int(monte // PX) * PX + 2 * PX
        s.fill(NEVE_FUNDA, (px, alto + 12, PX, 2 * PX))
        s.fill(NEVE_SOMBRA, (px, alto + 8, PX, 4 + (PX if _h(xw // PX, 3) % 3 == 0 else 0)))
        s.fill(NEVE, (px, y0, PX, alto + 8 - y0))
        s.fill(NEVE_LUZ, (px, y0, PX, PX))
        if _h(xw // PX, 91) % 13 == 0:
            s.fill((255, 255, 255), (px, y0 + PX, PX, PX))
    for px in range(0, QUADRADO, 2 * PX):
        gota = _h((x0 + px) // (2 * PX), 23) % 5
        if gota >= 3:
            s.fill(NEVE_SOMBRA, (px, alto + 16, PX, (gota - 1) * PX))
            s.fill(NEVE, (px, alto + 16, PX, PX))
    for lado, x in ((-1, 0), (1, QUADRADO - 2)):
        viz = chao.get(tx + lado)
        if viz is None or viz > chao[tx]:
            ate = FUNDO_GELEIRA if viz is None else (viz - chao[tx]) * QUADRADO
            cor = GELO_LUZ if lado > 0 else GELO_VEIO
            s.blit(faz_quina(cor, PROFUNDO_GELO, 12, min(ate, FUNDO_GELEIRA), (26, FUNDO_GELEIRA - 80.0)),
                   (x, alto + 12))
            s.fill(NEVE_LUZ, (x, alto + 2, 2, 10))
    return s


def buraco_da_geleira(tela, col0, col1, y, cam):
    alto = tela.get_height()
    x, w, sy = cam.transform_x(col0 * QUADRADO), (col1 - col0) * QUADRADO, cam.transform_y(y)
    if sy >= alto:
        return
    for grossura, cor in ((PX, NEVE_FUNDA), (3 * PX, GELO[3]),
                          (4 * PX, mistura(GELO[3], PROFUNDO_GELO, 0.5)),
                          (4 * PX, mistura(GELO_VEIO, PROFUNDO_GELO, 0.7))):
        tela.fill(cor, (x, sy, w, grossura))
        sy += grossura
    tela.fill(PROFUNDO_GELO, (x, sy, w, alto - sy))
    for k in range(0, w, 10):
        h = _h(col0 * QUADRADO + k, 9)
        if h % 3 == 0:
            tela.fill(NEVE_SOMBRA, (x + k + h % 6, cam.transform_y(y), 2 * PX, PX))


ESTILO = {"bosque": chao_do_bosque, "dunas": chao_das_dunas, "ilhas": chao_das_ilhas,
          "geleira": chao_da_geleira, "eclipse": chao_da_cidadela}
PREENCHER = {"bosque": (FUNDO_BOSQUE, PROFUNDO_BOSQUE), "dunas": (FUNDO_DUNAS, PROFUNDO_DUNAS),
             "geleira": (FUNDO_GELEIRA, PROFUNDO_GELO),
             "eclipse": (FUNDO_CIDADELA, PROFUNDO)}


FORCA_DO_CLIMA = 0.55
cores_la_embaixo = {}


def pinta_clima(s, fase, tx):
    c = clima(fase, (tx + 0.5) * QUADRADO)
    if c is None:
        return
    mult = [int(255 - (255 - m) * FORCA_DO_CLIMA) for m in c[0]]
    soma = [int(a * FORCA_DO_CLIMA * 0.6) for a in c[1]]
    s.fill(mult, special_flags=pygame.BLEND_RGB_MULT)
    s.fill(soma, special_flags=pygame.BLEND_RGB_ADD)


def pega_coluna(fase, tx):
    chave = (fase.qual_fase, tx)
    if chave not in colunas_prontas:
        s = ESTILO[fase.nome_da_musica](fase, tx)
        pinta_clima(s, fase, tx)
        colunas_prontas[chave] = s
        if len(colunas_prontas) > QUANTAS_GUARDA:
            del colunas_prontas[next(iter(colunas_prontas))]
    return colunas_prontas[chave]


ADIANTE = 6


def prepara(fase):
    if fase.nome_da_musica == "ilhas":
        contorno_da_ilha(fase)
    elif fase.nome_da_musica == "bosque":
        faz_lajes(fase)
    for tx in sorted(fase.chao_por_coluna)[:40]:
        pega_coluna(fase, tx)


def pula_pro_fim(fase, c1):
    chao = fase.chao_por_coluna
    for tx in range(c1, c1 + ADIANTE):
        if tx in chao and (fase.qual_fase, tx) not in colunas_prontas:
            pega_coluna(fase, tx)
            return


def desenha_atras(tela, fase, cam, c0, c1, tempo):
    if fase.nome_da_musica == "ilhas":
        contorno_da_ilha(fase)
        for x, y in pontas_prontas[fase.qual_fase]:
            if cam.x - 16 < x < cam.x + QUADRADO * (c1 - c0) + 16:
                faz_cascata(tela, cam.transform_x(x), cam.transform_y(y), tempo)


def cor_la_embaixo(fase, tx):
    chave = (fase.qual_fase, tx)
    if chave not in cores_la_embaixo:
        s = pygame.Surface((1, 1))
        s.fill(PREENCHER[fase.nome_da_musica][1])
        pinta_clima(s, fase, tx)
        cores_la_embaixo[chave] = s.get_at((0, 0))
    return cores_la_embaixo[chave]


def mostra_na_tela(tela, fase, tx, x, y):
    tela.blit(pega_coluna(fase, tx), (x, y - ACIMA))
    if fase.nome_da_musica in PREENCHER:
        fundo = PREENCHER[fase.nome_da_musica][0]
        alto = tela.get_height()
        if y + fundo < alto:
            tela.fill(cor_la_embaixo(fase, tx), (x, y + fundo, QUADRADO, alto - y - fundo))


def faz_cascata(tela, x, y, tempo):
    alto = tela.get_height() - y
    if alto <= 0:
        return
    tela.fill(CRISTAL, (x, y, 6, alto))
    tela.fill((128, 210, 247), (x + 4, y, 2, alto))
    desce = int(tempo * 150) % 22
    for yy in range(y - 22 + desce, y + alto, 22):
        tela.fill(BRILHO, (x + 1, max(y, yy), 2, 8))
