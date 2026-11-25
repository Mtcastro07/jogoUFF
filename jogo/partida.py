import math

import pygame
from PPlay.input_manager import InputManager

from . import arte, efeitos, mundo, notas, ui
from .audio import audio
from .camera import CamQueSegue
from .cena import TelaQualquer
from .cenario import FundoTodo, cena
from .imagem import Desenho
from .grupo import PorColuna, Monte
from .impacto import Impacto
from .kit import Botao, Menu, BarraDoTopo
from .leo import Leo
from .config import (LARG_TELA, ALT_TELA, QTD_VIDAS, TEMPINHO, BRANCO, CINZA,
                     AMARELO, VERDE, VERMELHO, COR_DO_ACERTO, COR_DA_DIFICULDADE, TAM_DO_LEO,
                     QUADRADO, CONTORNO)
from .ritmo import ContaRitmo
from .save import save
from .simulacao import passo
from .tempo import Agenda, Curvas

ESPERANDO, JOGANDO, PAUSADO, FIM, RETOMANDO = 0, 1, 2, 3, 4
CONTA_ATE = 3
COMBO_BONITO = 25
BORDA = 40


def faixa(cor, w, h, x, y, lado):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(4):
        alfa = int(255 * (1.0 - i / 4) ** 2)
        d = i * 10
        if lado == "cima":
            s.fill((*cor, alfa), (0, d, w, 10))
        elif lado == "baixo":
            s.fill((*cor, alfa), (0, h - d - 10, w, 10))
        elif lado == "esquerda":
            s.fill((*cor, alfa), (d, 0, 10, h))
        else:
            s.fill((*cor, alfa), (w - d - 10, 0, 10, h))
    img = Desenho(s)
    img.set_position(x, y)
    return img


def faz_luz_nas_bordas(cor):
    h = ALT_TELA - 2 * BORDA
    return [faixa(cor, LARG_TELA, BORDA, 0, 0, "cima"),
            faixa(cor, LARG_TELA, BORDA, 0, ALT_TELA - BORDA, "baixo"),
            faixa(cor, BORDA, h, 0, BORDA, "esquerda"),
            faixa(cor, BORDA, h, LARG_TELA - BORDA, BORDA, "direita")]


COMBO_DO_RASTRO = 10
vinhetas_prontas = []


def pega_vinheta():
    if not vinhetas_prontas:
        w, h = LARG_TELA // 8, ALT_TELA // 8
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            for x in range(w):
                d = math.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2))
                k = max(0.0, min(1.0, (d - 0.72) / 0.7))
                s.set_at((x, y), (6, 4, 16, int(110 * k ** 1.4)))
        vinhetas_prontas.append(Desenho(pygame.transform.smoothscale(s, (LARG_TELA, ALT_TELA))))
    return vinhetas_prontas[0]


PONTOS_DA_BOLINHA = 10


class Jogatina(TelaQualquer):
    para_se_cobrir = True

    def __init__(self, joguinho, fase):
        super().__init__(joguinho)
        self.fase = fase
        self.cenario = FundoTodo(fase.cores_da_fase)
        self.ar = efeitos.Ar(fase.cores_da_fase)
        self.ares_da_fase = {}
        for ato, jeito_do_ar in efeitos.AR_DO_ATO[fase.cores_da_fase.nome].items():
            self.ares_da_fase[ato] = efeitos.Ar(fase.cores_da_fase, jeito_do_ar)
        self.vento = efeitos.Vento()
        self.cor_do_vento = arte.clareia(fase.cores_da_fase.ceu, 0.55)
        mundo.prepara(fase)
        for tipo in COR_DO_ACERTO:
            ui.imagem(f"julgamento_{tipo}.png", 1.25)
        self.cor_da_poeira = arte.clareia(fase.cores_da_fase.chao_topo, 0.3)
        self.luz_da_batida = faz_luz_nas_bordas(fase.cores_da_fase.destaque)
        self.luz_do_dano = faz_luz_nas_bordas(VERMELHO)
        self.menu_da_pausa = Menu([
            Botao("CONTINUAR", LARG_TELA // 2 - 220, 330, 440, 60, VERDE),
            Botao("RECOMECAR", LARG_TELA // 2 - 220, 410, 440, 60, AMARELO),
            Botao("MENU DE FASES", LARG_TELA // 2 - 220, 490, 440, 60, VERMELHO),
        ])
        self.barra_de_cima = BarraDoTopo(760, 12, fase.cores_da_fase.destaque)
        self.barra_de_cima.set_position(250, ALT_TELA - 40)
        self.reinicia()

    def reinicia(self):
        self.leozinho = Leo(self.fase)
        self.ritmo = ContaRitmo(self.fase)
        self.cam = CamQueSegue(self.fase)
        self.em_que_ta = ESPERANDO
        self.espera = 0.0
        self.despertador = Agenda.nova()
        self.animacoes = Curvas.nova()
        self.escuro = 0.0
        self.placa = 0.0
        self.tempo_do_fim = 0.0
        self.tempo_na_pausa = 0.0
        self.volta = None
        self.impacto = Impacto.novo()
        self.tempo_sobrando = 0.0
        self.apertou_agora = False
        self.ta_apertando = False
        self.ja_soltou = False
        self.y_na_tela = self.leozinho.y
        self.resultado_final = None
        self.poeira = efeitos.Poeira()
        self.faiscas = efeitos.UmMonteDeFaisca()
        self.notas_voando = notas.NotasVoando(self.fase.cores_da_fase.destaque)
        self.pauta_do_fundo = notas.Partitura(self.fase)
        self.ecos = efeitos.ArgolasDoEco()
        self.no_ar = Monte(*self.fase.bolinhas)
        self.bolinhas_por_coluna = PorColuna()
        for eco in self.no_ar:
            c0 = int(eco.x // QUADRADO)
            c1 = int((eco.x + eco.width) // QUADRADO)
            self.bolinhas_por_coluna.add(eco, range(c0, c1 + 1))
        self.bolinhas_pegas = Monte()
        self.quando_pegou = None
        self.rastro_do_leo = []
        self.conta_do_rastro = 0
        self.morte = None
        self.pontos_mostrados = 0.0
        self.quando_doeu = None
        self.marco = None
        self.recorde_velho = save.recorde(self.fase.nome_da_musica)["melhor"]
        audio.para_musica()

    def sai_daqui(self):
        audio.para_musica()

    def toca_som(self, nome):
        audio.toca(nome)

    def comeca_de_novo(self):
        audio.para_musica()
        self.joguinho.faz_transicao(self.reinicia)

    def ve_teclas(self):
        if self.em_que_ta == ESPERANDO:
            if InputManager.action_pressed("largada"):
                self.comeca_a_jogar()
            elif InputManager.action_pressed("voltar"):
                self.toca_som("clique")
                self.joguinho.vai_pras_fases()
        elif self.em_que_ta == PAUSADO:
            self.botoes_da_pausa()
        elif self.em_que_ta == RETOMANDO:
            if InputManager.action_pressed("voltar"):
                self.pausa_tudo()
        elif self.em_que_ta == JOGANDO:
            if InputManager.action_pressed("pular") or self.mouse.button_down(self.mouse.LEFT):
                self.apertou_agora = True
            if InputManager.action_pressed("voltar"):
                self.pausa_tudo()
            elif InputManager.action_pressed("recomecar"):
                self.comeca_de_novo()

    def botoes_da_pausa(self):
        escolha = self.menu_da_pausa.ve_teclas(self.mouse, self.toca_som)
        if escolha == "ESC":
            escolha = "CONTINUAR"
        if escolha:
            self.toca_som("clique")
            if escolha == "CONTINUAR":
                self.em_que_ta = RETOMANDO
                self.volta = self.despertador.after(CONTA_ATE * self.tempo_de_cada_numero(), self.volta_pro_menu)
                self.ja_soltou = False
            elif escolha == "RECOMECAR":
                self.comeca_de_novo()
            else:
                self.joguinho.vai_pras_fases()

    def comeca_a_jogar(self):
        self.em_que_ta = JOGANDO
        self.ta_apertando = self.ta_segurando()
        self.apertou_agora = False
        self.ja_soltou = False
        audio.toca_musica(self.fase.nome_da_musica)

    def tempo_de_cada_numero(self):
        return min(0.6, self.fase.tempo_da_batida)

    def numero_da_contagem(self):
        return math.ceil(self.volta.tempo_restante / self.tempo_de_cada_numero())

    def pausa_tudo(self):
        self.em_que_ta = PAUSADO
        self.despertador.limpar()
        self.tempo_na_pausa = self.escuro = 0.0
        self.animacoes.limpar()
        self.animacoes.to(self, "escuro", 1.0, 0.15)
        self.menu_da_pausa.indice = 0
        self.apertou_agora = False
        audio.pausa_musica()
        self.toca_som("clique")

    def volta_pro_menu(self):
        self.em_que_ta = JOGANDO
        self.ta_apertando = self.ta_segurando()
        audio.volta_musica()

    def ta_segurando(self):
        return InputManager.is_active("pular") or self.mouse.button_pressed(self.mouse.LEFT)

    def atualiza(self, dt):
        if self.em_que_ta == PAUSADO:
            self.tempo_na_pausa += dt
            self.animacoes.vai_ate(self.tempo_na_pausa)
            return
        if self.em_que_ta == RETOMANDO:
            antes = self.numero_da_contagem()
            self.despertador.update(dt)
            if self.em_que_ta == RETOMANDO and self.numero_da_contagem() != antes:
                self.toca_som("navegar")
            return
        if self.em_que_ta == ESPERANDO:
            self.espera += dt
            return
        if self.em_que_ta == FIM:
            self.tempo_do_fim += dt
            self.poeira.update(dt)
            self.faiscas.update(dt)
            self.notas_voando.update(dt)
            self.cam.acalma(dt)
            if self.morte is not None:
                self.morte.update(dt)
            self.animacoes.vai_ate(self.tempo_do_fim)
            self.despertador.vai_ate(self.tempo_do_fim)
            return

        segurando = self.ta_segurando()
        if segurando and not self.ta_apertando:
            self.apertou_agora = True
        self.ta_apertando = segurando
        if not segurando:
            self.ja_soltou = True

        self.tempo_sobrando += min(dt, 0.1)
        while self.tempo_sobrando >= TEMPINHO and self.em_que_ta == JOGANDO:
            self.tempo_sobrando -= TEMPINHO
            self.um_passo()
        if self.janela.travou:
            audio.acerta_musica(self.leozinho.tempo + self.tempo_sobrando)
        self.cam.segue_leo(self.fase, self.leozinho, dt)
        self.poeira.update(dt)
        self.faiscas.update(dt)
        self.notas_voando.update(dt)
        self.ecos.update(dt)
        self.conta_do_rastro += 1
        if self.ritmo.combo >= COMBO_DO_RASTRO:
            if self.conta_do_rastro % 3 == 0:
                self.rastro_do_leo.append(self.leozinho.tira_foto(self.y_na_tela))
                del self.rastro_do_leo[:-3]
        elif self.rastro_do_leo and self.conta_do_rastro % 3 == 0:
            self.rastro_do_leo.pop(0)
        d = self.leozinho.y - self.y_na_tela
        if abs(d) < 30:
            self.y_na_tela = self.leozinho.y
        else:
            self.y_na_tela += d * min(1.0, dt * 22)

    def um_passo(self):
        leozinho, ritmo, cores_da_fase = self.leozinho, self.ritmo, self.fase.cores_da_fase
        apertou_agora = self.apertou_agora
        passo(self.fase, leozinho, self.ta_apertando or apertou_agora, apertou_agora,
              self.ta_apertando and self.ja_soltou)
        self.apertou_agora = False

        if leozinho.quebrou_agora:
            tx, ty = leozinho.quebrou_agora
            cx, cy = tx * QUADRADO + QUADRADO * 0.5, ty * QUADRADO + QUADRADO * 0.5
            self.poeira.solta_aqui(cx, cy, cores_da_fase.chao_topo, 10, 2.2)
            self.poeira.solta_aqui(cx, cy, arte.clareia(cores_da_fase.bloco, 0.2), 14, 2.6)
            self.toca_som("quebra")

        pe_x, pe_y = leozinho.x + TAM_DO_LEO * 0.5, leozinho.y + TAM_DO_LEO
        if leozinho.quem_jogou:
            self.faiscas.solta_aqui(pe_x, pe_y - TAM_DO_LEO * 0.5, cores_da_fase.destaque, 16)
            self.ecos.solta_aqui(pe_x, pe_y, cores_da_fase.destaque)
            self.cam.da_tremida(4.0)
        if leozinho.o_que_fez == "pulo":
            self.poeira.solta_aqui(pe_x, pe_y, self.cor_da_poeira, 6, 0.6, joga_pra_tras=1.0)
        elif leozinho.acabou_de_pousar:
            self.poeira.solta_aqui(pe_x, pe_y, self.cor_da_poeira, 9, 1.2)

        if leozinho.o_que_fez:
            self.toca_som(leozinho.quem_jogou or "pulo")
        if apertou_agora or leozinho.pulou_sozinho:
            self.ve_se_acertou()
        self.pega_bolinhas()
        if leozinho.dano_agora:
            self.impacto.flash(VERMELHO, 0.4, leozinho.tempo)
            self.quando_doeu = (leozinho.tempo, leozinho.vidas)
            self.levou_dano()
            ritmo.deu_erro(leozinho.tempo)
        if leozinho.ta_vivo and ritmo.passou_da_hora(leozinho.tempo):
            self.toca_som("erro")
        if not leozinho.ta_vivo:
            self.acaba(False)
        elif leozinho.ganhou:
            self.acaba(True)

    def ve_se_acertou(self):
        leozinho, ritmo, cor = self.leozinho, self.ritmo, self.fase.cores_da_fase.destaque
        tipo = ritmo.toca(leozinho.tempo)
        if tipo is None:
            return
        self.toca_som(tipo)
        x, y = leozinho.x + TAM_DO_LEO * 0.5, leozinho.y + TAM_DO_LEO * 0.4
        if tipo == "perfeito":
            self.ecos.solta_aqui(x, leozinho.y + TAM_DO_LEO, cor)
            self.faiscas.solta_aqui(x, y, cor, 12)
        else:
            self.faiscas.solta_aqui(x, y, AMARELO, 7)
        marco = ritmo.combo % COMBO_BONITO == 0
        self.notas_voando.solta_aqui(x, leozinho.y - 4, tipo == "perfeito", marco)
        if marco:
            self.marco = (leozinho.tempo, ritmo.combo)
            self.faiscas.solta_aqui(x, y, AMARELO, 20)

    def pega_bolinhas(self):
        centro = self.leozinho.centro()
        no_ar = self.bolinhas_por_coluna.em(int(centro.x // QUADRADO))
        eco = no_ar.collided(centro)
        while eco is not None:
            self.no_ar.remove(eco)
            self.bolinhas_por_coluna.remove(eco)
            self.bolinhas_pegas.add(eco)
            self.quando_pegou = self.leozinho.tempo
            self.ritmo.bonus += PONTOS_DA_BOLINHA
            self.faiscas.solta_aqui(eco.ponto.x, eco.ponto.y - TAM_DO_LEO * 0.5,
                                    self.fase.cores_da_fase.destaque, 8)
            self.toca_som("eco")
            eco = no_ar.collided(centro)

    def levou_dano(self):
        self.toca_som("erro")
        self.cam.da_tremida(12.0)

    def acaba(self, ganhou):
        leozinho, r = self.leozinho, self.ritmo
        self.em_que_ta = FIM
        self.ritmo.fecha_conta()
        audio.para_musica()
        self.animacoes.limpar()
        self.escuro = 0.0
        self.animacoes.to(self, "escuro", 1.0, 0.5)
        if ganhou:
            self.toca_som("vitoria")
            self.cam.da_tremida(8.0)
            self.animacoes.to(self, "placa", 1.0, 0.3, inicio=0.1)
            espera = 1.4
        else:
            self.toca_som("morte")
            self.cam.da_tremida(20.0)
            self.morte = efeitos.LeoSumindo(*leozinho.tira_foto(self.y_na_tela))
            self.animacoes.to(self, "placa", 1.0, 0.3, inicio=0.65)
            espera = 1.75
        self.despertador.after(math.nextafter(espera, math.inf), self.vai_pro_resultado)
        progresso = min(100.0, leozinho.x / self.fase.x_do_fim * 100.0)
        recorde_de_antes = save.recorde(self.fase.nome_da_musica)["pontos"]
        pontos = r.pontos + r.bonus
        save.anota(self.fase.nome_da_musica, progresso, ganhou, pontos, r.nota(),
                   r.precisao(), len(self.bolinhas_pegas))
        self.resultado_final = {
            "fase": self.fase, "completou": ganhou, "pontos": pontos,
            "ecos": len(self.bolinhas_pegas), "ecos_total": len(self.fase.bolinhas),
            "nota": r.nota(), "precisao": r.precisao(), "perfeitos": r.perfeitos,
            "bons": r.bons, "erros": r.erros, "combo": r.maior_combo,
            "progresso": progresso, "recorde": pontos > recorde_de_antes,
        }

    def vai_pro_resultado(self):
        self.joguinho.mostra_resultado(self.resultado_final)

    def quanto_pulsa(self):
        if self.em_que_ta == ESPERANDO:
            return 0.0
        altura_na_tela = (self.leozinho.tempo / self.fase.tempo_da_batida) % 1.0
        return max(0.0, 1.0 - altura_na_tela * 3.0)

    def olha_pra_frente(self):
        if self.em_que_ta != JOGANDO or not self.leozinho.ta_vivo or self.leozinho.ganhou:
            return 0.0
        return self.tempo_sobrando * self.fase.velocidade_em(self.leozinho.x)

    def mostra_na_tela(self, tela):
        adiante = self.olha_pra_frente()
        self.leozinho.x += adiante
        try:
            with self.cam.com_tremida(adiante) as cam:
                self.desenha_por_dentro(tela, cam)
        finally:
            self.leozinho.x -= adiante

    def desenha_por_dentro(self, tela, cam):
        pulso = self.quanto_pulsa()
        espera = None
        if self.em_que_ta == ESPERANDO:
            espera = self.espera
        leozinho, fase = self.leozinho, self.fase
        agora = self.espera + leozinho.tempo
        self.cenario.mostra_na_tela(tela, cam, agora, pulso, **cena(fase, leozinho.x))
        self.ar.draw(tela, cam, agora)
        ato = fase.ato(leozinho.x)
        if ato in self.ares_da_fase:
            self.ares_da_fase[ato].draw(tela, cam, agora)
        ta_correndo = fase.velocidade_em(leozinho.x) > fase.vx * 1.1
        self.vento.mostra_na_tela(tela, leozinho.tempo, ta_correndo, self.cor_do_vento, 1.0 / 60.0)
        with cam.usando_essa_cam():
            self.desenha_mundo(tela, cam, pulso, espera)
        pega_vinheta().draw(tela)
        self.pinta_bordas(tela, pulso)
        self.desenha_hud(tela, pulso)
        self.mostra_letreiro(tela)
        if self.em_que_ta == ESPERANDO and self.espera > 0.6 and int(self.espera * 1.6) % 4 != 3:
            ui.dicas(tela, (("ESPACO", "COMECA"),), ALT_TELA * 0.62)
        if self.em_que_ta == PAUSADO:
            ui.escurece_tela(tela, int(170 * ui.suaviza(self.escuro)))
            ui.escreve(tela, "PAUSADO", 56, LARG_TELA // 2, 200, self.fase.cores_da_fase.destaque)
            self.menu_da_pausa.mostra_na_tela(tela)
            ui.dicas(tela, (("SETAS", "ESCOLHEM"), ("ENTER", "CONFIRMA"), ("ESC", "CONTINUA")), 612)
        elif self.em_que_ta == RETOMANDO:
            quanto_falta = self.volta.tempo_restante / (CONTA_ATE * self.tempo_de_cada_numero())
            ui.escurece_tela(tela, int(170 * quanto_falta))
            n = max(1, self.numero_da_contagem())
            ui.escreve(tela, str(n), 96, LARG_TELA // 2, ALT_TELA * 0.4,
                       self.fase.cores_da_fase.destaque, borda_cor=CONTORNO)
        elif self.em_que_ta == FIM:
            ganhou = self.resultado_final["completou"]
            ui.escurece_tela(tela, int(120 * self.escuro))
            if self.morte is not None:
                with cam.usando_essa_cam():
                    self.morte.draw(tela)
            k = ui.suaviza(self.placa)
            if k > 0.0:
                if ganhou:
                    texto = ui.texto("FASE COMPLETA", 64, VERDE, CONTORNO)
                else:
                    texto = ui.texto("FIM DE JOGO", 64, VERMELHO, CONTORNO)
                if k < 1.0:
                    texto = arte.fantasma(texto, int(255 * k) // 16 * 16)
                tela.blit(texto, texto.get_rect(center=(LARG_TELA // 2, int(ALT_TELA * 0.42))))

    def desenha_mundo(self, tela, cam, pulso, espera):
        agora = self.espera + self.leozinho.tempo
        self.pauta_do_fundo.mostra_na_tela(tela, cam, agora)
        self.ecos.draw(tela)
        mundo.desenha_bolinhas(tela, self.fase, cam, self.no_ar, agora)
        rastro_do_leo = ()
        if self.em_que_ta == JOGANDO:
            rastro_do_leo = self.rastro_do_leo
        mundo.mostra_na_tela(tela, self.fase, self.leozinho, cam, pulso, espera, self.y_na_tela,
                             com_heroi=self.morte is None, rastro_do_leo=rastro_do_leo)
        self.poeira.draw(tela)
        self.faiscas.draw(tela)
        self.notas_voando.draw(tela)
        for dx, dy, texto in self.fase.dicas:
            if -200 <= cam.transform_x(dx) <= LARG_TELA + 200:
                ui.escreve(tela, texto, 18, int(cam.transform_x(dx)), int(cam.transform_y(dy)),
                           BRANCO, borda_cor=CONTORNO)

    def mostra_letreiro(self, tela):
        if self.em_que_ta == ESPERANDO:
            k = ui.suaviza((self.espera - 0.25) / 0.5)
        elif self.em_que_ta == JOGANDO and self.leozinho.tempo < 0.7:
            k = 1.0 - ui.suaviza(self.leozinho.tempo / 0.7)
        else:
            return
        if k <= 0.0:
            return
        alfa = int(255 * k) // 16 * 16
        y = ALT_TELA * 0.24
        f = self.fase
        linhas = ((ui.texto(f.nome, 48, f.cores_da_fase.destaque, CONTORNO), 0),
                  (ui.texto(f.dificil_quanto, 20, COR_DA_DIFICULDADE[f.dificil_quanto], CONTORNO), 48),
                  (ui.texto(f.info_da_musica.creditos, 18, CINZA, CONTORNO), 80))
        for img, dy in linhas:
            if alfa < 255:
                img = arte.fantasma(img, alfa)
            tela.blit(img, img.get_rect(center=(LARG_TELA // 2, int(y + dy))))

    def pinta_bordas(self, tela, pulso):
        luz = self.luz_do_dano
        alfa = int(200 * self.impacto.quanto_clarao(self.leozinho.tempo))
        if alfa == 0 and self.em_que_ta == JOGANDO and pulso > 0.05:
            luz = self.luz_da_batida
            if int(self.leozinho.tempo / self.fase.tempo_da_batida + 0.01) % 4 == 0:
                alfa = int(70 * pulso)
            else:
                alfa = int(32 * pulso)
        if alfa > 0:
            for img in luz:
                img.set_transparency(alfa)
                img.draw(tela)

    def desenha_hud(self, tela, pulso):
        self.mostra_vidas(tela, pulso)
        self.mostra_bolinhas(tela)
        self.mostra_pontos(tela)
        self.mostra_se_acertou(tela)
        self.mostra_barra(tela, pulso)

    def mostra_vidas(self, tela, pulso):
        leozinho = self.leozinho
        for i in range(QTD_VIDAS):
            ta_batendo = i == leozinho.vidas - 1 and pulso > 0.5
            coracao = arte.pega_coracao(i < leozinho.vidas, ta_batendo)
            coracao.bota_no_meio(28 + i * 46 + 18, 46)
            coracao.draw(tela)
        if self.quando_doeu is not None:
            t = leozinho.tempo - self.quando_doeu[0]
            i = self.quando_doeu[1]
            if 0.0 <= t < 0.45 and i < QTD_VIDAS:
                k = t / 0.45
                coracao = arte.pega_coracao(True, True)
                coracao.set_transparency(max(16, int(255 * (1.0 - k)) // 16 * 16))
                coracao.bota_no_meio(28 + i * 46 + 18, 46 - int(10 * k))
                coracao.draw(tela)

    def mostra_bolinhas(self, tela):
        cor = self.fase.cores_da_fase.destaque
        ui.escreve(tela, self.fase.nome, 18, 28, 92, cor, "esquerda", CONTORNO)
        tam, cor_texto, sobe = 18, cor, 0
        if self.quando_pegou is not None and 0.0 <= self.leozinho.tempo - self.quando_pegou < 0.18:
            tam, cor_texto, sobe = 20, BRANCO, 3
        tela.blit(mundo.icone_da_bolinha(cor), (28, 108 - sobe))
        texto = f"{len(self.bolinhas_pegas)}/{len(self.fase.bolinhas)}"
        ui.escreve(tela, texto, tam, 62, 122, cor_texto, "esquerda", CONTORNO)

    def mostra_pontos(self, tela):
        r, destaque = self.ritmo, self.fase.cores_da_fase.destaque
        total = r.pontos + r.bonus
        if self.pontos_mostrados < total:
            anda = max(1.0, (total - self.pontos_mostrados) * 0.25)
            self.pontos_mostrados = min(float(total), self.pontos_mostrados + anda)
        cor = BRANCO
        if self.pontos_mostrados < total:
            cor = destaque
        ui.escreve(tela, f"{int(self.pontos_mostrados):05d}", 44, LARG_TELA - 28, 50,
                   cor, "direita", CONTORNO)
        if r.combo < 3:
            return
        tam, cor = 30, AMARELO
        if r.combo >= 25:
            tam += 4
        if r.combo >= 50:
            tam += 4
        if self.marco is not None and self.marco[1] == r.combo:
            k = (self.leozinho.tempo - self.marco[0]) / 0.6
            if k < 1.0:
                tam += int(16 * (1.0 - ui.suaviza(k)))
                cor = destaque
                ui.escreve(tela, "SEQUENCIA!", 16, LARG_TELA - 28, 138, destaque,
                           "direita", CONTORNO)
        ui.escreve(tela, f"x{r.combo}", tam, LARG_TELA - 28, 100, cor, "direita", CONTORNO)

    def mostra_se_acertou(self, tela):
        j = self.ritmo.ultimo
        if j is None or self.em_que_ta != JOGANDO or self.leozinho.tempo - j.tempo >= 0.7:
            return
        k = 1.0 - (self.leozinho.tempo - j.tempo) / 0.7
        y = int(ALT_TELA * 0.28 - (1.0 - k) * 30)
        escala, tam = 1, 30
        if k > 0.85:
            escala, tam = 1.25, 34
        alfa = 255
        if k < 0.25:
            alfa = int(255 * k / 0.25) // 16 * 16
        letreiro = ui.objeto(f"julgamento_{j.tipo}.png", escala)
        letreiro.set_transparency(alfa)
        letreiro.bota_no_meio(LARG_TELA // 2, y)
        letreiro.draw(tela)
        pontos = Desenho(ui.texto(f"+{j.pontos}", tam, COR_DO_ACERTO[j.tipo], CONTORNO))
        pontos.set_transparency(alfa)
        pontos.bota_no_meio(LARG_TELA // 2, y + letreiro.height // 2 + 22)
        pontos.draw(tela)

    def mostra_barra(self, tela, pulso):
        barra_de_cima = self.barra_de_cima
        bx, by, bw, bh = barra_de_cima.x, barra_de_cima.y, barra_de_cima.width, barra_de_cima.height
        altura_na_tela = min(1.0, self.leozinho.x / self.fase.x_do_fim)
        barra_de_cima.set_value(altura_na_tela)
        barra_de_cima.draw(tela)
        melhor = self.recorde_velho / 100.0
        if 0.0 < melhor < 1.0:
            mx = int(bx + bw * melhor)
            cor = BRANCO
            if altura_na_tela >= melhor:
                cor = AMARELO
            pygame.draw.rect(tela, CONTORNO, (mx - 2, by - 12, 5, bh + 16))
            pygame.draw.rect(tela, cor, (mx - 1, by - 11, 3, bh + 14))
            pygame.draw.rect(tela, CONTORNO, (mx + 1, by - 14, 10, 8))
            pygame.draw.rect(tela, cor, (mx + 2, by - 13, 8, 6))
        px, py = bx + bw + 22, by + bh // 2
        rosto = arte.retrato(CONTORNO)
        tela.blit(rosto, (int(bx + bw * altura_na_tela - rosto.get_width() / 2),
                          by + 4 - rosto.get_height() - int(4 * pulso)))
        ui.escreve(tela, f"{altura_na_tela * 100:.0f}%", 22, px, py, CINZA, "esquerda", CONTORNO)
