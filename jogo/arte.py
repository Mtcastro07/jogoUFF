import os

import pygame

from .animacao import Animadinho
from .config import PASTA_DO_JOGO, IMAGEM_DO_LEO
from .imagem import abre_imagem

PASTA_ARTES = os.path.join(PASTA_DO_JOGO, "assets", "art")
FOLHAS = os.path.join(PASTA_DO_JOGO, "male_hero_free", "individual_sheets")

CELULA = 128
RECORTE = pygame.Rect(28, 24, 72, 60)
ESCALA = 2
PES = 56 * ESCALA
CENTRO = 32 * ESCALA
SUBIDA = [1, 2, 3, 4, 5]

todas_as_poses = {}
ja_feitos = {}
copias_prontas = {}
pngs_prontos = {}


def pega_png(*partes):
    if partes not in pngs_prontos:
        caminho = os.path.join(PASTA_ARTES, *partes)
        if os.path.exists(caminho):
            pngs_prontos[partes] = abre_imagem(caminho)
        else:
            pngs_prontos[partes] = None
    return pngs_prontos[partes]


def pega_tira(*partes, quadros):
    if pega_png(*partes) is None:
        return None
    if partes not in ja_feitos:
        ja_feitos[partes] = Animadinho(os.path.join(PASTA_ARTES, *partes), quadros)
    return ja_feitos[partes]


def peca(nome, fase):
    chave = ("peca", nome, fase)
    if chave not in ja_feitos:
        achada = None
        for arq in sorted(os.listdir(os.path.join(PASTA_ARTES, "objetos", "jogo", fase))):
            if arq == nome + ".png":
                achada = pega_tira("objetos", "jogo", fase, arq, quadros=1)
            elif arq.startswith(nome + "_") and arq.endswith("f.png"):
                quantos = arq[len(nome) + 1:-5]
                if quantos.isdigit():
                    achada = pega_tira("objetos", "jogo", fase, arq, quadros=int(quantos))
                    break
        ja_feitos[chave] = achada
    return ja_feitos[chave]


def guarda_copia(chave, img, nova):
    copias_prontas[chave] = (img, nova)
    if len(copias_prontas) > 600:
        del copias_prontas[next(iter(copias_prontas))]
    return nova


def recuar(img, cor, k):
    chave = ("recuar", id(img), cor, k)
    if chave in copias_prontas:
        return copias_prontas[chave][1]
    s = img.copy()
    v = int(255 * (1 - k))
    s.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
    s.fill((int(cor[0] * k), int(cor[1] * k), int(cor[2] * k)), special_flags=pygame.BLEND_RGB_ADD)
    return guarda_copia(chave, img, s)


def recuada(figurinha, cor, k):
    chave = ("recuada", id(figurinha), cor, k)
    if chave not in ja_feitos:
        ja_feitos[chave] = Animadinho.feito_de_quadros([recuar(q, cor, k) for q in figurinha.quadros])
    return ja_feitos[chave]


def aura(img, cor, raio=4):
    chave = ("aura", id(img), cor, raio)
    if chave in copias_prontas:
        return copias_prontas[chave][1]
    w, h = img.get_size()
    mascara = pygame.mask.from_surface(img, 128)
    forma = mascara.to_surface(setcolor=(*cor[:3], 255), unsetcolor=(0, 0, 0, 0))
    s = pygame.Surface((w + 2 * raio, h + 2 * raio), pygame.SRCALPHA)
    for d, alfa in ((raio, 46), (raio // 2, 80)):
        forma.set_alpha(alfa)
        for dx, dy in ((-d, 0), (d, 0), (0, -d), (0, d)):
            s.blit(forma, (raio + dx, raio + dy))
        for dx, dy in ((-d, -d), (d, -d), (-d, d), (d, d)):
            s.blit(forma, (raio + dx * 0.7, raio + dy * 0.7))
    return guarda_copia(chave, img, s)


def fantasma(img, alfa):
    chave = ("fantasma", id(img), alfa)
    if chave in copias_prontas:
        return copias_prontas[chave][1]
    s = img.copy()
    s.set_alpha(alfa)
    return guarda_copia(chave, img, s)


def fatia_tudo(folha, linha, n):
    quadros = []
    for i in range(n):
        x = i * CELULA + RECORTE.x
        y = linha * CELULA + RECORTE.y
        pedaco = folha.subsurface((x, y, RECORTE.w, RECORTE.h))
        quadros.append(pygame.transform.scale_by(pedaco, ESCALA))
    return Animadinho.feito_de_quadros(quadros)


def carrega_tudo():
    folha = abre_imagem(IMAGEM_DO_LEO)
    todas_as_poses["parado"] = fatia_tudo(folha, 1, 10)
    todas_as_poses["corre"] = fatia_tudo(folha, 3, 10)
    todas_as_poses["pula"] = fatia_tudo(folha, 4, 6)
    for nome, arq in (("cai", "male_hero-fall.png"), ("caindo", "male_hero-fall_loop.png")):
        folha = abre_imagem(os.path.join(FOLHAS, arq))
        todas_as_poses[nome] = fatia_tudo(folha, 0, folha.get_width() // CELULA)
    todas_as_poses["pouso"] = Animadinho.feito_de_quadros([todas_as_poses["pula"].pega_quadro(0)])


def pega_quadro(nome, i):
    return todas_as_poses[nome].pega_quadro(i)


def quantos_quadros(nome):
    return todas_as_poses[nome].total_frames


def quadro_do_pulo(vy, forca_do_pulo, tempo):
    if vy < 0.0:
        i = int((1.0 + vy / forca_do_pulo) * len(SUBIDA))
        return "pula", SUBIDA[min(len(SUBIDA) - 1, max(0, i))]
    k = vy / forca_do_pulo
    if k < 1.0:
        return "cai", min(quantos_quadros("cai") - 1, int(k * quantos_quadros("cai")))
    return "caindo", tempo * 10


def pega_heroi(nome, i):
    return pega_quadro(nome, i), CENTRO, PES


def faz_contorno(img, cor, e=2):
    borda = img.copy()
    borda.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
    borda.fill((*cor[:3], 0), special_flags=pygame.BLEND_RGBA_ADD)
    s = pygame.Surface((img.get_width() + 2 * e, img.get_height() + 2 * e), pygame.SRCALPHA)
    for dx in (-e, 0, e):
        for dy in (-e, 0, e):
            if dx or dy:
                s.blit(borda, (e + dx, e + dy))
    s.blit(img, (e, e))
    return s


def retrato(cor):
    chave = ("retrato", cor)
    if chave not in ja_feitos:
        q = pega_quadro("parado", 0)
        topo = q.get_bounding_rect(min_alpha=8).y
        xs = []
        for y in range(topo, topo + 16):
            for x in range(q.get_width()):
                if q.get_at((x, y)).a > 128:
                    xs.append(x)
        larg = max(xs) - min(xs) + 1
        corte = pygame.Rect(min(xs), topo, larg, round(larg * 0.95)).clip(q.get_rect())
        ja_feitos[chave] = faz_contorno(q.subsurface(corte).copy(), cor)
    return ja_feitos[chave]


def esticado(q, sx, sy):
    chave = ("esticado", id(q), sx, sy)
    if chave not in ja_feitos:
        w = max(1, round(q.get_width() * sx))
        h = max(1, round(q.get_height() * sy))
        ja_feitos[chave] = pygame.transform.scale(q, (w, h))
    return ja_feitos[chave]


def clareia(cor, k):
    return tuple(min(255, int(c + (255 - c) * k)) for c in cor[:3])


def escurece_cor(cor, k):
    return tuple(max(0, int(c * (1.0 - k))) for c in cor[:3])


CIANO = (120, 240, 255)


def nome_do_caco(quantidade, qual_desenho):
    if qual_desenho == 0:
        return f"caco{quantidade}"
    return f"caco{quantidade}v{qual_desenho + 1}"


def quantos_cacos(quantidade, fase):
    n = 1
    while peca(nome_do_caco(quantidade, n), fase):
        n += 1
    return n


def caco(quantidade, fase, qual_desenho=0):
    figurinha = peca(nome_do_caco(quantidade, qual_desenho), fase)
    if figurinha.total_frames > 1:
        return figurinha
    chave = ("caco", quantidade, fase, qual_desenho)
    if chave not in ja_feitos:
        ja_feitos[chave] = Animadinho.feito_de_quadros(pisca(figurinha.pega_quadro(0)))
    return ja_feitos[chave]


def contorno_do_caco(quantidade, fase, folga, qual_desenho):
    chave = ("perfil", quantidade, fase, qual_desenho)
    if chave not in ja_feitos:
        img = peca(nome_do_caco(quantidade, qual_desenho), fase).pega_quadro(0)
        w, h = img.get_size()
        perfil = []
        for x in range(w):
            y = 0
            while y < h and img.get_at((x, y)).a <= 128:
                y += 1
            perfil.append(min(h, y + folga))
        ja_feitos[chave] = perfil
    return ja_feitos[chave]


def acha_ponta(img):
    for y in range(img.get_height()):
        for x in range(img.get_width()):
            if img.get_at((x, y)).a > 128:
                return x, y


def pisca(base):
    w, h = base.get_size()
    x, y = acha_ponta(base)
    y += 3
    claro = clareia(CIANO, 0.4)
    faisca = base.copy()
    faisca.fill((255, 255, 255), (x - 1, y - 1, 3, 3))
    faisca.fill(claro, (x - 5, y, 2, 1))
    faisca.fill(claro, (x + 3, y, 2, 1))
    faisca.fill(claro, (x, y - 5, 1, 2))
    faisca.fill(claro, (x, y + 3, 1, 2))
    y0 = int(h * 0.55)
    fatia = base.copy()
    faixa = base.subsurface((0, y0, w, 4)).copy()
    fatia.fill((0, 0, 0, 0), (0, y0, w, 4))
    fatia.blit(faixa, (2, y0))
    for y in range(y0, y0 + 4):
        for x in range(w):
            if base.get_at((x, y)).a > 128:
                fatia.fill(CIANO, (x, y, 2, 1))
                break
    return [base] * 12 + [faisca, fatia, faisca, base]


def quantos_blocos(fase):
    n = 1
    while peca(f"bloco_v{n + 1}", fase):
        n += 1
    return n


def bloco(fase, qual_desenho):
    if qual_desenho == 0:
        return peca("bloco", fase).pega_quadro(0)
    return peca(f"bloco_v{qual_desenho + 1}", fase).pega_quadro(0)


def pega_coracao(cheio, ta_pulsando=False):
    figurinha = pega_tira("ui", "coracao_3f.png", quadros=3)
    if not cheio:
        figurinha.set_curr_frame(2)
    elif ta_pulsando:
        figurinha.set_curr_frame(1)
    else:
        figurinha.set_curr_frame(0)
    figurinha.set_transparency(255)
    return figurinha


TRONCO = ((30, 36, 34), (46, 54, 48), (66, 76, 64))
FOLHA = ((18, 40, 38), (28, 58, 50), (44, 84, 66), (74, 120, 88))
ARVORES = (
    (26, [(0, 0, 26), (-24, 9, 18), (25, 8, 19), (-10, -20, 17), (13, -17, 16),
          (-30, -4, 12), (31, -5, 12), (0, 14, 17)]),
    (0, [(0, 0, 11), (-12, 3, 9), (12, 2, 9), (-4, -6, 8), (5, -5, 7)]),
    (0, [(0, 0, 13), (-15, 4, 10), (15, 3, 11), (0, -8, 9)]),
    (30, [(0, 0, 24), (-22, 10, 17), (22, 9, 17), (-8, -18, 15), (11, -16, 15),
          (0, 13, 15)]),
    (0, [(0, 0, 9), (-10, 3, 7), (10, 2, 8), (0, -5, 6)]),
    (0, [(0, 0, 12), (-13, 3, 10), (13, 4, 9), (-3, -7, 8)]),
)


def arvore(qual_desenho):
    chave = ("arvore", qual_desenho)
    if chave not in ja_feitos:
        ja_feitos[chave] = pinta_arvore(*ARVORES[qual_desenho % len(ARVORES)])
    return ja_feitos[chave]


def pinta_arvore(tronco, bolas):
    raio_maior = max(abs(x) + r for x, _, r in bolas)
    tem_em_cima = max(r - y for _, y, r in bolas)
    abaixo = max(r + y for _, y, r in bolas)
    w, h = 2 * raio_maior + 4, tem_em_cima + abaixo + tronco + 2
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, tem_em_cima
    if tronco:
        sombra, corpo, luz = TRONCO
        s.fill(corpo, (cx - 3, cy, 7, h - cy))
        s.fill(luz, (cx + 2, cy, 2, h - cy))
        s.fill(sombra, (cx - 3, cy, 2, h - cy))
        for y in range(cy + 3, h - 3, 5):
            s.fill(sombra, (cx + (y % 3) - 1, y, 1, 2))
        s.fill(corpo, (cx - 6, h - 3, 13, 3))
        s.fill(sombra, (cx - 6, h - 1, 3, 1))
        s.fill(luz, (cx + 4, h - 3, 2, 1))
    cor_escura, cor_media, cor_clara, brilho = FOLHA
    for x, y, r in bolas:
        pygame.draw.circle(s, cor_escura, (cx + x, cy + y), r)
    for x, y, r in bolas:
        pygame.draw.circle(s, cor_media, (cx + x + 1, cy + y - 1), r - 2)
    for x, y, r in bolas:
        pygame.draw.circle(s, cor_clara, (cx + x + r // 3, cy + y - r // 3), r // 2)
        s.fill(brilho, (cx + x + r // 3, cy + y - r // 2, 2, 1))
    return pygame.transform.scale_by(s, 2)


POSTE = (46, 36, 66)


def portal_rapido(ta_rapido):
    chave = ("portal_vel", ta_rapido)
    if chave not in ja_feitos:
        ja_feitos[chave] = Animadinho.feito_de_quadros([pinta_portal(ta_rapido, q) for q in range(4)])
    return ja_feitos[chave]


def pinta_portal(ta_rapido, n_quadro):
    w, h = 44, 150
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    if ta_rapido:
        cor, sentido = (255, 196, 110), 2
    else:
        cor, sentido = (130, 210, 255), -2
    cor_clara = clareia(cor, 0.6)
    pygame.draw.rect(s, (*cor, 56), (6, 6, w - 12, h - 6))
    for x in (2, w - 6):
        s.fill(POSTE, (x, 0, 4, h))
        s.fill(cor, (x + 1, 4, 2, h - 4))
    s.fill(POSTE, (0, 0, w, 6))
    s.fill(cor_clara, (4, 2, w - 8, 2))
    for k in range(3):
        y = 30 + k * 40
        x = w // 2 - 6 + int(((n_quadro + k) % 4 - 1.5) * sentido)
        if ta_rapido:
            pontos = [(x, y), (x + 10, y + 10), (x, y + 20)]
        else:
            pontos = [(x + 10, y), (x, y + 10), (x + 10, y + 20)]
        pygame.draw.lines(s, cor_clara if (n_quadro + k) % 4 == 0 else cor, False, pontos, 3)
    return s
