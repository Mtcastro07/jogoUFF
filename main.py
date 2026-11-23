"""
RHYTHM STRIKER - jogo de plataforma ritmico 2D.

Leo foi sugado para dentro da tela e caiu no Rhythm Kingdom, uma dimensao
feita de som onde quem se move fora do compasso vira ruido. Para voltar para
casa ele precisa atravessar CINCO mundos pulando EM CIMA DA BATIDA.

Trabalho desenvolvido sobre a biblioteca Power PPlay 2.0 (IC-UFF).

COMO RODAR
    python3 -m venv .venv
    ./.venv/bin/python -m pip install -r requirements.txt
    ./.venv/bin/python main.py

O jogo inteiro se roda por ESTE arquivo: os modulos em `jogo/` usam imports
relativos e nao podem ser executados sozinhos (no VS Code, use F5).

COMO JOGAR
    O jogo abre com a cena do Leo sendo puxado para dentro da TV (qualquer
    tecla pula a cena). Vencidos os cinco mundos, uma cena final leva o Leo
    de volta para casa, seguida dos creditos.
    A fase abre parada; ESPACO da a largada.

    ESPACO / SETA CIMA / W / clique  ->  a unica acao do jogo
    Apertar na batida e um pulo, e o tempo apertado decide a altura: um
    TOQUE rapido e um pulo baixo; SEGURAR ate o alto do arco e o pulo
    inteiro. Os dois pousam no mesmo lugar, na batida seguinte, e os dois
    passam por quase tudo: nenhum obstaculo pede o botao segurado (so os
    pingentes da geleira pedem o toque rapido). Segurando alem
    do pouso, o Leo pula de novo a cada pouso. No bosque, a fase que
    ensina, tudo se passa so com toques e as guias mostram onde pular;
    depois dele nao ha guias -- o cenario e a musica dizem a hora. Nas
    dunas, os ENXAMES pairam no ar: ali NAO se pula. Nas ilhas, os portais
    mudam a velocidade da corrida. Na geleira, os PINGENTES pendem no alto
    do arco: ali so um TOQUE rapido passa -- segurar o botao bate neles.

    O mundo acelera junto com a musica: 84 BPM no bosque, 96 nas dunas,
    110 nas ilhas, 128 na geleira e 150 na cidadela -- o pulo dura sempre
    uma batida.
    ESC pausa      R recomeca      F11 tela cheia / janela 
    Cada acao exigida pela partitura e julgada pelo tempo do toque:
        PERFEITO!  50 pontos      BOM!  25 pontos      ERROU...  0 pontos
    Errar o tempo so custa pontos. Coracao se perde batendo em alguma coisa:
    num caco ou num bloco (o bloco se quebra). Cair num fosso e o fim na
    hora. Com os tres coracoes perdidos vem o fim de jogo; chegando ao fim da
    musica, a tela de resultado da a nota da fase (S / A / B / C).
"""

import gc
import sys
import time

try:
    import pygame
    from PPlay.window import Window
except ImportError as erro:
    print(f"\n[ERRO] falta uma dependencia: {erro}")
    print("Instale com:  ./.venv/bin/python -m pip install -r requirements.txt")
    print("e rode com:   ./.venv/bin/python main.py\n")
    sys.exit(1)

from jogo import arte, fases, menus
from jogo.abertura import Abertura
from jogo import final
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
        menus.preaquecer()              # tudo o que engasgaria o primeiro quadro, antes dele
        # o que foi carregado ate aqui (fases, imagens, fundos) vive o jogo
        # inteiro: a coleta de lixo do Python para de varrer esses milhares de
        # objetos -- era ela que, de vez em quando, segurava um quadro
        gc.collect()
        gc.freeze()
        audio.iniciar()
        audio.aplicar(save.opcoes)
        # controle: qualquer um ligado vale; os botoes viram as teclas do jogo
        pygame.joystick.init()
        self.controles = {}
        # a abertura: o Leo e puxado para dentro da TV, e a tela inicial assume
        self.tela = Abertura(self)
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

    def ir_para_opcoes(self):
        self._trocar(lambda: menus.TelaOpcoes(self))

    def ir_para_fases(self):
        self._trocar(lambda: menus.TelaFases(self))

    def ir_para_jogo(self, indice):
        self.fase_selecionada = indice

        def criar():
            partida = Partida(self, fases.carregar(indice))
            gc.collect()        # o lixo da partida de antes sai agora, debaixo da onda
            return partida
        self._trocar(criar)

    def mostrar_resultado(self, dados):
        if dados["completou"] and final.deve_tocar(save, dados["fase"]):
            # a vitoria que fecha os cinco mundos: o Leo volta para casa
            self._trocar(lambda: final.Final(self, dados))
            return
        tela = menus.TelaResultado if dados["completou"] else menus.TelaGameOver
        self._trocar(lambda: tela(self, dados))

    # -------------------------------------------------------------- controle
    BOTOES_PULO = (0, 2, 3)        # A, X, Y (no padrao mais comum)
    BOTOES_VOLTA = (1, 6, 7, 9)    # B, select, start

    def controle_segurado(self):
        """Algum botao de pulo de algum controle esta apertado?"""
        try:
            return any(c.get_button(b) for c in self.controles.values()
                       for b in self.BOTOES_PULO if b < c.get_numbuttons())
        except pygame.error:
            return False

    def _traduzir(self, ev):
        """Um evento de controle vira a tecla equivalente (os outros passam como vieram)."""
        tecla = None
        if ev.type == pygame.JOYDEVICEADDED:
            c = pygame.joystick.Joystick(ev.device_index)
            self.controles[c.get_instance_id()] = c
        elif ev.type == pygame.JOYDEVICEREMOVED:
            self.controles.pop(ev.instance_id, None)
        elif ev.type == pygame.JOYBUTTONDOWN:
            if ev.button in self.BOTOES_PULO:
                tecla = pygame.K_SPACE
            elif ev.button in self.BOTOES_VOLTA:
                tecla = pygame.K_ESCAPE
        elif ev.type == pygame.JOYHATMOTION:
            hx, hy = ev.value
            tecla = (pygame.K_UP if hy > 0 else pygame.K_DOWN if hy < 0 else
                     pygame.K_RIGHT if hx > 0 else pygame.K_LEFT if hx < 0 else None)
        if tecla is None:
            return ev
        return pygame.event.Event(pygame.KEYDOWN, key=tecla, mod=0, unicode="")

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
    def _limitar(self):
        """
        O ritmo dos quadros. Com vsync num monitor de 60 Hz (ou 120, 180...), o
        proprio monitor marca os 60 FPS. Num monitor de outra taxa (75, 144...),
        o jogo acompanha o monitor -- travar em 60 ali faria quadros de duracoes
        desiguais. Sem vsync, o relogio segura em 60, com precisao de espera
        ativa (o tick comum acorda com ate 1-2 ms de erro).
        """
        taxa = self.janela.taxa_do_monitor()
        if self.janela.vsync and taxa:
            if abs(taxa - 60) <= 2:
                return None                     # o vsync ja marca os 60
            if abs(taxa / 60.0 - round(taxa / 60.0)) * 60 <= 2:
                return "relogio"                # 120, 180, 240 Hz: 60 cai certinho
            return None                         # 75, 144, 165 Hz: segue o monitor
        return "relogio"

    def _esperar(self, alvo):
        """Espera ate o instante `alvo` (perf_counter): dorme o grosso e gira o fim."""
        falta = alvo - time.perf_counter()
        if falta > 0.004:
            time.sleep(falta - 0.003)       # o sono do sistema pode passar do ponto: folga de 3 ms
        while time.perf_counter() < alvo:
            pass

    def rodar(self):
        janela = self.janela
        limite = self._limitar()
        antes = time.perf_counter()
        # conferencia: ha driver que aceita o vsync e nao espera o monitor. Se os
        # primeiros quadros vierem rapidos demais, o relogio passa a segurar os 60
        conferir, inicio = 0, antes
        maximo = max(60, self.janela.taxa_do_monitor()) * 1.3
        periodo = 1.0 / FPS
        alvo = antes + periodo
        while True:
            # o dt do relogio de alta precisao: o do tick vem em ms inteiros, e
            # quadros de "16" e "17" ms faziam a fisica andar aos solavancos
            agora = time.perf_counter()
            dt = min(0.1, agora - antes)
            antes = agora
            if limite is None:
                conferir += 1
                if conferir == 1:
                    inicio = agora
                elif conferir == 121:
                    if 120 / max(1e-6, agora - inicio) > maximo:
                        limite = "relogio"
                        alvo = agora + periodo
                    conferir = -10 ** 9                 # conferido: nao conta mais
            transicao = self.transicao
            # enquanto a onda cobre, a tela velha nao ouve nada (nem um
            # segundo clique) e a partida fica parada
            if not transicao.cobrindo:
                for ev in janela.eventos:  # o QUIT ja foi tratado pela PPlay
                    self.tela.evento(self._traduzir(ev))
            if not (transicao.cobrindo and isinstance(self.tela, Partida)):
                self.tela.atualizar(dt)
            transicao.atualizar(dt)
            self.tela.desenhar(janela.screen)
            transicao.desenhar(janela.screen)
            if limite == "relogio":
                # o quadro pronto so vai para a tela no seu instante: multiplos
                # exatos de 1/60 s, por mais que o desenho tenha custado
                self._esperar(alvo)
                alvo += periodo
                if time.perf_counter() > alvo:
                    alvo = time.perf_counter() + periodo   # atrasou: recomeca a conta
            janela.update()


if __name__ == "__main__":
    App().rodar()
