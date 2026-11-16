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
from .cenario import Cenario, cena
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
MARCO_COMBO = 25                # a cada tantos acertos seguidos, a sequencia comemora
BORDA = 40                      # px da luz que bate nas bordas da tela


def _bordas(cor):
    """
    As quatro faixas de luz das bordas da tela, em degraus de pixel (nada de
    degrade liso): fortes rente a borda, sumindo para dentro.
    """
    passos = 4
    def faixa(w, h, horizontal, inverte):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(passos):
            alfa = int(255 * (1.0 - i / passos) ** 2)
            d = i * BORDA // passos
            e = BORDA // passos
            if horizontal:
                y = h - d - e if inverte else d
                s.fill((*cor, alfa), (0, y, w, e))
            else:
                x = w - d - e if inverte else d
                s.fill((*cor, alfa), (x, 0, e, h))
        return s
    return (faixa(LARGURA, BORDA, True, False), faixa(LARGURA, BORDA, True, True),
            faixa(BORDA, ALTURA - 2 * BORDA, False, False), faixa(BORDA, ALTURA - 2 * BORDA, False, True))


RASTRO_COMBO = 10      # a partir desta sequencia o Leo deixa um rastro
_vinhetas = []


def _vinheta():
    """Os cantos da tela escurecem de leve: o olho fica no meio, onde esta o jogo."""
    if not _vinhetas:
        w, h = LARGURA // 8, ALTURA // 8
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            for x in range(w):
                d = math.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2))
                s.set_at((x, y), (6, 4, 16, int(110 * max(0.0, min(1.0, (d - 0.72) / 0.7)) ** 1.4)))
        _vinhetas.append(pygame.transform.smoothscale(s, (LARGURA, ALTURA)))
    return _vinhetas[0]


PONTOS_ECO = 10                 # cada eco pego no ar
# ate onde o corpo do Leo alcanca um eco (px, para os lados e na altura): cabe o
# toque adiantado ou atrasado, e nao cabe o arco errado (o alto passa longe do baixo)
ALCANCE_ECO = (22, 34)


class Partida:
    def __init__(self, app, fase):
        self.app = app
        self.fase = fase
        self.cenario = Cenario(fase.tema)
        self.ar = efeitos.Ar(fase.tema)
        self.ar_atos = {ato: efeitos.Ar(fase.tema, cfg)
                        for ato, cfg in efeitos.AR_DO_ATO.get(fase.tema.nome, {}).items()}
        self.vento = efeitos.Vento()
        self.cor_vento = arte.clarear(fase.tema.ceu, 0.55)
        mundo.preparar(fase)                 # as contas da fase inteira, antes do 1o quadro
        for tipo in TEXTO_JULGAMENTO:        # e os letreiros, que entram estourados (1,25x)
            ui.imagem(f"julgamento_{tipo}.png", 1.25)
        # a poeira do pe: a linha do chao do mundo, clareada
        self.cor_poeira = arte.clarear(fase.tema.chao_topo, 0.3)
        self.luz_batida = _bordas(fase.tema.destaque)   # a batida acende as bordas
        self.luz_dano = _bordas(VERMELHO)               # e a pancada as tinge de vermelho
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
        self.ecos = efeitos.Ecos()
        self.pegos = set()         # indices dos ecos (fase.brilhos) ja pegos
        self.eco_em = None         # instante do ultimo eco pego (a conta do HUD salta)
        self.brilho_i = 0          # o primeiro eco que ainda nao ficou para tras
        self.rastro = []           # [(quadro, x, y)] do Leo, com a sequencia alta
        self.conta_rastro = 0
        self.morte = None          # a animacao da morte (Leo virando ruido)
        self.pontos_tela = 0.0     # a pontuacao do HUD conta ate a de verdade
        self.dano_em = None        # (instante, qual coracao) da ultima pancada
        self.marco = None          # (instante, sequencia) do ultimo marco de combo
        # o melhor progresso ate esta partida: uma marquinha no trilho do rodape
        self.melhor_antes = save.recorde(self.fase.ident)["melhor"]
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
                or pygame.mouse.get_pressed()[0]
                or getattr(self.app, "controle_segurado", bool)())

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
        self.ecos.atualizar(dt)
        # com a sequencia alta o Leo deixa um rastro: um quadro guardado a cada 3
        self.conta_rastro += 1
        if self.ritmo.combo >= RASTRO_COMBO and not self.fase.alpha:
            if self.conta_rastro % 3 == 0:
                self.rastro.append(mundo.sprite_heroi(self.fase, self.est, self.y_desenho))
                del self.rastro[:-3]
        elif self.rastro and self.conta_rastro % 3 == 0:
            self.rastro.pop(0)                              # perdeu a sequencia: o rastro some
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
        if est.impulso:
            # mola ou orbe: o salto estoura em luz, na cor do mundo
            self.faiscas.soltar(pe_x, pe_y - JOGADOR_TAM * 0.5, self.fase.tema.destaque, 16)
            self.ecos.soltar(pe_x, pe_y, self.fase.tema.destaque)
            self.cam.sacudir(4.0)
        if est.acao == "pulo":
            self.poeira.soltar(pe_x, pe_y, self.cor_poeira, 6, 0.6, para_tras=1.0)
        elif est.pousou:
            self.poeira.soltar(pe_x, pe_y, self.cor_poeira, 9, 1.2)

        if est.acao:
            self._som(est.impulso or "pulo")
        # o julgamento e do TOQUE, na hora dele -- mesmo guardado, com o pulo so
        # saindo no pouso. O pulo que se repete por segurar o botao e julgado
        # na hora em que sai.
        if apertou or est.repetido:
            tipo = ritmo.tocar(est.tempo)
            if tipo:
                self._som(tipo)
                # o acerto estoura em luz em volta do Leo: mais e na cor do mundo no PERFEITO
                perfeito = tipo == "perfeito"
                if perfeito:
                    self.ecos.soltar(est.x + JOGADOR_TAM * 0.5, est.y + JOGADOR_TAM,
                                     self.fase.tema.destaque)
                self.faiscas.soltar(est.x + JOGADOR_TAM * 0.5, est.y + JOGADOR_TAM * 0.4,
                                    self.fase.tema.destaque if perfeito else AMARELO,
                                    12 if perfeito else 7)
                if ritmo.combo and ritmo.combo % MARCO_COMBO == 0:
                    # o marco da sequencia: um estouro maior, em duas cores
                    self.marco = (est.tempo, ritmo.combo)
                    self.faiscas.soltar(est.x + JOGADOR_TAM * 0.5, est.y + JOGADOR_TAM * 0.4,
                                        AMARELO, 20)
        self._pegar_brilhos()
        if est.dano:
            self.dano_em = (est.tempo, est.vidas)   # o coracao que acabou de esvaziar
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

    def _pegar_brilhos(self):
        """Os ecos no ar: pega quem passa com o corpo por cima deles."""
        est, brilhos = self.est, self.fase.brilhos
        cx, cy = est.x + JOGADOR_TAM * 0.5, est.y + JOGADOR_TAM * 0.5
        while self.brilho_i < len(brilhos) and brilhos[self.brilho_i][0] < cx - ALCANCE_ECO[0]:
            self.brilho_i += 1
        i = self.brilho_i
        while i < len(brilhos) and brilhos[i][0] <= cx + ALCANCE_ECO[0]:
            bx, by, _ = brilhos[i]
            if i not in self.pegos and abs(by - JOGADOR_TAM * 0.5 - cy) <= ALCANCE_ECO[1]:
                self.pegos.add(i)
                self.eco_em = est.tempo
                self.ritmo.bonus += PONTOS_ECO
                self.faiscas.soltar(bx, by - JOGADOR_TAM * 0.5, self.fase.tema.destaque, 8)
                self._som("eco")
            i += 1

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
        save.registrar(self.fase.ident, progresso, venceu, r.pontos + r.bonus, r.nota(),
                       r.precisao(), len(self.pegos))
        self.resultado = {
            "fase": self.fase, "completou": venceu, "pontos": r.pontos + r.bonus,
            "ecos": len(self.pegos), "ecos_total": len(self.fase.brilhos),
            "nota": r.nota(), "precisao": r.precisao(), "perfeitos": r.perfeitos,
            "bons": r.bons, "erros": r.erros, "combo": r.melhor_combo,
            "progresso": progresso, "recorde": r.pontos + r.bonus > recorde_antes,
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
            self.cenario.desenhar(tela, cam_x, cam_y, self.espera + self.est.tempo, pulso,
                                  **cena(self.fase, self.est.x))
            self.ar.desenhar(tela, cam_x, cam_y, self.espera + self.est.tempo)
            ar_ato = self.ar_atos.get(self.fase.ato(self.est.x))
            if ar_ato:
                ar_ato.desenhar(tela, cam_x, cam_y, self.espera + self.est.tempo)
            # depois de um portal rapido, o vento corta o ceu
            self.vento.desenhar(tela, self.est.tempo,
                                self.fase.vx_em(self.est.x) > self.fase.vx * 1.1,
                                self.cor_vento, 1.0 / 60.0)
            self.ecos.desenhar(tela, cam_x, cam_y)
            mundo.desenhar_brilhos(tela, self.fase, cam_x, cam_y, self.pegos,
                                   self.espera + self.est.tempo)
            mundo.desenhar(tela, self.fase, self.est, cam_x, cam_y, pulso, espera, self.y_desenho,
                           heroi=self.morte is None,
                           rastro=self.rastro if self.morte is None and self.modo == JOGANDO else ())
            self.poeira.desenhar(tela, cam_x, cam_y)
            self.faiscas.desenhar(tela, cam_x, cam_y)
            for dx, dy, texto in self.fase.dicas:
                # a legenda da mecanica nova: escrita no mundo, passa com ele
                if -200 <= dx - cam_x <= LARGURA + 200:
                    ui.desenhar_texto(tela, texto, 18, int(dx - cam_x), int(dy - cam_y), BRANCO,
                                      contorno=CONTORNO_HUD)
            tela.blit(_vinheta(), (0, 0))
            self._bordas(tela, pulso)
            self._hud(tela, pulso)
        self._letreiro(tela)
        if self.modo == ESPERANDO and self.espera > 0.6 and int(self.espera * 1.6) % 4 != 3:
            # a fase espera o toque: sem este aviso ninguem sabia que era o ESPACO
            ui.dicas(tela, (("ESPACO", "COMECA"),), ALTURA * 0.62)
        if self.modo == PAUSADO:
            # o escuro chega suave, num instante; o menu ja esta la
            ui.escurecer_tela(tela, int(170 * ui.suave(self.tempo_pausa / 0.15)))
            ui.desenhar_texto(tela, "PAUSADO", 56, LARGURA // 2, 200, self.fase.tema.destaque)
            self.menu_pausa.desenhar(tela)
            ui.dicas(tela, (("SETAS", "ESCOLHEM"), ("ENTER", "CONFIRMA"), ("ESC", "CONTINUA")), 612)
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

    def _bordas(self, tela, pulso):
        """
        A batida acende as bordas da tela, de leve -- mais forte no primeiro
        tempo do compasso, para o jogador sentir o 1 sem olhar para nada. Uma
        pancada as tinge de vermelho por um instante.
        """
        alfa_dano = 0
        if self.dano_em is not None:
            alfa_dano = int(200 * max(0.0, 1.0 - (self.est.tempo - self.dano_em[0]) / 0.4))
        luz, alfa = self.luz_dano, alfa_dano
        if not alfa_dano and self.modo == JOGANDO and pulso > 0.05:
            tempo_do_compasso = int(self.est.tempo / self.fase.dur_batida + 0.01) % 4
            luz, alfa = self.luz_batida, int((70 if tempo_do_compasso == 0 else 32) * pulso)
        if alfa <= 0:
            return
        cima, baixo, esq, dir_ = luz
        for img, pos in ((cima, (0, 0)), (baixo, (0, ALTURA - BORDA)),
                         (esq, (0, BORDA)), (dir_, (LARGURA - BORDA, BORDA))):
            img.set_alpha(alfa)
            tela.blit(img, pos)

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
        if self.dano_em is not None:
            # o coracao que se perdeu: estoura cheio, cresce e some por cima do vazio
            t = est.tempo - self.dano_em[0]
            i = self.dano_em[1]
            if 0.0 <= t < 0.45 and i < VIDAS:
                k = t / 0.45
                img = arte.coracao(36 + int(28 * ui.suave(k)), VERMELHO, True, True)
                img = arte.fantasma(img, max(16, int(255 * (1.0 - k)) // 16 * 16))
                tela.blit(img, img.get_rect(center=(28 + i * 46 + 18, 46 - int(10 * k))))
        ui.desenhar_texto(tela, self.fase.nome, 18, 28, 92, tema.destaque, "esquerda", CONTORNO_HUD)
        if self.fase.brilhos:
            # os ecos pegos: o losango e a conta, que salta quando entra mais um
            novo = self.eco_em is not None and 0.0 <= est.tempo - self.eco_em < 0.18
            tela.blit(mundo.icone_eco(tema.destaque), (28, 108 - (3 if novo else 0)))
            ui.desenhar_texto(tela, f"{len(self.pegos)}/{len(self.fase.brilhos)}", 20 if novo else 18,
                              62, 122, BRANCO if novo else tema.destaque, "esquerda", CONTORNO_HUD)

        # canto superior direito: pontuacao e combo
        # a pontuacao conta ate a de verdade, e fica na cor do mundo enquanto conta
        total = r.pontos + r.bonus
        if self.pontos_tela < total:
            self.pontos_tela = min(float(total),
                                   self.pontos_tela + max(1.0, (total - self.pontos_tela) * 0.25))
        else:
            self.pontos_tela = float(total)
        contando = self.pontos_tela < total
        ui.desenhar_texto(tela, f"{int(self.pontos_tela):05d}", 44, LARGURA - 28, 50,
                          tema.destaque if contando else BRANCO, "direita", CONTORNO_HUD)
        if r.combo >= 3:
            # a sequencia cresce de tamanho conforme sobe: 30 px, 34 a partir de 25, 38 de 50
            base = 30 + (4 if r.combo >= 25 else 0) + (4 if r.combo >= 50 else 0)
            tam, cor = base, AMARELO
            if self.marco is not None and self.marco[1] == r.combo:
                k = (est.tempo - self.marco[0]) / 0.6
                if k < 1.0:      # o marco: o numero estoura e volta, na cor do mundo
                    tam, cor = base + int(16 * (1.0 - ui.suave(k))), tema.destaque
                    ui.desenhar_texto(tela, "SEQUENCIA!", 16, LARGURA - 28, 138, tema.destaque,
                                      "direita", CONTORNO_HUD)
            ui.desenhar_texto(tela, f"x{r.combo}", tam, LARGURA - 28, 100, cor, "direita",
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
        melhor = self.melhor_antes / 100.0
        if 0.0 < melhor < 1.0:
            # ate onde o jogador ja chegou: uma bandeirinha no trilho, que acende
            # quando ele passa dela
            mx = int(bx + bw * melhor)
            cor = AMARELO if frac >= melhor else BRANCO
            pygame.draw.rect(tela, CONTORNO_HUD, (mx - 2, by - 12, 5, bh + 16))
            pygame.draw.rect(tela, cor, (mx - 1, by - 11, 3, bh + 14))
            pygame.draw.rect(tela, CONTORNO_HUD, (mx + 1, by - 14, 10, 8))
            pygame.draw.rect(tela, cor, (mx + 2, by - 13, 8, 6))
        px, py = bx + bw + 22, by + bh // 2
        rosto = arte.retrato(CONTORNO_HUD)
        tela.blit(rosto, (int(bx + bw * frac - rosto.get_width() / 2),
                          by + 4 - rosto.get_height() - int(4 * pulso)))
        ui.desenhar_texto(tela, f"{frac * 100:.0f}%", 22, px, py, CINZA, "esquerda", CONTORNO_HUD)
