"""
Valida as fases com um robo que joga pela logica real da partida (a mesma
fisica, a mesma colisao e o mesmo julgamento do jogo), sem abrir janela.

    ./.venv/bin/python ferramentas/validar_fases.py [indice da fase ...]

Para cada fase, a promessa do jogo e: todo toque julgado BOM passa, seja um
toque rapido (o pulo baixo) ou o botao segurado ate o alto do arco (o pulo
inteiro). Nenhum passo pede o botao segurado.

    1. toque perfeito        rapido e segurado: termina sem dano, com nota S;
    2. sempre cedo / tarde   toques todos adiantados (ou atrasados) ate o
                             limite da janela BOM, rapidos e segurados: sem dano;
    3. erro sorteado         cada toque com um erro sorteado dentro da janela
                             BOM e segurado por um tempo sorteado: sem dano;
    4. a musica              a faixa dura a fase inteira.

Cada falha diz a batida, a parte da musica (introducao, A, B, A') e o motivo.
"""

import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.dont_write_bytecode = True

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from jogo import arte, fases
from jogo.config import PASSO_FISICA, JANELA_BOM, DIR_MUSICA
from jogo.partida import Partida, JOGANDO
from jogo.save import save

save.salvar = lambda: None          # o robo nunca grava recorde
arte.carregar()

LIMITE = JANELA_BOM * 0.95          # o erro maximo dos toques do robo (em batidas)
SORTEIOS = 12                       # partidas com erro sorteado por fase
RAPIDO = 0.06                       # segundos de um toque rapido (o pulo baixo)


class _App:
    """O minimo que a Partida pede do App."""
    fase_selecionada = 0
    save = save
    teclado = None

    def mouse(self):
        return (0, 0)

    def mostrar_resultado(self, dados):
        pass


def rapidos(fase):
    """Todo toque e rapido (o pulo baixo)."""
    return lambda i: RAPIDO


def jogar(fase, erro_de, segura_de=None, segurar=False):
    """
    Uma partida inteira; `erro_de(i)` e o erro (em batidas) do i-esimo toque e
    `segura_de(i)` quanto ele segura o botao: segundos, ou None para segurar
    ate o alto do pulo que ele fez (o pulo inteiro). Sem `segura_de`, sao
    toques rapidos (veja `rapidos`). Um toque novo sempre solta o anterior.
    `segurar`: o botao fica apertado a fase inteira (o pulo se repete sozinho).
    Devolve (partida, [(batida, motivo)] dos danos).
    """
    segura_de = segura_de or rapidos(fase)
    partida = Partida(_App(), fase)
    partida.modo = JOGANDO
    partida.liberou = segurar
    est = partida.est
    dur = fase.dur_batida
    # cada toque: [instante, segundos ou None, ja pulou, ja soltou]
    toques = [[(b + erro_de(i)) * dur, segura_de(i), False, False]
              for i, b in enumerate([] if segurar else fase.acoes)]
    danos = []
    while partida.modo == JOGANDO:
        t0 = est.tempo
        t1 = t0 + PASSO_FISICA
        novo = [tq for tq in toques if t0 < tq[0] <= t1]
        partida.apertou = bool(novo)
        segurando = segurar
        for tq in toques:
            inicio, segundos, pulou, solto = tq
            if solto or inicio > t1:
                continue
            if novo and tq is not novo[0]:
                tq[3] = True                          # soltou para apertar de novo
            elif segundos is not None:
                tq[3] = t1 >= inicio + segundos
            else:                                     # ate o alto do arco
                tq[3] = (pulou and est.vy >= 0.0) or t1 >= inicio + 2 * fase.duracao_pulo
            segurando = segurando or not tq[3]
        partida.pressionado = segurando
        if not segurando:
            partida.liberou = True
        partida._passo()
        if est.acao == "pulo":
            for tq in toques:
                if tq[0] <= est.tempo and not tq[3]:
                    tq[2] = True
        if est.dano:
            danos.append((est.tempo / dur, est.dano))
    return partida, danos


def parte(fase, batida):
    nome = "?"
    for n, b in fase.secoes:
        if batida >= b:
            nome = n
    return nome


def descrever(fase, danos):
    return ", ".join(f"batida {b:.1f} ({parte(fase, b)}): {m}" for b, m in danos[:4]) + \
        (" ..." if len(danos) > 4 else "")


def duracao_musica(cancao):
    try:
        pygame.mixer.init()
        return pygame.mixer.Sound(os.path.join(DIR_MUSICA, f"{cancao}.mp3")).get_length()
    except pygame.error:
        return None


def validar(indice):
    fase = fases.carregar(indice)
    falhas = 0
    print(f"\n\033[1m[{indice}] {fase.nome}\033[0m  {fase.bpm} BPM, {len(fase.acoes)} acoes, "
          f"{fase.duracao:.1f}s")
    print("   partes: " + "  ".join(f"{n} {b:g}" for n, b in fase.secoes))

    cheios = lambda i: None                  # noqa: E731 -- todo toque segura ate o alto
    for nome, segura_de in (("rapido  ", None), ("segurado", cheios)):
        partida, danos = jogar(fase, lambda i: 0.0, segura_de)
        ok = partida.est.venceu and not danos and partida.ritmo.nota() == "S"
        falhas += not ok
        print(f"  [{'ok' if ok else 'ERRO'}] {nome} perfeito: nota {partida.ritmo.nota()}"
              + (f" -- {descrever(fase, danos)}" if danos else ""))

    for nome, segura_de in (("rapido  ", None), ("segurado", cheios)):
        for erro in (-LIMITE, -LIMITE / 2, LIMITE / 2, LIMITE):
            partida, danos = jogar(fase, lambda i: erro, segura_de)
            ok = partida.est.venceu and not danos
            falhas += not ok
            print(f"  [{'ok' if ok else 'ERRO'}] {nome} sempre {'cedo ' if erro < 0 else 'tarde'} "
                  f"{abs(erro):.2f} batida" + (f" -- {descrever(fase, danos)}" if danos else ""))

    ruins = []
    for semente in range(SORTEIOS):
        rnd = random.Random(semente)
        erros = [rnd.uniform(-LIMITE, LIMITE) for _ in fase.acoes]
        # quanto cada toque segura: de um toque rapido a quase o pulo inteiro
        tempos = [rnd.uniform(0.02, 0.9 * fase.duracao_pulo) for _ in fase.acoes]
        partida, danos = jogar(fase, lambda i: erros[i], lambda i: tempos[i])
        if not partida.est.venceu or danos:
            ruins.append((semente, danos))
    falhas += len(ruins)
    print(f"  [{'ok' if not ruins else 'ERRO'}] erro e tempo segurado sorteados: "
          f"{SORTEIOS - len(ruins)} de {SORTEIOS} partidas sem dano")
    for semente, danos in ruins[:4]:
        print(f"        sorteio {semente}: {descrever(fase, danos)}")

    # so informativo: segurar o botao a fase inteira nao pode bastar
    partida, danos = jogar(fase, lambda i: 0.0, segurar=True)
    pct = min(100.0, partida.est.x / fase.fim_x * 100.0)
    if partida.est.venceu and not danos:
        print("  [aviso] segurando o botao a fase inteira, o Leo termina sem dano: "
              "falta ritmo quebrado para exigir atencao")
    else:
        print(f"  [info] segurando o botao direto: {pct:.0f}% da fase, "
              f"primeiro erro na {descrever(fase, danos[:1])}")

    musica = duracao_musica(fase.cancao)
    if musica is not None:
        fim = fase.trilha.inicio + fase.duracao
        ok = fim <= musica
        falhas += not ok
        print(f"  [{'ok' if ok else 'ERRO'}] musica: a fase vai ate {fim:.1f}s de {musica:.1f}s da faixa")
    return falhas


def main():
    indices = [int(a) for a in sys.argv[1:]] or list(range(len(fases.todas())))
    falhas = sum(validar(i) for i in indices)
    print(f"\n{'tudo certo' if not falhas else f'{falhas} problema(s)'}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
