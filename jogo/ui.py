import pygame

from . import arte
from .imagem import Desenho
from .config import FONTE, BRANCO, CONTORNO, LARG_TELA

fontes_prontas = {}
textos_prontos = {}
imagens_prontas = {}
_objetos = {}


def imagem(nome, escala=1):
    chave = (nome, escala)
    if chave not in imagens_prontas:
        img = arte.pega_png("ui", nome)
        if escala != 1:
            img = pygame.transform.scale_by(img, escala)
        imagens_prontas[chave] = img
    return imagens_prontas[chave]


def objeto(nome, escala=1):
    chave = (nome, escala)
    if chave not in _objetos:
        _objetos[chave] = Desenho(imagem(nome, escala))
    return _objetos[chave]


def fonte(tam):
    if tam not in fontes_prontas:
        fontes_prontas[tam] = pygame.font.Font(FONTE, tam)
    return fontes_prontas[tam]


def texto(s, tam, cor=BRANCO, borda_cor=None):
    chave = (s, tam, cor, borda_cor)
    if chave not in textos_prontos:
        if len(textos_prontos) > 2000:
            textos_prontos.clear()
        img = fonte(tam).render(s.replace("&", "E"), False, cor)
        if borda_cor is not None:
            img = arte.faz_contorno(img.convert_alpha(), borda_cor, max(2, tam // 16))
        textos_prontos[chave] = img
    return textos_prontos[chave]


def escreve(tela, s, tam, x, y, cor=BRANCO, lado_do_texto="centro", borda_cor=None):
    img = texto(s, tam, cor, borda_cor)
    if lado_do_texto == "centro":
        x -= img.get_width() // 2
    elif lado_do_texto == "direita":
        x -= img.get_width()
    tela.blit(img, (int(x), int(y - img.get_height() // 2)))


def escreve_cabendo(tela, s, tam, x, y, cabe_ate, cor=BRANCO):
    while tam > 10 and texto(s, tam, cor).get_width() > cabe_ate:
        tam -= 2
    escreve(tela, s, tam, x, y, cor)


MOLDURAS = {"padrao": 10, "foco": 10, "bosque": 12, "dunas": 12, "ilhas": 12, "geleira": 12,
            "eclipse": 14}
ESCALA_DA_MOLDURA = 2
molduras_prontas = {}


def corta_em_nove(img, quina, w, h):
    k = ESCALA_DA_MOLDURA
    img = pygame.transform.scale_by(img, k)
    fw, fh = img.get_size()
    q = quina * k
    n_colunas = ((0, q, 0, q), (q, k, q, w - 2 * q), (fw - q, q, w - q, q))
    linhas = ((0, q, 0, q), (q, k, q, h - 2 * q), (fh - q, q, h - q, q))
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for x, pw, dx, dw in n_colunas:
        for y, ph, dy, dh in linhas:
            if dw > 0 and dh > 0:
                pedaco = img.subsurface((x, y, pw, ph))
                s.blit(pygame.transform.scale(pedaco, (dw, dh)), (dx, dy))
    return s


def desenha_moldura(tela, nome, x, y, w, h, alpha=255):
    w, h = int(w), int(h)
    chave = (nome, w, h, alpha)
    if chave not in molduras_prontas:
        if len(molduras_prontas) > 200:
            molduras_prontas.clear()
        s = corta_em_nove(arte.pega_png("ui", f"moldura_{nome}.png"), MOLDURAS[nome], w, h)
        if alpha < 255:
            s.set_alpha(alpha)
        molduras_prontas[chave] = s
    tela.blit(molduras_prontas[chave], (int(x), int(y)))


def escurece_tela(tela, alpha):
    s = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    tela.blit(s, (0, 0))


def suaviza(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


COR_APAGADA = (196, 202, 228)
TECLA = (226, 230, 244)


def dicas(tela, pares, y):
    pecas = []
    larg = 0
    for tecla, o_que_faz in pares:
        t = texto(tecla, 16, CONTORNO)
        a = texto(o_que_faz, 16, COR_APAGADA, CONTORNO)
        pecas.append((t, a))
        larg += t.get_width() + 20 + 10 + a.get_width()
    larg += 36 * (len(pecas) - 1)
    x = (LARG_TELA - larg) // 2
    faixa = pygame.Surface((larg + 48, 40), pygame.SRCALPHA)
    faixa.fill((*CONTORNO, 120))
    tela.blit(faixa, (x - 24, int(y) - 20))
    for t, a in pecas:
        w = t.get_width() + 20
        pygame.draw.rect(tela, CONTORNO, (x - 2, int(y) - 15, w + 4, 32))
        pygame.draw.rect(tela, arte.escurece_cor(TECLA, 0.35), (x, int(y) - 13, w, 28))
        pygame.draw.rect(tela, TECLA, (x, int(y) - 13, w, 24))
        tela.blit(t, (x + 10, int(y) - 1 - t.get_height() // 2))
        tela.blit(a, (x + w + 10, int(y) - a.get_height() // 2))
        x += w + 10 + a.get_width() + 36
