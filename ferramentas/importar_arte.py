"""
Importa a arte crua do gerador para assets/art/, com o nome, a escala e a cor
que o jogo espera.

    ./.venv/bin/python ferramentas/importar_arte.py [pasta_crua]

O gerador entrega tudo em escala de tela e com nome automatico. Aqui cada
arquivo ganha o nome do contrato e passa por tres ajustes:

    recortar   tira a moldura transparente, para a peca medir o que desenha
    reduzir    o cenario vai para a escala do buffer (320x180): divide por 4
    enevoar    a camada distante recebe um veu da cor da colina -- e isso que
               cria profundidade: longe fica mais perto do fundo que de si

As pecas de objetos/jogo/ ainda viram cinza, porque quem poe a cor e o codigo
(uma forma serve as tres fases). O cinza e normalizado para o pixel mais claro
chegar a 255: tingido, ele volta exatamente a cor do tema.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "assets", "art")
# a arte crua do gerador: dentro do projeto (onde ela esta agora) ou, se nao,
# na copia antiga do projeto, onde ela nasceu
_CANDIDATAS = [os.path.join(RAIZ, "assets", "art", "objetos 2", "cenario"),
               "/home/matheus/JogoUFF/assets/objetos/cenario"]
CRUA = next((c for c in _CANDIDATAS if os.path.isdir(c)), _CANDIDATAS[0])

P = "Pixel_art_game_asset_for_a_2D"

# (arquivo cru, destino, altura alvo, veu)   veu = (cor, forca) ou None
COLINA_LONGE = ((13, 36, 39), 0.55)
COLINA_PERTO = ((20, 56, 60), 0.22)

BOSQUE = [
    # camada distante: silhuetas simples, pequenas, afogadas na cor da colina
    (f"{P} (3).png",   "cenario/bosque/longe_1.png", 26, COLINA_LONGE),
    ("arvore.png",     "cenario/bosque/longe_2.png", 22, COLINA_LONGE),
    ("arvore3 (2).png","cenario/bosque/longe_3.png", 20, COLINA_LONGE),
    ("arvore3.png",    "cenario/bosque/longe_4.png", 24, COLINA_LONGE),
    # camada proxima: as detalhadas, maiores, quase na cor cheia
    (f"{P} (4).png",   "cenario/bosque/perto_1.png", 44, COLINA_PERTO),
    (f"{P} (2).png",   "cenario/bosque/perto_2.png", 38, COLINA_PERTO),
    ("arvore2.png",    "cenario/bosque/perto_3.png", 34, COLINA_PERTO),
]

# pecas de jogo: viram cinza, o codigo tinge por fase.
# (cru, destino, largura, altura, ancora) -- a celula e exata: o caco precisa
# medir um tile, ou ele nao bate mais com a coluna em que a partitura o pos.
JOGO = [
    (f"bosque/{P} (7).png",  "jogo/caco1.png",   48,  48, "base"),
    (f"bosque/{P} (10).png", "jogo/caco2.png",   48,  48, "base"),
    (f"bosque/{P} (6).png",  "jogo/caco3.png",   48,  48, "base"),
    (f"bosque/{P} (11).png", "jogo/bloco.png",   48,  48, "encher"),
    (f"bosque/{P} (20).png", "jogo/chevron.png", 32,  32, "centro"),
    (f"bosque/{P} (23).png", "jogo/portal.png",  96, 192, "encher"),
]

# pecas de jogo PROPRIAS de uma fase: ja vem coloridas, o codigo nao tinge.
# O chao e o topo de pedra com musgo; abaixo dele o codigo pinta a cor do tema.
JOGO_FASE = [
    (f"bosque/{P} (15).png", "jogo/bosque/chao.png"),
]

# ================================================================= UI
# A pasta crua objetos/ui/ e a fonte oficial da interface. Os tres emblemas
# vieram como um CONJUNTO (coluna numa ilha com o astro atras, na paleta de
# cada fase): o da ilha gramada substitui o escudo com arvore do bosque.
CRUA_UI = os.path.join(os.path.dirname(CRUA), "ui")
EMB = "Level_emblem_icon_96x96_a_ro"
UI_EMBLEMAS = [
    (f"{EMB} (3).png", "emblema_bosque.png"),
    (f"{EMB} (2).png", "emblema_ilhas.png"),
    (f"{EMB}.png",     "emblema_eclipse.png"),
]
# no tamanho original: o codigo so posiciona (e amplia por fator inteiro)
UI_NATIVO = [
    (f"{P}.png",      "julgamento_perfeito.png"),
    (f"{P} (2).png",  "julgamento_bom.png"),
    (f"{P} (3).png",  "julgamento_erro.png"),
    (f"{P} (8).png",  "logo.png"),
]
UI_NOTAS = [(f"{P} (4).png", "nota_s.png"), (f"{P} (7).png", "nota_a.png"),
            (f"{P} (5).png", "nota_b.png"), (f"{P} (6).png", "nota_c.png")]
# coracao: vieram o cheio e o vazio. O do meio (cheio, na batida) e o cheio
# ampliado -- 32 -> 38 px, o mesmo pulso de ~6 px do coracao por codigo.
UI_CORACAO = (f"{P} (10).png", f"{P} (9).png", 38)

# molduras 9-slice da pasta "Painel e botao": recortadas no desenho; quem estica
# e o codigo (ui.moldura). Das 16, estas sao as que o jogo usa.
CRUA_PAINEIS = os.path.join(RAIZ, "assets", "art", "Painel e botao")
UI_MOLDURAS = [
    (f"{P} (13).png", "moldura_padrao.png"),     # borda clara simples
    (f"{P} (16).png", "moldura_foco.png"),       # a borda que brilha: botao em foco
    (f"{P}.png",      "moldura_bosque.png"),     # pedra com musgo
    (f"{P} (11).png", "moldura_ilhas.png"),      # cristal
    (f"{P} (9).png",  "moldura_eclipse.png"),    # estrelas e luas
    (f"{P} (3).png",  "trilho.png"),             # a barra de progresso, pontas de diamante
]

LUA = (f"bosque/{P}.png", "cenario/bosque/astro_3f.png")


# ================================================================== ILHAS
# Cores do tema (config.py): as pecas geradas na paleta errada sao recoloridas.
ILHAS_DESTAQUE = (255, 200, 130)
ILHAS_TOPO = (150, 226, 255)
ILHAS_LONGE = ((55, 39, 72), 0.45)        # a colina distante: escurecer(montanha, 0.35)
ILHAS_PERTO = ((86, 60, 112), 0.30)       # a colina proxima: a montanha

ILHAS_CENARIO = [
    # distantes: silhuetas escuras e pequenas, sem contorno, quase da cor do fundo
    (f"{P} (2).png", "cenario/ilhas/longe_1.png", 16, ILHAS_LONGE),
    (f"{P} (3).png", "cenario/ilhas/longe_2.png", 22, ILHAS_LONGE),
    (f"{P} (4).png", "cenario/ilhas/longe_3.png", 13, ILHAS_LONGE),
    (f"{P} (5).png", "cenario/ilhas/longe_4.png", 19, ILHAS_LONGE),
    # proximas: as das cascatas, maiores
    (f"{P} (6).png", "cenario/ilhas/perto_1.png", 36, ILHAS_PERTO),
    (f"{P} (7).png", "cenario/ilhas/perto_2.png", 30, ILHAS_PERTO),
    (f"{P} (8).png", "cenario/ilhas/perto_3.png", 34, ILHAS_PERTO),
]
# o sol ja vem em 3 quadros lado a lado (pequeno, grande na batida, pequeno)
ILHAS_SOL = (f"{P}.png", "cenario/ilhas/astro_3f.png")
# cada imagem de nuvem traz 3 ou 4 faixas: viram nuvens soltas, no tamanho original
ILHAS_NUVENS = [f"{P} (9).png", f"{P} (10).png", f"{P} (11).png"]

# pecas de jogo proprias das ilhas: coloridas, escala de tela
# (cru, destino, largura, altura, ancora)
ILHAS_JOGO = [
    (f"{P} (14).png", "jogo/ilhas/caco1.png",   48,  48, "base"),
    # os de 2 e 3 pontas vieram largos e baixos (25 px): a hitbox pegava o vao
    # entre as pontas e matava sem contato visivel. Esticados ate a altura das
    # pontas do bosque, voltam a cobrir a hitbox como o desenho por codigo.
    (f"{P} (13).png", "jogo/ilhas/caco2.png",   48,  48, "pontas"),
    (f"{P} (12).png", "jogo/ilhas/caco3.png",   48,  48, "pontas"),
    (f"{P} (15).png", "jogo/ilhas/bloco.png",   48,  48, "encher"),
    (f"{P} (26).png", "jogo/ilhas/portal.png",  96, 192, "base"),
]
# colunas: tamanho original (1 pixel de arte = 1 pixel), o 2o quadro e o
# capitel de gelo aceso -- a coluna acende na batida
ILHAS_COLUNAS = [f"{P} (27).png", f"{P} (28).png", f"{P} (29).png"]
# ponte: a tabua e o pilar vieram na paleta do bosque (verde) e sao recoloridos;
# a faixa de luz ja e ciano e branca, como o topo do chao das ilhas
ILHAS_TABUA = (165, 130, 84)               # escurecer(destaque, 0.35), como a ponte por codigo
# duas tabuas que se alternam: 24 tabuas iguais em fila parecem carimbo
ILHAS_PONTE_OFF = ([f"{P} (16).png", f"{P} (19).png"], ILHAS_TABUA)
ILHAS_PONTE_PRONTA = (f"{P} (21).png", ILHAS_DESTAQUE)
ILHAS_PONTE_VIVA = [f"{P} (17).png", f"{P} (22).png", f"{P} (25).png"]
ILHAS_PILAR = (f"{P} (20).png", ILHAS_TOPO)
ILHAS_CHEVRON = f"{P} (30).png"            # chegou depois: o "pule aqui" dourado das ilhas


# ================================================================ ECLIPSE
ECLIPSE_LONGE = ((31, 15, 52), 0.45)      # a colina distante: escurecer(montanha, 0.35)
ECLIPSE_PERTO = ((48, 24, 80), 0.25)      # a colina proxima: a montanha

# as duas imagens de cenario trazem varias construcoes soltas: cada uma vira uma
# peca. Sem tirar contorno: o roxo quase preto da muralha e porta e sombra, nao
# traco -- e sobre o fundo roxo ele nao endurece como o preto do bosque.
ECLIPSE_TORRES = (f"{P} (3).png", (26, 28, 25, 24))     # 4 torres -> longe_1..4
ECLIPSE_MURALHAS = (f"{P} (2).png", (40, 36, 32))       # 3 muralhas -> perto_1..3
# o sol eclipsado vem em 1 quadro: o pulso sai de 3 tamanhos dele, como a lua.
# O disco e preto DE PROPOSITO: aqui nao se tira contorno preto nenhum.
ECLIPSE_SOL = (f"{P}.png", (34, 38, 36))

ECLIPSE_JOGO = [
    (f"{P} (5).png",  "jogo/eclipse/caco1.png",    48,  48, "base"),
    (f"{P} (4).png",  "jogo/eclipse/caco2.png",    48,  48, "pontas"),
    (f"{P} (6).png",  "jogo/eclipse/caco3.png",    48,  48, "pontas"),
    (f"{P} (7).png",  "jogo/eclipse/bloco.png",    48,  48, "encher"),
    (f"{P} (26).png", "jogo/eclipse/portal.png",   96, 192, "base"),
]
# o chevron veio em chamas vermelho-alaranjadas: a mesma familia de cor dos
# cacos. Forma E cor marcam o perigo (e o que deixa o jogo legivel para
# daltonicos), entao a guia e recolorida para o dourado de destaque do tema.
ECLIPSE_CHEVRON = (f"{P} (10).png", (255, 206, 120))
# colunas alternando dois estilos, pilar gotico e torre com o orbe do eclipse.
# A (16) fica de fora: o sol dela tem raios pontudos, e so o perigo e pontudo.
ECLIPSE_COLUNAS = [f"{P} (18).png", f"{P} (14).png", f"{P} (19).png",
                   f"{P} (15).png", f"{P} (20).png"]
ECLIPSE_PONTE_VIVA = [f"{P} (8).png", f"{P} (9).png", f"{P} (24).png", f"{P} (25).png"]
ECLIPSE_PILARES = [f"{P} (17).png", f"{P} (21).png", f"{P} (22).png", f"{P} (23).png"]



# ------------------------------------------------------------------ ajustes
def recortar(img):
    bb = img.get_bounding_rect(min_alpha=8)
    return img.subsurface(bb).copy() if bb.w and bb.h else img


def por_altura(img, alvo):
    k = alvo / img.get_height()
    return pygame.transform.scale(img, (max(1, round(img.get_width() * k)), alvo))


def encaixar(img, w, h, ancora):
    """Poe a peca numa celula exata de w x h, sem distorcer (salvo 'encher')."""
    if ancora == "encher":
        return pygame.transform.scale(img, (w, h))
    if ancora == "pontas":
        # toda a largura, e as pontas a 1/6 do topo -- a altura das do bosque
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        alto = h - h // 6
        s.blit(pygame.transform.scale(img, (w, alto)), (0, h - alto))
        return s
    k = min(w / img.get_width(), h / img.get_height())
    q = pygame.transform.scale(img, (max(1, round(img.get_width() * k)),
                                     max(1, round(img.get_height() * k))))
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    x = (w - q.get_width()) // 2
    y = h - q.get_height() if ancora == "base" else (h - q.get_height()) // 2
    s.blit(q, (x, y))
    return s


def sem_contorno(img):
    """
    Troca o contorno preto puro pela cor de sombra da propria peca (a mais
    escura que nao e preta). A silhueta nao muda de tamanho; so some o traco
    duro, que numa camada de fundo achata a profundidade.
    """
    sombra, menor = None, 999
    for x in range(img.get_width()):
        for y in range(img.get_height()):
            c = img.get_at((x, y))
            L = 0.299 * c.r + 0.587 * c.g + 0.114 * c.b
            if c.a > 128 and 16 <= L < menor:
                sombra, menor = (c.r, c.g, c.b), L
    if sombra is None:
        return img
    s = img.copy()
    for x in range(s.get_width()):
        for y in range(s.get_height()):
            c = s.get_at((x, y))
            if c.a and 0.299 * c.r + 0.587 * c.g + 0.114 * c.b < 16:
                s.set_at((x, y), (*sombra, c.a))
    return s


def pedacos(img, minimo=6):
    """
    Cada desenho solto dentro da imagem (componentes conexas do alfa), da
    esquerda para a direita e de cima para baixo. Descarta sujeira de poucos px.
    """
    w, h = img.get_size()
    visto, achados = set(), []
    for x0 in range(w):
        for y0 in range(h):
            if (x0, y0) in visto or img.get_at((x0, y0)).a < 8:
                continue
            pilha, pts = [(x0, y0)], []
            visto.add((x0, y0))
            while pilha:
                x, y = pilha.pop()
                pts.append((x, y))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < w and 0 <= ny < h and (nx, ny) not in visto
                                and img.get_at((nx, ny)).a >= 8):
                            visto.add((nx, ny))
                            pilha.append((nx, ny))
            if len(pts) >= minimo:
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                r = pygame.Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
                achados.append((r, set(pts)))
    achados.sort(key=lambda a: (a[0].y // 8, a[0].x))
    saida = []
    for r, pts in achados:
        s = pygame.Surface(r.size, pygame.SRCALPHA)
        for x, y in pts:
            s.set_at((x - r.x, y - r.y), img.get_at((x, y)))
        saida.append(s)
    return saida


def limpar(img, minimo=12):
    """
    Some com a sujeira (pixel solto perdido no canto), mas guarda todo desenho
    de verdade: o orbe de eclipse que flutua em cima da torre e um pedaco
    separado dela, e nao pode ir embora junto com a sujeira.
    """
    w, h = img.get_size()
    visto, manter = set(), []
    for x0 in range(w):
        for y0 in range(h):
            if (x0, y0) in visto or img.get_at((x0, y0)).a < 8:
                continue
            pilha, pts = [(x0, y0)], []
            visto.add((x0, y0))
            while pilha:
                x, y = pilha.pop()
                pts.append((x, y))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < w and 0 <= ny < h and (nx, ny) not in visto
                                and img.get_at((nx, ny)).a >= 8):
                            visto.add((nx, ny))
                            pilha.append((nx, ny))
            if len(pts) >= minimo:
                manter.extend(pts)
    xs, ys = [p[0] for p in manter], [p[1] for p in manter]
    r = pygame.Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    s = pygame.Surface(r.size, pygame.SRCALPHA)
    for x, y in manter:
        s.set_at((x - r.x, y - r.y), img.get_at((x, y)))
    return s


def recolorir(img, cor):
    """Troca a paleta inteira por tons de `cor`, mantendo luz e sombra."""
    s = acinzentar(img)
    s.fill((*cor, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return s


def acender_topo(img, linhas=16, k=0.65, poupar_escuros=False):
    """
    O quadro 'aceso': as `linhas` de cima puxadas para o branco. Com
    `poupar_escuros`, so acende o que ja brilha -- o disco preto de um eclipse
    continua preto, e quem acende e a coroa em volta dele.
    """
    s = img.copy()
    for x in range(s.get_width()):
        for y in range(min(linhas, s.get_height())):
            c = s.get_at((x, y))
            if poupar_escuros and 0.299 * c.r + 0.587 * c.g + 0.114 * c.b < 40:
                continue
            if c.a:
                s.set_at((x, y), (int(c.r + (255 - c.r) * k), int(c.g + (255 - c.g) * k),
                                  int(c.b + (255 - c.b) * k), c.a))
    return s


def em_tira(quadros, w, h, ancora="centro"):
    """Monta uma tira horizontal com cada quadro numa celula de w x h."""
    s = pygame.Surface((w * len(quadros), h), pygame.SRCALPHA)
    for i, q in enumerate(quadros):
        x = i * w + (w - q.get_width()) // 2
        y = h - q.get_height() if ancora == "base" else (h - q.get_height()) // 2
        s.blit(q, (x, y))
    return s


def enevoar(img, cor, k):
    """Puxa os pixels na direcao de `cor`, preservando o alfa."""
    s = img.copy()
    for x in range(s.get_width()):
        for y in range(s.get_height()):
            c = s.get_at((x, y))
            if c.a:
                s.set_at((x, y), (int(c.r + (cor[0] - c.r) * k),
                                  int(c.g + (cor[1] - c.g) * k),
                                  int(c.b + (cor[2] - c.b) * k), c.a))
    return s


def acinzentar(img):
    """Luminancia normalizada: o pixel mais claro vira 255, para o tingimento."""
    s = img.copy()
    pico = 1
    for x in range(s.get_width()):
        for y in range(s.get_height()):
            c = s.get_at((x, y))
            if c.a > 8:
                pico = max(pico, int(0.299 * c.r + 0.587 * c.g + 0.114 * c.b))
    for x in range(s.get_width()):
        for y in range(s.get_height()):
            c = s.get_at((x, y))
            if c.a:
                L = min(255, int((0.299 * c.r + 0.587 * c.g + 0.114 * c.b) * 255 / pico))
                s.set_at((x, y), (L, L, L, c.a))
    return s


def salvar(img, destino):
    caminho = os.path.join(DESTINO, "objetos" if "/" in destino else "ui", destino)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    pygame.image.save(img, caminho)
    print(f"  {destino:34} {img.get_width()}x{img.get_height()}")


def abrir(*partes):
    return pygame.image.load(os.path.join(CRUA, *partes)).convert_alpha()


def importar_ilhas():
    ab = lambda nome: abrir("ilhas", nome)

    print("ilhas / cenario (escala do buffer, colorido):")
    for cru, destino, alt, veu in ILHAS_CENARIO:
        img = por_altura(sem_contorno(recortar(ab(cru))), alt)
        salvar(enevoar(img, *veu), destino)
    sois = pedacos(ab(ILHAS_SOL[0]))
    salvar(em_tira(sois, 44, 44), ILHAS_SOL[1])
    nuvens = [q for cru in ILHAS_NUVENS for q in pedacos(ab(cru))]
    for i, q in enumerate(nuvens, 1):
        salvar(q, f"cenario/ilhas/nuvem_{i}.png")

    print("ilhas / jogo (escala de tela, colorido, so desta fase):")
    for cru, destino, w, h, ancora in ILHAS_JOGO:
        salvar(encaixar(recortar(ab(cru)), w, h, ancora), destino)
    for i, cru in enumerate(ILHAS_COLUNAS, 1):
        col = limpar(ab(cru))
        salvar(em_tira([col, acender_topo(col)], 48, 96, "base"), f"jogo/ilhas/coluna_{i}_2f.png")
    seg = lambda cru: pygame.transform.scale(limpar(ab(cru)), (48, 14))
    for i, cru in enumerate(ILHAS_PONTE_OFF[0], 1):
        salvar(recolorir(seg(cru), ILHAS_PONTE_OFF[1]), f"jogo/ilhas/ponte_off_{i}.png")
    salvar(recolorir(seg(ILHAS_PONTE_PRONTA[0]), ILHAS_PONTE_PRONTA[1]), "jogo/ilhas/ponte_pronta.png")
    salvar(em_tira([seg(c) for c in ILHAS_PONTE_VIVA], 48, 14), "jogo/ilhas/ponte_viva_3f.png")
    pilar = limpar(ab(ILHAS_PILAR[0]))
    salvar(recolorir(pygame.transform.scale_by(pilar, 2), ILHAS_PILAR[1]), "jogo/ilhas/ponte_pilar.png")

    salvar(encaixar(recortar(ab(ILHAS_CHEVRON)), 32, 32, "centro"), "jogo/ilhas/chevron.png")




def importar_eclipse():
    ab = lambda nome: abrir("eclipse", nome)

    print("eclipse / cenario (escala do buffer, colorido):")
    for (cru, alturas), prefixo, veu in ((ECLIPSE_TORRES, "longe", ECLIPSE_LONGE),
                                         (ECLIPSE_MURALHAS, "perto", ECLIPSE_PERTO)):
        for i, (peca, alt) in enumerate(zip(pedacos(ab(cru)), alturas), 1):
            salvar(enevoar(por_altura(peca, alt), *veu), f"cenario/eclipse/{prefixo}_{i}.png")
    sol = recortar(ab(ECLIPSE_SOL[0]))
    salvar(em_tira([por_altura(sol, a) for a in ECLIPSE_SOL[1]], 44, 44),
           "cenario/eclipse/astro_3f.png")

    print("eclipse / jogo (escala de tela, colorido, so desta fase):")
    for cru, destino, w, h, ancora in ECLIPSE_JOGO:
        salvar(encaixar(recortar(ab(cru)), w, h, ancora), destino)
    chevron = encaixar(recortar(ab(ECLIPSE_CHEVRON[0])), 32, 32, "centro")
    salvar(recolorir(chevron, ECLIPSE_CHEVRON[1]), "jogo/eclipse/chevron.png")
    for i, cru in enumerate(ECLIPSE_COLUNAS, 1):
        col = limpar(ab(cru))
        salvar(em_tira([col, acender_topo(col, poupar_escuros=True)], 56, 96, "base"),
               f"jogo/eclipse/coluna_{i}_2f.png")
    faixas = [pygame.transform.scale(limpar(ab(c)), (48, 11)) for c in ECLIPSE_PONTE_VIVA]
    salvar(em_tira(faixas, 48, 11), "jogo/eclipse/ponte_viva_4f.png")
    for i, cru in enumerate(ECLIPSE_PILARES, 1):
        salvar(pygame.transform.scale_by(limpar(ab(cru)), 2), f"jogo/eclipse/ponte_pilar_{i}.png")




def importar_ui():
    ab = lambda nome: pygame.image.load(os.path.join(CRUA_UI, nome)).convert_alpha()
    print("ui (escala de tela, colorida):")
    for cru, destino in UI_EMBLEMAS:
        salvar(encaixar(recortar(ab(cru)), 96, 96, "centro"), destino)
    for cru, destino in UI_NATIVO:
        salvar(recortar(ab(cru)), destino)
    for cru, destino in UI_NOTAS:
        salvar(ab(cru), destino)                         # ja vem na celula de 64x64
    cheio, vazio = recortar(ab(UI_CORACAO[0])), recortar(ab(UI_CORACAO[1]))
    batendo = por_altura(cheio, round(cheio.get_height() * UI_CORACAO[2] / cheio.get_width()))
    salvar(em_tira([cheio, batendo, vazio], 40, 40), "coracao_3f.png")
    for cru, destino in UI_MOLDURAS:
        salvar(recortar(pygame.image.load(os.path.join(CRUA_PAINEIS, cru)).convert_alpha()), destino)


def main():
    global CRUA
    if len(sys.argv) > 1:
        CRUA = sys.argv[1]
    pygame.init()
    pygame.display.set_mode((1, 1))

    print("cenario (escala do buffer, colorido):")
    for cru, destino, alt, veu in BOSQUE:
        img = por_altura(sem_contorno(recortar(abrir("bosque", cru))), alt)
        salvar(enevoar(img, *veu) if veu else img, destino)

    # a lua vira uma tira de 3 quadros: repouso, estourada na batida, voltando
    print("astro (3 quadros de 44x44):")
    # a lua crua e cinza: puxo para o creme do tema, mantendo as crateras
    lua = enevoar(recortar(abrir(*LUA[0].split("/"))), (255, 226, 170), 0.6)
    tira = pygame.Surface((44 * 3, 44), pygame.SRCALPHA)
    for i, alt in enumerate((24, 28, 26)):
        q = por_altura(lua, alt)
        tira.blit(q, (i * 44 + (44 - q.get_width()) // 2, (44 - alt) // 2))
    salvar(tira, LUA[1])

    print("jogo (escala de tela, cinza -- o codigo tinge):")
    for cru, destino, w, h, ancora in JOGO:
        salvar(acinzentar(encaixar(recortar(abrir(*cru.split("/"))), w, h, ancora)),
               destino)

    print("jogo da fase (escala de tela, colorido, largura de 1 tile):")
    for cru, destino in JOGO_FASE:
        img = recortar(abrir(*cru.split("/")))
        salvar(pygame.transform.scale(img, (48, img.get_height() * 48 // img.get_width())),
               destino)

    importar_ilhas()
    importar_eclipse()
    importar_ui()


if __name__ == "__main__":
    main()
