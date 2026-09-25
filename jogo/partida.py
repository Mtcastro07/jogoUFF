"""
A partida: entrada, laco de jogo, julgamento, HUD, pausa e fim de fase.

A fisica roda em passos fixos (`simulacao.passo`) e o julgamento ritmico em
`ritmo.Ritmo`. Esta classe liga os dois ao teclado, ao som e a tela.

A fase abre parada, com Leo de pe na largada, e so comeca (musica e fisica
juntas) quando o jogador aperta ESPACO. Esse toque nao conta como pulo. Nao
ha aviso na tela: o jogador comeca quando quiser.

    ESPACO / SETA CIMA / W / clique   ->  pulo (toque) ou ponte (segurado)
    ESC                                ->  pausa
    R                                  ->  recomeca
"""

import pygame

from . import arte, efeitos, mundo, ui
from .audio import audio
from .cenario import Cenario
from .config import (LARGURA, ALTURA, VIDAS, PASSO_FISICA, BRANCO, CINZA,
                     AMARELO, VERDE, VERMELHO, COR_JULGAMENTO, JOGADOR_TAM)
from .ritmo import Ritmo
from .save import save
from .simulacao import Estado, passo, ferir

ESPERANDO, JOGANDO, PAUSADO, FIM = 0, 1, 2, 3
TEXTO_JULGAMENTO = {"perfeito": "PERFEITO!", "bom": "BOM!", "erro": "ERROU..."}


class Partida:
    def __init__(self, app, fase):
        self.app = app
        self.fase = fase
        self.cenario = Cenario(fase.tema)
        self.ar = efeitos.Ar(fase.tema)
        mundo.preparar(fase)                 # as contas da fase inteira, antes do 1o quadro
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
        self.acumulador = 0.0
        self.apertou = False       # o botao foi apertado desde o ultimo passo
        self.pressionado = False
        self.resultado = None
        self.poeira = efeitos.Poeira()
        audio.parar_musica()

    def sair(self):
        audio.parar_musica()

    # ---------------------------------------------------------------- entrada
    def evento(self, ev):
        if self.modo == ESPERANDO:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                self._comecar()
        elif self.modo == PAUSADO:
            self._evento_pausa(ev)
        elif self.modo == JOGANDO:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self.apertou = True
                elif ev.key == pygame.K_ESCAPE:
                    self._pausar()
                elif ev.key == pygame.K_r:
                    self.reiniciar()
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self.apertou = True

    def _evento_pausa(self, ev):
        menu = self.menu_pausa
        escolha = None
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_DOWN, pygame.K_s):
                menu.mover(1)
                audio.tocar("navegar")
            elif ev.key in (pygame.K_UP, pygame.K_w):
                menu.mover(-1)
                audio.tocar("navegar")
            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                escolha = menu.atual
            elif ev.key == pygame.K_ESCAPE:
                escolha = "CONTINUAR"
        elif ev.type == pygame.MOUSEMOTION:
            menu.passar_mouse(self.app.mouse())
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            escolha = menu.clique(self.app.mouse())
        if escolha:
            audio.tocar("clique")
            if escolha == "CONTINUAR":
                self.modo = JOGANDO
                audio.retomar_musica()
            elif escolha == "RECOMECAR":
                self.reiniciar()
            else:
                self.app.ir_para_fases()

    def _comecar(self):
        """ESPACO tira a fase da largada, junto com a musica."""
        self.modo = JOGANDO
        # o toque que deu a largada ja esta segurado: sem borda de subida,
        # ele nao vira um pulo
        self.pressionado = self._botao_segurado()
        self.apertou = False
        audio.tocar_musica(self.fase.cancao)

    def _pausar(self):
        self.modo = PAUSADO
        self.menu_pausa.indice = 0
        self.apertou = False
        audio.pausar_musica()
        audio.tocar("clique")

    def _botao_segurado(self):
        t = self.app.teclado
        return (t.key_pressed("SPACE") or t.key_pressed("UP") or t.key_pressed("W")
                or pygame.mouse.get_pressed()[0])

    # -------------------------------------------------------------- atualizar
    def atualizar(self, dt):
        if self.modo == PAUSADO:
            return
        if self.modo == ESPERANDO:
            self.espera += dt
            return
        if self.modo == FIM:
            self.tempo_fim += dt
            self.poeira.atualizar(dt)
            if self.tempo_fim > 1.4:
                self.app.mostrar_resultado(self.resultado)
            return

        # a borda de subida vem dos eventos (nao perde toques curtos) e tambem
        # da comparacao do estado, para o botao do mouse
        segurado = self._botao_segurado()
        if segurado and not self.pressionado:
            self.apertou = True
        self.pressionado = segurado

        self.acumulador += min(dt, 0.1)
        while self.acumulador >= PASSO_FISICA and self.modo == JOGANDO:
            self.acumulador -= PASSO_FISICA
            self._passo()
        self.cam.seguir(self.fase, self.est, dt)
        self.poeira.atualizar(dt)

    def _passo(self):
        est, ritmo = self.est, self.ritmo
        sustentava = est.sustentando
        passo(self.fase, est, self.pressionado or self.apertou, self.apertou)
        self.apertou = False

        if sustentava and not est.sustentando and est.ponte is not None and not est.no_chao:
            audio.tocar("quebra")          # soltou a nota no meio do vao

        # poeira: o pe empurra o chao para tras na saida, e espalha no pouso.
        # Na ponte de luz nao ha poeira nenhuma.
        pe_x, pe_y = est.x + JOGADOR_TAM * 0.5, est.y + JOGADOR_TAM
        if est.acao == "pulo":
            self.poeira.soltar(pe_x, pe_y, self.cor_poeira, 6, 0.6, para_tras=1.0)
        elif est.pousou and not est.sustentando:
            self.poeira.soltar(pe_x, pe_y, self.cor_poeira, 9, 1.2)

        if est.acao:
            audio.tocar("ponte" if est.acao == "sustentar" else "pulo")
            tipo = ritmo.tocar(est.tempo)
            if tipo:
                audio.tocar(tipo)
        if est.dano:
            self._doeu()
            ritmo.falhar(est.tempo)
        # marcas cuja janela passou sem toque viram erro e custam um coracao
        if ritmo.expirar(est.tempo, mostrar=est.invuln <= 0.0):
            ferir(self.fase, est, "ritmo", resgatar=False)
            if est.dano == "ritmo":
                self._doeu()
        if not est.vivo:
            self._encerrar(False)
        elif est.venceu:
            self._encerrar(True)

    def _doeu(self):
        audio.tocar("erro")
        self.cam.sacudir(12.0)

    def _encerrar(self, venceu):
        est, r = self.est, self.ritmo
        self.modo = FIM
        self.ritmo.fechar()
        audio.parar_musica()
        audio.tocar("vitoria" if venceu else "morte")
        self.cam.sacudir(8.0 if venceu else 20.0)
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
        # as estrelas piscam desde a largada, sem pular quando a musica entra
        self.cenario.desenhar(tela, cam_x, cam_y, self.espera + self.est.tempo, pulso)
        self.ar.desenhar(tela, cam_x, cam_y, self.espera + self.est.tempo)
        mundo.desenhar(tela, self.fase, self.est, cam_x, cam_y, pulso, espera)
        self.poeira.desenhar(tela, cam_x, cam_y)
        self._hud(tela, pulso)
        if self.modo == PAUSADO:
            ui.escurecer_tela(tela, 170)
            ui.desenhar_texto(tela, "PAUSADO", 56, LARGURA // 2, 200, self.fase.tema.destaque)
            self.menu_pausa.desenhar(tela)
        elif self.modo == FIM:
            ui.escurecer_tela(tela, int(120 * min(1.0, self.tempo_fim * 2)))
            venceu = self.resultado["completou"]
            ui.desenhar_texto(tela, "FASE COMPLETA" if venceu else "FIM DE JOGO", 64,
                              LARGURA // 2, ALTURA * 0.42, VERDE if venceu else VERMELHO)

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
        ui.desenhar_texto(tela, self.fase.nome, 18, 28, 92, tema.destaque, "esquerda")

        # canto superior direito: pontuacao e combo
        ui.desenhar_texto(tela, f"{r.pontos:05d}", 44, LARGURA - 28, 50, BRANCO, "direita")
        if r.combo >= 3:
            ui.desenhar_texto(tela, f"x{r.combo}", 24, LARGURA - 28, 96, AMARELO, "direita")

        # centro: julgamento da ultima acao, sumindo em menos de um segundo
        j = r.ultimo
        if j is not None and self.modo == JOGANDO and est.tempo - j.tempo < 0.7:
            k = 1.0 - (est.tempo - j.tempo) / 0.7
            y = ALTURA * 0.28 - (1.0 - k) * 30
            # o letreiro entra estourado por um instante e some aos poucos no fim
            letreiro = ui.imagem(f"julgamento_{j.tipo}.png", 1.25 if k > 0.85 else 1)
            if letreiro is not None:
                if k < 0.25:
                    letreiro = arte.fantasma(letreiro, int(255 * k / 0.25) // 16 * 16)
                tela.blit(letreiro, letreiro.get_rect(center=(LARGURA // 2, int(y))))
            else:
                ui.desenhar_texto(tela, TEXTO_JULGAMENTO[j.tipo], 36 + int(10 * k),
                                  LARGURA // 2, y, COR_JULGAMENTO[j.tipo])
            if j.pontos:
                ui.desenhar_texto(tela, f"+{j.pontos}", 22, LARGURA // 2, y + 40, BRANCO)

        # rodape: barra de progresso com as pontes marcadas e a porcentagem
        bx, by, bw, bh = 240, ALTURA - 44, 760, 12
        pct = min(100.0, est.x / self.fase.fim_x * 100.0)
        ui.painel(tela, bx - 16, by - 16, bw + 130, bh + 32, alpha=150, borda=None)
        ui.barra(tela, bx, by, bw, bh, pct / 100.0, tema.destaque)
        for p in self.fase.pontes:
            x0 = bx + bw * p.x0 / self.fase.fim_x
            larg = max(4, bw * (p.x1 - p.x0) / self.fase.fim_x)
            pygame.draw.rect(tela, AMARELO, (int(x0), by - 6, int(larg), 4))
        ui.desenhar_texto(tela, f"{pct:.0f}%", 22, bx + bw + 20, by + bh // 2, CINZA, "esquerda")
