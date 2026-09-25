"""
As fases: modelo, construtor ritmico e as tres partituras.

O jogador anda sempre para a direita com velocidade constante, entao a
posicao horizontal e uma funcao do tempo:

    x = batida * TILES_POR_BATIDA * TILE

A fisica e calibrada para que um pulo dure exatamente UMA batida e cubra
exatamente 4 tiles. Assim, colocar um obstaculo na coluna C equivale a exigir
um pulo na batida C / 4: a fase e escrita como uma partitura de batidas e o
Construtor traduz a partitura em geometria.
"""

from .audio import TRILHAS
from .config import (TILE, TILES_POR_BATIDA, ALTURA_PULO, LINHA_CHAO,
                     PONTE_ZONA, TEMAS)

PROFUNDIDADE = 8      # linhas de bloco solido abaixo do topo do chao

# Colunas: (uma vaga a cada quantos tiles de chao plano, % das vagas que ganham
# coluna). Nas ilhas elas sao ruinas espacadas, nao uma cerca ao longo da fase.
COLUNAS = {"ilhas": (12, 55), "eclipse": (12, 65)}
COLUNAS_PADRAO = (6, 100)

# Largura da hitbox de um caco (fracao do tile) conforme o numero de pontas.
# O desenho ocupa o tile inteiro; a hitbox e menor para raspar nao matar.
LARGURA_HITBOX = {1: 0.30, 2: 0.45, 3: 0.60}


class Perigo:
    """Caco de ruido: um ou mais triangulos mortais dentro de um tile."""

    def __init__(self, x, y, w, h, quantidade=1):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.quantidade = quantidade
        self.hw = w * LARGURA_HITBOX[quantidade]
        self.hx = x + (w - self.hw) * 0.5
        self.hy = y + h * 0.5          # so a metade de cima do caco e "pontuda"
        self.hh = h * 0.5

    def colide(self, bx, by, bw, bh):
        return (bx < self.hx + self.hw and bx + bw > self.hx and
                by < self.hy + self.hh and by + bh > self.hy)


class Ponte:
    """Ponte de eco: so e solida enquanto o jogador segura o botao."""

    def __init__(self, x0, x1, y, batida):
        self.x0, self.x1, self.y = x0, x1, y
        self.zona_x0 = x0 - PONTE_ZONA   # a partir daqui o botao significa "sustentar"
        self.batida = batida


class Deco:
    """Enfeite de cenario (coluna ou portal). Nao colide com nada."""

    def __init__(self, tipo, x, y, w, h, variante=0):
        self.tipo, self.x, self.y, self.w, self.h = tipo, x, y, w, h
        self.variante = variante      # qual dos desenhos da coluna, quando ha varios


class Fase:
    def __init__(self, ident, nome, dificuldade, cancao):
        self.ident = ident
        self.nome = nome
        self.dificuldade = dificuldade
        self.cancao = cancao
        self.tema = TEMAS[cancao]
        self.trilha = TRILHAS[cancao]

        self.bpm = self.trilha.bpm_grade
        self.dur_batida = 60.0 / self.bpm
        self.vx = TILES_POR_BATIDA * TILE / self.dur_batida
        # gravidade e impulso que fazem o pulo durar 1 batida e subir ALTURA_PULO
        self.gravidade = 8.0 * ALTURA_PULO / self.dur_batida ** 2
        self.v_pulo = 4.0 * ALTURA_PULO / self.dur_batida

        self.chao_y = LINHA_CHAO * TILE
        self.limite_baixo = (LINHA_CHAO + PROFUNDIDADE) * TILE

        self.solidos = set()      # {(tx, ty)} de tudo que e solido
        self.chao_col = {}        # tx -> linha do topo do chao naquela coluna
        self.blocos = []          # [(tx, ty)] blocos soltos (torres)
        self.perigos = []
        self.col_perigos = {}     # tx -> [perigos naquela coluna]
        self.pontes = []
        self.marcas = []          # [(x, y)] guias de "pule aqui"
        self.decos = []
        self.acoes = []           # batidas em que o jogador precisa agir
        self.fim_x = 0.0
        self.duracao = 0.0

    def ponte_em(self, x):
        """Ponte de eco cuja zona contem `x`, ou None."""
        for p in self.pontes:
            if p.zona_x0 <= x <= p.x1:
                return p
        return None

    def nivel_chao(self, tx):
        """Linha do chao na coluna `tx` (ou na primeira coluna a frente com chao)."""
        for c in range(tx, tx + 40):
            if c in self.chao_col:
                return self.chao_col[c]
        return LINHA_CHAO


class Construtor:
    """
    Escreve a fase a partir de uma partitura.

    `b` e o cursor de tempo (em batidas) e `nivel` o cursor de altura (linha do
    grid). Cada trecho consome batidas, pode mudar o nivel e devolve o proprio
    construtor, para encadear chamadas.

    Onde fica cada obstaculo em relacao a coluna `j` do pulo:

        caco    j + 2   (o apice do arco)
        torre   j + 2   (um bloco solto: pular cedo demais so pousa em cima dele)
        degrau  j + 3   (a quina; da folga igual para o toque cedo e atrasado)
        vao     j + 1   (2 tiles de buraco)
    """

    def __init__(self, fase):
        self.f = fase
        self.b = 0.0
        self.nivel = LINHA_CHAO

    # ------------------------------------------------------------ primitivas
    def col(self, batida):
        return int(round(batida * TILES_POR_BATIDA))

    def piso(self, c0, c1):
        """Chao solido nas colunas [c0, c1), no nivel atual."""
        self.abrir(c0, c1)
        for tx in range(c0, c1):
            self.f.chao_col[tx] = self.nivel
            for ty in range(self.nivel, self.nivel + PROFUNDIDADE):
                self.f.solidos.add((tx, ty))

    def abrir(self, c0, c1):
        """Tira o chao das colunas [c0, c1): abre um abismo."""
        for tx in range(c0, c1):
            n = self.f.chao_col.pop(tx, None)
            if n is not None:
                for ty in range(n, n + PROFUNDIDADE):
                    self.f.solidos.discard((tx, ty))

    def bloco(self, tx, ty):
        self.f.solidos.add((tx, ty))
        self.f.blocos.append((tx, ty))

    def caco(self, tx, ty=None, quantidade=1):
        n = self.nivel if ty is None else ty
        self.f.perigos.append(Perigo(tx * TILE, (n - 1) * TILE, TILE, TILE, quantidade))

    def marca(self, batida):
        """Registra uma acao exigida e a guia visual na coluna dela."""
        self.f.acoes.append(round(batida, 3))
        self.f.marcas.append((self.col(batida) * TILE, self.nivel * TILE))

    # --------------------------------------------------------------- trechos
    def descanso(self, batidas):
        self.piso(self.col(self.b), self.col(self.b + batidas))
        self.b += batidas
        return self

    def cacos(self, batidas, intervalo=2, quantidade=1):
        """Um salto a cada `intervalo` batidas, sobre um caco de `quantidade` pontas."""
        b0 = self.b
        self.descanso(batidas)
        b = b0
        while b + intervalo <= b0 + batidas:
            self.marca(b)
            self.caco(self.col(b) + 2, quantidade=quantidade)
            b += intervalo
        return self

    def sincopado(self, batidas):
        """Saltos em 0, 1.5, 3, 4.5...: o ritmo pontuado."""
        b0 = self.b
        self.descanso(batidas)
        b = b0
        while b + 1.5 <= b0 + batidas:
            self.marca(b)
            self.caco(self.col(b) + 2)
            b += 1.5
        return self

    def vaos(self, batidas, intervalo=2, largura=2):
        """Buracos no chao, com cacos no fundo."""
        b0 = self.b
        self.descanso(batidas)
        b = b0
        while b + intervalo <= b0 + batidas:
            j = self.col(b)
            self.marca(b)
            self.abrir(j + 1, j + 1 + largura)
            for tx in range(j + 1, j + 1 + largura):
                self.caco(tx, self.nivel + 3)
            b += intervalo
        return self

    def torres(self, batidas, intervalo=2):
        """Um bloco solto no topo do arco do pulo: atrasar e bater de frente nele."""
        b0 = self.b
        self.descanso(batidas)
        b = b0
        while b + intervalo <= b0 + batidas:
            self.marca(b)
            self.bloco(self.col(b) + 2, self.nivel - 1)
            b += intervalo
        return self

    def ponte(self, batidas):
        """Abismo com uma ponte de eco: toque na batida e segure por `batidas`."""
        b0 = self.b
        j0, j1 = self.col(b0), self.col(b0 + batidas)
        self.marca(b0)
        self.abrir(j0, j1)
        for tx in range(j0, j1):
            self.caco(tx, self.nivel + 4)
        self.f.pontes.append(Ponte(j0 * TILE, j1 * TILE, self.nivel * TILE, b0))
        self.piso(j1, j1 + 8)                # duas batidas de descanso depois
        self.b = b0 + batidas + 2
        return self

    # ---------------------------------------------------------------- relevo
    def subir(self, degraus, intervalo=2):
        """Sobe um tile por salto. A quina do degrau fica na coluna j + 3."""
        for _ in range(degraus):
            j = self.col(self.b)
            self.piso(j, j + 3)
            self.marca(self.b)
            self.nivel -= 1
            self.piso(j + 3, self.col(self.b + intervalo))
            self.b += intervalo
        return self

    def descer(self, degraus):
        """
        Desce um tile por batida, de graca: descer nunca custa um pulo. O degrau
        fica no COMECO da batida, para sobrar chao plano antes da proxima marca.
        """
        for _ in range(degraus):
            self.nivel += 1
            self.descanso(1)
        return self

    def zigue_zague(self, pares, intervalo=2):
        """Sobe um degrau e desce outro: o chao vira uma onda."""
        for k in range(pares * 2):
            subindo = k % 2 == 0
            j = self.col(self.b)
            corte = 3 if subindo else 4      # descendo, a quina pode ficar no pouso
            self.piso(j, j + corte)
            self.marca(self.b)
            self.nivel += -1 if subindo else 1
            self.piso(j + corte, self.col(self.b + intervalo))
            self.b += intervalo
        return self

    # ----------------------------------------------------------- finalizacao
    def fim(self, batidas=6):
        f = self.f
        c1 = self.col(self.b + batidas)
        self.piso(self.col(self.b), c1 + 40)
        self.b += batidas
        f.fim_x = c1 * TILE
        f.duracao = self.b * f.dur_batida
        f.acoes.sort()
        for p in f.perigos:
            f.col_perigos.setdefault(int(p.x // TILE), []).append(p)
        # o portal de volta e so cenario: solido, mataria o jogador na chegada
        f.decos.append(Deco("portal", c1 * TILE, (self.nivel - 4) * TILE,
                            TILE * 2, TILE * 4))
        self._decorar()
        return f

    def _decorar(self):
        """
        Uma coluna a cada 6 colunas de chao plano, longe dos obstaculos.
        O bosque nao ganha enfeite nenhum: so o fundo de colinas e a lua.
        """
        f = self.f
        if f.cancao == "bosque":
            return
        espaco, chance = COLUNAS.get(f.cancao, COLUNAS_PADRAO)
        ocupadas = {int(p.x // TILE) for p in f.perigos}
        ocupadas |= {int(x // TILE) for x, _ in f.marcas}
        # o portal de casa e o fim da fase: nenhuma coluna plantada na frente dele
        ocupadas |= {int(d.x // TILE) + k for d in f.decos if d.tipo == "portal"
                     for k in range(int(d.w // TILE))}
        # nem atravessando o pilar de uma ponte ou um bloco solto
        for p in f.pontes:
            for q in (int((p.x0 - 6) // TILE), int((p.x1 + 6) // TILE)):
                ocupadas |= {q - 1, q, q + 1}
        ocupadas |= {tx for tx, _ in f.blocos}
        for tx, n in f.chao_col.items():
            plano = f.chao_col.get(tx - 1) == n == f.chao_col.get(tx + 1)
            sorteio = (tx * 2654435761 >> 7) % 100        # fixo por coluna
            if (tx % espaco == espaco // 2 and plano and tx not in ocupadas
                    and sorteio < chance):
                alt = TILE * (2 + tx % 2)
                f.decos.append(Deco("coluna", tx * TILE, n * TILE - alt, TILE, alt,
                                    variante=tx // espaco))


# ---------------------------------------------------------------- partituras
def _fase1():
    """Bosque: so pulos simples e a primeira ponte de eco. Batidas largas."""
    c = Construtor(Fase(0, "BOSQUE DOS ECOS", "FACIL", "bosque"))
    c.descanso(6)
    c.cacos(12, intervalo=4)                 # um salto a cada 3,2 s
    c.cacos(12, intervalo=2)                 # dobra a densidade
    c.descanso(2)
    c.subir(4)                               # 10 -> 6
    c.cacos(10, intervalo=2)
    c.vaos(8, intervalo=4)
    c.ponte(4)                               # 1a nota longa
    c.subir(3)                               # 6 -> 3
    c.torres(12, intervalo=3)
    c.cacos(8, intervalo=2, quantidade=2)
    c.descer(5)                              # 3 -> 8
    c.cacos(10, intervalo=2, quantidade=2)
    c.ponte(6)
    c.subir(3)                               # 8 -> 5
    c.cacos(8, intervalo=2)
    c.descer(5)                              # 5 -> 10
    c.cacos(6, intervalo=2)
    c.descanso(2)
    return c.fim(6)


def _fase2():
    """Ilhas: torres, sincope e pontes mais longas."""
    c = Construtor(Fase(1, "ILHAS SUSPENSAS", "NORMAL", "ilhas"))
    c.descanso(8)
    c.cacos(16, intervalo=2)
    c.cacos(12, intervalo=2, quantidade=2)
    c.descanso(2)
    c.subir(5)                               # 10 -> 5
    c.vaos(12, intervalo=2)
    c.torres(16, intervalo=4)
    c.ponte(6)
    c.subir(3)                               # 5 -> 2, o ponto mais alto
    c.cacos(16, intervalo=4, quantidade=3)
    c.descer(6)                              # 2 -> 8
    c.cacos(10, intervalo=2)
    c.sincopado(12)
    c.descanso(2)
    c.cacos(16, intervalo=2)
    c.descanso(2)
    c.subir(5)                               # 8 -> 3
    c.torres(12, intervalo=2)
    c.ponte(8)
    c.descer(7)                              # 3 -> 10
    c.cacos(12, intervalo=2, quantidade=2)
    c.zigue_zague(2)
    c.cacos(12, intervalo=2)
    c.descanso(2)
    return c.fim(8)


def _fase3():
    """Cidadela: tudo junto, com saltos a cada batida."""
    c = Construtor(Fase(2, "CIDADELA DO ECLIPSE", "DIFICIL", "eclipse"))
    c.descanso(6)
    c.cacos(12, intervalo=2, quantidade=2)
    c.cacos(12, intervalo=1)                 # um salto por batida
    c.descanso(2)
    c.subir(6)                               # 10 -> 4
    c.cacos(12, intervalo=2, quantidade=3)
    c.vaos(12, intervalo=2)
    c.torres(16, intervalo=2)
    c.ponte(8)
    c.sincopado(12)
    c.descer(7)                              # 4 -> 11
    c.cacos(10, intervalo=2)
    c.cacos(12, intervalo=2, quantidade=2)
    c.torres(12, intervalo=2)
    c.zigue_zague(3)
    c.subir(8)                               # 11 -> 3, a torre inteira
    c.cacos(12, intervalo=1)
    c.ponte(8)
    c.sincopado(12)
    c.cacos(12, intervalo=1)
    c.descer(7)                              # 3 -> 10, o portal de casa
    c.cacos(12, intervalo=2, quantidade=3)
    c.cacos(10, intervalo=1)
    c.descanso(2)
    return c.fim(8)


_CONSTRUTORES = (_fase1, _fase2, _fase3)
_cache = {}


def carregar(indice):
    """Devolve a fase `indice` (construida uma unica vez)."""
    if indice not in _cache:
        _cache[indice] = _CONSTRUTORES[indice]()
    return _cache[indice]


def todas():
    return [carregar(i) for i in range(len(_CONSTRUTORES))]
