"""
Fisica do jogador, em passos fixos de 1/240 s. Nada aqui desenha nada.

Leo tem UMA acao, no unico botao:

    PULO         o tempo apertado decide a ALTURA: um toque rapido e um pulo
                 baixo, segurar ate o alto do arco e o pulo inteiro. Os dois
                 pousam no mesmo lugar e na mesma batida -- o ritmo nunca se
                 perde. Segurado alem do pouso, ele pula de novo a cada pouso.
                 (No bosque, a fase so de toques, o pulo e sempre o inteiro e
                 segurar nao faz nada.)

O pulo e travado no RITMO: quando o toque chega com o Leo ainda no ar, ele
fica guardado e o pulo sai no pouso -- mais curto (mesma altura, menos tempo),
para pousar quando pousaria se tivesse saido na hora do toque. Assim um pouso
atrasado (descer um degrau cai mais longe) nunca empurra os pulos seguintes.

Bater num caco do chao, num bloco ou na parede de um degrau custa um coracao:
o bloco se quebra, e Leo fica um instante invulneravel (piscando). Cair num
fosso NAO tem volta: Leo desce ate os cacos do fundo e a partida acaba ali.

A colisao e a do que se ve: contra o chao e as paredes vale a SOLA do Leo (o
meio da caixa, onde o corpo dele esta), contra os cacos vale o CORPO -- com
as pernas encolhidas quando ele esta no ar -- e o DESENHO de cada caco, ponta
por ponta. Quem pousa rente a quina de um degrau sobe nele em vez de bater.
"""

import math

from .config import (PASSO_FISICA, TILE, JOGADOR_TAM, LARGURA_APOIO, CORPO_LARGURA,
                     CORPO_ALTURA, CORPO_FRENTE, FOLGA_PE, FOLGA_PE_AR, QUINA, PULO_MINIMO,
                     CORTE_PULO, COYOTE, BUFFER_PULO, VIDAS, INVULNERAVEL)

APOIO = (JOGADOR_TAM - LARGURA_APOIO) * 0.5     # onde a sola comeca, dentro da caixa


class Estado:
    """Tudo que muda no jogador durante a partida."""

    def __init__(self, fase):
        self.x = 0.0
        self.y = fase.chao_y - JOGADOR_TAM
        self.vy = 0.0
        self.tempo = 0.0
        self.no_chao = True
        self.coyote = 0.0         # segundos em que ainda da para pular apos sair do chao
        self.buffer = 0.0         # segundos em que um toque recente ainda vale
        self.vidas = VIDAS
        self.invuln = 0.0
        self.vivo = True
        self.venceu = False
        self.quebrados = set()    # blocos que Leo quebrou nesta tentativa
        self.preso = False        # bateu na parede de dentro de um fosso: so resta cair
        self.toque = -1.0         # instante do ultimo toque (o pulo guardado conta dali)
        self.gravidade = fase.gravidade   # a do pulo em curso (um pulo encurtado e mais forte)
        self.pulando = False      # no ar por causa de um pulo (e nao de uma queda)
        self.y_saida = 0.0        # de onde o pulo saiu: mede o quanto ja subiu
        self.cortou = False       # o botao ja foi solto neste pulo
        self.fim_pulo = 0.0       # quando o pulo em curso pousa (no nivel de onde saiu)
        # o que aconteceu NESTE passo (a partida le e reage)
        self.acao = None          # "pulo" quando ele pulou neste passo
        self.repetido = False     # o pulo saiu so por segurar o botao (sem toque novo)
        self.dano = None          # "parede", "bloco", "perigo", "fosso" ou "abismo"
        self.quebrou = None       # a celula do bloco que se quebrou agora
        self.pousou = False
        self.pouso = -1.0         # instante do ultimo pouso (a arte mostra o pe tocando o chao)
        self.pulo = -1.0          # instante do ultimo pulo (a arte estica o corpo na saida)


def _colunas(x):
    """Colunas do grid sob a SOLA do jogador (o meio da caixa)."""
    return int((x + APOIO) // TILE), int((x + APOIO + LARGURA_APOIO - 0.001) // TILE)


def _linhas(y):
    return range(int(y // TILE), int((y + JOGADOR_TAM - 0.001) // TILE) + 1)


def _solido(fase, est, c, ty):
    return (c, ty) in fase.solidos and (c, ty) not in est.quebrados


def corpo(est):
    """
    (x, y, largura, altura) da parte do Leo que os cacos ferem: pernas e
    tronco como aparecem no sprite -- no ar, com as pernas encolhidas.
    """
    x = est.x + (JOGADOR_TAM - CORPO_LARGURA) * 0.5 + CORPO_FRENTE
    folga = FOLGA_PE if est.no_chao else FOLGA_PE_AR
    y = est.y + JOGADOR_TAM - folga - CORPO_ALTURA
    return x, y, CORPO_LARGURA, CORPO_ALTURA


def _livre(fase, est, x, y):
    """A caixa do Leo em (x, y) nao entra em nada solido?"""
    c0, c1 = _colunas(x)
    return not any(_solido(fase, est, c, ty) for c in (c0, c1) for ty in _linhas(y))


def linha_segura(fase, est):
    """
    Altura (y) em que Leo pode ficar de pe agora: o chao mais alto das colunas
    que ele cobre -- ou, se esta sobre um buraco, o da primeira coluna a
    frente que tem chao. Blocos soltos nao contam.
    """
    c0, c1 = _colunas(est.x)
    niveis = [fase.chao_col[c] for c in (c0, c1) if c in fase.chao_col]
    return (min(niveis) if niveis else fase.nivel_chao(c1)) * TILE


def _resgatar(fase, est):
    """Recoloca Leo de pe na linha segura, sem mudar o x (ele nunca volta)."""
    est.y = linha_segura(fase, est) - JOGADOR_TAM
    est.vy = 0.0
    est.buffer = 0.0
    est.pulando = False


def _baixar(fase, est):
    """
    O botao saiu na subida: refaz o resto do arco. O novo alto e o que o pulo
    alcancaria com so CORTE_PULO da velocidade de agora (nunca menos que
    PULO_MINIMO da altura), e o pouso continua no instante marcado: o arco
    baixo e so mais lento para cair.
    """
    subiu = est.y_saida - est.y
    alvo = max(fase.altura_pulo * PULO_MINIMO,
               subiu + (CORTE_PULO * est.vy) ** 2 / (2.0 * est.gravidade))
    resta = est.fim_pulo - est.tempo
    if resta <= 0.0 or alvo <= subiu:
        return
    k = math.sqrt((alvo - subiu) / alvo)
    ate_o_alto = resta * k / (1.0 + k)
    est.gravidade = 2.0 * alvo / (resta - ate_o_alto) ** 2
    est.vy = -est.gravidade * ate_o_alto


def ferir(fase, est, motivo, resgatar=True):
    """
    Leo errou: tira um coracao (se nao estiver invulneravel) e o resgata.
    Devolve True se foi o ultimo coracao.
    """
    if est.invuln <= 0.0:
        est.vidas -= 1
        est.dano = motivo
        est.invuln = INVULNERAVEL * fase.dur_batida
        if est.vidas <= 0:
            est.vivo = False
            return True
    if resgatar:
        _resgatar(fase, est)
    return False


def morrer(est, motivo):
    """O fim sem volta: Leo caiu num fosso (ou no abismo)."""
    est.vidas = 0
    est.vivo = False
    est.dano = motivo


def passo(fase, est, pressionado, apertou, repetir=False, dt=PASSO_FISICA):
    """
    Avanca a simulacao em um passo.

    `pressionado`: o botao esta segurado.   `apertou`: foi apertado agora.
    `repetir`: o botao segurado vale como pulo a cada pouso.
    """
    if not est.vivo or est.venceu:
        return
    est.tempo += dt
    est.acao = est.dano = est.quebrou = None
    est.repetido = est.pousou = False
    est.invuln = max(0.0, est.invuln - dt)
    est.coyote = max(0.0, est.coyote - dt)
    est.buffer = BUFFER_PULO * fase.dur_batida if apertou else max(0.0, est.buffer - dt)
    if apertou:
        est.toque = est.tempo

    # 1. anda para a direita. Entrar numa parede e bater -- a nao ser que so a
    # ponta do pe tenha passado da quina de cima: ai ele sobe no degrau, que e
    # o que o olho ve acontecer. Um bloco solto nao segura o Leo: se quebra.
    # E quem bate na parede de DENTRO de um fosso (sem chao sob a sola) nao e
    # resgatado: fica preso ali e desce ate os cacos do fundo.
    if not est.preso:
        est.x += fase.vx_em(est.x) * dt
    c0, c_dir = _colunas(est.x)
    batidas = [ty for ty in _linhas(est.y) if _solido(fase, est, c_dir, ty)]
    if batidas:
        topo = min(batidas) * TILE
        no_fosso = c0 not in fase.chao_col             # a sola esta sobre o vazio
        if est.y + JOGADOR_TAM - topo <= QUINA and _livre(fase, est, est.x, topo - JOGADOR_TAM):
            est.y = topo - JOGADOR_TAM
            est.vy = min(est.vy, 0.0)
        elif all((c_dir, ty) in fase.celulas_bloco for ty in batidas):
            est.quebrados.update((c_dir, ty) for ty in batidas)
            est.quebrou = (c_dir, batidas[0])
            if ferir(fase, est, "bloco", resgatar=False):
                return
        elif no_fosso:
            est.preso = True
            est.x = c_dir * TILE - APOIO - LARGURA_APOIO      # encostado na parede
            est.buffer = 0.0
        elif ferir(fase, est, "parede"):
            return

    # 2. a altura do pulo: com o botao solto na subida, o arco fica mais baixo
    # -- quanto mais cedo soltar, mais baixo --, mas pousa no MESMO lugar e na
    # mesma batida. O corte so vale depois que o Leo sobe `altura_corte`: todo
    # toque rapido da o MESMO pulo baixo (PULO_MINIMO da altura). Na fase so
    # de toques o pulo e sempre o inteiro.
    if (est.pulando and not est.cortou and est.vy < 0.0 and not pressionado and
            not fase.so_toques and est.y_saida - est.y >= fase.altura_corte):
        _baixar(fase, est)
        est.cortou = True

    # gravidade e colisao vertical com o que e solido
    est.vy = min(est.vy + est.gravidade * dt, fase.v_pulo * 1.5)
    est.y += est.vy * dt
    estava_no_chao = est.no_chao
    est.no_chao = False
    c0, c1 = _colunas(est.x)
    if est.vy > 0.0:
        ty = int((est.y + JOGADOR_TAM - 0.001) // TILE)
        if _solido(fase, est, c0, ty) or _solido(fase, est, c1, ty):
            est.y = ty * TILE - JOGADOR_TAM
            est.vy = 0.0
            est.no_chao = True
    elif est.vy < 0.0:
        ty = int(est.y // TILE)
        if _solido(fase, est, c0, ty) or _solido(fase, est, c1, ty):
            est.y = (ty + 1) * TILE
            est.vy = 0.0

    if est.no_chao:
        est.coyote = COYOTE
        est.gravidade = fase.gravidade        # de pe, qualquer queda e a normal
        est.pulando = False
        est.pousou = not estava_no_chao
        if est.pousou:
            est.pouso = est.tempo

    # 3. caiu alem de tudo: o abismo
    if est.y > fase.limite_baixo:
        morrer(est, "abismo")
        return

    # 4. cacos: o corpo do Leo contra o desenho de cada caco das colunas dele.
    # Os do fundo de um fosso matam sempre, invulneravel ou nao.
    bx, by, bw, bh = corpo(est)
    for tx in range(int(bx // TILE), int((bx + bw) // TILE) + 1):
        for p in fase.col_perigos.get(tx, ()):
            if (p.fatal or est.invuln <= 0.0) and p.colide(bx, by, bw, bh):
                if p.fatal:
                    morrer(est, "fosso")
                    return
                if ferir(fase, est, "perigo"):
                    return
                break
        if est.dano:
            break

    # 5. pulo: um toque recente, ou o botao segurado
    # (menos na fase so de toques, em que segurar nao pula de novo).
    repetir = repetir and not fase.so_toques
    # Toque guardado no ar: o pulo sai agora, encurtado para pousar no tempo
    # do toque -- a mesma altura, em menos tempo (ate 30% mais curto).
    if (not est.preso and (est.buffer > 0.0 or repetir) and
            (est.no_chao or est.coyote > 0.0)):
        atraso = min(est.tempo - est.toque, 0.3 * fase.duracao_pulo) if est.buffer > 0.0 else 0.0
        duracao = fase.duracao_pulo - max(0.0, atraso)
        est.gravidade = 8.0 * fase.altura_pulo / duracao ** 2
        est.vy = -4.0 * fase.altura_pulo / duracao
        est.repetido = est.buffer <= 0.0
        est.pulando, est.y_saida, est.cortou = True, est.y, False
        est.fim_pulo = est.tempo + duracao
        est.no_chao = False
        est.coyote = 0.0
        est.buffer = 0.0
        est.acao = "pulo"
        est.pulo = est.tempo

    if est.x >= fase.fim_x:
        est.venceu = True
