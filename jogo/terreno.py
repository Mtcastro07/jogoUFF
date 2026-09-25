"""
O chao desenhado das fases 2 e 3. Nas Ilhas Suspensas cada trecho de chao e uma ilha de
pedra flutuando -- linha de cristal no topo, rocha em camadas e o fundo
arredondado, com o ceu aparecendo por baixo. A paleta e a das ilhas geradas
para a fase, entao o chao e o cenario sao da mesma familia.

So muda o DESENHO: a colisao continua sendo o grid de fases.py.

Cada coluna de 1 tile e desenhada uma vez numa superficie e guardada; na tela,
o chao e so uma copia por coluna visivel.
"""

import math
import random
from collections import OrderedDict

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

ACIMA = 8           # espaco acima do topo, para os cristais que nascem da borda
PENDE = 30          # espaco abaixo do fundo, para as raizes que pendem

_perfis = {}
_pontas = {}
# colunas ja desenhadas, da mais antiga para a mais recente. Sai uma de cada
# vez: apagar tudo de uma vez faria o jogo redesenhar a tela inteira num quadro
# so -- um tranco no meio da musica.
_colunas = OrderedDict()
GUARDA = 180


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
    # pontas de ilha junto de um vao grande (e a largada): de la cai uma cascata
    pontas = []
    for i in range(n):
        if topo[i] is None:
            continue
        if (i + 1 >= n or buraco[i + 1]) and i - 4 >= 0:
            pontas.append((i - 4, +1))
        if (i == 0 or buraco[i - 1]) and i + 4 < n:
            pontas.append((i + 4, -1))

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
    # a agua sai de baixo da rocha, um pouco para dentro da ponta
    _pontas[fase.ident] = [(x0 + i * UNID, fundo[x0 // UNID + i] - 6) for i, _ in pontas
                           if x0 // UNID + i in fundo]
    return fundo


# ------------------------------------------------------------------ coluna
def _desenhar_coluna(fase, tx):
    chao = fase.chao_col
    topo = chao[tx] * TILE
    perfil = _perfil(fase)
    faixas = [perfil[(tx * TILE) // UNID + k] - topo for k in range(TILE // UNID)]
    s = pygame.Surface((TILE, ACIMA + max(faixas) + UNID + PENDE), pygame.SRCALPHA)
    alto = ACIMA                                    # y do topo dentro da superficie
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
            s.fill(cor, (x, alto + j * UNID, UNID, UNID))
    s.fill(BRILHO, (0, alto, TILE, 2))              # a linha do chao

    # degrau: o lado virado para o vizinho mais baixo mostra a rocha, com a
    # quina iluminada; na beira de um vao, a mesma luz desce pela ponta
    for lado, x in ((-1, 0), (1, TILE - UNID)):
        viz = chao.get(tx + lado)
        if viz is None or viz > chao[tx]:
            fim = faixas[0 if lado < 0 else -1]
            ate = fim if viz is None else min(fim, (viz - chao[tx]) * TILE)
            s.fill(ROCHA_CLARA, (x, alto + UNID * 5, UNID, max(0, ate - UNID * 6)))
            s.fill(CRISTAL, (x, alto, UNID, UNID * 2))
            s.fill(BRILHO, (x + (0 if lado < 0 else UNID - 2), alto, 2, UNID * 2))

    # um no de cristal nascendo da borda (quadrado, nunca pontudo: pontudo e
    # so o perigo), e nunca junto de um caco, para nao disputar a leitura
    perto_de_caco = any(fase.col_perigos.get(tx + d) for d in (-1, 0, 1))
    if not perto_de_caco and rnd.random() < 0.34:
        k = rnd.randrange(1, TILE // UNID - 2) * UNID
        if rnd.random() < 0.5:
            s.fill(TOPO, (k, alto - UNID, UNID * 2, UNID))
            s.fill(CRISTAL, (k + UNID, alto - UNID, UNID, UNID // 2))
        else:
            s.fill(CRISTAL, (k, alto - UNID * 2, UNID, UNID * 2))
            s.fill(BRILHO, (k, alto - UNID * 2, 2, UNID))
    # raizes de pedra pendendo da barriga, com uma gota de cristal na ponta
    for _ in range(2):
        if rnd.random() < 0.3:
            k = rnd.randrange(2, TILE // UNID - 2)
            fim = alto + faixas[k] - 2
            comp = rnd.randrange(3, PENDE // UNID - 1) * UNID
            s.fill(SOMBRA, (k * UNID + 1, fim, 2, comp))
            s.fill(CRISTAL, (k * UNID, fim + comp, UNID, UNID))
    return s


# ------------------------------------------------------------- a cidadela
# O chao da Cidadela do Eclipse e alvenaria: pedra de coroamento no topo e
# fiadas de tijolo com junta desencontrada, na paleta das muralhas geradas para
# a fase. As fiadas seguem o y do MUNDO, entao os tijolos continuam de uma
# coluna para a outra e atravessam os degraus como uma parede de verdade.
FIADA = 16          # altura de uma fiada de tijolos
FUNDO_CIDADELA = 6 * TILE      # abaixo disso a pedra ja e so sombra: o resto e preenchido
LAVANDA = (206, 168, 255)       # a linha do chao da fase
COROA_CLARA = (99, 61, 122)
COROA = (89, 50, 113)
TIJOLO = (51, 32, 74)
TIJOLO_ESCURO = (38, 22, 58)
JUNTA = (24, 11, 40)
PROFUNDO = (18, 8, 32)
RUNA = (206, 168, 255)


def _misturar(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def _desenhar_cidadela(fase, tx):
    chao = fase.chao_col
    topo = chao[tx] * TILE
    s = pygame.Surface((TILE, ACIMA + FUNDO_CIDADELA), pygame.SRCALPHA)
    alto = ACIMA
    x0 = tx * TILE
    rnd = random.Random(tx * 104729)
    # corpo: fiadas pelo y do mundo, juntas desencontradas pelo x do mundo
    for y in range(topo + 14, topo + FUNDO_CIDADELA, FIADA):
        fiada = y // FIADA
        larg = 32 if fiada % 3 else 24
        desloc = (fiada * 13) % larg
        escurece = min(0.9, max(0.0, (y - topo - 30) / 170.0))   # o detalhe forte e na borda
        sy = alto + (y - topo)
        # cada tijolo com o seu tom, como pedra cortada a mao
        bx = x0 - (x0 - desloc) % larg
        while bx < x0 + TILE:
            cor = TIJOLO if ((bx // larg) * 7 + fiada) % 5 else TIJOLO_ESCURO
            cor = _misturar(cor, PROFUNDO, escurece)
            a, b = max(bx, x0), min(bx + larg, x0 + TILE)
            s.fill(cor, (a - x0, sy, b - a, FIADA))
            junta = _misturar(_misturar(JUNTA, TIJOLO, 0.35), PROFUNDO, escurece)
            if bx > x0 - larg:
                s.fill(junta, (max(0, bx - x0), sy, 2, FIADA))
            bx += larg
        s.fill(_misturar(_misturar(JUNTA, TIJOLO, 0.35), PROFUNDO, escurece), (0, sy, TILE, 2))
    # uma rachadura aqui e ali, e raramente uma runa acesa na pedra
    if rnd.random() < 0.3:
        cx, cy = rnd.randrange(8, TILE - 12), alto + rnd.randrange(24, 90)
        for k in range(5):
            s.fill(JUNTA, (cx + k * 2, cy + k * 3 + (k % 2), 2, 3))
    if rnd.random() < 0.12:
        # a runa: um anel de luz pequeno gravado na pedra (redondo -- pontudo e o perigo)
        cx, cy = rnd.randrange(10, TILE - 16), alto + 30
        for dx, dy in ((2, 0), (4, 0), (0, 2), (6, 2), (0, 4), (6, 4), (2, 6), (4, 6)):
            s.fill(RUNA, (cx + dx, cy + dy, 2, 2))
        s.fill(_misturar(RUNA, TIJOLO, 0.55), (cx + 2, cy + 2, 4, 4))
    # coroamento: a pedra de cima, com a linha clara que o olho segue
    s.fill(COROA, (0, alto, TILE, 14))
    s.fill(COROA_CLARA, (0, alto + 2, TILE, 2))
    s.fill(JUNTA, (0, alto + 12, TILE, 2))
    junta = (x0 // 48) % 2 * 24 + 12
    s.fill(JUNTA, (junta, alto + 4, 2, 8))
    s.fill(LAVANDA, (0, alto, TILE, 2))
    # degrau e beira de vao: a quina iluminada desce pela pedra
    for lado, x in ((-1, 0), (1, TILE - 2)):
        viz = chao.get(tx + lado)
        if viz is None or viz > chao[tx]:
            ate = FUNDO_CIDADELA if viz is None else (viz - chao[tx]) * TILE
            s.fill(COROA_CLARA, (x, alto + 2, 2, min(ate, FUNDO_CIDADELA) - 2))
            s.fill(LAVANDA, (x, alto, 2, 12))
    return s


ESTILO = {"ilhas": _desenhar_coluna, "eclipse": _desenhar_cidadela}


def coluna(fase, tx):
    chave = (fase.ident, tx)
    s = _colunas.get(chave)
    if s is None:
        s = _colunas[chave] = ESTILO[fase.cancao](fase, tx)
        if len(_colunas) > GUARDA:
            _colunas.popitem(last=False)
    else:
        _colunas.move_to_end(chave)
    return s


def preparar(fase):
    """As contas da fase inteira (o fundo das ilhas), feitas antes do 1o quadro."""
    if fase.cancao == "ilhas":
        _perfil(fase)


def desenhar(tela, fase, cam_x, cam_y, c0, c1, tempo=0.0):
    """O chao das colunas [c0, c1) visiveis, no lugar do chao desenhado por codigo."""
    chao = fase.chao_col
    if fase.cancao == "ilhas":
        _perfil(fase)
        for x, y in _pontas[fase.ident]:
            if cam_x - 16 < x < cam_x + TILE * (c1 - c0) + 16:
                _cascata(tela, x - cam_x, y - cam_y, tempo)
    cidadela = fase.cancao == "eclipse"
    for tx in range(c0, c1):
        if tx in chao:
            x, y = tx * TILE - cam_x, chao[tx] * TILE - cam_y
            tela.blit(coluna(fase, tx), (x, y - ACIMA))
            if cidadela and y + FUNDO_CIDADELA < tela.get_height():
                tela.fill(PROFUNDO, (x, y + FUNDO_CIDADELA, TILE, tela.get_height() - y - FUNDO_CIDADELA))


def _cascata(tela, x, y, tempo):
    """Agua caindo da ponta da ilha ate o mar de nuvens, com o brilho descendo."""
    alto = tela.get_height() - y
    if alto <= 0:
        return
    tela.fill(CRISTAL, (x, y, 6, alto))
    tela.fill((128, 210, 247), (x + 4, y, 2, alto))
    desce = int(tempo * 150) % 22
    for yy in range(y - 22 + desce, y + alto, 22):
        tela.fill(BRILHO, (x + 1, max(y, yy), 2, 8))
