"""
Mede o custo de cada quadro em todas as telas e nas fases inteiras (o robo
joga), e aponta os quadros que estouram o orcamento de 60 FPS (16,7 ms).

    ./.venv/bin/python ferramentas/medir_fps.py            # tudo
    ./.venv/bin/python ferramentas/medir_fps.py geleira    # so uma fase
    ./.venv/bin/python ferramentas/medir_fps.py -p         # com perfil dos quadros lentos

Roda sem janela (driver dummy): mede o trabalho da CPU, que e o que trava.
"""
import cProfile
import gc
import io
import os
import pstats
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

pygame.init()
tela = pygame.display.set_mode((1280, 720))

from jogo import arte, fases, menus, partida as P
from jogo.audio import audio
from jogo.config import PASSO_FISICA
from jogo.save import save

save.salvar = lambda: None
audio.tocar = lambda *a, **k: None
audio.tocar_musica = lambda *a, **k: None
arte.carregar()
menus.preaquecer()          # como o jogo faz na abertura

ORCAMENTO = 1000.0 / 60.0
PERFIL = "-p" in sys.argv
SO = [a for a in sys.argv[1:] if not a.startswith("-")]


class App:
    fase_selecionada = 0
    save = save
    teclado = None
    def mouse(self): return (0, 0)
    def mostrar_resultado(self, d): pass
    def controle_segurado(self): return False
    def ir_para_jogo(self, i): pass
    def ir_para_fases(self): pass
    def ir_para_menu(self): pass


def medir(nome, quadro, n):
    """Roda `quadro()` n vezes; devolve os tempos (ms) e mostra o resumo."""
    gastos, lentos = [], []
    for i in range(n):
        if PERFIL:
            pr = cProfile.Profile(); pr.enable()
        a = time.perf_counter()
        if quadro() is False:
            break
        d = (time.perf_counter() - a) * 1000.0
        gastos.append(d)
        if d > ORCAMENTO:
            lentos.append((i, d))
            if PERFIL and len(lentos) <= 3:
                pr.disable()
                s = io.StringIO()
                pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(14)
                print(f"--- {nome}, quadro {i}: {d:.0f} ms\n" + "\n".join(s.getvalue().splitlines()[6:26]))
        elif PERFIL:
            pr.disable()
    g = sorted(gastos)
    print(f"{nome:28s} {len(g):5d} quadros  medio {sum(g)/len(g):5.1f} ms  p99 {g[int(len(g)*0.99)]:5.1f}"
          f"  pior {g[-1]:6.1f}  acima de 16,7 ms: {len(lentos)}"
          + (f"  (quadros {[i for i, _ in lentos[:8]]})" if lentos else ""))
    return lentos


def tela_menu(t, n):
    def q():
        t.atualizar(1 / 60); t.desenhar(tela)
    return q


app = App()
total = 0
if not SO:
    total += len(medir("menu principal", tela_menu(menus.TelaMenu(app), 0), 180))
    total += len(medir("opcoes", tela_menu(menus.TelaOpcoes(app), 0), 120))
    tf = menus.TelaFases(app)
    k = [0]
    def trocando():
        k[0] += 1
        if k[0] % 20 == 0:            # troca de carta a cada 1/3 s, como quem passa o mouse
            tf._selecionar((tf.indice + 1) % len(tf.lista))
        tf.atualizar(1 / 60); tf.desenhar(tela)
    total += len(medir("selecao (trocando cartas)", trocando, 400))

for f0 in fases.todas():
    if SO and f0.cancao not in SO:
        continue
    a = time.perf_counter()
    f = fases.do_mundo(f0.cancao)
    app.fase_selecionada = f.ident
    p = P.Partida(app, f)
    print(f"{f.cancao}: criar a partida levou {(time.perf_counter() - a) * 1000:.0f} ms (debaixo da transicao)")
    for _ in range(60):                       # a espera antes do toque
        p.atualizar(1 / 60); p.desenhar(tela)
    p._botao_segurado = lambda: False
    p.modo = P.JOGANDO
    toques = [b * f.dur_batida for b in f.acoes]
    i = [0]
    orig = p._passo
    def passo():
        if i[0] < len(toques) and toques[i[0]] <= p.est.tempo + PASSO_FISICA:
            p.apertou = True
            i[0] += 1
        orig()
    p._passo = passo
    def jogar():
        if p.modo != P.JOGANDO:
            return False
        p.atualizar(1 / 60); p.desenhar(tela)
    total += len(medir(f"partida {f.cancao}", jogar, 100000))
    for _ in range(120):                      # o letreiro do fim
        p.atualizar(1 / 60); p.desenhar(tela)
    if not SO:
        dados = p.resultado
        total += len(medir(f"resultado {f.cancao}", tela_menu(menus.TelaResultado(app, dados), 0), 120))
print(f"\nquadros acima do orcamento: {total}")
