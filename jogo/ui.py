"""
Kit de interface: fonte pixelada, texto, paineis, barras, botoes e menus.

A fonte e a Silkscreen (SIL OFL), renderizada SEM antialias para continuar
pixel art. Cada texto e rasterizado uma vez e guardado em cache.
"""

import pygame

from . import arte
from .config import FONTE, BRANCO, PAINEL, AZUL, CINZA

_fontes = {}
_textos = {}
_imagens = {}


def imagem(nome, escala=1):
    """
    Peca de assets/art/ui/ ampliada por `escala`, sem suavizar -- ou None, e
    quem chamou desenha por codigo, como antes da arte existir.
    """
    chave = (nome, escala)
    if chave not in _imagens:
        img = arte.png("ui", nome)
        _imagens[chave] = img if img is None or escala == 1 else pygame.transform.scale_by(img, escala)
    return _imagens[chave]


def fonte(tam):
    f = _fontes.get(tam)
    if f is None:
        f = _fontes[tam] = pygame.font.Font(FONTE, tam)
    return f


def texto(s, tam, cor=BRANCO):
    chave = (s, tam, cor)
    surf = _textos.get(chave)
    if surf is None:
        if len(_textos) > 2000:
            _textos.clear()
        surf = _textos[chave] = fonte(tam).render(s, False, cor)
    return surf


def desenhar_texto(tela, s, tam, x, y, cor=BRANCO, alinhar="centro"):
    """Desenha `s` com o centro vertical em `y`; `alinhar` diz o que fica em `x`."""
    surf = texto(s, tam, cor)
    if alinhar == "centro":
        x -= surf.get_width() // 2
    elif alinhar == "direita":
        x -= surf.get_width()
    tela.blit(surf, (int(x), int(y - surf.get_height() // 2)))
    return surf


def desenhar_texto_ajustado(tela, s, tam, x, y, largura_max, cor=BRANCO):
    """Como `desenhar_texto` (centrado), diminuindo o corpo ate caber em `largura_max`."""
    while tam > 10 and texto(s, tam, cor).get_width() > largura_max:
        tam -= 2
    return desenhar_texto(tela, s, tam, x, y, cor)


# Molduras 9-slice (assets/art/ui/moldura_*.png): nome -> quina, em px da arte.
# Quinas ficam como desenhadas; lados e miolo esticam a partir de uma faixa de
# 1 pixel da arte, entao nenhum enfeite se repete nem deforma. Ampliadas 2x.
MOLDURAS = {"padrao": 10, "foco": 10, "bosque": 12, "ilhas": 12, "eclipse": 14}
ESCALA_MOLDURA = 2
_molduras = {}


def _nove_fatias(img, quina, w, h, k):
    fonte_ = pygame.transform.scale_by(img, k)
    q, fw, fh = quina * k, fonte_.get_width(), fonte_.get_height()
    q = min(q, w // 2, h // 2)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    def pedaco(x, y, pw, ph, dx, dy, dw, dh):
        if dw > 0 and dh > 0:
            s.blit(pygame.transform.scale(fonte_.subsurface((x, y, pw, ph)), (dw, dh)), (dx, dy))
    mw, mh = w - 2 * q, h - 2 * q
    for (sx, dx) in ((0, 0), (fw - q, w - q)):                 # quinas
        for (sy, dy) in ((0, 0), (fh - q, h - q)):
            pedaco(sx, sy, q, q, dx, dy, q, q)
    pedaco(q, 0, k, q, q, 0, mw, q)                             # lados
    pedaco(q, fh - q, k, q, q, h - q, mw, q)
    pedaco(0, q, q, k, 0, q, q, mh)
    pedaco(fw - q, q, q, k, w - q, q, q, mh)
    pedaco(q, q, k, k, q, q, mw, mh)                            # miolo
    return s


def moldura(tela, nome, x, y, w, h, alpha=255):
    """Desenha a moldura `nome` esticada para w x h. False se nao ha arte."""
    img = arte.png("ui", f"moldura_{nome}.png")
    if img is None:
        return False
    chave = (nome, int(w), int(h), alpha)
    s = _molduras.get(chave)
    if s is None:
        if len(_molduras) > 200:
            _molduras.clear()
        s = _molduras[chave] = _nove_fatias(img, MOLDURAS[nome], int(w), int(h), ESCALA_MOLDURA)
        if alpha < 255:
            s.set_alpha(alpha)
    tela.blit(s, (int(x), int(y)))
    return True


def painel(tela, x, y, w, h, cor=PAINEL, borda=AZUL, alpha=220):
    s = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
    s.fill((*cor, alpha))
    tela.blit(s, (int(x), int(y)))
    if borda is not None:
        pygame.draw.rect(tela, borda, (int(x), int(y), int(w), int(h)), 3)


def barra(tela, x, y, w, h, valor, cor):
    x, y, w, h = int(x), int(y), int(w), int(h)
    trilho = arte.png("ui", "trilho.png")
    if trilho is not None:
        # o trilho de pontas de diamante: 8 px de ponta, e o miolo tem a altura da barra
        k = ESCALA_MOLDURA
        t = pygame.transform.scale_by(trilho, k)
        ponta, alto = 8 * k, t.get_height()
        y0 = y + h // 2 - alto // 2
        tela.blit(t, (x - ponta, y0), (0, 0, ponta, alto))
        tela.blit(pygame.transform.scale(t.subsurface((ponta, 0, k, alto)), (w, alto)), (x, y0))
        tela.blit(t, (x + w, y0), (t.get_width() - ponta, 0, ponta, alto))
    else:
        pygame.draw.rect(tela, arte.escurecer(cor, 0.8), (x, y, w, h))
    cheio = int(w * max(0.0, min(1.0, valor)))
    if cheio:
        pygame.draw.rect(tela, cor, (x, y, cheio, h))
        pygame.draw.rect(tela, arte.clarear(cor, 0.5), (x, y, cheio, 3))
    if trilho is None:
        pygame.draw.rect(tela, arte.clarear(cor, 0.2), (x, y, w, h), 2)


def escurecer_tela(tela, alpha):
    s = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    tela.blit(s, (0, 0))


class Botao:
    def __init__(self, rotulo, x, y, w=440, h=64, cor=AZUL):
        self.rotulo = rotulo
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.cor = cor

    def desenhar(self, tela, focado):
        r = self.rect.inflate(16, 8) if focado else self.rect
        if not moldura(tela, "foco" if focado else "padrao", r.x, r.y, r.w, r.h):
            painel(tela, r.x, r.y, r.w, r.h, arte.escurecer(self.cor, 0.85) if focado else PAINEL,
                   self.cor if focado else CINZA)
        if focado:
            # a barrinha na cor da acao (verde segue, vermelho sai), por dentro da borda
            pygame.draw.rect(tela, self.cor, (r.x + 16, r.y + 14, 6, r.h - 28))
        desenhar_texto(tela, self.rotulo, 24, r.centerx + (8 if focado else 0),
                       r.centery, BRANCO if focado else CINZA)


class Menu:
    """Lista de botoes navegavel por teclado (cima/baixo) e por mouse."""

    def __init__(self, botoes):
        self.botoes = botoes
        self.indice = 0

    def mover(self, d):
        self.indice = (self.indice + d) % len(self.botoes)

    def passar_mouse(self, pos):
        for i, b in enumerate(self.botoes):
            if b.rect.collidepoint(pos):
                self.indice = i

    def clique(self, pos):
        """Rotulo do botao clicado, ou None."""
        for b in self.botoes:
            if b.rect.collidepoint(pos):
                return b.rotulo
        return None

    @property
    def atual(self):
        return self.botoes[self.indice].rotulo

    def desenhar(self, tela):
        for i, b in enumerate(self.botoes):
            b.desenhar(tela, i == self.indice)
