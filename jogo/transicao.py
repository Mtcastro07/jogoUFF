import pygame

from .config import LARG_TELA, ALT_TELA, FUNDO
from .tempo import Curvas
from .ui import suaviza

COBRIR, REVELAR = 0.28, 0.35

PARADA, COBRINDO, REVELANDO = 0, 1, 2


class Cortina:
    def __init__(self):
        self.estado = PARADA
        self.t = 0.0
        self.animacoes = Curvas.nova()
        self.o_que_faz = None
        self.veu = pygame.Surface((LARG_TELA, ALT_TELA))
        self.veu.fill(FUNDO)

    @property
    def ta_cobrindo(self):
        return self.estado == COBRINDO

    def liga(self, o_que_faz):
        if self.estado == COBRINDO:
            return
        t = 0.0
        if self.estado == REVELANDO:
            t = 1.0 - self.t
        self.o_que_faz = o_que_faz
        self.muda(COBRINDO, COBRIR, t)

    def muda(self, estado, duracao, t=0.0):
        self.estado, self.t = estado, 0.0
        self.animacoes.limpar()
        self.animacoes.to(self, "t", 1.0, duracao, progresso=t)
        self.t = t

    def revela(self):
        self.muda(REVELANDO, REVELAR)

    def atualiza(self, dt):
        if self.estado == COBRINDO:
            self.animacoes.update(dt)
            if self.t >= 1.0:
                self.o_que_faz()
                self.muda(REVELANDO, REVELAR)
        elif self.estado == REVELANDO:
            self.animacoes.update(min(dt, 1.0 / 30.0))
            if self.t >= 1.0:
                self.estado = PARADA

    def mostra_na_tela(self, tela):
        if self.estado == PARADA:
            return
        k = suaviza(self.t)
        if self.estado == REVELANDO:
            k = 1.0 - k
        if k >= 1.0:
            tela.fill(FUNDO)
        elif k > 0.0:
            self.veu.set_alpha(int(255 * k))
            tela.blit(self.veu, (0, 0))
