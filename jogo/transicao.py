"""
Transicao entre telas: a tela escurece, troca e clareia de novo.

    COBRINDO   a tela velha escurece ate o preto (e fica parada)
    (troca)    `acao()` roda com a tela toda preta -- carregar uma fase
               pesada aqui nao aparece como engasgo
    REVELANDO  a tela nova clareia a partir do preto
"""

import pygame

from .config import LARGURA, ALTURA, FUNDO

COBRIR, REVELAR = 0.28, 0.35    # segundos de cada metade

PARADA, COBRINDO, REVELANDO = 0, 1, 2


def _suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


class Transicao:
    def __init__(self):
        self.estado = PARADA
        self.t = 0.0
        self.acao = None
        self.veu = pygame.Surface((LARGURA, ALTURA))
        self.veu.fill(FUNDO)

    @property
    def ativa(self):
        return self.estado != PARADA

    @property
    def cobrindo(self):
        return self.estado == COBRINDO

    def iniciar(self, acao, cor=None):
        """Escurece, roda `acao()` e clareia. False se ja ha uma em curso."""
        if self.ativa:
            return False
        self.estado, self.t, self.acao = COBRINDO, 0.0, acao
        return True

    def revelar(self, cor=None):
        """Comeca no preto e so clareia (a abertura do jogo)."""
        self.estado, self.t, self.acao = REVELANDO, 0.0, None

    def atualizar(self, dt):
        if self.estado == COBRINDO:
            self.t += dt / COBRIR
            if self.t >= 1.0:
                acao, self.acao = self.acao, None
                if acao is not None:
                    acao()
                # o quadro da troca pode ter demorado (carregar a fase): o
                # clarear comeca do zero no proximo quadro, sem pular
                self.estado, self.t = REVELANDO, 0.0
        elif self.estado == REVELANDO:
            self.t += min(dt, 1.0 / 30.0) / REVELAR
            if self.t >= 1.0:
                self.estado = PARADA

    def desenhar(self, tela):
        if self.estado == PARADA:
            return
        k = _suave(self.t) if self.estado == COBRINDO else 1.0 - _suave(self.t)
        if k >= 1.0:
            tela.fill(FUNDO)
        elif k > 0.0:
            self.veu.set_alpha(int(255 * k))
            tela.blit(self.veu, (0, 0))
