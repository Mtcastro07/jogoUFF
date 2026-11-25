import pygame
from PPlay.gameimage import GameImage
from PPlay.gameobject import GameObject
from PPlay.window import Window

from .janela import Janelona


def abre_imagem(caminho):
    return GameImage(caminho).image


class TemDesenho:
    def imagem_dele(self):
        return self.image

    def cantinho(self):
        return self.x, self.y

    def tamanho_de_verdade(self):
        if self.scale_x == 1.0 and self.scale_y == 1.0:
            return pygame.Rect((0, 0), self.imagem_dele().get_size())
        return pygame.Rect(0, 0, max(1, int(self.width * self.scale_x)),
                           max(1, int(self.height * self.scale_y)))

    def bota_no_meio(self, cx, cy):
        r = self.tamanho_de_verdade()
        r.center = (cx, cy)
        self.set_position(r.x, r.y)

    def poe_na_direita(self, x, y):
        self.set_position(x - self.width, y)

    def draw(self, tela=None):
        if self.scale_x != 1.0 or self.scale_y != 1.0 or self.rotation != 0:
            with Janelona.pintando_em(tela):
                super().draw()
            return
        alvo = Window.get_screen() if tela is None else tela
        img = self.imagem_dele()
        if self.transparency >= 255:
            alvo.blit(img, self.cantinho())
        elif self.transparency > 0:
            img.set_alpha(self.transparency)
            alvo.blit(img, self.cantinho())
            img.set_alpha(255)


class Desenho(TemDesenho, GameImage):
    def __init__(self, origem, escala=1):
        if isinstance(origem, pygame.Surface):
            GameObject.__init__(self)
            self.image = origem
        else:
            super().__init__(origem)
        if escala != 1:
            self.image = pygame.transform.scale_by(self.image, escala)
        self.rect = self.image.get_rect()
        self.width, self.height = self.rect.size
