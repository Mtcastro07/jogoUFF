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
    Apertar na batida e um pulo, e o tempo apertado decide a altura: um
    TOQUE rapido e um pulo baixo; SEGURAR ate o alto do arco e o pulo
    inteiro. Os dois pousam no mesmo lugar, na batida seguinte, e os dois
    passam por tudo: nenhum obstaculo pede o botao segurado. Segurando alem
    do pouso, o Leo pula de novo a cada pouso. No bosque, a fase que
    ensina, tudo se passa so com toques e as guias mostram onde pular;
    depois dele nao ha guias -- o cenario e a musica dizem a hora. Nas
    ilhas, os portais mudam a velocidade da corrida.

    A fase 1 esta, temporariamente, desenhada como a VERSAO ALPHA do jogo
    (so formas simples, sem animacao): config.ALPHA.

    O mundo acelera junto com a musica: 84 BPM no bosque, 110 nas ilhas e
    150 na cidadela -- o pulo dura sempre uma batida.
    ESC pausa      R recomeca      F11 tela cheia / janela 
    Cada acao exigida pela partitura e julgada pelo tempo do toque:
        PERFEITO!  50 pontos      BOM!  25 pontos      ERROU...  0 pontos
    Errar o tempo so custa pontos. Coracao se perde batendo em alguma coisa:
    num caco ou num bloco (o bloco se quebra). Cair num fosso e o fim na
    hora. Com os tres coracoes perdidos vem o fim de jogo; chegando ao fim da
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
from jogo.transicao import Transicao


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
        self.transicao = Transicao()
        self.transicao.revelar(self._cor())         # o jogo abre saindo da onda

    # ------------------------------------------------------------ navegacao
    # Toda troca de tela passa pela transicao: a tela nova so e CRIADA com a
    # velha ja coberta (carregar uma fase nao aparece como engasgo).
    def _cor(self):
        return self.tela.fase.tema.destaque

    def transitar(self, acao):
        """Cobre a tela, roda `acao()` e revela. Ignorado se ja ha uma em curso."""
        return self.transicao.iniciar(acao, self._cor())

    def _trocar(self, criar):
        if isinstance(self.tela, Partida):
            self.tela.sair()                        # a musica ja some junto com a onda
        def troca():
            self.tela = criar()
        self.transitar(troca)

    def ir_para_menu(self):
        self._trocar(lambda: menus.TelaMenu(self))

    def ir_para_fases(self):
        self._trocar(lambda: menus.TelaFases(self))

    def ir_para_jogo(self, indice):
        self.fase_selecionada = indice
        self._trocar(lambda: Partida(self, fases.carregar(indice)))

    def mostrar_resultado(self, dados):
        tela = menus.TelaResultado if dados["completou"] else menus.TelaGameOver
        self._trocar(lambda: tela(self, dados))

    def mouse(self):
        return self.janela.mouse.get_position()

    def sair(self):
        """O SAIR do menu: a onda cobre a tela e o jogo fecha."""
        self.transitar(self.encerrar)

    def encerrar(self):
        save.salvar()
        pygame.quit()
        sys.exit(0)

    # ------------------------------------------------------------------ laco
    def rodar(self):
        janela = self.janela
        while True:
            dt = min(0.1, self.clock.tick(FPS) / 1000.0)
            transicao = self.transicao
            # enquanto a onda cobre, a tela velha nao ouve nada (nem um
            # segundo clique) e a partida fica parada
            if not transicao.cobrindo:
                for ev in janela.eventos:  # o QUIT ja foi tratado pela PPlay
                    self.tela.evento(ev)
            if not (transicao.cobrindo and isinstance(self.tela, Partida)):
                self.tela.atualizar(dt)
            transicao.atualizar(dt)
            self.tela.desenhar(janela.screen)
            transicao.desenhar(janela.screen)
            janela.update()


if __name__ == "__main__":
    App().rodar()
