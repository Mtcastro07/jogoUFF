"""
A partida: entrada, laco de jogo, julgamento, HUD, pausa e fim de fase.

A fisica roda em passos fixos (`simulacao.passo`) e o julgamento ritmico em
`ritmo.Ritmo`. Esta classe liga os dois ao teclado, ao som e a tela.

A fase abre parada, com Leo de pe na largada, e so comeca (musica e fisica
juntas) quando o jogador aperta ESPACO. Esse toque nao conta como pulo. Nao
ha aviso na tela: o jogador comeca quando quiser.

    ESPACO / SETA CIMA / W / clique   ->  pulo: quanto mais tempo segurado,
                                           mais alto (ate o alto do arco);
                                           segurado alem do pouso, ele pula
                                           de novo
    ESC                                ->  pausa (ao continuar, uma contagem
                                           na batida antes de a musica voltar)
    R                                  ->  recomeca

Enquanto a fase espera, o nome dela e a musica aparecem no alto da tela; o
letreiro some aos poucos quando a musica entra.
"""

import math

import pygame

from . import alpha, arte, efeitos, mundo, ui
from .audio import audio
from .cenario import Cenario
from .config import (LARGURA, ALTURA, VIDAS, PASSO_FISICA, BRANCO, CINZA,
                     AMARELO, VERDE, VERMELHO, COR_JULGAMENTO, COR_DIFICULDADE, JOGADOR_TAM,
                     TILE, CONTORNO)
from .ritmo import Ritmo
from .save import save
from .simulacao import Estado, passo

ESPERANDO, JOGANDO, PAUSADO, FIM, RETOMANDO = 0, 1, 2, 3, 4
CONTAGEM = 3                    # batidas da contagem antes de a musica voltar da pausa
TEXTO_JULGAMENTO = {"perfeito": "PERFEITO!", "bom": "BOM!", "erro": "ERROU..."}
CONTORNO_HUD = CONTORNO         # contorno do texto do HUD: le em cima de qualquer ceu


class Partida:
    def __init__(self, app, fase):
        self.app = app
        self.fase = fase
        self.cenario = Cenario(fase.tema)
        self.ar = efeitos.Ar(fase.tema)
        self.vento = efeitos.Vento()
        self.cor_vento = arte.clarear(fase.tema.ceu, 0.55)
        mundo.preparar(fase)                 # as contas da fase inteira, antes do 1o quadro
        for tipo in TEXTO_JULGAMENTO:        # e os letreiros, que entram estourados (1,25x)
            ui.imagem(f"julgamento_{tipo}.png", 1.25)
        # a poeira do pe: a linha do chao do mundo, clareada
        self.cor_poeira = arte.clarear(fase.tema.chao_topo, 0.3)
        self.menu_pausa = ui.Menu([
            ui.Botao("CONTINUAR", LARGURA // 2 - 220, 330, 440, 60, VERDE),
            ui.Botao("RECOMECAR", LARGURA // 2 - 220, 410, 440, 60, AMARELO),
            ui.Botao("MENU DE FASES", LARGURA // 2 - 220, 490, 440, 60, VERMELHO),
        ])
        self.reiniciar()

    def reiniciar(self):
        self.est = Estado(self.fase)
        self.ritmo = Ritmo(self.fase)
        self.cam = mundo.Camera(self.fase)
        self.modo = ESPERANDO
        self.espera = 0.0          # tempo parado na largada (anima o Leo de pe)
        self.tempo_fim = 0.0
        self.tempo_pausa = 0.0     # desde quando o menu de pausa esta aberto
        self.contagem = 0.0        # segundos que faltam para voltar da pausa
        self.acumulador = 0.0
        self.apertou = False       # o botao foi apertado desde o ultimo passo
        self.pressionado = False
        # segurar o botao pula de novo a cada pouso -- mas so depois de solta-lo
        # uma vez: o toque que deu a largada nao vale
        self.liberou = False
        self.y_desenho = self.est.y   # onde o Leo e desenhado: o resgate nao teletransporta
        self.resultado = None
        self.poeira = efeitos.Poeira()
        self.faiscas = efeitos.Faiscas()
        self.morte = None          # a animacao da morte (Leo virando ruido)
        audio.parar_musica()

    def sair(self):
        audio.parar_musica()

    def _som(self, nome):
        """Um efeito sonoro -- a versao alpha nao tem nenhum (so a musica)."""
        if not self.fase.alpha:
            audio.tocar(nome)

    def _recomecar(self):
        """R ou RECOMECAR: a musica some, a onda cobre a tela e a fase volta a largada."""
        audio.parar_musica()
        self.app.transitar(self.reiniciar)

    # ---------------------------------------------------------------- entrada
    def evento(self, ev):
        if self.modo == ESPERANDO:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                self._comecar()
        elif self.modo == PAUSADO:
            self._evento_pausa(ev)
        elif self.modo == RETOMANDO:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self._pausar()                 # desistiu de voltar: pausa de novo
        elif self.modo == JOGANDO:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self.apertou = True
                elif ev.key == pygame.K_ESCAPE:
                    self._pausar()
                elif ev.key == pygame.K_r:
                    self._recomecar()
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self.apertou = True

    def _evento_pausa(self, ev):
        menu = self.menu_pausa
        escolha = None
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_DOWN, pygame.K_s):
                menu.mover(1)
                self._som("navegar")
            elif ev.key in (pygame.K_UP, pygame.K_w):
                menu.mover(-1)
                self._som("navegar")
            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                escolha = menu.atual
            elif ev.key == pygame.K_ESCAPE:
                escolha = "CONTINUAR"
        elif ev.type == pygame.MOUSEMOTION:
            menu.passar_mouse(self.app.mouse())
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            escolha = menu.clique(self.app.mouse())
        if escolha:
            self._som("clique")
            if escolha == "CONTINUAR":
                # a musica volta na batida, depois de uma contagem: ninguem
                # e jogado de volta no meio de um pulo sem aviso
                self.modo = RETOMANDO
                self.contagem = CONTAGEM * self._tempo_contagem()
                self.liberou = False
            elif escolha == "RECOMECAR":
                self._recomecar()
            else:
                self.app.ir_para_fases()

    def _comecar(self):
        """ESPACO tira a fase da largada, junto com a musica."""
        self.modo = JOGANDO
        # o toque que deu a largada ja esta segurado: sem borda de subida,
        # ele nao vira um pulo
        self.pressionado = self._botao_segurado()
        self.apertou = False
        self.liberou = False
        audio.tocar_musica(self.fase.cancao)

    def _tempo_contagem(self):
        """Segundos de cada numero da contagem: uma batida (no maximo 0,6 s)."""
        return min(0.6, self.fase.dur_batida)

    def _pausar(self):
        self.modo = PAUSADO
        self.tempo_pausa = 0.0
        self.menu_pausa.indice = 0
        self.apertou = False
        audio.pausar_musica()
        self._som("clique")

    def _botao_segurado(self):
        t = self.app.teclado
        return (t.key_pressed("SPACE") or t.key_pressed("UP") or t.key_pressed("W")
                or pygame.mouse.get_pressed()[0])

    # -------------------------------------------------------------- atualizar
    def atualizar(self, dt):
        if self.modo == PAUSADO:
            self.tempo_pausa += dt
            return
        if self.modo == RETOMANDO:
            passo = self._tempo_contagem()
            antes = math.ceil(self.contagem / passo)
            self.contagem -= dt
            if self.contagem <= 0.0:
                self.modo = JOGANDO
                audio.retomar_musica()
            elif math.ceil(self.contagem / passo) != antes:
                self._som("navegar")        # o tique de cada numero
            return
        if self.modo == ESPERANDO:
            self.espera += dt
            return
        if self.modo == FIM:
            self.tempo_fim += dt
            self.poeira.atualizar(dt)
            self.faiscas.atualizar(dt)
            self.cam.tremor = max(0.0, self.cam.tremor - dt * 40.0)   # o tranco passa
            if self.morte is not None:
                self.morte.atualizar(dt)
            # na morte, a tela espera o Leo terminar de virar ruido
            if self.tempo_fim > (1.4 if self.morte is None else 1.75):
                self.app.mostrar_resultado(self.resultado)
            return

        # a borda de subida vem dos eventos (nao perde toques curtos) e tambem
        # da comparacao do estado, para o botao do mouse
        segurado = self._botao_segurado()
        if segurado and not self.pressionado:
            self.apertou = True
        self.pressionado = segurado
        if not segurado:
            self.liberou = True

        self.acumulador += min(dt, 0.1)
        while self.acumulador >= PASSO_FISICA and self.modo == JOGANDO:
            self.acumulador -= PASSO_FISICA
            self._passo()
        self.cam.seguir(self.fase, self.est, dt)
        self.poeira.atualizar(dt)
        self.faiscas.atualizar(dt)
        # o Leo e desenhado onde a fisica diz; so um salto grande de uma vez (o
        # resgate depois de bater numa parede) e percorrido em uns quadros
        d = self.est.y - self.y_desenho
        self.y_desenho = self.est.y if abs(d) < 30 else self.y_desenho + d * min(1.0, dt * 22)

    def _passo(self):
        est, ritmo = self.est, self.ritmo
        apertou = self.apertou
        passo(self.fase, est, self.pressionado or apertou, apertou,
              repetir=self.pressionado and self.liberou)
        self.apertou = False

        if est.quebrou:
            # o bloco estoura em cacos de pedra, na cor dele
            tx, ty = est.quebrou
            cx, cy = tx * TILE + TILE * 0.5, ty * TILE + TILE * 0.5
            tema = self.fase.tema
            self.poeira.soltar(cx, cy, tema.chao_topo, 10, 2.2)
            self.poeira.soltar(cx, cy, arte.clarear(tema.bloco, 0.2), 14, 2.6)
            self._som("quebra")

        # poeira: o pe empurra o chao para tras na saida, e espalha no pouso
        pe_x, pe_y = est.x + JOGADOR_TAM * 0.5, est.y + JOGADOR_TAM
        if est.acao == "pulo":
            self.poeira.soltar(pe_x, pe_y, self.cor_poeira, 6, 0.6, para_tras=1.0)
        elif est.pousou:
            self.poeira.soltar(pe_x, pe_y, self.cor_poeira, 9, 1.2)

        if est.acao:
            self._som("pulo")
        # o julgamento e do TOQUE, na hora dele -- mesmo guardado, com o pulo so
        # saindo no pouso. O pulo que se repete por segurar o botao e julgado
        # na hora em que sai.
        if apertou or est.repetido:
            tipo = ritmo.tocar(est.tempo)
            if tipo:
                self._som(tipo)
                # o acerto estoura em luz em volta do Leo: mais e na cor do mundo no PERFEITO
                perfeito = tipo == "perfeito"
                self.faiscas.soltar(est.x + JOGADOR_TAM * 0.5, est.y + JOGADOR_TAM * 0.4,
                                    self.fase.tema.destaque if perfeito else AMARELO,
                                    12 if perfeito else 7)
        if est.dano:
            self._doeu()
            ritmo.falhar(est.tempo)
        # marca cuja janela passou sem toque vira ERROU: sem ponto e sem
        # sequencia -- mas coracao so se perde batendo em alguma coisa
        if est.vivo and ritmo.expirar(est.tempo):
            self._som("erro")
        if not est.vivo:
            self._encerrar(False)
        elif est.venceu:
            self._encerrar(True)

    def _doeu(self):
        self._som("erro")
        self.cam.sacudir(12.0)

    def _encerrar(self, venceu):
        est, r = self.est, self.ritmo
        self.modo = FIM
        self.ritmo.fechar()
        audio.parar_musica()
        self._som("vitoria" if venceu else "morte")
        self.cam.sacudir(8.0 if venceu else 20.0)
        if not venceu and not self.fase.alpha:          # a versao alpha nao tem animacao
            self.morte = efeitos.Desintegracao(*mundo.sprite_heroi(self.fase, est, self.y_desenho))
        progresso = min(100.0, est.x / self.fase.fim_x * 100.0)
        recorde_antes = save.recorde(self.fase.ident)["pontos"]
        save.registrar(self.fase.ident, progresso, venceu, r.pontos, r.nota(), r.precisao())
        self.resultado = {
            "fase": self.fase, "completou": venceu, "pontos": r.pontos,
            "nota": r.nota(), "precisao": r.precisao(), "perfeitos": r.perfeitos,
            "bons": r.bons, "erros": r.erros, "combo": r.melhor_combo,
            "progresso": progresso, "recorde": r.pontos > recorde_antes,
        }

    # --------------------------------------------------------------- desenhar
    def _pulso(self):
        """1 exatamente na batida, caindo a 0 antes da proxima (0 na largada)."""
        if self.modo == ESPERANDO:
            return 0.0
        frac = (self.est.tempo / self.fase.dur_batida) % 1.0
        return max(0.0, 1.0 - frac * 3.0)

    def desenhar(self, tela):
        cam_x, cam_y = self.cam.na_tela()
        pulso = self._pulso()
        espera = self.espera if self.modo == ESPERANDO else None
        if self.fase.alpha:
            alpha.desenhar(tela, self, cam_x, cam_y, espera)   # a versao alpha, simplificada
        else:
            # as estrelas piscam desde a largada, sem pular quando a musica entra
            self.cenario.desenhar(tela, cam_x, cam_y, self.espera + self.est.tempo, pulso)
            self.ar.desenhar(tela, cam_x, cam_y, self.espera + self.est.tempo)
            # depois de um portal rapido, o vento corta o ceu
            self.vento.desenhar(tela, self.est.tempo,
                                self.fase.vx_em(self.est.x) > self.fase.vx * 1.1,
                                self.cor_vento, 1.0 / 60.0)
            mundo.desenhar(tela, self.fase, self.est, cam_x, cam_y, pulso, espera, self.y_desenho,
                           heroi=self.morte is None)
            self.poeira.desenhar(tela, cam_x, cam_y)
            self.faiscas.desenhar(tela, cam_x, cam_y)
            self._hud(tela, pulso)
        self._letreiro(tela)
        if self.modo == PAUSADO:
            # o escuro chega suave, num instante; o menu ja esta la
            ui.escurecer_tela(tela, int(170 * ui.suave(self.tempo_pausa / 0.15)))
            ui.desenhar_texto(tela, "PAUSADO", 56, LARGURA // 2, 200, self.fase.tema.destaque)
            self.menu_pausa.desenhar(tela)
        elif self.modo == RETOMANDO:
            passo = self._tempo_contagem()
            falta = self.contagem / (CONTAGEM * passo)
            ui.escurecer_tela(tela, int(170 * falta))
            n = max(1, math.ceil(self.contagem / passo))
            ui.desenhar_texto(tela, str(n), 96, LARGURA // 2, ALTURA * 0.4,
                              self.fase.tema.destaque, contorno=CONTORNO_HUD)
        elif self.modo == FIM:
            venceu = self.resultado["completou"]
            ui.escurecer_tela(tela, int(120 * min(1.0, self.tempo_fim * 2)))
            if self.morte is not None:
                # por cima do escuro: o Leo se desfazendo e o que o olho segue
                self.morte.desenhar(tela, cam_x, cam_y)
            # o letreiro aparece aos poucos (na morte, depois do Leo se desfazer)
            k = ui.suave((self.tempo_fim - (0.1 if venceu else 0.65)) / 0.3)
            if k > 0.0:
                texto = ui.texto("FASE COMPLETA" if venceu else "FIM DE JOGO", 64,
                                 VERDE if venceu else VERMELHO, CONTORNO_HUD)
                if k < 1.0:
                    texto = arte.fantasma(texto, int(255 * k) // 16 * 16)
                tela.blit(texto, texto.get_rect(center=(LARGURA // 2, int(ALTURA * 0.42))))

    def _letreiro(self, tela):
        """
        O nome da fase e a musica, no alto: aparecem aos poucos enquanto a
        fase espera e somem aos poucos quando a musica entra.
        """
        if self.fase.alpha:
            return                                  # a versao alpha nao apresenta a musica
        if self.modo == ESPERANDO:
            k = ui.suave((self.espera - 0.25) / 0.5)
        elif self.modo == JOGANDO and self.est.tempo < 0.7:
            k = 1.0 - ui.suave(self.est.tempo / 0.7)
        else:
            return
        if k <= 0.0:
            return
        alfa = int(255 * k) // 16 * 16
        y = ALTURA * 0.24
        f = self.fase
        linhas = ((ui.texto(f.nome, 48, f.tema.destaque, CONTORNO_HUD), 0),
                  (ui.texto(f.dificuldade, 20, COR_DIFICULDADE[f.dificuldade], CONTORNO_HUD), 48),
                  (ui.texto(f.trilha.creditos, 18, CINZA, CONTORNO_HUD), 80))
        for img, dy in linhas:
            if alfa < 255:
                img = arte.fantasma(img, alfa)
            tela.blit(img, img.get_rect(center=(LARGURA // 2, int(y + dy))))

    def _hud(self, tela, pulso):
        est, r, tema = self.est, self.ritmo, self.fase.tema
        # canto superior esquerdo: coracoes e nome da fase
        for i in range(VIDAS):
            cheio = i < est.vidas
            batendo = cheio and i == est.vidas - 1 and pulso > 0.5
            tam = 36 + (int(6 * pulso) if cheio and i == est.vidas - 1 else 0)
            img = arte.coracao(tam, VERMELHO, cheio, batendo)
            # centrado: o coracao que bate cresce para todos os lados, sem pular
            tela.blit(img, img.get_rect(center=(28 + i * 46 + 18, 46)))
        ui.desenhar_texto(tela, self.fase.nome, 18, 28, 92, tema.destaque, "esquerda", CONTORNO_HUD)

        # canto superior direito: pontuacao e combo
        ui.desenhar_texto(tela, f"{r.pontos:05d}", 44, LARGURA - 28, 50, BRANCO, "direita", CONTORNO_HUD)
        if r.combo >= 3:
            ui.desenhar_texto(tela, f"x{r.combo}", 24, LARGURA - 28, 96, AMARELO, "direita",
                              CONTORNO_HUD)

        # centro: julgamento da ultima acao, sumindo em menos de um segundo
        j = r.ultimo
        if j is not None and self.modo == JOGANDO and est.tempo - j.tempo < 0.7:
            k = 1.0 - (est.tempo - j.tempo) / 0.7
            y = ALTURA * 0.28 - (1.0 - k) * 30
            # o letreiro entra estourado por um instante e some aos poucos no fim
            estourado = k > 0.85
            alfa = int(255 * k / 0.25) // 16 * 16 if k < 0.25 else 255
            letreiro = ui.imagem(f"julgamento_{j.tipo}.png", 1.25 if estourado else 1)
            if letreiro is not None:
                if alfa < 255:
                    letreiro = arte.fantasma(letreiro, alfa)
                tela.blit(letreiro, letreiro.get_rect(center=(LARGURA // 2, int(y))))
                abaixo = letreiro.get_height() // 2 + 22
            else:
                ui.desenhar_texto(tela, TEXTO_JULGAMENTO[j.tipo], 36 + int(10 * k),
                                  LARGURA // 2, y, COR_JULGAMENTO[j.tipo])
                abaixo = 44
            # logo abaixo, os pontos que o toque valeu (+0 no ERROU), na cor do
            # julgamento, estourando e sumindo junto com o letreiro
            pontos = ui.texto(f"+{j.pontos}", 34 if estourado else 30, COR_JULGAMENTO[j.tipo],
                              CONTORNO_HUD)
            if alfa < 255:
                pontos = arte.fantasma(pontos, alfa)
            tela.blit(pontos, pontos.get_rect(center=(LARGURA // 2, int(y) + abaixo)))

        self._progresso(tela, pulso)

    def _progresso(self, tela, pulso):
        """
        Rodape: o trilho da fase e a porcentagem no fim. O rostinho do Leo anda
        por ele pulando na batida -- a progressao do personagem no mapa, como
        pede o GDD.
        """
        fase, tema = self.fase, self.fase.tema
        bx, by, bw, bh = 250, ALTURA - 40, 760, 12
        frac = min(1.0, self.est.x / fase.fim_x)
        ui.barra(tela, bx, by, bw, bh, frac, tema.destaque)
        px, py = bx + bw + 22, by + bh // 2
        rosto = arte.retrato(CONTORNO_HUD)
        tela.blit(rosto, (int(bx + bw * frac - rosto.get_width() / 2),
                          by + 4 - rosto.get_height() - int(4 * pulso)))
        ui.desenhar_texto(tela, f"{frac * 100:.0f}%", 22, px, py, CINZA, "esquerda", CONTORNO_HUD)
