import math
import random

import pygame

from . import arte, menus, ui
from .audio import audio
from .cena import TelaQualquer, troca_tela
from .config import LARG_TELA, ALT_TELA, BRANCO, CONTORNO
from .imagem import Desenho
from .impacto import Impacto
from .tempo import Agenda
from .ui import suaviza

TV = pygame.Rect(232 * 4, 88 * 4, 57 * 4, 32 * 4)
PES = (176 * 4, 162 * 4)
FOCO = ((PES[0] + TV.centerx) / 2, 400)
LETRA = 0.05
Y_FALA = 682

ACENDE = 1.0
PENSA = 1.3
START = 3.9
PUXA = (4.2, 5.6)
MERGULHO = (5.5, 6.9)
FIM = MERGULHO[1]
FALA = "SÓ MAIS UMA FASE..."


def fase(t, faixa):
    return max(0.0, min(1.0, (t - faixa[0]) / (faixa[1] - faixa[0])))


def acabou_de_pular(cena):
    return cena.teclado.qualquer_tecla() or cena.mouse.button_down(cena.mouse.LEFT)


def dica_de_tecla():
    aviso = Desenho(ui.texto("ESPACO PULA", 14, (150, 156, 190), CONTORNO))
    aviso.poe_na_direita(LARG_TELA - 22, 18)
    return aviso


class QuartoDoLeo:
    def __init__(self, fundo, imagem_do_leo, tela_da_tv):
        base = arte.pega_png("trailer", fundo)
        self.base = Desenho(pygame.transform.scale(base, (LARG_TELA, ALT_TELA)).convert())
        self.cena = pygame.Surface((LARG_TELA, ALT_TELA)).convert()
        mascara = pygame.transform.scale(arte.pega_png("trailer", "brilho_tv.png"), (LARG_TELA, ALT_TELA)).convert()
        cor = pygame.transform.average_color(pygame.transform.smoothscale(tela_da_tv, TV.size))[:3]
        self.bolinhas = []
        for i in range(10):
            k = 0.55 + 1.2 * i / 9
            tom = [min(255, int((40 + c * 0.8) * k)) for c in cor]
            g = mascara.copy()
            g.fill(tom, special_flags=pygame.BLEND_MULT)
            self.bolinhas.append(g)
        self.linhas = pygame.Surface(TV.size, pygame.SRCALPHA)
        for y in range(0, TV.h, 2):
            self.linhas.fill((0, 0, 0, 70), (0, y, TV.w, 1))
        self.leo = pygame.transform.scale_by(arte.pega_png("personagens", imagem_do_leo), 4)
        self.em_pe = Desenho(self.leo)
        self.leo_todo_branco = self.leo.copy()
        self.leo_todo_branco.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        self.telinha_da_tv = pygame.Surface(TV.size).convert()
        self.telinha_da_tv.fill(BRANCO)

    def desenha_leo(self, tela, t, puxao):
        if puxao <= 0:
            respira = 0
            if math.sin(t * 2.6) > 0.55:
                respira = 4
            self.em_pe.set_position(PES[0] - self.em_pe.width // 2, PES[1] - self.em_pe.height + respira)
            self.em_pe.draw(tela)
            return
        if puxao >= 1:
            return
        e = suaviza(puxao)
        corpo = self.leo.copy()
        branco = self.leo_todo_branco.copy()
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

    def pega_quadro(self, tela, t, puxao, brilho, z0, u):
        cena = self.cena
        self.base.draw(cena)
        self.desenha_leo(cena, t, puxao)
        if brilho is not None:
            cena.blit(self.bolinhas[min(9, int(brilho * 9.99))], (0, 0), special_flags=pygame.BLEND_ADD)
        z, foco = z0, FOCO
        if u > 0:
            s = suaviza(u)
            z = math.exp(math.log(z0) + (math.log(LARG_TELA / TV.w) - math.log(z0)) * s)
            foco = (FOCO[0] + (TV.centerx - FOCO[0]) * s, FOCO[1] + (TV.centery - FOCO[1]) * s)
        cw, ch = LARG_TELA / z, ALT_TELA / z
        x0 = min(max(foco[0] - cw / 2, 0), LARG_TELA - cw)
        y0 = min(max(foco[1] - ch / 2, 0), ALT_TELA - ch)
        if z > 1.001:
            recorte = cena.subsurface((int(x0), int(y0), max(1, int(cw)), max(1, int(ch))))
            pygame.transform.scale(recorte, (LARG_TELA, ALT_TELA), tela)
        else:
            tela.blit(cena, (0, 0))
        if u >= 0.999:
            return tela.get_rect()
        return pygame.Rect(round((TV.x - x0) * z), round((TV.y - y0) * z), round(TV.w * z), round(TV.h * z))

    def tv(self, tela, r, imagem, branco=0.0, u=0.0):
        if r.w <= TV.w * 1.05:
            pequena = pygame.transform.smoothscale(imagem, TV.size)
            tela.blit(pygame.transform.scale(pequena, r.size), r)
        else:
            tela.blit(pygame.transform.smoothscale(imagem, r.size), r)
        if branco > 0:
            v = pygame.transform.scale(self.telinha_da_tv, r.size)
            v.set_alpha(int(255 * min(1.0, branco)))
            tela.blit(v, r)
        if u < 1:
            linhas = pygame.transform.scale(self.linhas, r.size)
            linhas.set_alpha(int(255 * (1 - u)))
            tela.blit(linhas, r)


def falhas(tela, t, momentos):
    for t0 in momentos:
        d = t - t0
        if 0 <= d < 0.12:
            dado = random.Random(int(t * 60))
            forca = 1 - d / 0.12
            for _ in range(6):
                y = dado.randrange(0, ALT_TELA - 8)
                h = min(dado.randrange(6, 40), ALT_TELA - y)
                faixa = tela.subsurface((0, y, LARG_TELA, h)).copy()
                tela.blit(faixa, (dado.randint(-60, 60) * forca, y))


def balao_de_pensamento(tela, fala, d, sai):
    if d < 0 or sai <= 0:
        return
    n = min(len(fala), int(d / LETRA) + 1)
    cheio = ui.texto(fala, 32, BRANCO, CONTORNO)
    img = ui.texto(fala[:n], 32, BRANCO, CONTORNO)
    if sai < 0.2:
        img = arte.fantasma(img, max(16, int(255 * sai / 0.2) // 16 * 16))
    tela.blit(img, img.get_rect(midleft=(LARG_TELA // 2 - cheio.get_width() // 2, Y_FALA)))


class Comecinho(TelaQualquer):
    def __init__(self, joguinho):
        super().__init__(joguinho)
        self.tempo = 0.0
        self.acabou_de_pular = False
        self.despertador = Agenda.nova()
        self.despertador.after(START, self.toca_som, "clique")
        self.despertador.after(PUXA[0] + 0.1, self.toca_som, "orbe")
        self.impacto = Impacto.novo()
        self.despertador.after(PUXA[1], self.impacto.flash, BRANCO, 0.3, PUXA[1])
        self.despertador.after(FIM, self.chegando)
        self.menu = menus.TelaInicial(joguinho)
        self.fase = self.menu.fase
        self.foto_da_tela = pygame.Surface((LARG_TELA, ALT_TELA)).convert()
        self.menu.mostra_na_tela(self.foto_da_tela)
        self.quarto = QuartoDoLeo("quarto_noite.png", "east.png", self.foto_da_tela)
        self.veu = pygame.Surface((LARG_TELA, ALT_TELA)).convert()
        self.dica = dica_de_tecla()

    def ve_teclas(self):
        if acabou_de_pular(self) and not self.acabou_de_pular:
            self.acabou_de_pular = True
            audio.toca("clique")
            self.joguinho.vai_pro_menu()

    def atualiza(self, dt):
        if self.acabou_de_pular:
            return
        self.tempo += min(dt, 1.0 / 30.0)
        self.despertador.vai_ate(self.tempo)

    def toca_som(self, nome):
        audio.toca(nome)

    def chegando(self):
        troca_tela(self.menu)

    def mostra_na_tela(self, tela):
        t = self.tempo
        puxao = fase(t, PUXA)
        u = fase(t, MERGULHO)
        z0 = 1.0 + 0.08 * suaviza(t / START)
        r = self.quarto.pega_quadro(tela, t, puxao, suaviza(puxao), z0, u)
        branco = 0.0
        if t >= START:
            branco = 0.55 * max(0.0, 1 - (t - START) / 0.25)
        branco = max(branco, 0.9 * suaviza(puxao * 1.4) * (1 - suaviza(u * 1.3)))
        self.quarto.tv(tela, r, self.foto_da_tela, branco, u)
        falhas(tela, t, (PUXA[0] + 0.3, PUXA[0] + 0.8, PUXA[0] + 1.2))
        balao_de_pensamento(tela, FALA, t - PENSA, START + 0.2 - t)
        if t > 0.6 and u <= 0:
            self.dica.draw(tela)
        if t < ACENDE:
            self.veu.fill((0, 0, 0))
            self.veu.set_alpha(int(255 * (1 - suaviza(t / ACENDE))))
            tela.blit(self.veu, (0, 0))
        self.impacto.draw_flash(tela, self.veu, t, 150)
