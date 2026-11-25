import math

import pygame
from PPlay.collision import Collision
from PPlay.gameobject import GameObject
from PPlay.point import Point

from . import aparencia, arte
from .config import QUADRADO, TAM_DO_LEO, LARG_TELA


class OQueTaVendo:
    def __init__(self, tela, cores_da_fase, cam, tempo, pulso=0.0, leo=None):
        self.tela = tela
        self.cores_da_fase = cores_da_fase
        self.cam = cam
        self.tempo = tempo
        self.pulso = pulso
        self.leo = leo
        self.cor_do_brilho = arte.clareia(cores_da_fase.perigo, 0.3)

    def ta_perto(self, x, antes, depois=0):
        return self.cam.x - antes <= x <= self.cam.x + LARG_TELA + depois


class Coisa(GameObject):
    o_que_ta_vendo = None

    def __init__(self, x=0, y=0, width=0, height=0):
        super().__init__()
        self.set_position(x, y)
        self.width, self.height = width, height


class Ponto(Coisa):
    pass


class CaixaDoLeo(Coisa):
    nao_machuca = False

    def collided(self, perigo):
        if self.nao_machuca and not perigo.mata_na_hora:
            return False
        return perigo.machuca(self)


class CoisaQueMachuca(Coisa):
    def __init__(self, x, y, width, height, quantidade=1, mata_na_hora=False):
        super().__init__(x, y, width, height)
        self.quantidade = quantidade
        self.mata_na_hora = mata_na_hora
        self.qual_desenho = 0
        self.perfil = []

    def machuca(self, corpo):
        if not Collision.collided(corpo, self):
            return False
        a = max(0, int(corpo.x - self.x))
        b = min(len(self.perfil), math.ceil(corpo.x + corpo.width - self.x))
        if a >= b:
            return False
        return corpo.y + corpo.height > self.y + min(self.perfil[a:b])

    def draw(self):
        v = self.o_que_ta_vendo
        figurinha = arte.caco(self.quantidade, v.cores_da_fase.nome, self.qual_desenho)
        atrasinho = (int(self.x // QUADRADO) * 2654435761 >> 11) % 16
        figurinha.set_curr_frame(int(v.tempo * 12) + atrasinho)
        figurinha.set_position(self.x, self.y)
        aparencia.desenha_com_brilho(v.tela, figurinha, v.cor_do_brilho)


class CoisaQueVoa(Coisa):
    tipo = None
    mata_na_hora = False

    def __init__(self, centro, chao, tamanhos):
        larg, pe, topo = tamanhos
        super().__init__(centro - larg * 0.5, chao - topo, larg, topo - pe)

    def machuca(self, corpo):
        return Collision.collided(corpo, self)


class Bichos(CoisaQueVoa):
    tipo = "enxame"

    def draw(self):
        v = self.o_que_ta_vendo
        if not v.ta_perto(self.x, QUADRADO):
            return
        figurinha = arte.peca("enxame", v.cores_da_fase.nome)
        figurinha.set_curr_frame(v.tempo * 14 + self.x * 0.07)
        y = self.y + self.height * 0.5 - figurinha.height * 0.5
        y += math.sin(v.tempo * 4.3 + self.x * 0.05) * 3.0
        figurinha.set_position(self.x + self.width * 0.5 - figurinha.width * 0.5, y)
        aparencia.desenha_com_brilho(v.tela, figurinha, v.cor_do_brilho)


class CoisaPendurada(CoisaQueVoa):
    tipo = "pingente"

    def draw(self):
        v = self.o_que_ta_vendo
        if not v.ta_perto(self.x, 2 * QUADRADO, QUADRADO):
            return
        figurinha = arte.peca("pingente", v.cores_da_fase.nome)
        figurinha.set_curr_frame(v.tempo * 6 + self.x * 0.01)
        figurinha.set_position(self.x + self.width * 0.5 - figurinha.width * 0.5,
                               self.y + self.height - figurinha.height)
        aparencia.desenha_com_brilho(v.tela, figurinha, v.cor_do_brilho)


class Mola(Coisa):
    def __init__(self, x, fim, chao):
        super().__init__(x, chao, fim - x, 0)
        self.fim = fim

    def draw(self):
        v = self.o_que_ta_vendo
        tela, cor = v.tela, v.cores_da_fase.destaque
        a, b = v.cam.transform_x(self.x + 8), v.cam.transform_x(self.fim + TAM_DO_LEO - 8)
        if b < 0 or a > LARG_TELA:
            return
        sy = v.cam.transform_y(self.y)
        larg = int(b - a)
        alto = 8 + int(4 * v.pulso)
        pygame.draw.rect(tela, arte.escurece_cor(cor, 0.5), (a - 3, sy - alto - 3, larg + 6, alto + 6))
        pygame.draw.rect(tela, cor, (a, sy - alto, larg, alto))
        pygame.draw.rect(tela, (255, 255, 255), (a, sy - alto, larg, 3))
        seta = aparencia.setinha_pra_cima(arte.clareia(cor, 0.6))
        n = max(2, larg // 44)
        for k in range(n):
            cx = a + (k + 0.5) * larg / n
            for passo in range(3):
                sobe = (v.tempo * 60.0 + passo * 16) % 48
                alfa = int(255 * (1.0 - sobe / 48.0)) // 32 * 32 + 31
                img = arte.fantasma(seta, alfa)
                tela.blit(img, (cx - seta.get_width() // 2, sy - alto - 14 - sobe))


class CoisaDePegar(Coisa):
    def __init__(self, x, y, distancia_x, distancia_y):
        esq, larg = self.faixa(x, distancia_x)
        topo, alto = self.faixa(y, distancia_y)
        super().__init__(esq, topo, larg, alto)
        self.ponto = Point(x, y)

    def faixa(self, meio, alcance):
        inicio = math.nextafter(meio - alcance, -math.inf)
        fim = math.nextafter(meio + alcance, math.inf)
        tamanho = fim - inicio
        while inicio + tamanho < fim:
            tamanho = math.nextafter(tamanho, math.inf)
        return inicio, tamanho


class Orbe(CoisaDePegar):
    def draw(self):
        v = self.o_que_ta_vendo
        if not v.ta_perto(self.ponto.x, QUADRADO * 2, QUADRADO * 2):
            return
        cor = v.cores_da_fase.destaque
        if self in v.leo.orbes:
            img = aparencia.anel(cor, 6 if v.pulso > 0.5 else 5, 2)
        else:
            img = arte.fantasma(aparencia.anel(arte.escurece_cor(cor, 0.4), 5, 1), 96)
        v.tela.blit(img, (v.cam.transform_x(self.ponto.x) - img.get_width() // 2,
                          v.cam.transform_y(self.ponto.y) - img.get_height() // 2))


ATE_ONDE_PEGA = (22, 34)


class Bolinha(CoisaDePegar):
    def __init__(self, x, y, alto):
        super().__init__(x, y - TAM_DO_LEO * 0.5, *ATE_ONDE_PEGA)
        self.ponto = Point(x, y)
        self.alto = alto
        self.numero = 0

    def draw(self):
        v = self.o_que_ta_vendo
        x, y = self.ponto.x, self.ponto.y
        if not v.ta_perto(x, QUADRADO, QUADRADO):
            return
        n_quadro = (int(v.tempo * 6) + self.numero * 3) % 8
        figurinha = aparencia.eco(v.cores_da_fase.destaque, self.alto)
        if n_quadro == 0:
            figurinha.set_curr_frame(2)
        elif n_quadro == 4:
            figurinha.set_curr_frame(1)
        else:
            figurinha.set_curr_frame(0)
        dy = math.sin(v.tempo * 3.0 + self.numero * 1.7) * 3.0
        figurinha.set_position(x - figurinha.width // 2, y - TAM_DO_LEO * 0.5 - figurinha.height // 2 + dy)
        figurinha.draw(v.tela)

    def ordem_dela(self):
        return self.ponto.x, self.ponto.y, self.alto


class SetinhaGuia(Ponto):
    def draw(self):
        v = self.o_que_ta_vendo
        if not v.leo.x - QUADRADO <= self.x <= v.cam.x + LARG_TELA:
            return
        seta = arte.peca("chevron", v.cores_da_fase.nome).pega_quadro(1 if v.pulso > 0.5 else 0)
        v.tela.blit(seta, (v.cam.transform_x(self.x) + QUADRADO // 2 - seta.get_width() // 2,
                           v.cam.transform_y(self.y) - 74 - seta.get_height() - int(8 * v.pulso)))


class PortalDeVelocidade(Ponto):
    def __init__(self, x, y, ta_rapido):
        super().__init__(x, y)
        self.ta_rapido = ta_rapido

    def draw(self):
        v = self.o_que_ta_vendo
        if not v.ta_perto(self.x, QUADRADO, QUADRADO):
            return
        figurinha = arte.portal_rapido(self.ta_rapido)
        figurinha.set_curr_frame(v.tempo * 12)
        figurinha.set_position(self.x - figurinha.width // 2, self.y - figurinha.height + 4)
        figurinha.draw(v.tela)


class Enfeitezinho(Coisa):
    def __init__(self, x, y, width, height, qual_desenho=0):
        super().__init__(x, y, width, height)
        self.qual_desenho = qual_desenho
        self.ato = None

    def draw(self):
        if self.o_que_ta_vendo.ta_perto(self.x, self.width):
            self.mostra_na_tela(self.o_que_ta_vendo)


class Arvorezona(Enfeitezinho):
    tipo = "arvore"

    def mostra_na_tela(self, v):
        img = aparencia.arvore(self, v.cores_da_fase)
        x = v.cam.transform_x(self.x) + (self.width - img.get_width()) // 2
        y = v.cam.transform_y(self.y) + self.height - img.get_height()
        v.tela.blit(img, (x, y + aparencia.AFUNDA_A_ARVORE))


class Enfeite(Enfeitezinho):
    tipo = "enfeite"

    def mostra_na_tela(self, v):
        figurinha = aparencia.enfeite(self, v.cores_da_fase)
        ta_vivo = figurinha.total_frames > 1
        ja_acordou = self.x < v.leo.x + aparencia.QUANDO_ACORDA
        x = v.cam.transform_x(self.x)
        pe = v.cam.transform_y(self.y) + self.height + aparencia.AFUNDA_O_ENFEITE
        v.tela.blit(aparencia.sombra(max(20, figurinha.width - 8), 8, 80),
                    (x + (self.width - figurinha.width) // 2 + 4, pe - aparencia.AFUNDA_O_ENFEITE - 4))
        if ta_vivo and not ja_acordou:
            figurinha = arte.recuada(figurinha, (10, 8, 22), 0.5)
            figurinha.set_curr_frame(0)
        else:
            figurinha.set_curr_frame(int(v.tempo * 7) + self.qual_desenho)
        figurinha.set_position(self.x + (self.width - figurinha.width) // 2,
                               self.y + self.height + aparencia.AFUNDA_O_ENFEITE - figurinha.height)
        figurinha.draw(v.tela)
        if ta_vivo and ja_acordou:
            perto = 1.0 - min(1.0, max(0.0, (v.leo.x + aparencia.QUANDO_ACORDA - self.x) / (QUADRADO * 1.5)))
            larg = 96 + int(40 * perto)
            v.tela.blit(aparencia.poca(v.cores_da_fase.destaque, larg),
                        (x + self.width // 2 - larg // 2, pe - aparencia.AFUNDA_O_ENFEITE - 12),
                        special_flags=pygame.BLEND_RGB_ADD)


class PortalDoFim(Enfeitezinho):
    tipo = "portal"

    def mostra_na_tela(self, v):
        figurinha = arte.peca("portal", v.cores_da_fase.nome)
        figurinha.set_curr_frame(v.tempo * 8)
        figurinha.set_position(self.x + (self.width - figurinha.width) // 2,
                               self.y + self.height - figurinha.height)
        figurinha.draw(v.tela)
