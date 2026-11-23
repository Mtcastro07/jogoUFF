"""
Fotos de uma fase com o robo jogando (toques perfeitos), para conferir a arte.

    ./.venv/bin/python ferramentas/geradores/fotos.py MUNDO PASTA batida[,batida...]
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pygame

pygame.init()
tela = pygame.display.set_mode((1280, 720))
from jogo import arte, fases, partida as P
from jogo.audio import audio
from jogo.config import PASSO_FISICA
from jogo.save import save

save.salvar = lambda: None
audio.tocar = lambda n: None
audio.tocar_musica = lambda c: None
arte.carregar()


class App:
    fase_selecionada = 0
    save = save
    teclado = None

    def mouse(self):
        return (0, 0)

    def mostrar_resultado(self, d):
        pass

    def controle_segurado(self):
        return False


fase = fases.do_mundo(sys.argv[1])
p = P.Partida(App(), fase)
p.modo = P.JOGANDO
alvos = sorted(float(b) for b in sys.argv[3].split(","))
toques = [b * fase.dur_batida for b in fase.acoes]
os.makedirs(sys.argv[2], exist_ok=True)
i = [0]
orig = p._passo


def passo():
    if i[0] < len(toques) and toques[i[0]] <= p.est.tempo + PASSO_FISICA:
        p.apertou = True
        i[0] += 1
    orig()


p._passo = passo
p._botao_segurado = lambda: False
while alvos and p.modo == P.JOGANDO:
    p.atualizar(1 / 60.0)
    if p.est.tempo >= alvos[0] * fase.dur_batida:
        p.desenhar(tela)
        nome = os.path.join(sys.argv[2], f"{sys.argv[1]}_{alvos[0]:06.1f}.png")
        pygame.image.save(tela, nome)
        print(nome, "vidas", p.est.vidas)
        alvos.pop(0)
