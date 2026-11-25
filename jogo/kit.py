import math

import pygame
from PPlay.input_manager import InputManager
from PPlay.uikit import Button, ProgressBar

from . import arte, ui
from .config import BRANCO, CONTORNO, LARG_TELA, PAINEL

VAZIO = (70, 74, 104)


class Botao(Button):
    def __init__(self, texto, x, y, w, h, cor):
        super().__init__(w, h, texto, cor_base=PAINEL, cor_hover=cor)
        self.set_position(int(x), int(y))
        self.cor_texto = BRANCO
        self.foco = 0.0

    def draw(self, tela, ta_focado):
        cor = self.cor_hover
        alvo = 1.0 if ta_focado else 0.0
        self.foco += (alvo - self.foco) * 0.3
        if abs(self.foco - round(self.foco)) < 0.01:
            self.foco = float(round(self.foco))
        k = self.foco
        r = pygame.Rect(self.x, self.y, self.width, self.height).inflate(int(16 * k), int(8 * k))
        if k > 0.5:
            nome, cor_texto = "foco", self.cor_texto
        else:
            nome, cor_texto = "padrao", ui.COR_APAGADA
        ui.desenha_moldura(tela, nome, r.x, r.y, r.w, r.h)
        if k > 0.05:
            alto = int((r.h - 28) * k)
            pygame.draw.rect(tela, cor, (r.x + 16, r.centery - alto // 2, 6, alto))
        ui.escreve(tela, self.texto, 26, r.centerx + int(8 * k), r.centery,
                   cor_texto)
        if k > 0.5:
            ta_indo_pra = int(3 * math.sin(pygame.time.get_ticks() * 0.008))
            for lado in (-1, 1):
                x = r.centerx + lado * (r.w // 2 + 22 + ta_indo_pra)
                y = r.centery
                pygame.draw.polygon(tela, CONTORNO, [(x + lado * 12, y - 13), (x - lado * 5, y),
                                                     (x + lado * 12, y + 13)])
                pygame.draw.polygon(tela, cor, [(x + lado * 9, y - 8), (x - lado, y),
                                                (x + lado * 9, y + 8)])


class Menu:
    def __init__(self, botoes):
        self.botoes = botoes
        self.indice = 0

    def mexe(self, d):
        self.indice = (self.indice + d) % len(self.botoes)

    def ve_teclas(self, mouse, toca_o_som):
        for b in self.botoes:
            b.update()
        if InputManager.action_pressed("baixo"):
            self.mexe(1)
            toca_o_som("navegar")
        elif InputManager.action_pressed("cima"):
            self.mexe(-1)
            toca_o_som("navegar")
        if mouse.mouse_mexeu():
            for i, b in enumerate(self.botoes):
                if b.hovered:
                    self.indice = i
        if mouse.button_down(mouse.LEFT):
            for b in self.botoes:
                if b.is_clicked():
                    return b.texto
        elif InputManager.action_pressed("confirmar"):
            return self.botoes[self.indice].texto
        elif InputManager.action_pressed("voltar"):
            return "ESC"
        return None

    def mostra_na_tela(self, tela):
        for i, b in enumerate(self.botoes):
            b.draw(tela, i == self.indice)


class LinhaDeOpcao(Button):
    def __init__(self, texto, y, chave, maximo, cor):
        super().__init__(760, 64, texto, cor_base=ui.COR_APAGADA, cor_hover=cor)
        self.set_position(LARG_TELA // 2 - 380, y - 32)
        self.cor_texto = BRANCO
        self.chave = chave
        self.maximo = maximo
        self.n_degraus = Pauzinhos(maximo, 16, 22, 23, borda=2)

    def ta_mudado(self, valor, d):
        return max(0, min(self.maximo, valor + d))

    def draw(self, tela, ta_focada, valor, tempo):
        destaque = self.cor_hover
        x, y, w = self.x, self.y + 32, self.width
        if ta_focada:
            nome, cor = "foco", self.cor_texto
        else:
            nome, cor = "padrao", self.cor_base
        ui.desenha_moldura(tela, nome, x, y - 30, w, 60)
        if self.chave is None:
            ui.escreve(tela, self.texto, 26, LARG_TELA // 2, y, cor)
            return
        ui.escreve(tela, self.texto, 22, x + 36, y, cor, "esquerda")
        bx, bw = x + 400, 230
        self.n_degraus.cor_barra = destaque if ta_focada else self.cor_base
        self.n_degraus.set_position(bx + 1, y - 11)
        self.n_degraus.set_value(valor)
        self.n_degraus.draw(tela)
        if ta_focada:
            ta_indo_pra = int(3 * math.sin(tempo * 8.0))
            ui.escreve(tela, "<", 26, bx - 30 - ta_indo_pra, y, destaque)
            ui.escreve(tela, ">", 26, bx + bw + 30 + ta_indo_pra, y, destaque)


class BarraQueEnche(ProgressBar):
    def __init__(self, largura, altura, cor, maximo=100.0):
        super().__init__(largura, altura, cor_barra=cor, cor_fundo=VAZIO)
        self.valor_max = maximo
        self.set_value(0.0)

    def cheio(self):
        return int(self.width * self.valor_atual / self.valor_max)

    def draw(self, tela):
        x, y, w, h = self.x, self.y, self.width, self.height
        pygame.draw.rect(tela, CONTORNO, (x - 2, y - 2, w + 4, h + 4))
        pygame.draw.rect(tela, self.cor_fundo, (x, y, w, h))
        pygame.draw.rect(tela, self.cor_barra, (x, y, self.cheio(), h))


class Pauzinhos(ProgressBar):
    def __init__(self, total, largura, altura, passo, borda=1, cor=BRANCO, brilho=0):
        super().__init__(largura, altura, cor_barra=cor, cor_fundo=VAZIO)
        self.valor_max = total
        self.passo, self.borda, self.brilho = passo, borda, brilho
        self.set_value(0)

    def draw(self, tela):
        w, h, b = self.width, self.height, self.borda
        for i in range(self.valor_max):
            x = self.x + i * self.passo
            pygame.draw.rect(tela, CONTORNO, (x - b, self.y - b, w + 2 * b, h + 2 * b))
            if i < self.valor_atual:
                pygame.draw.rect(tela, self.cor_barra, (x, self.y, w, h))
                pygame.draw.rect(tela, BRANCO, (x, self.y, w, self.brilho))
            else:
                pygame.draw.rect(tela, self.cor_fundo, (x, self.y, w, h))


class BarraDoTopo(BarraQueEnche):
    PONTA = 8 * ui.ESCALA_DA_MOLDURA

    def __init__(self, largura, altura, cor):
        super().__init__(largura, altura, cor, maximo=1.0)
        t = pygame.transform.scale_by(arte.pega_png("ui", "trilho.png"), ui.ESCALA_DA_MOLDURA)
        w, h = t.get_size()
        miolo = t.subsurface((self.PONTA, 0, ui.ESCALA_DA_MOLDURA, h))
        self.pecas = (t.subsurface((0, 0, self.PONTA, h)),
                      pygame.transform.scale(miolo, (largura, h)),
                      t.subsurface((w - self.PONTA, 0, self.PONTA, h)))

    def draw(self, tela):
        x, y, w, h = self.x, self.y, self.width, self.height
        esq, miolo, dir_ = self.pecas
        y0 = y + h // 2 - miolo.get_height() // 2
        tela.blit(esq, (x - self.PONTA, y0))
        tela.blit(miolo, (x, y0))
        tela.blit(dir_, (x + w, y0))
        cheio = self.cheio()
        if cheio:
            pygame.draw.rect(tela, self.cor_barra, (x, y, cheio, h))
            pygame.draw.rect(tela, arte.clareia(self.cor_barra, 0.5), (x, y, cheio, 3))
