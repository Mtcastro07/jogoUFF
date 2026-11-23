"""
Onde da para passar SO SEGURANDO o botao? (o pulo se repete a cada pouso)

    ./.venv/bin/python ferramentas/medir_segurar.py [indice da fase ...] [--trechos]

O robo joga certo (toques perfeitos) ate uma acao; dali em diante so segura o
botao. Para cada acao de partida, mede quantas batidas ele anda ate se ferir.
Um trecho que se passa segurando e um trecho em que o ritmo nao pede atencao.

    pior trecho        o maior numero de batidas seguras segurando
    acima de 16        de quantas acoes se segura mais de 16 batidas (4 compassos)
    da largada         segurando desde a primeira acao: ate onde vai, e com quantos danos

`--trechos` lista os trechos longos (inicio e fim, em batidas, e a parte da musica).
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.dont_write_bytecode = True
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))

from validar_fases import _App, RAPIDO, parte  # noqa: E402 (abre o pygame sem janela)
from jogo import fases  # noqa: E402
from jogo.config import PASSO_FISICA  # noqa: E402
from jogo.partida import Partida, JOGANDO  # noqa: E402

LONGO = 16          # batidas: um trecho maior que isso, so segurando, e longo demais


def segurar_desde(fase, i, ate_fim=False):
    """Toques perfeitos ate a acao i; dela em diante, o botao segurado.
    Devolve (batidas andadas segurando ate o 1o dano, danos ate o fim, venceu)."""
    p = Partida(_App(), fase)
    p.modo = JOGANDO
    est = p.est
    dur = fase.dur_batida
    toques = [b * dur for b in fase.acoes[:i]]
    inicio = fase.acoes[i] * dur
    soltar_em = -1.0
    primeiro = None
    danos = 0
    while p.modo == JOGANDO:
        t1 = est.tempo + PASSO_FISICA
        if est.tempo >= inicio:
            p.apertou = est.tempo < inicio + PASSO_FISICA
            p.pressionado = True
        else:
            novo = any(est.tempo < t <= t1 for t in toques)
            if novo:
                soltar_em = t1 + RAPIDO
            p.apertou = novo
            p.pressionado = t1 < soltar_em
            if not p.pressionado:
                p.liberou = True
        p._passo()
        if est.dano and est.tempo >= inicio:
            danos += 1
            if primeiro is None:
                primeiro = est.tempo / dur
                if not ate_fim:
                    break
    fim = primeiro if primeiro is not None else est.tempo / dur
    return fim - fase.acoes[i], danos, est.venceu


def medir(indice, trechos=False):
    fase = fases.carregar(indice)
    print(f"\n[{indice}] {fase.nome}  ({fase.bpm:g} BPM, {len(fase.acoes)} acoes)")
    if fase.so_toques:
        print("   segurar nao repete o pulo nesta fase: nao se passa nada so segurando")
        return
    seguros = [segurar_desde(fase, i)[0] for i in range(len(fase.acoes))]
    longos = [(fase.acoes[i], s) for i, s in enumerate(seguros) if s > LONGO]
    pior = max(range(len(seguros)), key=lambda i: seguros[i])
    andou, danos, venceu = segurar_desde(fase, 0, ate_fim=True)
    print(f"   pior trecho: {seguros[pior]:.0f} batidas, da batida {fase.acoes[pior]:g} "
          f"({parte(fase, fase.acoes[pior])})")
    print(f"   acima de {LONGO}: de {len(longos)} das {len(seguros)} acoes")
    print(f"   media segurando: {sum(seguros) / len(seguros):.1f} batidas ate o 1o dano")
    print(f"   da largada, segurando a fase inteira: {'VENCE' if venceu else 'nao termina'}, "
          f"{danos} danos")
    if trechos and longos:
        # junta as acoes vizinhas num trecho so
        blocos = []
        for b, s in longos:
            if blocos and b <= blocos[-1][1]:
                blocos[-1][1] = max(blocos[-1][1], b + s)
            else:
                blocos.append([b, b + s])
        for b0, b1 in blocos:
            print(f"      batidas {b0:g} a {b1:.0f} ({parte(fase, b0)})")
    return seguros


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for i in (map(int, args) if args else range(len(fases.todas()))):
        medir(i, "--trechos" in sys.argv)
