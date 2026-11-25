import gc
import sys

try:
    import pygame
    from PPlay.scenemanager import SceneManager
except ImportError as erro:
    print(f"\n[ERRO] falta uma dependencia: {erro}")
    print("Instale com:  ./.venv/bin/python -m pip install -r requirements.txt")
    print("e rode com:   ./.venv/bin/python main.py\n")
    sys.exit(1)

from jogo import arte, fases, final, menus
from jogo.abertura import Comecinho
from jogo.audio import audio
from jogo.cena import atual, troca_tela
from jogo.config import TELA_CHEIA
from jogo.janela import Janelona
from jogo.partida import Jogatina
from jogo.save import save
from jogo.transicao import Cortina


class Joguinho:
    def __init__(self):
        self.janela = Janelona(tela_cheia=TELA_CHEIA)
        self.janela.close = self.fecha_tudo
        self.save = save
        self.fase_escolhida = 0
        arte.carrega_tudo()
        menus.deixa_pronto()
        gc.collect()
        gc.freeze()
        audio.liga()
        audio.aplica(save.opcoes)
        pygame.joystick.init()
        self.transicao = Cortina()
        troca_tela(Comecinho(self))
        self.transicao.revela()

    @property
    def tela(self):
        return atual()

    @tela.setter
    def tela(self, nova):
        troca_tela(nova)

    def faz_transicao(self, o_que_fez):
        self.transicao.liga(o_que_fez)

    def troca_de_tela(self, faz_a_tela):
        self.tela.sai_daqui()
        self.faz_transicao(lambda: troca_tela(faz_a_tela()))

    def vai_pro_menu(self):
        self.troca_de_tela(lambda: menus.TelaInicial(self))

    def vai_pras_opcoes(self):
        self.troca_de_tela(lambda: menus.TelaConfig(self))

    def vai_pras_fases(self):
        self.troca_de_tela(lambda: menus.TelaEscolheFase(self))

    def vai_pro_jogo(self, indice):
        self.fase_escolhida = indice

        def faz_a_tela():
            partida = Jogatina(self, fases.carrega_fase(indice))
            gc.collect()
            return partida

        self.troca_de_tela(faz_a_tela)

    def mostra_resultado(self, dados):
        if dados["completou"] and final.tem_final(save, dados["fase"]):
            self.troca_de_tela(lambda: final.Finalzinho(self, dados))
        elif dados["completou"]:
            self.troca_de_tela(lambda: menus.TelaGanhou(self, dados))
        else:
            self.troca_de_tela(lambda: menus.TelaPerdeu(self, dados))

    def sai_daqui(self):
        self.faz_transicao(self.fecha_tudo)

    def fecha_tudo(self):
        save.salva()
        pygame.quit()
        sys.exit(0)

    def roda(self):
        self.janela.comeca()
        while True:
            SceneManager.run()
            self.janela.update()


if __name__ == "__main__":
    Joguinho().roda()
