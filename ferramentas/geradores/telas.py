"""
Fotografa todas as telas de interface, para conferir de olho:

    ./.venv/bin/python ferramentas/geradores/telas.py PASTA

Menu, opcoes, selecao de fase com cada carta escolhida, a partida esperando,
pausada e retomando, resultado e fim de jogo. Nao grava nada no save.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pygame

pygame.init()
tela = pygame.display.set_mode((1280, 720))

from jogo import arte, fases, menus, partida as P
from jogo.audio import audio
from jogo.save import save

save.salvar = lambda: None
audio.tocar = lambda *a, **k: None
audio.tocar_musica = lambda *a, **k: None
arte.carregar()
PASTA = sys.argv[1] if len(sys.argv) > 1 else "telas"
os.makedirs(PASTA, exist_ok=True)


class App:
    fase_selecionada = 0
    save = save
    teclado = None
    mouse_em = (0, 0)
    def mouse(self): return self.mouse_em
    def mostrar_resultado(self, d): pass
    def controle_segurado(self): return False
    def ir_para_jogo(self, i): pass
    def ir_para_fases(self): pass
    def ir_para_menu(self): pass


def foto(t, nome, segundos=1.0, passos=None):
    for _ in range(passos or int(segundos * 60)):
        t.atualizar(1 / 60)
    t.desenhar(tela)
    pygame.image.save(tela, os.path.join(PASTA, nome + ".png"))
    print(nome)


app = App()
mundos = [f.cancao for f in fases.todas()]
foto(menus.TelaMenu(app), "menu", 2.0)
foto(menus.TelaOpcoes(app), "opcoes")
for i, m in enumerate(mundos):
    app.fase_selecionada = i
    foto(menus.TelaFases(app), f"fases_{i}_{m}")
for m in ("geleira", "dunas"):
    f = fases.do_mundo(m)
    app.fase_selecionada = f.ident
    p = P.Partida(app, f)
    foto(p, f"partida_{m}_espera", 1.4)
    p.modo = P.JOGANDO
    p._botao_segurado = lambda: False
    for _ in range(90):
        p.atualizar(1 / 60)
    p._pausar()
    foto(p, f"partida_{m}_pausa", 0.5)
    base = dict(fase=f, completou=True, nota="A", precisao=0.912, pontos=12345, recorde=True,
                perfeitos=180, bons=25, erros=6, combo=97, ecos=120, ecos_total=len(f.brilhos),
                progresso=100.0)
    foto(menus.TelaResultado(app, base), f"resultado_{m}", 2.0)
    foto(menus.TelaGameOver(app, dict(base, completou=False, progresso=63.0)), f"gameover_{m}", 1.0)
