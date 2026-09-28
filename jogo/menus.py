"""
As telas fora da partida: menu principal, selecao de fase, resultado e fim
de jogo. Todas desenham o cenario da fase escolhida rolando devagar ao fundo.
Sem animacoes de menu (o GDD): a troca de uma tela para outra e que e suave
(jogo/transicao.py).
"""

import math

import pygame

from . import arte, efeitos, fases, ui
from .audio import audio
from .cenario import Cenario, ceu
from .config import (LARGURA, ALTURA, BRANCO, CINZA, AMARELO, VERDE, VERMELHO,
                     AZUL, COR_DIFICULDADE, COR_NOTA, CONTORNO)


class Tela:
    """Base: cenario rolando ao fundo e, opcionalmente, um menu de botoes."""

    def __init__(self, app, fase=None, botoes=()):
        self.app = app
        self.fase = fase or fases.carregar(app.fase_selecionada)
        self.cenario = Cenario(self.fase.tema)
        self.ar = efeitos.Ar(self.fase.tema)
        self.menu = ui.Menu(list(botoes)) if botoes else None
        self.tempo = 0.0

    def evento(self, ev):
        if self.menu is None:
            return
        escolha = None
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_DOWN, pygame.K_s):
                self.menu.mover(1)
                audio.tocar("navegar")
            elif ev.key in (pygame.K_UP, pygame.K_w):
                self.menu.mover(-1)
                audio.tocar("navegar")
            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                escolha = self.menu.atual
            elif ev.key == pygame.K_ESCAPE:
                escolha = "ESC"
        elif ev.type == pygame.MOUSEMOTION:
            self.menu.passar_mouse(self.app.mouse())
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            escolha = self.menu.clique(self.app.mouse())
        if escolha:
            audio.tocar("clique")
            self.escolher(escolha)

    def escolher(self, rotulo):
        pass

    def atualizar(self, dt):
        self.tempo += dt

    def _fundo(self, tela, cenario, ar):
        pulso = max(0.0, 1.0 - (self.tempo * 2.0 % 1.0) * 3.0)
        cenario.desenhar(tela, self.tempo * 40.0, 0.0, self.tempo, pulso)
        ar.desenhar(tela, self.tempo * 40.0, 0.0, self.tempo)

    def desenhar(self, tela):
        self._fundo(tela, self.cenario, self.ar)
        ui.escurecer_tela(tela, 130)
        if self.menu is not None:
            self.menu.desenhar(tela)

    def titulo(self, tela, s, tam, y, cor):
        """Um titulo centrado na altura `y`, com o contorno do HUD: o astro do fundo
        passa por tras dos titulos, e sem contorno uma letra sumia em cima dele."""
        ui.desenhar_texto(tela, s, tam, LARGURA // 2, y, cor, contorno=CONTORNO)


# ------------------------------------------------------------------- menu
class TelaMenu(Tela):
    def __init__(self, app):
        x = LARGURA // 2 - 200
        super().__init__(app, botoes=[ui.Botao("JOGAR", x, 400, 400, 64, VERDE),
                                      ui.Botao("SAIR", x, 490, 400, 64, VERMELHO)])

    def escolher(self, rotulo):
        if rotulo == "JOGAR":
            self.app.ir_para_fases()
        else:
            self.app.sair()

    def desenhar(self, tela):
        super().desenhar(tela)
        y = 220 + math.sin(self.tempo * 2.0) * 6
        logo = ui.imagem("logo.png", 3)
        if logo is not None:
            tela.blit(logo, logo.get_rect(center=(LARGURA // 2, int(y) - 22)))
        else:
            ui.desenhar_texto(tela, "RHYTHM STRIKER", 72, LARGURA // 2, y, self.fase.tema.destaque)


# -------------------------------------------------------- selecao de fase
class TelaFases(Tela):
    LARG, ALT, VAO = 360, 420, 40

    TROCA_FUNDO = 0.35        # segundos do cenario de uma fase se desfazendo no da outra

    def __init__(self, app):
        super().__init__(app)
        self.lista = fases.todas()
        self.indice = app.fase_selecionada
        self.foco = [1.0 if i == self.indice else 0.0 for i in range(len(self.lista))]
        self.saindo = None        # (foto do fundo de antes da troca, instante da troca)
        # a carta embaixo do mouse. So ENTRAR numa carta a escolhe: o mouse
        # tremendo dentro dela nao desfaz o que as setas escolheram, e a carta
        # onde ele ja estava quando a tela abriu (o JOGAR do menu fica em cima
        # da do meio) nao se escolhe sozinha
        self.sob_mouse = self._carta_em(app.mouse())

    def _rect(self, i):
        n = len(self.lista)
        x0 = (LARGURA - n * self.LARG - (n - 1) * self.VAO) // 2
        return pygame.Rect(x0 + i * (self.LARG + self.VAO), 190, self.LARG, self.ALT)

    def _carta_em(self, pos):
        """O indice da carta embaixo de `pos`, ou None."""
        for i in range(len(self.lista)):
            if self._rect(i).collidepoint(pos):
                return i
        return None

    def _selecionar(self, i):
        self.indice = self.app.fase_selecionada = i
        # o fundo como esta na tela -- ate no meio de outra troca -- vira uma
        # foto que se desfaz por cima do mundo novo: passando o mouse pelas
        # cartas, uma troca atras da outra, nenhum mundo some de repente
        a, b = _camadas_opacas()
        foto = b if self.saindo is not None and self.saindo[0] is a else a
        self._fundo(foto, self.cenario, self.ar)
        self._desfazer(foto)
        self.saindo = (foto, self.tempo)
        self.cenario = Cenario(self.lista[i].tema)
        self.ar = efeitos.Ar(self.lista[i].tema)
        audio.tocar("navegar")

    def _desfazer(self, tela):
        """Por cima do fundo, a foto do de antes da troca, cada vez mais apagada."""
        if self.saindo is None:
            return
        foto, t0 = self.saindo
        k = (self.tempo - t0) / self.TROCA_FUNDO
        if k >= 1.0:
            self.saindo = None
            return
        foto.set_alpha(int(255 * (1.0 - ui.suave(k))))
        tela.blit(foto, (0, 0))

    def evento(self, ev):
        app = self.app
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_RIGHT, pygame.K_d):
                self._selecionar((self.indice + 1) % len(self.lista))
            elif ev.key in (pygame.K_LEFT, pygame.K_a):
                self._selecionar((self.indice - 1) % len(self.lista))
            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                audio.tocar("clique")
                app.ir_para_jogo(self.indice)
            elif ev.key == pygame.K_ESCAPE:
                audio.tocar("clique")
                app.ir_para_menu()
        elif ev.type == pygame.MOUSEMOTION:
            # passar o mouse por cima de uma carta a escolhe, com a mesma troca das setas
            i = self._carta_em(app.mouse())
            if i != self.sob_mouse:
                self.sob_mouse = i
                if i is not None and i != self.indice:
                    self._selecionar(i)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            i = self._carta_em(app.mouse())
            if i == self.indice:
                audio.tocar("clique")
                app.ir_para_jogo(i)
            elif i is not None:
                self._selecionar(i)

    def desenhar(self, tela):
        self._fundo(tela, self.cenario, self.ar)
        self._desfazer(tela)
        ui.escurecer_tela(tela, 130)
        self.titulo(tela, "ESCOLHA A FASE", 48, 100, BRANCO)
        self.titulo(tela, "SETAS ESCOLHEM  -  ENTER JOGA  -  ESC VOLTA", 16, ALTURA - 50, CINZA)
        for i, f in enumerate(self.lista):
            sel = i == self.indice
            self.foco[i] += ((1.0 if sel else 0.0) - self.foco[i]) * 0.25
            self._carta(tela, self._rect(i), f, sel, self.foco[i])

    def _carta(self, tela, r, f, sel, foco):
        cor = COR_DIFICULDADE[f.dificuldade]
        # a escolhida cresce aos poucos (e a que perdeu o foco encolhe)
        r = r.inflate(int(20 * foco), int(20 * foco))
        # cada carta na moldura do seu mundo; a escolhida cresce e fica opaca
        if not ui.moldura(tela, f.cancao, r.x, r.y, r.w, r.h, 255 if sel else 200):
            ui.painel(tela, r.x, r.y, r.w, r.h, borda=cor if sel else CINZA, alpha=235 if sel else 200)
        # uma amostra do mundo: o ceu do tema com o chao e um caco
        amostra = pygame.Rect(r.x + 20, r.y + 20, r.w - 40, 120)
        tela.blit(pygame.transform.scale(ceu(f.tema), amostra.size), amostra.topleft)
        pygame.draw.rect(tela, f.tema.chao, (amostra.x, amostra.bottom - 30, amostra.w, 30))
        pygame.draw.rect(tela, f.tema.chao_topo, (amostra.x, amostra.bottom - 30, amostra.w, 5))
        emblema = arte.png("ui", f"emblema_{f.cancao}.png")
        if emblema is not None:
            tela.blit(emblema, emblema.get_rect(center=(amostra.centerx + 60, amostra.centery)))
        else:
            tela.blit(arte.caco(1, f.tema.perigo), (amostra.centerx + 50, amostra.bottom - 78))
        arte.desenhar_heroi(tela, "parado", self.tempo * 8, amostra.x + 70, amostra.bottom - 30)
        pygame.draw.rect(tela, cor, amostra, 2)

        cx = r.centerx
        ui.desenhar_texto(tela, f.nome, 22, cx, r.y + 172, BRANCO)
        ui.desenhar_texto(tela, f.dificuldade, 18, cx, r.y + 204, cor)
        rec = self.app.save.recorde(f.ident)
        nota = rec["nota"]
        medalha = ui.imagem(f"nota_{nota.lower()}.png") if nota != "-" else None
        if medalha is not None:
            tela.blit(medalha, medalha.get_rect(center=(cx, r.y + 264)))
        else:   # ainda sem nota: o "?" no quadradinho
            if not ui.moldura(tela, "padrao", cx - 32, r.y + 232, 64, 64):
                ui.painel(tela, cx - 32, r.y + 232, 64, 64, borda=COR_NOTA[nota])
            ui.desenhar_texto(tela, "?" if nota == "-" else nota, 36, cx, r.y + 264, COR_NOTA[nota])
        ui.desenhar_texto(tela, f"MELHOR: {rec['melhor']:.0f}%  -  {rec['pontos']} PTS", 16,
                          cx, r.y + 320, CINZA)
        ui.desenhar_texto_ajustado(tela, f.trilha.titulo, 18, cx, r.y + 360, r.w - 30, AMARELO)
        ui.desenhar_texto_ajustado(tela, f.trilha.artista, 16, cx, r.y + 388, r.w - 30, CINZA)


_opacas = []


def _camadas_opacas():
    """Duas superficies do tamanho da tela (sem canal alfa), reaproveitadas."""
    if not _opacas:
        _opacas.extend(pygame.Surface((LARGURA, ALTURA)).convert() for _ in range(2))
    return _opacas


# -------------------------------------------------------------- resultado
class TelaResultado(Tela):
    def __init__(self, app, dados):
        x = LARGURA // 2 - 200
        super().__init__(app, dados["fase"], [
            ui.Botao("JOGAR DE NOVO", x, 520, 400, 48, AZUL),
            ui.Botao("PROXIMA FASE", x, 578, 400, 48, VERDE),
            ui.Botao("MENU DE FASES", x, 636, 400, 48, AMARELO)])
        self.dados = dados
        if dados["completou"]:
            self.menu.indice = 1

    def escolher(self, rotulo):
        app, f = self.app, self.fase
        if rotulo == "JOGAR DE NOVO":
            app.ir_para_jogo(f.ident)
        elif rotulo == "PROXIMA FASE":
            app.ir_para_jogo((f.ident + 1) % len(fases.todas()))
        else:
            app.ir_para_fases()

    def desenhar(self, tela):
        super().desenhar(tela)
        d = self.dados
        cor = VERDE if d["completou"] else AMARELO
        self.titulo(tela, "FASE COMPLETA" if d["completou"] else "RESULTADO", 52, 56, cor)
        self.titulo(tela, self.fase.nome, 22, 102, CINZA)

        x, y, w, h = (LARGURA - 900) // 2, 136, 900, 360
        if not ui.moldura(tela, self.fase.cancao, x, y, w, h):
            ui.painel(tela, x, y, w, h, borda=cor)
        # esquerda: a nota e a precisao que a produziu
        nota = d["nota"]
        medalha = ui.imagem(f"nota_{nota.lower()}.png", 2)
        if medalha is not None:
            tela.blit(medalha, medalha.get_rect(center=(x + 190, y + 140)))
        else:
            if not ui.moldura(tela, "padrao", x + 110, y + 60, 160, 160):
                ui.painel(tela, x + 110, y + 60, 160, 160, borda=COR_NOTA[nota])
            ui.desenhar_texto(tela, nota, 96, x + 190, y + 140, COR_NOTA[nota])
        ui.desenhar_texto(tela, f"{d['precisao'] * 100:.1f}%", 36, x + 190, y + 262, BRANCO)
        ui.desenhar_texto(tela, "DE PRECISAO", 16, x + 190, y + 300, CINZA)
        # direita: pontuacao e contagens
        mostra = int(d["pontos"] * min(1.0, self.tempo / 0.8))
        ui.desenhar_texto(tela, "PONTUACAO", 18, x + 620, y + 50, CINZA)
        ui.desenhar_texto(tela, str(mostra), 64, x + 620, y + 100, BRANCO)
        if d["recorde"]:
            ui.desenhar_texto(tela, "NOVO RECORDE!", 20, x + 620, y + 150, AMARELO)
        linhas = (("PERFEITO", d["perfeitos"], VERDE), ("BOM", d["bons"], AMARELO),
                  ("ERROU", d["erros"], VERMELHO), ("MAIOR SEQUENCIA", d["combo"], BRANCO))
        for i, (rotulo, valor, c) in enumerate(linhas):
            yy = y + 200 + i * 34
            ui.desenhar_texto(tela, rotulo, 18, x + 440, yy, CINZA, "esquerda")
            ui.desenhar_texto(tela, str(valor), 22, x + 820, yy, c, "direita")
        ui.desenhar_texto_ajustado(tela, self.fase.trilha.creditos, 16, LARGURA // 2,
                                   y + h - 22, w - 40, CINZA)


# -------------------------------------------------------------- game over
class TelaGameOver(Tela):
    def __init__(self, app, dados):
        x = LARGURA // 2 - 200
        super().__init__(app, dados["fase"], [
            ui.Botao("TENTAR DE NOVO", x, 430, 400, 56, AZUL),
            ui.Botao("MENU DE FASES", x, 500, 400, 56, AMARELO),
            ui.Botao("MENU PRINCIPAL", x, 570, 400, 56, VERMELHO)])
        self.dados = dados

    def escolher(self, rotulo):
        app = self.app
        if rotulo == "TENTAR DE NOVO":
            app.ir_para_jogo(self.fase.ident)
        elif rotulo == "MENU DE FASES":
            app.ir_para_fases()
        else:
            app.ir_para_menu()

    def desenhar(self, tela):
        super().desenhar(tela)
        d = self.dados
        tremor = math.sin(self.tempo * 30) * max(0.0, 1.0 - self.tempo * 2) * 8
        ui.desenhar_texto(tela, "FIM DE JOGO", 80, LARGURA // 2 + tremor, 170, VERMELHO,
                          contorno=CONTORNO)
        x, y, w = (LARGURA - 800) // 2, 260, 800
        if not ui.moldura(tela, self.fase.cancao, x, y, w, 120):
            ui.painel(tela, x, y, w, 120, borda=VERMELHO)
        campos = (("FASE", self.fase.nome), ("PROGRESSO", f"{d['progresso']:.0f}%"),
                  ("PONTUACAO", str(d["pontos"])))
        for i, (rotulo, valor) in enumerate(campos):
            cx = x + w * (0.2 + i * 0.3)
            ui.desenhar_texto(tela, rotulo, 16, cx, y + 40, CINZA)
            ui.desenhar_texto(tela, valor, 22, cx, y + 80, BRANCO)
