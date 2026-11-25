import pygame
from PPlay.tilemap import TileMap

from . import aparencia, arte, terreno
from .camera import Camera
from .config import QUADRADO, LARG_TELA
from .objetos import Coisa

QUAO_FUNDO = 8


def o_que_aparece(cam):
    return int(cam.x // QUADRADO) - 1, int((cam.x + LARG_TELA) // QUADRADO) + 2


class MapaDaFase(TileMap):
    def __init__(self, azulejos=()):
        super().__init__(QUADRADO)
        self.quadradinhos_ocupados = {}
        self.cam_do_mapa = Camera()
        self.primeira_coluna = 0
        if azulejos:
            self.monta(azulejos)

    def monta(self, azulejos):
        self.primeira_coluna = min(t.tx for t in azulejos)
        primeira_linha = min(t.ty for t in azulejos)
        n_colunas = max(t.tx for t in azulejos) - self.primeira_coluna + 1
        linhas = max(t.ty for t in azulejos) - primeira_linha + 1
        self.mapa_tiles = [[None] * n_colunas for _ in range(linhas)]
        for t in azulejos:
            self.mapa_tiles[t.ty - primeira_linha][t.tx - self.primeira_coluna] = t
            for casa in t.casas():
                self.quadradinhos_ocupados[casa] = t
        self.tiles_colidiveis = [t for t in azulejos if t.solido]
        self.largura_mapa_px, self.altura_mapa_px = n_colunas * QUADRADO, linhas * QUADRADO
        self.cam_do_mapa.altura = self.altura_mapa_px

    def draw(self):
        if self.mapa_tiles:
            c0, c1 = o_que_aparece(Coisa.o_que_ta_vendo.cam)
            self.cam_do_mapa.x = (c0 - self.primeira_coluna) * QUADRADO
            self.cam_do_mapa.largura = (c1 - c0 - 1) * QUADRADO
            with self.cam_do_mapa.usando_essa_cam():
                super().draw()


class Azulejo(Coisa):
    solido = True

    def __init__(self, fase, tx, ty, linhas=1):
        super().__init__(tx * QUADRADO, ty * QUADRADO, QUADRADO, linhas * QUADRADO)
        self.fase, self.tx, self.ty, self.linhas = fase, tx, ty, linhas

    def casas(self):
        return [(self.tx, self.ty + k) for k in range(self.linhas)]


class PedacoDeChao(Azulejo):
    def __init__(self, fase, tx, ty):
        super().__init__(fase, tx, ty, QUAO_FUNDO)

    def draw(self):
        v = self.o_que_ta_vendo
        x, y = v.cam.transform_x(self.x), v.cam.transform_y(self.y)
        terreno.mostra_na_tela(v.tela, self.fase, self.tx, x, y)


class Pontezinha(Azulejo):
    solido = False

    def draw(self):
        v, casas = self.o_que_ta_vendo, self.fase.pontezinhas.quadradinhos_ocupados
        esq = (self.tx - 1, self.ty) not in casas
        dir_ = (self.tx + 1, self.ty) not in casas
        img = laje(v.cores_da_fase, esq, dir_)
        x, y = v.cam.transform_x(self.x), v.cam.transform_y(self.y)
        v.tela.blit(aparencia.sombra(QUADRADO, 6, 60), (x, y + 18))
        v.tela.blit(img, (x, y))


class BlocoDuro(Azulejo):
    def draw(self):
        v = self.o_que_ta_vendo
        if (self.tx, self.ty) in v.leo.blocos_quebrados:
            return
        cores_da_fase = v.cores_da_fase
        x, y = v.cam.transform_x(self.x), v.cam.transform_y(self.y)
        if self.fase.chao_por_coluna.get(self.tx) == self.ty + 1:
            self.pezinho(v.tela, x, y, aparencia.CORES_DO_LUGAR[cores_da_fase.nome][2])
        qual_desenho = (self.tx * 2654435761 >> 8) % arte.quantos_blocos(cores_da_fase.nome)
        v.tela.blit(arte.bloco(cores_da_fase.nome, qual_desenho), (x, y))

    def pezinho(self, tela, x, y, cores):
        tela.blit(aparencia.sombra(QUADRADO + 16, 10, 120), (x - 8, y + QUADRADO - 5))
        cor_escura, cor_media, cor_clara = cores
        for k, (dx, cor) in enumerate(((-7, cor_media), (-3, cor_clara), (QUADRADO + 2, cor_media),
                                       (QUADRADO - 1, cor_escura))):
            if (self.tx * 7 + k * 3) % 4 != 0:
                tela.fill(cor, (x + dx, y + QUADRADO - 4, 4, 4))


lajes_prontas = {}


def laje(cores_da_fase, esq, dir_):
    chave = (cores_da_fase.nome, esq, dir_)
    if chave not in lajes_prontas:
        img = pygame.Surface((QUADRADO, 20), pygame.SRCALPHA)
        cor_escura = arte.escurece_cor(cores_da_fase.bloco, 0.6)
        a, b = 0, QUADRADO
        if esq:
            a = 3
        if dir_:
            b = QUADRADO - 3
        x0, x1 = a, b
        if esq:
            x0 += 3
        if dir_:
            x1 -= 3
        pygame.draw.rect(img, cor_escura, (a, 0, b - a, 17))
        pygame.draw.rect(img, arte.clareia(cores_da_fase.bloco, 0.12), (x0, 3, x1 - x0, 11))
        pygame.draw.rect(img, cores_da_fase.chao_topo, (a, 0, b - a, 6))
        pygame.draw.rect(img, arte.clareia(cores_da_fase.chao_topo, 0.6), (a, 0, b - a, 3))
        for x in range(a + 9, b - 6, 15):
            pygame.draw.rect(img, cor_escura, (x, 6, 3, 6))
        if esq:
            pygame.draw.rect(img, cor_escura, (a + 3, 14, 6, 6))
        elif dir_:
            pygame.draw.rect(img, cor_escura, (b - 9, 14, 6, 6))
        lajes_prontas[chave] = img
    return lajes_prontas[chave]
