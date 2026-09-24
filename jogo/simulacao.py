"""
Fisica do jogador, em passos fixos de 1/240 s. Nada aqui desenha nada.

Leo tem DUAS acoes, as duas no mesmo botao:

    PULO         toque curto      ->  o salto de sempre
    SUSTENTACAO  botao segurado   ->  a ponte de eco aparece sob os pes dele

Bater em alguma coisa nao reinicia a fase: custa um coracao. Leo fica um
instante invulneravel (piscando) e e "resgatado" para a linha segura mais
proxima, sempre a frente, para a fase continuar. Enquanto esta invulneravel
ele atravessa os cacos e nao cai em buraco nenhum.
"""

from .config import (PASSO_FISICA, TILE, JOGADOR_TAM, HITBOX_PERIGO, COYOTE,
                     BUFFER_PULO, VIDAS, INVULNERAVEL, PONTE_GRAVIDADE,
                     PONTE_RESGATE)


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
        self.ponte = None         # ponte de eco cuja zona contem Leo
        self.carona = None        # ponte que o carrega de graca depois de um erro
        self.sustentando = False  # a ponte esta viva sob os pes dele
        # o que aconteceu NESTE passo (a partida le e reage)
        self.acao = None          # "pulo" ou "sustentar"
        self.dano = None          # "parede", "perigo", "abismo" ou "ritmo"
        self.pousou = False
        self.pouso = -1.0         # instante do ultimo pouso (a arte mostra o pe tocando o chao)


def _colunas(x):
    """Colunas do grid cobertas pela caixa do jogador."""
    return int(x // TILE), int((x + JOGADOR_TAM - 0.001) // TILE)


def _linhas(y):
    return range(int(y // TILE), int((y + JOGADOR_TAM - 0.001) // TILE) + 1)


def caixa_perigo(est):
    """Hitbox reduzida usada contra os cacos: raspar nao mata."""
    lado = JOGADOR_TAM * HITBOX_PERIGO
    margem = (JOGADOR_TAM - lado) * 0.5
    return est.x + margem, est.y + margem, lado, lado


def linha_segura(fase, est):
    """
    Altura (y) em que Leo pode ficar de pe agora: o chao mais alto das colunas
    que ele cobre -- ou, se esta sobre um buraco, o da primeira coluna a
    frente que tem chao. Blocos soltos nao contam: invulneravel, ele os
    atravessa.
    """
    c0, c1 = _colunas(est.x)
    niveis = [fase.chao_col[c] for c in (c0, c1) if c in fase.chao_col]
    return (min(niveis) if niveis else fase.nivel_chao(c1)) * TILE


def _resgatar(fase, est):
    """Recoloca Leo de pe na linha segura, sem mudar o x (ele nunca volta)."""
    est.y = linha_segura(fase, est) - JOGADOR_TAM
    est.vy = 0.0
    est.buffer = 0.0
    p = est.ponte
    est.carona = p if (p is not None and est.x + JOGADOR_TAM > p.x0) else None


def ferir(fase, est, motivo, resgatar=True):
    """
    Leo errou: tira um coracao (se nao estiver invulneravel) e o resgata.
    Devolve True se foi o ultimo coracao.
    """
    if est.invuln <= 0.0:
        est.vidas -= 1
        est.dano = motivo
        est.invuln = INVULNERAVEL
        if est.vidas <= 0:
            est.vivo = False
            return True
    if resgatar:
        _resgatar(fase, est)
    return False


def passo(fase, est, pressionado, apertou, dt=PASSO_FISICA):
    """
    Avanca a simulacao em um passo.

    `pressionado`: o botao esta segurado.   `apertou`: foi apertado agora.
    """
    if not est.vivo or est.venceu:
        return
    solidos = fase.solidos
    est.tempo += dt
    est.acao = est.dano = None
    est.pousou = False
    est.invuln = max(0.0, est.invuln - dt)
    est.coyote = max(0.0, est.coyote - dt)
    est.buffer = BUFFER_PULO if apertou else max(0.0, est.buffer - dt)

    # 1. anda para a direita; se entrou numa parede, bateu
    est.x += fase.vx * dt
    c_dir = _colunas(est.x)[1]
    if any((c_dir, ty) in solidos for ty in _linhas(est.y)):
        if ferir(fase, est, "parede"):
            return

    # 2. na zona de uma ponte de eco o botao significa "sustentar", nao pular
    ponte = fase.ponte_em(est.x + JOGADOR_TAM * 0.5)
    est.ponte = ponte
    if ponte is None:
        est.carona = None
    elif apertou:
        est.acao = "sustentar"
        est.buffer = 0.0

    # 3. gravidade e colisao vertical com o que e solido
    g = fase.gravidade * (PONTE_GRAVIDADE if ponte is not None else 1.0)
    est.vy = min(est.vy + g * dt, fase.v_pulo * 1.5)
    est.y += est.vy * dt
    estava_no_chao = est.no_chao
    est.no_chao = False
    c0, c1 = _colunas(est.x)
    if est.vy > 0.0:
        ty = int((est.y + JOGADOR_TAM - 0.001) // TILE)
        if (c0, ty) in solidos or (c1, ty) in solidos:
            est.y = ty * TILE - JOGADOR_TAM
            est.vy = 0.0
            est.no_chao = True
    elif est.vy < 0.0:
        ty = int(est.y // TILE)
        if (c0, ty) in solidos or (c1, ty) in solidos:
            est.y = (ty + 1) * TILE
            est.vy = 0.0

    # 4. a ponte segura Leo enquanto a nota e sustentada (ou ele esta de carona)
    est.sustentando = False
    if ponte is not None and not est.no_chao and est.x + JOGADOR_TAM > ponte.x0:
        pes = est.y + JOGADOR_TAM
        if ((pressionado or est.carona is ponte) and est.vy >= 0.0 and
                ponte.y <= pes <= ponte.y + PONTE_RESGATE):
            est.y = ponte.y - JOGADOR_TAM
            est.vy = 0.0
            est.no_chao = True
            est.sustentando = True

    # 5. invulneravel, Leo nunca cai abaixo da linha segura
    if est.invuln > 0.0 and est.vy >= 0.0:
        linha = linha_segura(fase, est)
        if est.y + JOGADOR_TAM > linha:
            est.y = linha - JOGADOR_TAM
            est.vy = 0.0
            est.no_chao = True

    if est.no_chao:
        est.coyote = COYOTE
        est.pousou = not estava_no_chao
        if est.pousou:
            est.pouso = est.tempo

    # 6. caiu no abismo
    if est.y > fase.limite_baixo and ferir(fase, est, "abismo"):
        return

    # 7. cacos
    if est.invuln <= 0.0:
        bx, by, bw, bh = caixa_perigo(est)
        for tx in (c0, c1):
            for p in fase.col_perigos.get(tx, ()):
                if p.colide(bx, by, bw, bh):
                    if ferir(fase, est, "perigo"):
                        return
                    break
            if est.dano:
                break

    # 8. pulo (fora da zona de ponte)
    if ponte is None and est.buffer > 0.0 and (est.no_chao or est.coyote > 0.0):
        est.vy = -fase.v_pulo
        est.no_chao = False
        est.coyote = 0.0
        est.buffer = 0.0
        est.acao = "pulo"

    if est.x >= fase.fim_x:
        est.venceu = True
