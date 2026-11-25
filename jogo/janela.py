import time
from contextlib import contextmanager

import pygame
from PPlay.window import Window

from .comandos import Controlezinho, Mouzinho, TecladoDoJogo
from .config import LARG_TELA, ALT_TELA, FPS

NOME_DO_JOGO = "RHYTHM STRIKER"
DT_MAIOR = 0.1


class Janelona(Window):
    def __new__(cls, *args, **kwargs):
        if Window._instance is None:
            Window._instance = object.__new__(cls)
        return Window._instance

    def __init__(self, tela_cheia=False):
        if hasattr(self, "_already_init"):
            return
        super().__init__(LARG_TELA, ALT_TELA, NOME_DO_JOGO, tela_cheia=tela_cheia)
        self.os_controles = Controlezinho()
        self.keyboard = TecladoDoJogo(self.os_controles)
        self.mouse = Mouzinho()
        self.comeca()

    @classmethod
    def pega_janela(cls):
        return Window._instance or cls()

    @classmethod
    @contextmanager
    def pintando_em(cls, tela):
        janela = cls.pega_janela()
        antes = janela.screen
        if tela is not None:
            janela.screen = Window.screen = tela
        try:
            yield
        finally:
            janela.screen = Window.screen = antes

    @classmethod
    @contextmanager
    def com_esse_tempo(cls, dt):
        janela = cls.pega_janela()
        antes = janela._delta_time
        janela._delta_time = dt
        try:
            yield
        finally:
            janela._delta_time = antes

    def _abrir(self, vsync):
        pronta = pygame.display.get_surface()
        if pronta is not None and not hasattr(self, "real_screen"):
            return pronta
        return super()._abrir(vsync)

    def precisa_limitar(self):
        taxa = self.taxa_do_monitor()
        if self.vsync and taxa:
            if abs(taxa - 60) <= 2:
                return False
            if abs(taxa / 60.0 - round(taxa / 60.0)) * 60 <= 2:
                return True
            return False
        return True

    def comeca(self):
        self.usa_relogio = self.precisa_limitar()
        self.tempo_antes = time.perf_counter()
        self.tempo_do_quadro = 1.0 / FPS
        self.proximo_quadro = self.tempo_antes + self.tempo_do_quadro
        self._delta_time = 0.0
        self.travou = False
        self.quadros_contados, self.tempo_inicial = 0, self.tempo_antes
        self.fps_max = max(60, self.taxa_do_monitor()) * 1.3

    def espera_um_pouco(self):
        quanto_falta = self.proximo_quadro - time.perf_counter()
        if quanto_falta > 0.004:
            time.sleep(quanto_falta - 0.003)
        while time.perf_counter() < self.proximo_quadro:
            pass
        self.proximo_quadro += self.tempo_do_quadro
        if time.perf_counter() > self.proximo_quadro:
            self.proximo_quadro = time.perf_counter() + self.tempo_do_quadro

    def update(self):
        if self.usa_relogio:
            self.espera_um_pouco()
        super().update()
        self.eventos = [self.os_controles.traduz(ev) for ev in self.eventos]
        agora = time.perf_counter()
        self.travou = agora - self.tempo_antes > DT_MAIOR
        self._delta_time = min(DT_MAIOR, agora - self.tempo_antes)
        self.tempo_antes = agora
        if not self.usa_relogio and self.quadros_contados < 120:
            self.quadros_contados += 1
            if self.quadros_contados == 120 and 120 / max(1e-6, agora - self.tempo_inicial) > self.fps_max:
                self.usa_relogio = True
                self.proximo_quadro = agora + self.tempo_do_quadro
