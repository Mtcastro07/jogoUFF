import pygame
from PPlay.parallax import ParallaxLayer, ParallaxSystem

from .camera import Camera
from .imagem import Desenho
from .janela import Janelona


class OndeTaOFundo:
    def __init__(self, tela, cx, dy, tempo, pulso, astro, noite, aurora):
        self.tela = tela
        self.cx, self.dy = cx, dy
        self.tempo, self.pulso = tempo, pulso
        self.astro, self.noite, self.aurora = astro, noite, aurora


class FundoQueAnda(ParallaxSystem):
    agora_ta = None

    def __init__(self):
        super().__init__()
        self.camera = Camera()

    def add_layer(self, camada):
        camada.fundo = self
        self.camadas.append(camada)

    def pinta_tudo(self, agora_ta):
        self.agora_ta = agora_ta
        self.camera.x = agora_ta.cx
        with Janelona.pintando_em(agora_ta.tela), self.camera.usando_essa_cam():
            self.draw()


class Fundinho(ParallaxLayer):
    fundo = None

    def __init__(self, velocidade=0.0, altura_na_tela=0.0, peso=1, imagem=None):
        self.fator = self.velocidade = velocidade
        self.altura_na_tela, self.peso = altura_na_tela, peso
        if imagem is not None:
            self.sprite = Desenho(imagem)
            self.largura, self.altura = imagem.get_size()

    def quanto_andou(self):
        return self.fundo.agora_ta.cx * self.velocidade

    def base(self):
        q = self.fundo.agora_ta
        return q.tela.get_height() * self.altura_na_tela + q.dy * self.peso


class ImagemRepetida(Fundinho):
    def __init__(self, velocidade, imagem, altura_na_tela=0.0, peso=1):
        super().__init__(velocidade, altura_na_tela, peso, imagem)
        self.fator = 1.0
        self.cam_propria = Camera()

    def passo(self):
        return int(self.quanto_andou())

    def topo(self):
        return int(self.base()) - self.altura

    def draw(self):
        tela, topo = self.fundo.agora_ta.tela, self.topo()
        w, h = tela.get_size()
        alto = min(self.altura, h - topo)
        if alto > 0:
            self.cam_propria.x = self.passo()
            faixa = tela.subsurface(pygame.Rect(0, topo, w, alto))
            with Janelona.pintando_em(faixa), self.cam_propria.usando_essa_cam():
                super().draw()
