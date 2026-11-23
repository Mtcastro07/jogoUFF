"""
A abertura: o comeco da historia, antes da tela inicial.

03:12 da madrugada. O Leo, de pijama, joga no quarto escuro; a TV mostra a
tela inicial do Rhythm Striker. Ele pensa "so mais uma fase...", aperta START
e a tela o puxa: o corpo clareia, espicha e some dentro da TV. A camera
mergulha na TV ate ela ocupar a tela inteira -- e o que estava nela e a tela
inicial de verdade, que assume dali (o mesmo quadro: a troca nao aparece).

Qualquer tecla, clique ou botao do controle pula a abertura.

O quarto (a classe Quarto) e compartilhado com o final (final.py), que faz o
caminho de volta. A arte e a do trailer (ferramentas/geradores/pintar_quarto.py,
em assets/art/trailer/): 320x180, ampliada 4x. Tudo o que e caro (o quarto, o
brilho da TV) e montado uma vez, no comeco da cena.
"""

import math
import random

import pygame

from . import arte, menus, ui
from .audio import audio
from .config import LARGURA, ALTURA, BRANCO, CONTORNO

TV = pygame.Rect(232 * 4, 88 * 4, 57 * 4, 32 * 4)    # a tela da TV, em pixels do jogo
PES = (176 * 4, 162 * 4)                             # os pes do Leo
FOCO = ((PES[0] + TV.centerx) / 2, 400)              # o centro do quadro fora da TV
LETRA = 0.05           # uma letra do pensamento a cada 50 ms
Y_FALA = 682

# a linha do tempo da abertura, em segundos
ACENDE = 1.0           # o quarto sai do escuro
PENSA = 1.3            # "so mais uma fase..."
START = 3.9            # o clique
PUXA = (4.2, 5.6)      # a tela puxa o Leo
MERGULHO = (5.5, 6.9)  # a camera entra na TV
FIM = MERGULHO[1]
FALA = "SÓ MAIS UMA FASE..."


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def fase(t, faixa):
    return max(0.0, min(1.0, (t - faixa[0]) / (faixa[1] - faixa[0])))


def pular(ev):
    """O que pula uma cena: qualquer tecla (menos o F11) ou o clique."""
    return (ev.type == pygame.KEYDOWN and ev.key != pygame.K_F11) or \
           (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1)


class Quarto:
    """O quarto do Leo, a TV e a camera que entra nela (ou sai dela)."""

    def __init__(self, fundo, leo_png, tela_tv):
        base = arte.png("trailer", fundo)
        self.base = pygame.transform.scale(base, (LARGURA, ALTURA)).convert()
        self.cena = pygame.Surface((LARGURA, ALTURA)).convert()
        # o brilho da TV no quarto, tingido pela cor media da tela, em alguns
        # niveis: ele cresce quando a TV puxa (ou devolve) o Leo
        mascara = pygame.transform.scale(arte.png("trailer", "brilho_tv.png"), (LARGURA, ALTURA)).convert()
        cor = pygame.transform.average_color(pygame.transform.smoothscale(tela_tv, TV.size))[:3]
        self.brilhos = []
        for i in range(10):
            k = 0.55 + 1.2 * i / 9
            g = mascara.copy()
            g.fill(tuple(min(255, int((40 + c * 0.8) * k)) for c in cor), special_flags=pygame.BLEND_MULT)
            self.brilhos.append(g)
        self.linhas = pygame.Surface(TV.size, pygame.SRCALPHA)   # as linhas de varredura do tubo
        for y in range(0, TV.h, 2):
            self.linhas.fill((0, 0, 0, 70), (0, y, TV.w, 1))
        self.leo = pygame.transform.scale_by(arte.png("personagens", leo_png), 4)
        self.leo_branco = self.leo.copy()
        self.leo_branco.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        self.veu_tv = pygame.Surface(TV.size).convert()
        self.veu_tv.fill(BRANCO)

    def _leo(self, tela, t, puxao):
        if puxao <= 0:
            respira = 4 if math.sin(t * 2.6) > 0.55 else 0     # um pixel: ele respira
            tela.blit(self.leo, (PES[0] - self.leo.get_width() // 2, PES[1] - self.leo.get_height() + respira))
            return
        if puxao >= 1:
            return
        # o corpo clareia, espicha na direcao da TV e some dentro dela
        e = suave(puxao)
        corpo = self.leo.copy()
        branco = self.leo_branco.copy()
        branco.set_alpha(int(255 * min(1.0, e * 1.6)))
        corpo.blit(branco, (0, 0))
        w = max(1, int(corpo.get_width() * (1 + 2.2 * e)))
        h = max(1, int(corpo.get_height() * max(0.04, 1 - 0.9 * e)))
        corpo = pygame.transform.scale(corpo, (w, h))
        m = e ** 1.6
        meio = PES[1] - self.leo.get_height() / 2
        cx = PES[0] + (TV.centerx - PES[0]) * m
        cy = meio + (TV.centery - meio) * m
        tela.blit(corpo, corpo.get_rect(center=(int(cx), int(cy))))

    def quadro(self, tela, t, puxao, brilho, z0, u):
        """
        O quarto na tela, pela camera: `puxao` 0 (o Leo de pe) a 1 (dentro da
        TV), `brilho` 0 a 1 (None: a TV apagada), `z0` o zoom no quarto e `u` 0
        (no quarto) a 1 (a TV enche a tela). Devolve onde a TV caiu na tela.
        """
        cena = self.cena
        cena.blit(self.base, (0, 0))
        self._leo(cena, t, puxao)
        if brilho is not None:
            cena.blit(self.brilhos[min(9, int(brilho * 9.99))], (0, 0), special_flags=pygame.BLEND_ADD)
        z, foco = z0, FOCO
        if u > 0:
            s = suave(u)
            z = math.exp(math.log(z0) + (math.log(LARGURA / TV.w) - math.log(z0)) * s)
            foco = (FOCO[0] + (TV.centerx - FOCO[0]) * s, FOCO[1] + (TV.centery - FOCO[1]) * s)
        cw, ch = LARGURA / z, ALTURA / z
        x0 = min(max(foco[0] - cw / 2, 0), LARGURA - cw)
        y0 = min(max(foco[1] - ch / 2, 0), ALTURA - ch)
        if z > 1.001:
            recorte = cena.subsurface((int(x0), int(y0), max(1, int(cw)), max(1, int(ch))))
            pygame.transform.scale(recorte, (LARGURA, ALTURA), tela)
        else:
            tela.blit(cena, (0, 0))
        if u >= 0.999:
            return tela.get_rect()
        return pygame.Rect(round((TV.x - x0) * z), round((TV.y - y0) * z), round(TV.w * z), round(TV.h * z))

    def tv(self, tela, r, imagem, branco=0.0, u=0.0):
        """O que passa na TV (uma tela do jogo em 1280x720), no retangulo `r` da tela."""
        if r.w <= TV.w * 1.05:
            pequena = pygame.transform.smoothscale(imagem, TV.size)
            tela.blit(pygame.transform.scale(pequena, r.size) if r.size != TV.size else pequena, r)
        else:
            tela.blit(pygame.transform.smoothscale(imagem, r.size), r)
        if branco > 0:
            v = pygame.transform.scale(self.veu_tv, r.size)
            v.set_alpha(int(255 * min(1.0, branco)))
            tela.blit(v, r)
        if u < 1:
            linhas = self.linhas if r.size == TV.size else pygame.transform.scale(self.linhas, r.size)
            linhas.set_alpha(int(255 * (1 - u)))
            tela.blit(linhas, r)


def falhas(tela, t, momentos):
    """A imagem falha: por um instante, faixas da tela escorregam para os lados."""
    for t0 in momentos:
        d = t - t0
        if 0 <= d < 0.12:
            rnd = random.Random(int(t * 60))
            forca = 1 - d / 0.12
            for _ in range(6):
                y = rnd.randrange(0, ALTURA - 8)
                h = min(rnd.randrange(6, 40), ALTURA - y)
                faixa = tela.subsurface((0, y, LARGURA, h)).copy()
                tela.blit(faixa, (rnd.randint(-60, 60) * forca, y))


def pensamento(tela, fala, d, sai):
    """O Leo pensando: branco, letra por letra, embaixo dele. `d`: ha quanto tempo
    comecou; `sai`: quanto falta para sumir."""
    if d < 0 or sai <= 0:
        return
    n = min(len(fala), int(d / LETRA) + 1)
    cheio = ui.texto(fala, 32, BRANCO, CONTORNO)
    img = ui.texto(fala[:n], 32, BRANCO, CONTORNO)
    if sai < 0.2:
        img = arte.fantasma(img, max(16, int(255 * sai / 0.2) // 16 * 16))
    tela.blit(img, img.get_rect(midleft=(LARGURA // 2 - cheio.get_width() // 2, Y_FALA)))


class Abertura:
    """Uma tela como as de menus.py (evento, atualizar, desenhar), sem cenario de fundo."""

    def __init__(self, app):
        self.app = app
        self.tempo = 0.0
        self.pulou = False
        self.clicou = False
        self.soou = False
        # a tela inicial que vai assumir no fim: a TV mostra ela parada no
        # instante zero, o mesmo quadro que ela desenha quando entra
        self.menu = menus.TelaMenu(app)
        self.fase = self.menu.fase                      # a cor da transicao (App._cor)
        self.foto = pygame.Surface((LARGURA, ALTURA)).convert()
        self.menu.desenhar(self.foto)
        self.quarto = Quarto("quarto_noite.png", "east.png", self.foto)
        self.veu = pygame.Surface((LARGURA, ALTURA)).convert()
        self.dica = ui.texto("ESPACO PULA", 14, (150, 156, 190), CONTORNO)

    def evento(self, ev):
        if pular(ev) and not self.pulou:
            self.pulou = True
            audio.tocar("clique")
            self.app.ir_para_menu()

    def atualizar(self, dt):
        if self.pulou:
            return
        self.tempo += min(dt, 1.0 / 30.0)     # um quadro atrasado nao pula um pedaco da cena
        t = self.tempo
        if t >= START and not self.clicou:
            self.clicou = True
            audio.tocar("clique")
        if t >= PUXA[0] + 0.1 and not self.soou:
            self.soou = True
            audio.tocar("orbe")
        if t >= FIM:
            # a camera chegou dentro da TV: a tela inicial assume, no mesmo quadro
            self.app.tela = self.menu

    def desenhar(self, tela):
        t = self.tempo
        puxao = fase(t, PUXA)
        u = fase(t, MERGULHO)
        z0 = 1.0 + 0.08 * suave(t / START)
        r = self.quarto.quadro(tela, t, puxao, suave(puxao), z0, u)
        branco = 0.55 * max(0.0, 1 - (t - START) / 0.25) if t >= START else 0.0   # o clique acende a tela
        branco = max(branco, 0.9 * suave(puxao * 1.4) * (1 - suave(u * 1.3)))
        self.quarto.tv(tela, r, self.foto, branco, u)
        falhas(tela, t, (PUXA[0] + 0.3, PUXA[0] + 0.8, PUXA[0] + 1.2))
        pensamento(tela, FALA, t - PENSA, START + 0.2 - t)
        if t > 0.6 and u <= 0:
            tela.blit(self.dica, self.dica.get_rect(topright=(LARGURA - 22, 18)))
        if t < ACENDE:                                  # o quarto sai do escuro
            a = int(255 * (1 - suave(t / ACENDE)))
            if a >= 255:
                tela.fill((0, 0, 0))                    # o blit com alfa 255 e lento no SDL
            else:
                self.veu.fill((0, 0, 0))
                self.veu.set_alpha(a)
                tela.blit(self.veu, (0, 0))
        d = t - PUXA[1]                                 # o clarao de quando o Leo some na TV
        if 0 <= d < 0.3:
            self.veu.fill(BRANCO)
            self.veu.set_alpha(int(150 * (1 - d / 0.3)))
            tela.blit(self.veu, (0, 0))
