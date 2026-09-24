"""
O chao das Ilhas Suspensas: cada trecho de chao e desenhado como uma ilha de
pedra flutuando -- linha de cristal no topo, rocha em camadas e o fundo
arredondado, com o ceu aparecendo por baixo. A paleta e a das ilhas geradas
para a fase, entao o chao e o cenario sao da mesma familia.

So muda o DESENHO: a colisao continua sendo o grid de fases.py.

Cada coluna de 1 tile e desenhada uma vez numa superficie e guardada; na tela,
o chao e so uma copia por coluna visivel.
"""

import math
import random

import pygame

from .config import TILE

UNID = 4            # o "pixel" da rocha: 4 px, o mesmo tamanho de pixel do fundo
ESPESSURA = 128     # quanto a ilha desce abaixo do topo, em media (~2,7 tiles)
AFINA = 120         # nos ultimos px antes de um vao grande, a ilha afina ate a ponta
VAO_GRANDE = 4      # vao de ate 3 tiles e uma fenda: a ilha nao afina...
QUINA = 36          # ...so arredonda as quinas de baixo, nos ultimos px antes dela

# a paleta das ilhas com cascata que o gerador fez para esta fase
BRILHO = (212, 244, 255)       # a linha do chao, a que o olho segue
CRISTAL = (148, 219, 250)
TOPO = (128, 100, 139)
ROCHA_CLARA = (105, 79, 120)
ROCHA = (86, 66, 106)
ROCHA_ESCURA = (69, 50, 87)
SOMBRA = (57, 42, 74)
FUNDO = (46, 33, 61)

_perfis = {}
_colunas = {}


# ------------------------------------------------------------------ perfil
def _ruido(rnd, n, passo):
    """Ruido suave: um valor sorteado a cada `passo` faixas, interpolado em cosseno."""
    pontos = [rnd.uniform(-1.0, 1.0) for _ in range(n // passo + 3)]
    saida = []
    for i in range(n):
        k, r = divmod(i, passo)
        t = (1.0 - math.cos(math.pi * r / passo)) * 0.5
        saida.append(pontos[k] * (1.0 - t) + pontos[k + 1] * t)
    return saida


def _perfil(fase):
    """
    {faixa: y do fundo da ilha} para cada faixa de UNID px que tem chao. O
    fundo segue o topo SUAVIZADO (um degrau nao vira um degrau embaixo) e sobe
    nas pontas das ilhas, ate a ponta arredondada.
    """
    if fase.ident in _perfis:
        return _perfis[fase.ident]
    chao = fase.chao_col
    tx0, tx1 = min(chao), max(chao) + 1
    x0 = tx0 * TILE
    n = (tx1 - tx0) * TILE // UNID
    rnd = random.Random(f"ilhas/{fase.ident}")
    barriga = _ruido(rnd, n, 26)            # a barriga ondula a cada ~100 px
    pedras = _ruido(rnd, n, 5)              # e as pedras do contorno, a cada ~20 px

    topo = [None] * n
    for i in range(n):
        tx = (x0 + i * UNID) // TILE
        if tx in chao:
            topo[i] = chao[tx] * TILE

    # distancia ate o vao GRANDE mais proximo (fenda pequena nao conta)
    fenda = VAO_GRANDE * TILE // UNID
    buraco = [t is None for t in topo]
    i = 0
    while i < n:
        if buraco[i]:
            j = i
            while j < n and buraco[j]:
                j += 1
            if j - i < fenda and i > 0 and j < n:
                for k in range(i, j):
                    buraco[k] = False           # a fenda conta como ilha
            i = j
        else:
            i += 1
    def distancias(vazio):
        # antes do primeiro e depois do ultimo tile de chao ha o vazio: as duas
        # pontas da fase afinam como a beira de qualquer ilha
        d = [0.0] * n
        ultimo = -1
        for i in range(n):
            if vazio[i]:
                ultimo = i
            d[i] = (i - ultimo) * UNID
        ultimo = n
        for i in range(n - 1, -1, -1):
            if vazio[i]:
                ultimo = i
            d[i] = min(d[i], (ultimo - i) * UNID)
        return d
    dist = distancias(buraco)                           # ate o vao grande
    dist_fenda = distancias([t is None for t in topo])  # ate qualquer vao

    # topo suavizado dentro de cada ilha (media movel de +-2 tiles)
    raio = 2 * TILE // UNID
    suave = [None] * n
    for i in range(n):
        if topo[i] is None:
            continue
        viz = [topo[k] for k in range(max(0, i - raio), min(n, i + raio + 1))
               if topo[k] is not None]
        suave[i] = sum(viz) / len(viz)

    fundo = {}
    for i in range(n):
        if topo[i] is None:
            continue
        d = ESPESSURA + barriga[i] * 24 + pedras[i] * 8
        t = min(1.0, dist[i] / AFINA)
        d *= 0.2 + 0.8 * t * t * (3.0 - 2.0 * t)      # ponta arredondada
        q = min(1.0, dist_fenda[i] / QUINA)
        d *= 0.55 + 0.45 * math.sqrt(q)                # quina de baixo, na fenda
        y = max(topo[i] + 36, suave[i] + d)
        fundo[x0 // UNID + i] = int(y) // UNID * UNID  # borda no grid de pixel
    _perfis[fase.ident] = fundo
    return fundo


# ------------------------------------------------------------------ coluna
def _desenhar_coluna(fase, tx):
    chao = fase.chao_col
    topo = chao[tx] * TILE
    perfil = _perfil(fase)
    faixas = [perfil[(tx * TILE) // UNID + k] - topo for k in range(TILE // UNID)]
    s = pygame.Surface((TILE, max(faixas) + UNID), pygame.SRCALPHA)
    rnd = random.Random(tx * 7919)
    for k, fim in enumerate(faixas):
        x = k * UNID
        linhas = fim // UNID
        escura = int(linhas * 0.62)                 # o terco de baixo fica na sombra
        onda = (tx * 3 + k // 3) % 7                # os veios nao sao retos
        passo = 7 + (tx % 3)                        # nem igualmente espacados
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
            elif j >= escura:
                cor = SOMBRA if (j + onda) % passo == 0 else ROCHA_ESCURA
            else:
                cor = ROCHA_ESCURA if (j + onda) % passo == 0 else ROCHA
            # pedrinhas claras e, raramente, um veio de cristal
            if 5 < j < escura:
                sorte = rnd.random()
                if sorte < 0.03:
                    cor = ROCHA_CLARA
                elif sorte < 0.034:
                    cor = CRISTAL
            s.fill(cor, (x, j * UNID, UNID, UNID))
    s.fill(BRILHO, (0, 0, TILE, 2))                 # a linha do chao

    # degrau: o lado virado para o vizinho mais baixo mostra a rocha, com a
    # quina iluminada; na beira de um vao, a mesma luz desce pela ponta
    for lado, x in ((-1, 0), (1, TILE - UNID)):
        viz = chao.get(tx + lado)
        if viz is None or viz > chao[tx]:
            fim = faixas[0 if lado < 0 else -1]
            ate = fim if viz is None else min(fim, (viz - chao[tx]) * TILE)
            s.fill(ROCHA_CLARA, (x, UNID * 5, UNID, max(0, ate - UNID * 6)))
            s.fill(CRISTAL, (x, 0, UNID, UNID * 2))
            s.fill(BRILHO, (x + (0 if lado < 0 else UNID - 2), 0, 2, UNID * 2))
    return s


def coluna(fase, tx):
    chave = (fase.ident, tx)
    s = _colunas.get(chave)
    if s is None:
        if len(_colunas) > 500:
            _colunas.clear()
        s = _colunas[chave] = _desenhar_coluna(fase, tx)
    return s


def desenhar(tela, fase, cam_x, cam_y, c0, c1):
    """O chao das colunas [c0, c1) visiveis, no lugar do chao desenhado por codigo."""
    chao = fase.chao_col
    for tx in range(c0, c1):
        if tx in chao:
            tela.blit(coluna(fase, tx), (tx * TILE - cam_x, chao[tx] * TILE - cam_y))
