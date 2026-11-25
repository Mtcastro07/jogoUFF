from contextlib import contextmanager

from PPlay import camera as pplay
from PPlay.gameobject import GameObject

from .config import QUADRADO, TAM_DO_LEO, LARG_TELA, ALT_TELA
from .impacto import Impacto

ONDE_LEO_FICA_X = 0.30
ONDE_LEO_FICA_Y = 0.66


class Camera(pplay.Camera):
    def __init__(self, x=0.0, y=0.0):
        cam_de_antes = pplay.Camera.get_instance()
        super().__init__(LARG_TELA, ALT_TELA)
        pplay.Camera._instance = cam_de_antes
        self.x, self.y = x, y

    @contextmanager
    def usando_essa_cam(self):
        antes = pplay.Camera.get_instance()
        pplay.Camera._instance = self
        try:
            yield self
        finally:
            pplay.Camera._instance = antes


class CamQueSegue(Camera):
    def __init__(self, fase):
        super().__init__(-LARG_TELA * ONDE_LEO_FICA_X, fase.y_do_chao - ALT_TELA * ONDE_LEO_FICA_Y)
        self.impacto = Impacto.novo()
        self.quadradao_da_cam = GameObject()
        self.quadradao_da_cam.width, self.quadradao_da_cam.height = LARG_TELA, ALT_TELA

    def da_tremida(self, forca):
        self.impacto.shake(forca)

    def acalma(self, dt):
        self.impacto.update(dt)

    def segue_leo(self, fase, leozinho, dt):
        self.x = leozinho.x - LARG_TELA * ONDE_LEO_FICA_X
        chao = fase.altura_do_chao(int((leozinho.x + TAM_DO_LEO) // QUADRADO)) * QUADRADO
        alvo = chao - ALT_TELA * ONDE_LEO_FICA_Y
        alvo = min(alvo, leozinho.y - ALT_TELA * 0.24)
        self.quadradao_da_cam.set_position(self.x, alvo)
        self.follow(self.quadradao_da_cam, min(1.0, dt * 5.0))
        self.acalma(dt)

    @contextmanager
    def com_tremida(self, adiante):
        x, y = self.x, self.y
        self.x += adiante
        with self.usando_essa_cam():
            self.impacto.apply_to_camera()
        self.x, self.y = int(self.x), int(self.y)
        try:
            yield self
        finally:
            self.x, self.y = x, y
