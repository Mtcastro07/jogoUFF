"""
O chao desenhado das fases. Nas Dunas do Chocalho e areia sobre arenito em
camadas; na Geleira da Aurora, neve sobre gelo glacial. No Bosque dos Ecos e um caminho de lajes com
musgo sobre terra em camadas. Nas Ilhas Suspensas cada trecho de chao e uma
ilha de pedra flutuando -- linha de cristal no topo, rocha em camadas e o fundo
arredondado, com o ceu aparecendo por baixo. Na Cidadela e alvenaria. A paleta
de cada uma e a da arte gerada para a fase, entao o chao e o cenario sao da
mesma familia.

So muda o DESENHO: a colisao continua sendo o grid de fases.py.

Cada coluna de 1 tile e desenhada uma vez numa superficie e guardada; na tela,
o chao e so uma copia por coluna visivel.
"""

import bisect
import functools
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

ACIMA = 12          # espaco acima do topo, para os cristais e as flores que nascem da borda
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
    rnd = random.Random(f"ilhas/{fase.semente}")
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
    _detalhar_ilha(s, fase, tx, faixas, alto)
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


def _detalhar_ilha(s, fase, tx, faixas, alto):
    """
    O detalhe por cima da rocha da ilha: a borda de cima escorrendo irregular,
    veios de cristal (os mesmos do bloco das ilhas), uma pedra incrustada e um
    tufo na superficie. Sorteio proprio: os cristais e as raizes da coluna nao
    mudam de lugar.
    """
    rnd = random.Random(tx * 104723 + 5)
    n = TILE // UNID
    # a borda da faixa de cima nao e reta: escorre uma ou duas unidades aqui e ali
    for k in range(n):
        if faixas[k] // UNID > 8:
            sorte = rnd.random()
            if sorte < 0.4:
                s.fill(TOPO, (k * UNID, alto + 4 * UNID, UNID, UNID * (2 if sorte < 0.12 else 1)))
    s.fill(_misturar(TOPO, BRILHO, 0.25), (0, alto + UNID, TILE, UNID // 2))
    fundo = min(faixas) // UNID
    # um veio de cristal descendo na diagonal, sem sair da coluna
    if fundo > 14 and rnd.random() < 0.3:
        passo = rnd.choice((-1, 1))
        k = rnd.randrange(3, n - 3)
        j = rnd.randrange(7, max(8, int(fundo * 0.55)))
        for _ in range(rnd.randrange(3, 6)):
            if not 0 <= k < n:
                break
            s.fill(CRISTAL, (k * UNID, alto + j * UNID, UNID, UNID))
            s.fill(BRILHO, (k * UNID, alto + j * UNID, 2, 2))
            s.fill(ROCHA_ESCURA, (k * UNID, alto + (j + 1) * UNID, UNID, UNID // 2))
            k += passo
            j += 1
    # uma pedra incrustada, redonda, acesa em cima
    if fundo > 12 and rnd.random() < 0.35:
        k = rnd.randrange(1, n - 4)
        j = rnd.randrange(6, max(7, int(fundo * 0.5)))
        x, y = k * UNID, alto + j * UNID
        s.fill(ROCHA_CLARA, (x + UNID, y, UNID * 2, UNID * 2))
        s.fill(ROCHA_CLARA, (x, y + UNID, UNID * 4, UNID))
        s.fill(TOPO, (x + UNID, y, UNID * 2, UNID // 2))
        s.fill(SOMBRA, (x + UNID, y + UNID * 2, UNID * 3, UNID // 2))
    # tufo de musgo lilas na superficie, longe dos cacos
    if not any(fase.col_perigos.get(tx + d) for d in (-1, 0, 1)) and rnd.random() < 0.28:
        k = rnd.randrange(1, n - 3)
        s.fill(TOPO, (k * UNID, alto - UNID // 2, UNID * 3, UNID // 2))
        s.fill(_misturar(TOPO, BRILHO, 0.35), (k * UNID + UNID // 2, alto - UNID, UNID * 2, UNID // 2))


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
SETEIRA = (255, 176, 90)        # a luz de dentro da muralha
PANO = (92, 40, 118)            # o estandarte
PANO_ESCURO = (58, 22, 80)
OURO = (255, 206, 120)


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
    # a arquitetura, de tantas em tantas colunas: uma seteira acesa na parede ou
    # um estandarte pendurado do coroamento, com o anel do eclipse bordado
    sorte = (tx * 2654435761 >> 9) % 100
    if sorte < 9:
        x = 20 + (tx % 2) * 4
        s.fill(JUNTA, (x - 2, alto + 30, 8, 26))
        s.fill(SETEIRA, (x, alto + 34, 4, 18))
        s.fill(_misturar(SETEIRA, (255, 255, 255), 0.4), (x, alto + 34, 2, 6))
    elif sorte < 16:
        x = 14
        s.fill(JUNTA, (x - 2, alto + 14, 24, 4))                       # a haste
        s.fill(PANO_ESCURO, (x, alto + 18, 20, 40))
        s.fill(PANO, (x + 2, alto + 18, 16, 38))
        s.fill(LAVANDA, (x, alto + 18, 2, 40))
        s.fill(LAVANDA, (x + 18, alto + 18, 2, 40))
        s.fill(PANO, (x + 4, alto + 58, 12, 2))                        # a barra, redonda
        s.fill(PANO_ESCURO, (x + 6, alto + 60, 8, 2))
        for dx, dy in ((6, 0), (8, 0), (4, 2), (10, 2), (4, 4), (10, 4), (6, 6), (8, 6)):
            s.fill(OURO, (x + dx, alto + 32 + dy, 2, 2))               # o anel do eclipse
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


# --------------------------------------------------------------- o bosque
# O chao do Bosque dos Ecos: um caminho de lajes de pedra com musgo, na paleta
# do chao.png gerado para a fase, sobre terra em camadas com pedras e raizes.
# Lajes, camadas e pedras seguem o x/y do MUNDO: continuam de uma coluna para
# a outra e nunca se repetem como carimbo. O "pixel" e de 2 px, o do Leo.
PX = 2
LAJE_ALTA = 12 * PX             # altura do caminho de lajes
FUNDO_BOSQUE = 6 * TILE         # abaixo disso a terra ja e so sombra: o resto e preenchido
CAMADA = 24                     # altura media de uma camada de terra
LAJE_LUZ = (138, 152, 126)      # o topo da laje, aceso pela lua
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
SOMBRA_LAJE = (18, 36, 34)      # a sombra que o caminho joga na terra logo abaixo
PROFUNDO_BOSQUE = (12, 26, 28)
PEDRA_LUZ = (94, 114, 106)
PEDRA_CORPO = (66, 86, 82)
PEDRA_SOMBRA = (42, 60, 58)
RAIZ = (46, 50, 42)
RAIZ_NO = (74, 80, 62)
FLORES = ((236, 226, 150), (176, 214, 255), (228, 236, 240))   # nada de rosa: rosa e o perigo
AMARELO_MIOLO = (250, 196, 90)
COGUMELO = (150, 255, 200)      # o que brilha no escuro
CAULE = (196, 206, 196)

_juntas = {}


def _h(*valores):
    """Um numero fixo para cada posicao do mundo: o mesmo sorteio em toda partida."""
    x = 0x9E3779B1
    for v in valores:
        x = ((x ^ (v & 0xFFFFFFFF)) * 0x85EBCA6B) & 0xFFFFFFFF
        x ^= x >> 13
    return x


@functools.lru_cache(maxsize=4096)
def _no_fundo(cor, prof):
    """A terra escurece com a profundidade ate virar o PROFUNDO do pe da tela."""
    return _misturar(cor, PROFUNDO_BOSQUE, min(1.0, max(0.0, (prof - 36) / (FUNDO_BOSQUE - 84))))


def _lajes(fase):
    """x do mundo de cada junta entre duas lajes, do comeco ao fim da fase."""
    if fase.ident not in _juntas:
        chao = fase.chao_col
        x, fim = min(chao) * TILE, (max(chao) + 1) * TILE
        rnd = random.Random(f"bosque/{fase.semente}")
        lista = []
        x += rnd.randrange(8, 40, PX)
        while x < fim:
            lista.append(x)
            x += rnd.randrange(26, 64, PX)
        _juntas[fase.ident] = lista
    return _juntas[fase.ident]


def _divisa(xw, k):
    """y do mundo onde a camada k comeca, ondulando com o x (sempre no grid de 2 px)."""
    return k * CAMADA + PX * round(1.3 * math.sin(xw * 0.045 + k * 2.3) +
                                   0.6 * math.sin(xw * 0.11 + k))


def _pedra(s, x, y, w, h, prof):
    """Pedra redonda na terra: topo e lado direito acesos pela lua, base na sombra."""
    corpo, luz, sombra = (_no_fundo(c, prof) for c in (PEDRA_CORPO, PEDRA_LUZ, PEDRA_SOMBRA))
    s.fill(corpo, (x + PX, y, w - 2 * PX, h))
    s.fill(corpo, (x, y + PX, w, h - 2 * PX))
    s.fill(luz, (x + PX, y, w - 2 * PX, PX))
    s.fill(luz, (x + w - PX, y + PX, PX, max(0, h - 3 * PX)))
    s.fill(sombra, (x + PX, y + h - PX, w - 2 * PX, PX))
    s.fill(_no_fundo(TERRA_VEIO, prof), (x + 2 * PX, y + h, w - 3 * PX, PX))


def _desenhar_bosque(fase, tx):
    chao = fase.chao_col
    n = chao[tx]
    topo = n * TILE
    x0 = tx * TILE
    s = pygame.Surface((TILE, ACIMA + FUNDO_BOSQUE), pygame.SRCALPHA)
    a = ACIMA                                       # y do topo dentro da superficie
    rnd = random.Random(tx * 7727 + n)
    ini, fim = topo + LAJE_ALTA, topo + FUNDO_BOSQUE

    # terra em camadas pelo y do mundo, com a divisa ondulando pelo x do mundo
    for xs in range(0, TILE, PX):
        xw = x0 + xs
        k = ini // CAMADA - 1
        de = _divisa(xw, k)
        while de < fim:
            ate = _divisa(xw, k + 1)
            y0, y1 = max(ini, de), min(fim, ate)
            if y1 > y0:
                cor = TERRA_TONS[k % 3]
                s.fill(_no_fundo(cor, (y0 + y1) // 2 - topo), (xs, a + y0 - topo, PX, y1 - y0))
                if y1 < fim:
                    # o veio entre duas camadas, e de vez em quando um sedimento claro
                    s.fill(_no_fundo(TERRA_VEIO, y1 - topo), (xs, a + y1 - topo, PX, PX))
                    if _h(xw // 6, k, 3) % 5 == 0:
                        s.fill(_no_fundo(TERRA_LUZ, y1 - topo), (xs, a + y1 - topo + PX, PX, PX))
            k, de = k + 1, ate

    # a sombra que o caminho joga na terra logo abaixo dele
    s.fill(SOMBRA_LAJE, (0, a + LAJE_ALTA, TILE, PX))
    s.fill(_misturar(SOMBRA_LAJE, TERRA_TONS[0], 0.5), (0, a + LAJE_ALTA + PX, TILE, PX))

    # pedras enterradas: uma grade do mundo, cada celula sorteia se tem pedra.
    # Poucas e de tamanhos bem diferentes -- muitas iguais viram pontilhado.
    for cy in range(ini // 34, fim // 34 + 1):
        for cx in range((x0 - 30) // 44, (x0 + TILE + 30) // 44 + 1):
            h = _h(cx, cy, 5)
            if h % 100 >= 24:
                continue
            grande = (h >> 24) % 4 == 0
            w = (8 if grande else 4) + (h >> 7) % 4 * PX
            alto = (6 if grande else 4) + (h >> 10) % 2 * PX
            px = cx * 44 + (h >> 13) % (44 - w) // PX * PX
            py = cy * 34 + (h >> 18) % (34 - alto) // PX * PX
            if ini + 8 <= py and py + alto <= fim - 40:
                _pedra(s, px - x0, a + py - topo, w, alto, py - topo)

    # raizes pendendo do caminho: grossas em cima, afinando, com um lado aceso
    for _ in range(2):
        if rnd.random() < 0.45:
            x = rnd.randrange(4, TILE - 8, PX)
            comp = rnd.randrange(14, 46, PX)
            for i in range(0, comp, PX):
                if i > 4 and rnd.random() < 0.3:
                    x = min(TILE - 4, max(2, x + rnd.choice((-PX, PX))))
                prof = LAJE_ALTA + i
                grossa = i < comp // 3
                s.fill(_no_fundo(RAIZ, prof), (x, a + prof, 2 * PX if grossa else PX, PX))
                if grossa or i % 6 == 0:
                    s.fill(_no_fundo(RAIZ_NO, prof), (x + (PX if grossa else 0), a + prof, PX, PX))

    # o caminho: lajes de largura sorteada, cada uma com o seu tom
    juntas = _lajes(fase)
    i0 = bisect.bisect_right(juntas, x0)
    i1 = bisect.bisect_left(juntas, x0 + TILE)
    cortes = [x0] + juntas[i0:i1] + [x0 + TILE]
    for xa, xb in zip(cortes, cortes[1:]):
        tom = LAJE_TONS[_h(bisect.bisect_right(juntas, xa), 1) % 3]
        s.fill(LAJE_LUZ, (xa - x0, a + PX, xb - xa, PX))
        s.fill(tom, (xa - x0, a + 2 * PX, xb - xa, 7 * PX))
        s.fill(LAJE_MEIA, (xa - x0, a + 9 * PX, xb - xa, PX))
        s.fill(LAJE_SOMBRA, (xa - x0, a + 10 * PX, xb - xa, PX))
    s.fill(JUNTA_LAJE, (0, a + 11 * PX, TILE, PX))
    # o que cada laje tem, pelo x do mundo: pintas, rachadura e musgo na quina
    for laje in range(i0 - 1, i1):
        la = juntas[laje] if laje >= 0 else juntas[0] - 60
        lb = juntas[laje + 1] if laje + 1 < len(juntas) else la + 60
        h = _h(laje, 7)
        for k in range(3):
            hk = _h(laje, 11, k)
            s.fill(LAJE_MEIA, (la + PX + hk % max(PX, lb - la - 3 * PX) // PX * PX - x0,
                               a + (3 + (hk >> 8) % 5) * PX, PX, PX))
        if h % 10 < 3:
            # rachadura: desce do topo da laje andando de lado ao acaso
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
        # a junta, com as duas quinas de cima arredondadas
        s.fill(JUNTA_LAJE, (j - x0, a + PX, PX, 10 * PX))
        s.fill(LAJE_MEIA, (j - x0 - PX, a + PX, PX, PX))
        s.fill(LAJE_MEIA, (j - x0 + PX, a + PX, PX, PX))
    # musgo escorrendo por baixo do caminho
    for _ in range(rnd.randrange(1, 4)):
        s.fill(MUSGO_ESCURO, (rnd.randrange(0, TILE - PX, PX), a + LAJE_ALTA,
                              PX, rnd.randrange(1, 4) * PX))
    s.fill(fase.tema.chao_topo, (0, a, TILE, PX))   # a linha clara que o olho segue

    # degrau e beira de vao: a laje termina arredondada, a luz desce pela
    # quina e a face da terra aparece -- acesa do lado da lua (a direita)
    for lado, x in ((-1, 0), (1, TILE - PX)):
        viz = chao.get(tx + lado)
        if viz is None or viz > n:
            ate = FUNDO_BOSQUE if viz is None else min(FUNDO_BOSQUE, (viz - n) * TILE)
            s.fill((0, 0, 0, 0), (x, a, PX, PX))
            s.fill(fase.tema.chao_topo, (x, a + PX, PX, 10 * PX))
            face = TERRA_LUZ if lado > 0 else TERRA_VEIO
            for y in range(LAJE_ALTA, ate, 16):
                s.fill(_no_fundo(face, y), (x, a + y, PX, min(16, ate - y)))
            for _ in range(3):
                if rnd.random() < 0.7:
                    dx = x - lado * rnd.randrange(0, 4) * PX
                    s.fill(MUSGO, (dx, a + LAJE_ALTA - PX, PX, rnd.randrange(2, 8) * PX))
                    s.fill(MUSGO_CLARO, (dx, a + LAJE_ALTA - PX, PX, PX))

    # enfeites em cima do caminho: tufo de musgo, florzinha ou cogumelo que
    # brilha. Todos redondos (pontudo e so o perigo) e longe de caco e bloco,
    # para nao disputar a leitura do obstaculo.
    perto = any(fase.col_perigos.get(tx + d) for d in (-1, 0, 1)) or \
        any(bx in (tx - 1, tx, tx + 1) for bx, _ in fase.blocos)
    sorte = rnd.random()
    if not perto and sorte < 0.55:
        x = rnd.randrange(6, TILE - 14, PX)
        if sorte < 0.32:
            # tufo de musgo: um montinho redondo com o topo aceso
            w = rnd.randrange(4, 8) * PX
            s.fill(MUSGO_ESCURO, (x, a - PX, w, PX))
            s.fill(MUSGO, (x + PX, a - 2 * PX, w - 2 * PX, PX))
            s.fill(MUSGO, (x + 2 * PX, a - 3 * PX, w - 4 * PX, PX))
            s.fill(MUSGO_CLARO, (x + 2 * PX, a - 3 * PX, PX, PX))
            s.fill(MUSGO_CLARO, (x + PX, a - 2 * PX, PX, PX))
        elif sorte < 0.46:
            # florzinha: caule, folha e a flor em cruz com o miolo
            s.fill(MUSGO, (x, a - 3 * PX, PX, 3 * PX))
            s.fill(MUSGO_CLARO, (x + PX, a - 2 * PX, PX, PX))
            flor = FLORES[rnd.randrange(len(FLORES))]
            s.fill(flor, (x - PX, a - 4 * PX, 3 * PX, PX))
            s.fill(flor, (x, a - 5 * PX, PX, 3 * PX))
            s.fill(AMARELO_MIOLO, (x, a - 4 * PX, PX, PX))
        else:
            # cogumelo que brilha: chapeu redondo, pe claro
            s.fill(CAULE, (x + PX, a - 2 * PX, PX, 2 * PX))
            s.fill(_misturar(COGUMELO, (0, 0, 0), 0.35), (x, a - 3 * PX, 3 * PX, PX))
            s.fill(COGUMELO, (x, a - 4 * PX, 3 * PX, PX))
            s.fill(_misturar(COGUMELO, (255, 255, 255), 0.6), (x + PX, a - 4 * PX, PX, PX))
    return s


def fosso(tela, tx0, tx1, y, cam_x, cam_y):
    """
    O fundo de um fosso do bosque: terra com musgo onde os cacos estao
    cravados, escurecendo ate o pe da tela. Sem ele os cacos boiariam no ar.
    """
    alto = tela.get_height()
    x, w, sy = tx0 * TILE - cam_x, (tx1 - tx0) * TILE, y - cam_y
    if sy >= alto:
        return
    faixas = ((PX, MUSGO_ESCURO), (3 * PX, TERRA_TONS[2]), (4 * PX, TERRA_TONS[0]),
              (4 * PX, _misturar(TERRA_VEIO, PROFUNDO_BOSQUE, 0.4)))
    for grossura, cor in faixas:
        tela.fill(cor, (x, sy, w, grossura))
        sy += grossura
    tela.fill(PROFUNDO_BOSQUE, (x, sy, w, alto - sy))
    for k in range(0, w, 12):
        h = _h(tx0 * TILE + k, 9)
        if h % 3 == 0:
            tela.fill(PEDRA_CORPO, (x + k + h % 8 // PX * PX, y - cam_y + 2 * PX, 3 * PX, PX))

# ---------------------------------------------------------------- as dunas
# O chao das Dunas do Chocalho: uma capa de areia clara, penteada pelo vento,
# sobre ARENITO em camadas onduladas (ocre, ferrugem, creme), como a parede de
# um canion. As camadas seguem o x/y do MUNDO: continuam de uma coluna para a
# outra. Aqui e ali, um fossil em espiral, um caco de anfora ou um glifo
# turquesa -- redondos: pontudo, nas dunas, so o perigo.
FUNDO_DUNAS = 6 * TILE          # abaixo disso o arenito ja e so sombra
AREIA_LUZ = (255, 232, 160)     # a linha do chao, a que o olho segue
AREIA = (238, 196, 126)
AREIA_MEIA = (220, 170, 106)
AREIA_SOMBRA = (190, 134, 86)
ARENITO = ((198, 124, 78), (174, 100, 66), (212, 146, 92), (156, 86, 60), (186, 112, 72))
VEIO_DUNAS = (126, 66, 52)
CREME = (232, 190, 132)
PROFUNDO_DUNAS = (64, 32, 38)
GLIFO = (72, 226, 208)
FOSSIL = (240, 214, 170)


# --- a pedra em camadas, rapida ----------------------------------------------
# Nas dunas e na geleira a cor de um ponto da pedra so depende de UMA conta,
# u = altura no mundo + onda(x): a camada (ou faixa) e o lugar dentro dela.
# Entao a cor de cada u e pintada UMA vez por fase, numa faixa de PX de largura
# (`_textura`), e cada coluna do chao so recorta dela um pedaco por x -- em vez
# de calcular celula por celula, o que custava 9 a 16 ms por coluna e travava a
# partida toda vez que uma coluna nova entrava na tela.
_texturas = {}
_sombras = {}
_quinas = {}


def _textura(nome, cor_de, u0, u1):
    """
    {paridade: surface PX x (u1 - u0)} e {u: (cor, so_pedra)}: a linha r da
    surface de paridade p tem a cor de u = u0 + p + 2 * (r // 2), repetida em PX
    linhas -- recortar a partir de r0 = b - u0 - p da as celulas u = b, b+2, ...
    """
    chave = (nome, u0, u1)
    if chave not in _texturas:
        cores = {u: cor_de(u) for u in range(u0, u1 + 2 * PX)}
        faixas = {}
        for p in (0, 1):
            f = pygame.Surface((PX, u1 - u0 + 2 * PX)).convert()
            for r in range(0, u1 - u0, 2):
                f.fill(cores[u0 + p + r][0], (0, r, PX, 2))
            faixas[p] = f
        _texturas[chave] = (faixas, cores)
    return _texturas[chave]


def _faixa_da_fase(fase, folga):
    """O intervalo de u que a fase inteira usa (com folga para a onda)."""
    alturas = [c * TILE for c in fase.chao_col.values()]
    return min(alturas) - folga, max(alturas) + 6 * TILE + folga


def _recortar(s, textura, u0, x, b, y, alto):
    """Copia para a coluna (no x, a partir de y) as celulas u = b, b+2, ... da textura."""
    p = (b - u0) % 2
    s.blit(textura[p], (x, y), (0, b - u0 - p, PX, alto))


def _sombra(cor, inicio, largura, alto, fim, curva):
    """O escurecer com a profundidade, por cima da coluna inteira (uma blit)."""
    chave = (cor, inicio, largura, alto, fim, curva)
    if chave not in _sombras:
        f = pygame.Surface((largura, alto), pygame.SRCALPHA)
        for y in range(0, alto, PX):
            k = min(1.0, max(0.0, (y - fim[0]) / fim[1])) ** curva
            f.fill((*cor, int(round(255 * k))), (0, y, largura, PX))
        _sombras[chave] = f
    return _sombras[chave]


def _quina(cor, fundo, de, ate, fim, curva=1.0):
    """A quina acesa (ou sombreada) de um degrau: uma tira de 2 px, guardada."""
    chave = (cor, fundo, de, ate, fim, curva)
    if chave not in _quinas:
        f = pygame.Surface((2, max(1, ate - de))).convert()
        for y in range(de, ate, PX):
            k = min(1.0, max(0.0, (y - fim[0]) / fim[1])) ** curva
            f.fill(_misturar(cor, fundo, k), (0, y - de, 2, PX))
        _quinas[chave] = f
    return _quinas[chave]


def _camada_dunas(xw, y):
    """Em qual camada de arenito o ponto (x do mundo, profundidade y) esta."""
    onda = 6.0 * math.sin(xw * 0.017) + 2.5 * math.sin(xw * 0.049 + 1.3)
    return int((y + onda) // 26)


def _cor_dunas(u):
    """(cor, e miolo de camada) da pedra das dunas no ponto u = altura + onda."""
    k = u // 26
    cor = ARENITO[_h(k, 3) % len(ARENITO)]
    if (u - PX) // 26 != k:
        return _misturar(cor, VEIO_DUNAS, 0.55), False      # o veio entre camadas
    if (u - 2 * PX) // 26 != k and _h(k, 5) % 4 == 0:
        return _misturar(cor, CREME, 0.5), False            # a camada mais dura, clara
    desce = 0.0                                             # o pe da camada, mais escuro
    for d in (4, 8, 12):
        if (u + d * PX) // 26 != k:
            desce = (13 - d) / 26.0
            break
    return _misturar(cor, VEIO_DUNAS, desce * 0.5), True


def _desenhar_dunas(fase, tx):
    chao = fase.chao_col
    topo = chao[tx] * TILE
    s = pygame.Surface((TILE, ACIMA + FUNDO_DUNAS), pygame.SRCALPHA)
    alto = ACIMA
    x0 = tx * TILE
    # o arenito: camadas largas e onduladas, cada uma com o seu tom, que vai
    # escurecendo de cima para baixo dentro da camada (o sol bate na de cima)
    # e com a profundidade. Entre duas camadas, so um veio discreto.
    u0, u1 = _faixa_da_fase(fase, 16)
    textura, cores = _textura("dunas", _cor_dunas, u0, u1)
    for px in range(0, TILE, PX):
        xw = x0 + px
        onda = 6.0 * math.sin(xw * 0.017) + 2.5 * math.sin(xw * 0.049 + 1.3)
        b = topo + 10 + int(math.floor(onda + 0.5))          # as camadas sao do MUNDO
        _recortar(s, textura, u0, px, b, alto + 10, FUNDO_DUNAS - 10)
        # os graos: poucos por x, em alturas sorteadas pelo x do mundo
        xc = xw // PX
        passo = 31
        yc = _h(xc, 7) % passo
        while yc < (FUNDO_DUNAS - 10) // PX:
            cor, pedra = cores[b + yc * PX]
            if pedra:
                s.fill(_misturar(cor, VEIO_DUNAS, 0.3), (px, alto + 10 + yc * PX, PX, PX))
            yc += 20 + _h(xc, yc, 8) % 23
    s.blit(_sombra(PROFUNDO_DUNAS, 10, TILE, FUNDO_DUNAS + alto, (alto + 30, FUNDO_DUNAS - 90.0), 0.8),
           (0, 0), special_flags=0)
    # achados na pedra, raros: fossil em espiral, glifo, caco de anfora
    sorte = _h(tx, 11) % 100
    if sorte < 9:
        cx, cy = 10 + _h(tx, 12) % 20, alto + 34 + _h(tx, 13) % 50
        for dx, dy in ((2, 0), (4, 0), (6, 2), (6, 4), (4, 6), (2, 6), (0, 4), (0, 2), (2, 2), (3, 3)):
            s.fill(FOSSIL if (dx + dy) % 4 else _misturar(FOSSIL, VEIO_DUNAS, 0.4), (cx + dx, cy + dy, PX, PX))
    elif sorte < 15:
        # o sol da caravana gravado na pedra: um anel turquesa com raios curtos
        cx, cy = 16 + _h(tx, 14) % 14, alto + 34
        tinta = _misturar(GLIFO, ARENITO[3], 0.35)
        sulco = _misturar(VEIO_DUNAS, ARENITO[3], 0.3)
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
    # a capa de areia: o topo aceso e as marcas do vento, que seguem o x do mundo
    s.fill(AREIA_SOMBRA, (0, alto + 8, TILE, 4))
    s.fill(AREIA_MEIA, (0, alto + 4, TILE, 6))
    s.fill(AREIA, (0, alto + 2, TILE, 4))
    s.fill(AREIA_LUZ, (0, alto, TILE, 2))
    for px in range(0, TILE, PX):
        xw = x0 + px
        onda = int(2.0 + 1.6 * math.sin(xw * 0.19) + 1.2 * math.sin(xw * 0.071 + 2.0))
        s.fill(AREIA_MEIA, (px, alto + 4 + onda // 2 * PX, PX, PX))             # a marola
        if _h(xw // PX, 21) % 9 == 0:
            s.fill(AREIA_LUZ, (px, alto + 4, PX, PX))                           # um grao que brilha
        # a areia escorre para dentro do arenito, em dentes irregulares
        dente = _h(xw // (2 * PX), 23) % 4
        s.fill(AREIA_SOMBRA, (px, alto + 12, PX, dente * PX))
    # um tufo de capim seco de vez em quando (dourado e curvo, nunca em ponta de lanca)
    if _h(tx, 31) % 5 == 0:
        gx = 6 + _h(tx, 32) % 30
        for k, (dx, h) in enumerate(((0, 6), (2, 9), (4, 7), (6, 5))):
            s.fill((214, 176, 92) if k % 2 else (176, 140, 70), (gx + dx, alto - h + 2, PX, h))
        s.fill((236, 206, 120), (gx + 2, alto - 9 + 2, PX, PX))
    # degrau e beira de vao: a quina acesa pelo sol desce pela pedra
    for lado, x in ((-1, 0), (1, TILE - 2)):
        viz = chao.get(tx + lado)
        if viz is None or viz > chao[tx]:
            ate = FUNDO_DUNAS if viz is None else (viz - chao[tx]) * TILE
            cor = CREME if lado > 0 else VEIO_DUNAS       # o sol vem da direita
            s.blit(_quina(cor, PROFUNDO_DUNAS, 12, min(ate, FUNDO_DUNAS), (40, FUNDO_DUNAS - 70.0)),
                   (x, alto + 12))
            s.fill(AREIA_LUZ, (x, alto, 2, 12))
    return s


def fosso_dunas(tela, tx0, tx1, y, cam_x, cam_y):
    """
    O fundo de um fosso das dunas: areia escura de sombra onde os cactos estao
    cravados, afundando ate o pe da tela.
    """
    alto = tela.get_height()
    x, w, sy = tx0 * TILE - cam_x, (tx1 - tx0) * TILE, y - cam_y
    if sy >= alto:
        return
    for grossura, cor in ((PX, AREIA_SOMBRA), (3 * PX, ARENITO[3]),
                          (4 * PX, _misturar(ARENITO[3], PROFUNDO_DUNAS, 0.45)),
                          (4 * PX, _misturar(VEIO_DUNAS, PROFUNDO_DUNAS, 0.6))):
        tela.fill(cor, (x, sy, w, grossura))
        sy += grossura
    tela.fill(PROFUNDO_DUNAS, (x, sy, w, alto - sy))
    for k in range(0, w, 10):
        h = _h(tx0 * TILE + k, 9)
        if h % 3 == 0:
            tela.fill(AREIA_MEIA, (x + k + h % 6, y - cam_y, 2 * PX, PX))


# ---------------------------------------------------------------- a geleira
# O chao da Geleira da Aurora: uma capa de neve fofa, em montinhos que seguem o
# x do MUNDO, sobre gelo glacial em faixas azuis inclinadas, com bolhas presas,
# fendas finas e, no fundo, o azul escuro do gelo velho. A lua vem da direita.
FUNDO_GELEIRA = 6 * TILE
NEVE_LUZ = (244, 252, 255)       # a linha do chao, a que o olho segue
NEVE = (216, 236, 252)
NEVE_SOMBRA = (162, 196, 236)
NEVE_FUNDA = (120, 160, 214)
GELO = ((76, 128, 188), (64, 112, 172), (90, 146, 204), (58, 100, 160))
GELO_VEIO = (44, 78, 132)
GELO_LUZ = (150, 214, 250)
BOLHA = (206, 238, 255)
PROFUNDO_GELO = (12, 20, 46)
AURORA_GELO = (110, 255, 214)


def _faixa_gelo(xw, y):
    """Em qual faixa do gelo o ponto esta: faixas largas, inclinadas, levemente onduladas."""
    return int((y + xw * 0.18 + 4.0 * math.sin(xw * 0.023)) // 22)


def _cor_geleira(u):
    """(cor, e miolo de faixa) do gelo no ponto u = altura + inclinacao(x)."""
    k = u // 22
    cor = GELO[_h(k, 4) % len(GELO)]
    if (u - PX) // 22 != k:
        return _misturar(cor, GELO_VEIO, 0.6), False        # a junta entre as faixas
    if (u - 2 * PX) // 22 != k:
        return _misturar(cor, GELO_LUZ, 0.35), False        # e o brilho logo abaixo dela
    return cor, True


def _desenhar_geleira(fase, tx):
    chao = fase.chao_col
    topo = chao[tx] * TILE
    s = pygame.Surface((TILE, ACIMA + FUNDO_GELEIRA), pygame.SRCALPHA)
    alto = ACIMA
    x0 = tx * TILE
    # a inclinacao das faixas cresce com o x: o intervalo de u vai ate o fim da fase
    u0, u1 = _faixa_da_fase(fase, 8)
    u1 += int(max(fase.chao_col) * TILE * 0.18) + TILE
    textura, _ = _textura("geleira", _cor_geleira, u0, u1)
    for px in range(0, TILE, PX):
        xw = x0 + px
        b = topo + 12 + int(math.floor(xw * 0.18 + 4.0 * math.sin(xw * 0.023) + 0.5))
        _recortar(s, textura, u0, px, b, alto + 12, FUNDO_GELEIRA - 12)
    s.blit(_sombra(PROFUNDO_GELO, 12, TILE, FUNDO_GELEIRA + alto, (alto + 26, FUNDO_GELEIRA - 80.0), 0.75),
           (0, 0))
    # bolhas presas no gelo: redondas, claras, mais raras no fundo
    for n in range(3):
        if _h(tx, 40 + n) % 3 == 0:
            bx = 4 + _h(tx, 50 + n) % 38
            by = 22 + _h(tx, 60 + n) % 110
            luz = _misturar(BOLHA, PROFUNDO_GELO, min(0.8, by / 160.0))
            s.fill(luz, (bx, alto + by, PX * 2, PX))
            s.fill(luz, (bx - PX, alto + by + PX, PX * 4, PX))
            s.fill(luz, (bx, alto + by + 2 * PX, PX * 2, PX))
            s.fill(_misturar(luz, (255, 255, 255), 0.6), (bx, alto + by, PX, PX))
    # uma fenda fina descendo em zigue-zague, de vez em quando
    if _h(tx, 71) % 4 == 0:
        fx = 8 + _h(tx, 72) % 30
        for y in range(16, 120, PX):
            fx += (1 if (y // 6) % 2 else -1) * (PX if _h(tx, y) % 3 == 0 else 0)
            prof = min(1.0, y / 140.0)
            s.fill(_misturar(GELO_VEIO, PROFUNDO_GELO, prof * 0.6), (fx, alto + y, PX, PX))
            if y < 60:
                s.fill(_misturar(GELO_LUZ, GELO[0], 0.4), (fx + PX, alto + y, PX, PX))
    # raramente, uma runa da aurora gravada no gelo (redonda: pontudo e o perigo)
    if _h(tx, 81) % 17 == 0:
        cx, cy = 18 + _h(tx, 82) % 10, alto + 44
        for dx, dy in ((2, 0), (4, 0), (0, 2), (6, 2), (0, 4), (6, 4), (2, 6), (4, 6), (3, 3)):
            s.fill(_misturar(AURORA_GELO, GELO[1], 0.3), (cx + dx, cy + dy, PX, PX))
    # a capa de neve: montinhos que seguem o x do mundo, com a sombra azul por baixo
    for px in range(0, TILE, PX):
        xw = x0 + px
        monte = 2.0 + 1.6 * math.sin(xw * 0.09) + 1.2 * math.sin(xw * 0.031 + 1.7)
        y0 = alto - int(monte // PX) * PX + 2 * PX
        s.fill(NEVE_FUNDA, (px, alto + 12, PX, 2 * PX))
        s.fill(NEVE_SOMBRA, (px, alto + 8, PX, 4 + (PX if _h(xw // PX, 3) % 3 == 0 else 0)))
        s.fill(NEVE, (px, y0, PX, alto + 8 - y0))
        s.fill(NEVE_LUZ, (px, y0, PX, PX))
        if _h(xw // PX, 91) % 13 == 0:
            s.fill((255, 255, 255), (px, y0 + PX, PX, PX))  # um cristal de neve que brilha
    # a neve pinga para dentro do gelo, em gotas que congelaram
    for px in range(0, TILE, 2 * PX):
        gota = _h((x0 + px) // (2 * PX), 23) % 5
        if gota >= 3:
            s.fill(NEVE_SOMBRA, (px, alto + 16, PX, (gota - 1) * PX))
            s.fill(NEVE, (px, alto + 16, PX, PX))
    # degrau e beira de vao: a quina acesa pela lua (a direita), sombra na esquerda
    for lado, x in ((-1, 0), (1, TILE - 2)):
        viz = chao.get(tx + lado)
        if viz is None or viz > chao[tx]:
            ate = FUNDO_GELEIRA if viz is None else (viz - chao[tx]) * TILE
            cor = GELO_LUZ if lado > 0 else GELO_VEIO
            s.blit(_quina(cor, PROFUNDO_GELO, 12, min(ate, FUNDO_GELEIRA), (26, FUNDO_GELEIRA - 80.0)),
                   (x, alto + 12))
            s.fill(NEVE_LUZ, (x, alto + 2, 2, 10))
    return s


def fosso_geleira(tela, tx0, tx1, y, cam_x, cam_y):
    """O fundo de uma fenda da geleira: gelo escuro onde os cristais estao cravados."""
    alto = tela.get_height()
    x, w, sy = tx0 * TILE - cam_x, (tx1 - tx0) * TILE, y - cam_y
    if sy >= alto:
        return
    for grossura, cor in ((PX, NEVE_FUNDA), (3 * PX, GELO[3]),
                          (4 * PX, _misturar(GELO[3], PROFUNDO_GELO, 0.5)),
                          (4 * PX, _misturar(GELO_VEIO, PROFUNDO_GELO, 0.7))):
        tela.fill(cor, (x, sy, w, grossura))
        sy += grossura
    tela.fill(PROFUNDO_GELO, (x, sy, w, alto - sy))
    for k in range(0, w, 10):
        h = _h(tx0 * TILE + k, 9)
        if h % 3 == 0:
            tela.fill(NEVE_SOMBRA, (x + k + h % 6, y - cam_y, 2 * PX, PX))


ESTILO = {"bosque": _desenhar_bosque, "dunas": _desenhar_dunas, "ilhas": _desenhar_coluna,
          "geleira": _desenhar_geleira, "eclipse": _desenhar_cidadela}
# a parte de baixo que ja e so sombra: abaixo da superficie guardada, a tela e preenchida
PREENCHER = {"bosque": (FUNDO_BOSQUE, PROFUNDO_BOSQUE), "dunas": (FUNDO_DUNAS, PROFUNDO_DUNAS),
             "geleira": (FUNDO_GELEIRA, PROFUNDO_GELO),
             "eclipse": (FUNDO_CIDADELA, PROFUNDO)}


FORCA_CLIMA = 0.55     # o chao pega o clima do ceu pela metade: a linha que o olho segue fica


def _no_clima(s, fase, tx):
    """
    Tinge a coluna com o clima do ato em que ela esta (cenario.clima), mais
    fraco que no ceu. E feito uma vez, quando a coluna e desenhada: de graca.
    """
    from .cenario import clima
    c = clima(fase, (tx + 0.5) * TILE)
    if not c:
        return s
    mult = tuple(int(255 - (255 - m) * FORCA_CLIMA) for m in c[0])
    soma = tuple(int(a * FORCA_CLIMA * 0.6) for a in c[1])
    s.fill(mult, special_flags=pygame.BLEND_RGB_MULT)
    s.fill(soma, special_flags=pygame.BLEND_RGB_ADD)
    return s


def coluna(fase, tx):
    chave = (fase.ident, tx)
    s = _colunas.get(chave)
    if s is None:
        s = _colunas[chave] = _no_clima(ESTILO[fase.cancao](fase, tx), fase, tx)
        if len(_colunas) > GUARDA:
            _colunas.popitem(last=False)
    else:
        _colunas.move_to_end(chave)
    return s


ADIANTE = 6        # colunas pintadas antes de entrar na tela, uma por quadro


def preparar(fase):
    """
    As contas da fase inteira (o fundo das ilhas, as lajes do bosque) e as
    primeiras colunas do chao, antes do 1o quadro -- debaixo da transicao.
    """
    if fase.cancao == "ilhas":
        _perfil(fase)
    elif fase.cancao == "bosque":
        _lajes(fase)
    if fase.cancao in ESTILO:
        for tx in sorted(fase.chao_col)[:40]:
            coluna(fase, tx)


def _adiantar(fase, c1):
    """Pinta a proxima coluna que ainda vai entrar na tela (no maximo uma por quadro)."""
    chao = fase.chao_col
    for tx in range(c1, c1 + ADIANTE):
        if tx in chao and (fase.ident, tx) not in _colunas:
            coluna(fase, tx)
            return


def desenhar(tela, fase, cam_x, cam_y, c0, c1, tempo=0.0):
    """O chao das colunas [c0, c1) visiveis, no lugar do chao desenhado por codigo."""
    chao = fase.chao_col
    if fase.cancao == "ilhas":
        _perfil(fase)
        for x, y in _pontas[fase.ident]:
            if cam_x - 16 < x < cam_x + TILE * (c1 - c0) + 16:
                _cascata(tela, x - cam_x, y - cam_y, tempo)
    fundo, sombra = PREENCHER.get(fase.cancao, (None, None))
    alto = tela.get_height()
    for tx in range(c0, c1):
        if tx in chao:
            x, y = tx * TILE - cam_x, chao[tx] * TILE - cam_y
            tela.blit(coluna(fase, tx), (x, y - ACIMA))
            if fundo and y + fundo < alto:
                tela.fill(sombra, (x, y + fundo, TILE, alto - y - fundo))
    _adiantar(fase, c1)


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
