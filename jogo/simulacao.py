import math

from PPlay.physics import KinematicBody, Physics
from PPlay.window import Window

from .config import (TEMPINHO, QUADRADO, TAM_DO_LEO, LARG_DO_PE, QUINA, PULINHO,
                     CORTA_O_PULO, PULO_ATRASADO, PULO_ADIANTADO, TEMPO_SEM_LEVAR_DANO)
from .janela import Janelona

ALTURA_DA_MOLA = 6.0

APOIO = (TAM_DO_LEO - LARG_DO_PE) * 0.5
SKIN = 0.001


def colunas_dele(x):
    return int((x + APOIO) // QUADRADO), int((x + APOIO + LARG_DO_PE - SKIN) // QUADRADO)


def linhas_dele(y):
    return range(int(y // QUADRADO), int((y + TAM_DO_LEO - SKIN) // QUADRADO) + 1)


def ta_solido(fase, leozinho, c, ty):
    return (c, ty) in fase.solidos and (c, ty) not in leozinho.blocos_quebrados


def mola_embaixo(fase, leozinho):
    for mola in fase.molas:
        if mola.x <= leozinho.x < mola.fim:
            return mola
    return None


def ta_livre(fase, leozinho, x, y):
    for c in colunas_dele(x):
        for ty in linhas_dele(y):
            if ta_solido(fase, leozinho, c, ty):
                return False
    return True


def chao_seguro(fase, leozinho):
    c0, c1 = colunas_dele(leozinho.x)
    niveis = [fase.chao_por_coluna[c] for c in (c0, c1) if c in fase.chao_por_coluna]
    if not niveis:
        return fase.altura_do_chao(c1) * QUADRADO
    return min(niveis) * QUADRADO


def bota_de_volta(fase, leozinho):
    leozinho.y = chao_seguro(fase, leozinho) - TAM_DO_LEO
    leozinho.vy = 0.0
    leozinho.body.jump_buffer_timer = 0.0
    leozinho.ta_pulando = False


def machuca_leo(fase, leozinho, por_que, volta_pro_chao=True):
    if leozinho.tempo_invencivel <= 0.0:
        leozinho.vidas -= 1
        leozinho.dano_agora = por_que
        leozinho.tempo_invencivel = TEMPO_SEM_LEVAR_DANO * fase.tempo_da_batida
        if leozinho.vidas <= 0:
            leozinho.ta_vivo = False
            return True
    if volta_pro_chao:
        bota_de_volta(fase, leozinho)
    return False


def mata(leozinho, por_que):
    leozinho.vidas = 0
    leozinho.ta_vivo = False
    leozinho.dano_agora = por_que


class FisicaDoJogo(Physics):
    def __init__(self, fase):
        super().__init__(gravidade=fase.gravidade, vel_terminal=fase.forca_do_pulo * 1.5)
        self.fase = fase
        self.SKIN = SKIN
        self.PASSO_MINIMO = math.inf

    def processar_movimento(self, leo, solidos):
        pes = leo.y + TAM_DO_LEO
        vx, leo.vx = leo.vx, 0.0
        super().processar_movimento(leo, ())
        leo.vx = vx
        fase = self.fase
        c0, c1 = colunas_dele(leo.x)
        if leo.vy > 0.0:
            ty = int((leo.y + TAM_DO_LEO - self.SKIN) // QUADRADO)
            pontes = fase.pontezinhas.quadradinhos_ocupados
            ta_firme = ta_solido(fase, leo, c0, ty) or ta_solido(fase, leo, c1, ty)
            if pes <= ty * QUADRADO + 0.5 and ((c0, ty) in pontes or (c1, ty) in pontes):
                ta_firme = True
            if ta_firme:
                leo.y = ty * QUADRADO - TAM_DO_LEO
                leo.vy = 0.0
                leo.no_chao = True
        elif leo.vy < 0.0:
            ty = int(leo.y // QUADRADO)
            if ta_solido(fase, leo, c0, ty) or ta_solido(fase, leo, c1, ty):
                leo.y = (ty + 1) * QUADRADO
                leo.vy = 0.0


class FisicaDoLeo(KinematicBody):
    def __init__(self, leo, fisica):
        super().__init__(leo, fisica)
        fase = fisica.fase
        self.coyote_max = PULO_ATRASADO
        self.jump_buffer_max = PULO_ADIANTADO * fase.tempo_da_batida
        self.pulo = fase.forca_do_pulo
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.ta_apertando = self.apertou_agora = False

    def escuta(self, ta_apertando, apertou_agora):
        self.ta_apertando, self.apertou_agora = ta_apertando, apertou_agora

    def update(self, solidos):
        dt = Window.get_instance().delta_time()
        self.coyote_timer = max(0.0, self.coyote_timer - dt)
        if self.apertou_agora:
            self.jump_buffer_timer = self.jump_buffer_max
        else:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
        self.anda_pra_frente()
        if self.sprite.ta_vivo:
            self.corta_pulo()
            self.cai_no_chao(solidos)

    def anda_pra_frente(self):
        leozinho, fase = self.sprite, self.engine.fase
        if not leozinho.ta_preso:
            leozinho.vx = fase.velocidade_em(leozinho.x)
            leozinho.move_x(leozinho.vx)
        c0, coluna_da_direita = colunas_dele(leozinho.x)
        onde_bateu = []
        for ty in linhas_dele(leozinho.y):
            if ta_solido(fase, leozinho, coluna_da_direita, ty):
                onde_bateu.append(ty)
        if not onde_bateu:
            return
        topo = min(onde_bateu) * QUADRADO
        if leozinho.y + TAM_DO_LEO - topo <= QUINA and ta_livre(fase, leozinho, leozinho.x, topo - TAM_DO_LEO):
            leozinho.y = topo - TAM_DO_LEO
            leozinho.vy = min(leozinho.vy, 0.0)
        elif all((coluna_da_direita, ty) in fase.torres.quadradinhos_ocupados for ty in onde_bateu):
            for ty in onde_bateu:
                leozinho.blocos_quebrados.add((coluna_da_direita, ty))
            leozinho.quebrou_agora = (coluna_da_direita, onde_bateu[0])
            machuca_leo(fase, leozinho, "bloco", volta_pro_chao=False)
        elif c0 not in fase.chao_por_coluna:
            leozinho.ta_preso = True
            leozinho.x = coluna_da_direita * QUADRADO - APOIO - LARG_DO_PE
            self.jump_buffer_timer = 0.0
        else:
            machuca_leo(fase, leozinho, "parede")

    def corta_pulo(self):
        leozinho, fase = self.sprite, self.engine.fase
        if not leozinho.ta_pulando or leozinho.ja_cortou or leozinho.vy >= 0.0:
            return
        if self.ta_apertando or fase.sem_segurar:
            return
        if leozinho.y_de_onde_pulou - leozinho.y >= fase.altura_pra_cortar:
            self.baixa_o_pulo()
            leozinho.ja_cortou = True

    def baixa_o_pulo(self):
        leozinho, fisica = self.sprite, self.engine
        subiu = leozinho.y_de_onde_pulou - leozinho.y
        alvo = max(fisica.fase.altura_do_pulo * PULINHO,
                   subiu + (CORTA_O_PULO * leozinho.vy) ** 2 / (2.0 * fisica.gravidade))
        quanto_resta = leozinho.quando_acaba_o_pulo - leozinho.tempo
        if quanto_resta <= 0.0 or alvo <= subiu:
            return
        k = math.sqrt((alvo - subiu) / alvo)
        tempo_ate_o_alto = quanto_resta * k / (1.0 + k)
        fisica.gravidade = 2.0 * alvo / (quanto_resta - tempo_ate_o_alto) ** 2
        leozinho.vy = -fisica.gravidade * tempo_ate_o_alto

    def cai_no_chao(self, solidos):
        leozinho, fisica = self.sprite, self.engine
        tava_no_chao = leozinho.no_chao
        fisica.processar_movimento(leozinho, solidos)
        if leozinho.no_chao:
            self.coyote_timer = self.coyote_max
            fisica.gravidade = fisica.fase.gravidade
            leozinho.ta_pulando = False
            leozinho.acabou_de_pousar = not tava_no_chao
            if leozinho.acabou_de_pousar:
                leozinho.pouso = leozinho.tempo

    def ta_apoiado(self):
        return self.sprite.no_chao or self.coyote_timer > 0.0

    def salta(self, forca):
        leozinho = self.sprite
        leozinho.no_chao = True
        leozinho.pular(forca)
        self.jump_buffer_timer = 0.0
        leozinho.o_que_fez = "pulo"
        leozinho.pulo = leozinho.tempo


def passo(fase, leozinho, ta_apertando, apertou_agora, repetir):
    dt = TEMPINHO
    if not leozinho.ta_vivo or leozinho.ganhou:
        return
    leozinho.tempo += dt
    leozinho.o_que_fez = leozinho.dano_agora = leozinho.quebrou_agora = leozinho.quem_jogou = None
    leozinho.pulou_sozinho = leozinho.acabou_de_pousar = False
    leozinho.tempo_invencivel = max(0.0, leozinho.tempo_invencivel - dt)
    if apertou_agora:
        leozinho.hora_do_toque = leozinho.tempo

    leozinho.body.escuta(ta_apertando, apertou_agora)
    with Janelona.com_esse_tempo(dt):
        leozinho.update_physics(fase.solidos)
    if not leozinho.ta_vivo:
        return

    if leozinho.y > fase.y_do_abismo:
        mata(leozinho, "abismo")
        return
    ve_se_bateu(fase, leozinho)
    if not leozinho.ta_vivo:
        return
    tenta_pular(fase, leozinho, repetir and not fase.sem_segurar, dt)
    if leozinho.x >= fase.x_do_fim:
        leozinho.ganhou = True


def ve_se_bateu(fase, leozinho):
    corpo = leozinho.corpo()
    n_colunas = range(int(corpo.x // QUADRADO), int((corpo.x + corpo.width) // QUADRADO) + 1)
    for tx in n_colunas:
        perigo = fase.perigos_por_coluna.em(tx).collided(corpo)
        if perigo is not None:
            if perigo.mata_na_hora:
                mata(leozinho, "fosso")
                return
            if machuca_leo(fase, leozinho, "perigo"):
                return
        if leozinho.dano_agora:
            break
    if leozinho.tempo_invencivel > 0.0:
        return
    for tx in n_colunas:
        voador = fase.voadores_por_coluna.em(tx).collided(corpo)
        if voador is not None:
            machuca_leo(fase, leozinho, voador.tipo, volta_pro_chao=False)
            return


def tenta_pular(fase, leozinho, repetir, dt):
    corpo = leozinho.body
    guardado = corpo.jump_buffer_timer > 0.0
    if not corpo.ta_apoiado():
        if guardado and not leozinho.ta_preso:
            pula_na_luz(fase, leozinho)
        return
    mola = mola_embaixo(fase, leozinho)
    foi_lancado = False
    if mola is not None and leozinho.no_chao:
        foi_lancado = leozinho.x + fase.velocidade_em(leozinho.x) * dt >= mola.fim
    if leozinho.ta_preso or not (guardado or repetir or foi_lancado):
        return
    atraso = 0.0
    if guardado:
        atraso = max(0.0, min(leozinho.tempo - leozinho.hora_do_toque, 0.3 * fase.tempo_do_pulo))
    altura = fase.altura_do_pulo
    duracao = fase.tempo_do_pulo - atraso
    if mola is not None:
        altura = ALTURA_DA_MOLA * QUADRADO
        duracao = 2.0 * fase.tempo_do_pulo - atraso
        leozinho.quem_jogou = "mola"
    corpo.engine.gravidade = 8.0 * altura / duracao ** 2
    leozinho.pulou_sozinho = not guardado and not foi_lancado
    leozinho.ta_pulando = mola is None
    leozinho.ja_cortou = mola is not None
    leozinho.y_de_onde_pulou = leozinho.y
    leozinho.quando_acaba_o_pulo = leozinho.tempo + duracao
    corpo.coyote_timer = 0.0
    corpo.salta(4.0 * altura / duracao)


def pula_na_luz(fase, leozinho):
    orbe = leozinho.orbes.collided(leozinho.centro())
    if orbe is None:
        return
    leozinho.orbes.remove(orbe)
    leozinho.body.engine.gravidade = fase.gravidade
    leozinho.ta_pulando = False
    leozinho.ja_cortou = True
    leozinho.quem_jogou = "orbe"
    leozinho.body.salta(leozinho.body.pulo)
