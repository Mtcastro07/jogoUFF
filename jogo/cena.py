from PPlay.scenemanager import Scene, SceneManager

from .janela import Janelona


class TelaQualquer(Scene):
    para_se_cobrir = False

    def __init__(self, joguinho):
        Janelona.pega_janela()
        super().__init__()
        self.joguinho = joguinho

    def loop(self):
        dt = self.janela.delta_time()
        transicao = self.joguinho.transicao
        if not transicao.ta_cobrindo:
            self.ve_teclas()
        if not (transicao.ta_cobrindo and self.para_se_cobrir):
            self.atualiza(dt)
        transicao.atualiza(dt)

    def draw(self):
        self.mostra_na_tela(self.janela.screen)
        self.joguinho.transicao.mostra_na_tela(self.janela.screen)

    def ve_teclas(self):
        pass

    def atualiza(self, dt):
        pass

    def mostra_na_tela(self, tela):
        pass

    def sai_daqui(self):
        pass


def atual():
    return SceneManager._current_scene


def troca_tela(nova):
    SceneManager.change_scene(nova)
