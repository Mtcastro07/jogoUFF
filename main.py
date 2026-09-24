"""
RHYTHM STRIKER - jogo de plataforma ritmico 2D.

Leo foi sugado para dentro da tela e caiu no Rhythm Kingdom, uma dimensao
feita de som onde quem se move fora do compasso vira ruido. Para voltar para
casa ele precisa atravessar TRES mundos pulando EM CIMA DA BATIDA.

Trabalho desenvolvido sobre a biblioteca Power PPlay 2.0 (IC-UFF).

COMO RODAR
    python3 -m venv .venv
    ./.venv/bin/python -m pip install -r requirements.txt
    ./.venv/bin/python main.py

O jogo inteiro se roda por ESTE arquivo: os modulos em `jogo/` usam imports
relativos e nao podem ser executados sozinhos (no VS Code, use F5).

COMO JOGAR
    A fase abre parada; ESPACO da a largada.

    ESPACO / SETA CIMA / W / clique  ->  a unica acao do jogo
    Um TOQUE curto na batida e um pulo. O botao SEGURADO faz nascer a ponte
    de eco sobre os abismos: ela so e solida enquanto voce sustenta a nota.
    ESC pausa      R recomeca      F11 tela cheia / janela

    Cada acao exigida pela partitura e julgada pelo tempo do toque:
        PERFEITO!  50 pontos      BOM!  25 pontos      ERROU...  -1 coracao
    Com os tres coracoes perdidos vem o fim de jogo; chegando ao fim da
    musica, a tela de resultado da a nota da fase (S / A / B / C).
"""

import sys

try:
    import pygame
    from PPlay.window import Window
except ImportError as erro:
    print(f"\n[ERRO] falta uma dependencia: {erro}")
    print("Instale com:  ./.venv/bin/python -m pip install -r requirements.txt")
    print("e rode com:   ./.venv/bin/python main.py\n")
    sys.exit(1)

from jogo import arte, fases, menus
from jogo.audio import audio
from jogo.config import LARGURA, ALTURA, FPS, TELA_CHEIA
from jogo.partida import Partida
from jogo.save import save


class App:
    """Janela, laco principal e a troca de telas."""

    def __init__(self):
        self.janela = Window(LARGURA, ALTURA, "RHYTHM STRIKER", tela_cheia=TELA_CHEIA)
        self.janela.close = self.encerrar      # o X da janela salva antes de sair
        self.teclado = self.janela.keyboard
        self.clock = pygame.time.Clock()
        self.save = save
        self.fase_selecionada = 0
        arte.carregar()
        audio.iniciar()
        self.tela = menus.TelaMenu(self)

    # ------------------------------------------------------------ navegacao
    def _trocar(self, nova):
        if isinstance(self.tela, Partida):
            self.tela.sair()
        self.tela = nova

    def ir_para_menu(self):
        self._trocar(menus.TelaMenu(self))

    def ir_para_fases(self):
        self._trocar(menus.TelaFases(self))

    def ir_para_jogo(self, indice):
        self.fase_selecionada = indice
        self._trocar(Partida(self, fases.carregar(indice)))

    def mostrar_resultado(self, dados):
        if dados["completou"]:
            self._trocar(menus.TelaResultado(self, dados))
        else:
            self._trocar(menus.TelaGameOver(self, dados))

    def mouse(self):
        return self.janela.mouse.get_position()

    def encerrar(self):
        save.salvar()
        pygame.quit()
        sys.exit(0)

    # ------------------------------------------------------------------ laco
    def rodar(self):
        janela = self.janela
        while True:
            dt = min(0.1, self.clock.tick(FPS) / 1000.0)
            for ev in janela.eventos:      # o QUIT ja foi tratado pela PPlay
                self.tela.evento(ev)
            self.tela.atualizar(dt)
            self.tela.desenhar(janela.screen)
            janela.update()


if __name__ == "__main__":
    App().rodar()
