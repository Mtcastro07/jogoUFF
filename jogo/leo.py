import pygame
from PPlay.sprite import Sprite

from . import arte
from .animacao import Animadinho
from .config import (QUADRADO, TAM_DO_LEO, LARG_DO_CORPO, ALT_DO_CORPO, CORPO_PRA_FRENTE, FOLGA_DO_PE,
                     FOLGA_DO_PE_NO_AR, IMAGEM_DO_LEO, QTD_VIDAS)
from .grupo import Monte
from .objetos import CaixaDoLeo, Ponto
from .simulacao import FisicaDoLeo, FisicaDoJogo

TEMPO_DO_POUSO = 0.07
QUANTO_ESTICA = 0.10
QUANTO_AMASSA = 0.12


class Bonequinho(Animadinho, Sprite):
    def __init__(self):
        super().__init__(IMAGEM_DO_LEO, 1)
        self.pose("parado", 0)

    def pose(self, nome, i):
        figurinha = arte.todas_as_poses[nome]
        self.quadros = figurinha.quadros
        self.total_frames = figurinha.total_frames
        self.set_curr_frame(i)

    def pega_figura(self):
        q = self.imagem_dele()
        sx, sy = self.get_scale()
        if sx == 1.0 and sy == 1.0:
            return q, arte.CENTRO, arte.PES
        return arte.esticado(q, sx, sy), arte.CENTRO * sx, arte.PES * sy

    def bota_em_pe(self, tela, cx, pes):
        q, ax, ay = self.pega_figura()
        tela.blit(q, (int(cx - ax), int(pes - ay)))

    def draw(self, tela):
        self.bota_em_pe(tela, self.x, self.y)


class Leo(Bonequinho):
    def __init__(self, fase):
        super().__init__()
        self.fase = fase
        self.width = self.height = TAM_DO_LEO
        self.set_position(0.0, fase.y_do_chao - TAM_DO_LEO)
        self.vx, self.vy = fase.vx, 0.0
        self.no_chao = True
        self.setup_physics(FisicaDoJogo(fase))
        self.rodando = False
        self.tempo = 0.0
        self.vidas = QTD_VIDAS
        self.tempo_invencivel = 0.0
        self.ta_vivo = True
        self.ganhou = False
        self.blocos_quebrados = set()
        self.ta_preso = False
        self.hora_do_toque = -1.0
        self.ta_pulando = False
        self.y_de_onde_pulou = 0.0
        self.ja_cortou = False
        self.quando_acaba_o_pulo = 0.0
        self.o_que_fez = None
        self.pulou_sozinho = False
        self.dano_agora = None
        self.quebrou_agora = None
        self.acabou_de_pousar = False
        self.pouso = -1.0
        self.pulo = -1.0
        self.quem_jogou = None
        self.orbes = Monte(*fase.orbes)
        self.corpo_dele = CaixaDoLeo(0, 0, LARG_DO_CORPO, ALT_DO_CORPO)
        self.meio_dele = Ponto()

    def setup_physics(self, fisica):
        self.body = FisicaDoLeo(self, fisica)

    def corpo(self):
        folga = FOLGA_DO_PE_NO_AR
        if self.no_chao:
            folga = FOLGA_DO_PE
        x = self.x + (TAM_DO_LEO - LARG_DO_CORPO) * 0.5 + CORPO_PRA_FRENTE
        y = self.y + TAM_DO_LEO - folga - ALT_DO_CORPO
        self.corpo_dele.set_position(x, y)
        self.corpo_dele.nao_machuca = self.tempo_invencivel > 0.0
        return self.corpo_dele

    def centro(self):
        self.meio_dele.set_position(self.x + TAM_DO_LEO * 0.5, self.y + TAM_DO_LEO * 0.5)
        return self.meio_dele

    def bota_roupa(self, espera=None):
        fase = self.fase
        self.set_scale(*self.estica_e_amassa(espera))
        if espera is not None:
            self.pose("parado", espera * 6)
        elif not self.no_chao:
            self.pose(*arte.quadro_do_pulo(self.vy, fase.forca_do_pulo, self.tempo))
        elif self.tempo - self.pouso < TEMPO_DO_POUSO:
            self.pose("pouso", 0)
        else:
            self.pose("corre", self.tempo / fase.tempo_da_batida * arte.quantos_quadros("corre"))

    def tira_foto(self, y):
        self.bota_roupa()
        q, ax, ay = self.pega_figura()
        return q, int(self.x + TAM_DO_LEO * 0.5 - ax), int(y + TAM_DO_LEO - ay)

    def draw(self, tela, cam, espera, y):
        if self.ta_vivo and self.tempo_invencivel > 0.0 and int(self.tempo * 20) % 2 == 0:
            return
        self.bota_roupa(espera)
        cx = cam.transform_x(self.x + TAM_DO_LEO * 0.5)
        self.desenha_sombra(tela, cx, cam, y)
        self.bota_em_pe(tela, cx, cam.transform_y(y + TAM_DO_LEO))

    def desenha_sombra(self, tela, cx, cam, y):
        chao = self.fase.chao_por_coluna.get(int((self.x + TAM_DO_LEO * 0.5) // QUADRADO))
        if chao is None or y + TAM_DO_LEO > chao * QUADRADO + 1:
            return
        dist = min(1.0, max(0.0, (chao * QUADRADO - y - TAM_DO_LEO) / (QUADRADO * 4)))
        larg = int(TAM_DO_LEO * (1.1 - 0.5 * dist))
        sombra = pygame.Surface((larg, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, int(120 * (1 - dist * 0.6))), (0, 0, larg, 8))
        tela.blit(sombra, (cx - larg // 2, cam.transform_y(chao * QUADRADO) - 4))

    def estica_e_amassa(self, espera):
        if espera is not None:
            return 1.0, 1.0
        t = self.tempo - self.pulo
        if 0.0 <= t < QUANTO_ESTICA and not self.no_chao:
            k = 1.0 - t / QUANTO_ESTICA
            return redondinho(1.0 - 0.14 * k), redondinho(1.0 + 0.16 * k)
        t = self.tempo - self.pouso
        if 0.0 <= t < QUANTO_AMASSA and self.no_chao:
            k = 1.0 - t / QUANTO_AMASSA
            return redondinho(1.0 + 0.16 * k), redondinho(1.0 - 0.14 * k)
        return 1.0, 1.0


def redondinho(k):
    return round(k * 20) / 20
