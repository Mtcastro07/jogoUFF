"""
As fases: modelo, construtor ritmico e as partituras.

O jogador anda sempre para a direita, numa velocidade que so muda nos portais
de velocidade, entao a posicao horizontal e uma funcao do tempo:

    x = batida * tiles por batida * TILE        (em cada trecho de velocidade)

A fisica e calibrada para que todo pulo dure um numero inteiro de batidas
(sai na batida e pousa na batida) e cubra exatamente o comprimento L do pulo;
o toque rapido so faz um arco mais baixo, que pousa no mesmo lugar. Assim,
colocar um obstaculo no meio do arco equivale a exigir um pulo na batida
certa: a fase e escrita como uma partitura de batidas e o Construtor traduz a
partitura em geometria.

Mexeu numa partitura? Rode o validador, que joga a fase com um robo (toques
perfeitos, adiantados, atrasados e sorteados dentro da janela BOM):

    ./.venv/bin/python ferramentas/validar_fases.py
"""

import bisect
import math

from .audio import TRILHAS
from .simulacao import MOLA_ALTURA
from .config import JOGADOR_TAM
from .config import (TILE, LINHA_CHAO, TEMAS, ALPHA, FOLGA_CACO, PULO_MINIMO,
                     CORTE_PULO, JANELA_BOM)

PROFUNDIDADE = 8      # linhas de bloco solido abaixo do topo do chao

# O pulo de cada mundo: (batidas no ar, tiles por batida, altura em tiles).
# O pulo dura UMA batida e cobre 6 tiles (7 na cidadela); o que muda e o
# andamento: 84 BPM no bosque (0,7 s no ar), 110 nas ilhas (0,55 s) e 150 na
# cidadela (0,4 s) -- o mundo acelera junto com a musica, como pede o GDD.
PULO = {"bosque": (1, 6, 3.5), "dunas": (1, 6, 3.5), "ilhas": (1, 6, 3.5),
        "geleira": (1, 6, 3.5), "eclipse": (1, 7, 3.5)}
# O mundo que ensina e so de toques: la o pulo e sempre o inteiro, segurar o
# botao nao pula de novo.
SO_TOQUES = {"bosque"}
# As guias de "pule aqui" so aparecem no mundo que ensina. Dali em diante o
# jogador le o cenario e a musica sozinho (as referencias do GDD: Geometry Dash
# e Rhythm Heaven).
GUIAS = {"bosque"}

# O pulo baixo (um toque rapido): o botao solto so vale depois que o Leo sobe
# ALTURA_CORTE da altura -- dali o arco para em PULO_MINIMO (simulacao._baixar).
ALTURA_CORTE = (PULO_MINIMO - CORTE_PULO ** 2) / (1.0 - CORTE_PULO ** 2)

# Colunas: (uma vaga a cada quantos tiles de chao plano, % das vagas que ganham
# coluna). Nas ilhas elas sao ruinas espacadas, nao uma cerca ao longo da fase.
COLUNAS = {"ilhas": (12, 55), "eclipse": (12, 65)}
COLUNAS_PADRAO = (6, 100)
# No bosque, no lugar das colunas: arvores e moitas, bem mais juntas -- e mata
ARVOREDO = (5, 80)
# enfeites miudos de qualquer mundo: (de quantas em quantas colunas, chance em %)
ENFEITES = (4, 70)
# O ENXAME (das dunas em diante): paira sobre o chao plano e so fere quem pula
# -- a pausa da partitura virou obstaculo. (largura, do pe ao topo acima do
# chao), em px: o pe fica bem acima da cabeca de quem corre, e a faixa pega
# tanto o alto do pulo baixo quanto o do inteiro.
ENXAME = (30, 74, 198)
# O PINGENTE (da geleira em diante): cristais pendurados de uma laje de gelo,
# no alto do arco, sobre um caco. O pulo inteiro bate neles; o toque rapido
# (o pulo baixo) passa por baixo. E o obstaculo que pede o botao SOLTO.
# (largura, do pe ao topo acima do chao), em px: o pe fica acima do alto de
# um toque de ate ~0,11 s e abaixo do alto do pulo inteiro.
PINGENTE = (72, 180, 300)
# OS SILENCIOS: segurar o botao faz o Leo pular a cada pouso -- em toda batida.
# Onde a partitura so pede pulo em toda batida, segurar e jogar certo; mas nas
# batidas VAZIAS (o chao entre dois saltos, a pausa) a musica pede silencio. O
# construtor anota essas batidas e, no fim, poe um enxame em algumas delas, o
# minimo para que, de qualquer acao, segurar o botao bata num "nao pule" em ate
# SILENCIO batidas. Nenhum pulo da partitura muda: so as batidas sem pulo ganham
# o que as guarda. O mundo que ensina fica de fora (la segurar nao repete o pulo).
SILENCIO = 10
# o nome do que paira no ar em cada mundo (a legenda da primeira vez)
NOME_ENXAME = {"dunas": "ENXAME", "ilhas": "REVOADA", "geleira": "MORCEGOS", "eclipse": "MORCEGOS"}
# Onde a partitura pede pulo em TODA batida nao ha batida vazia: ali o que
# separa quem joga de quem segura e a altura. Um caco ganha o que pende no alto
# do arco (o pingente de cada mundo) e pede o toque rapido -- o pulo continua
# na mesma batida. So quando nao ha batida vazia que sirva.
NOME_PINGENTE = {"ilhas": "CRISTAIS", "geleira": "PINGENTE", "eclipse": "ESPETOS"}


def perfil_padrao(quantidade, w=TILE, h=TILE, folga=FOLGA_CACO):
    """
    [topo do caco em cada x do tile]: `quantidade` triangulos lado a lado, base
    no pe do tile e ponta a 3 px do alto -- o caco desenhado por codigo
    (arte._caco_parado). A arte de cada fase troca isto pelo perfil do proprio
    desenho (mundo.preparar). `folga` px de cada ponta nao contam.
    """
    larg = w // quantidade
    meio = larg / 2.0
    perfil = []
    for x in range(w):
        dx = x % larg
        if x >= larg * quantidade or not 2 <= dx <= larg - 2:
            perfil.append(h)                   # sem caco nesta coluna de pixels
            continue
        alto = (1.0 - abs(dx - meio) / (meio - 2)) * (h - 3)
        perfil.append(min(h, int(h - alto) + folga))
    return perfil


class Perigo:
    """
    Caco de ruido: um ou mais triangulos mortais dentro de um tile. Colide pelo
    DESENHO: em cada x ele e solido do seu perfil para baixo. Os do fundo de
    um fosso sao `fatal`: quem cai la nao volta.
    """

    def __init__(self, x, y, w, h, quantidade=1, fatal=False):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.quantidade = quantidade
        self.fatal = fatal
        self.variante = 0         # qual dos desenhos da fase (mundo.preparar sorteia)
        self.perfil = perfil_padrao(quantidade, int(w), int(h))

    def colide(self, bx, by, bw, bh):
        """A caixa (bx, by, bw, bh) encosta no desenho do caco?"""
        a = max(0, int(bx - self.x))
        b = min(len(self.perfil), int(math.ceil(bx + bw - self.x)))
        if a >= b or by >= self.y + self.h:
            return False
        return by + bh > self.y + min(self.perfil[a:b])


class Deco:
    """Enfeite de cenario (coluna, arvore ou portal). Nao colide com nada."""

    def __init__(self, tipo, x, y, w, h, variante=0):
        self.tipo, self.x, self.y, self.w, self.h = tipo, x, y, w, h
        self.variante = variante      # qual dos desenhos da coluna, quando ha varios
        self.ato = None               # a parte da musica em que ele esta (so os enfeites)


class Fase:
    def __init__(self, ident, nome, dificuldade, cancao):
        self.ident = ident        # a posicao na lista de fases (carregar() acerta)
        self.semente = ident      # o numero de nascimento: os sorteios fixos da fase
        self.nome = nome
        self.dificuldade = dificuldade
        self.cancao = cancao
        self.tema = TEMAS[cancao]
        self.trilha = TRILHAS[cancao]

        self.bpm = self.trilha.bpm_grade
        self.dur_batida = 60.0 / self.bpm
        self.batidas_pulo, self.tiles_batida, altura = PULO[cancao]
        self.altura_pulo = altura * TILE
        self.vx = self.tiles_batida * TILE / self.dur_batida
        # gravidade e impulso que fazem o pulo durar `batidas_pulo` batidas e
        # subir `altura_pulo`
        self.duracao_pulo = self.batidas_pulo * self.dur_batida
        self.gravidade = 8.0 * self.altura_pulo / self.duracao_pulo ** 2
        self.v_pulo = 4.0 * self.altura_pulo / self.duracao_pulo
        self.altura_corte = ALTURA_CORTE * self.altura_pulo   # veja simulacao.passo
        self.so_toques = cancao in SO_TOQUES
        self.guias = cancao in GUIAS
        self.alpha = cancao in ALPHA          # desenhada como a versao alpha (jogo/alpha.py)
        # trechos de velocidade: [x a partir do qual vale] e [vx]; os portais
        # (x, y, mais rapido?) marcam no chao onde a velocidade muda
        self.vel_x, self.vel_vx = [-1e9], [self.vx]
        self.portais = []

        self.chao_y = LINHA_CHAO * TILE
        self.limite_baixo = (LINHA_CHAO + PROFUNDIDADE) * TILE

        self.solidos = set()      # {(tx, ty)} de tudo que e solido
        self.chao_col = {}        # tx -> linha do topo do chao naquela coluna
        self.blocos = []          # [(tx, ty)] blocos soltos (torres)
        self.celulas_bloco = set()   # os mesmos, para a fisica: um bloco se quebra
        self.perigos = []
        self.col_perigos = {}     # tx -> [perigos naquela coluna]
        self.marcas = []          # [(x, y)] guias de "pule aqui"
        self.saltos = []          # [(batida, x exato, y)] de onde sai cada pulo
        self.brilhos = []         # [(x, y, alto?)] ecos para pegar no ar, em ordem de x
        self.molas = []           # [(x inicial, x final, y do chao)] molas, em ordem de x
        self.molas_x = []         # os x iniciais (para a busca)
        self.orbes = []           # [(x, y, alcance x, alcance y)] orbes de pulo no ar
        self.brilhos_extra = []   # os ecos do arco das molas
        self.pontes = set()       # {(tx, ty)} passarelas no ar: so seguram quem vem de cima
        self.duplas = []          # [(batida inicial, batida final)] das rotas duplas
        self.voadores = []        # [(x, y, w, h, tipo)] no ar: "enxame" ou "pingente"
        self.guardas = []         # batidas que ja tem um enxame ou pingente
        self.folgas = []          # [(batida, x, chao)] batidas vazias que podem ganhar um enxame
        self.toques = []          # [(batida, x, chao)] saltos de caco que podem virar pingente
        self.col_voadores = {}    # tx -> [os voadores que passam naquela coluna]
        self.curtos = set()       # batidas das acoes que pedem o toque rapido (pingentes)
        self.dicas = []           # [(x, y, texto)] a 1a vez de cada mecanica, escrita no mundo
        self.decos = []
        self.acoes = []           # batidas em que o jogador precisa agir
        self.secoes = []          # [(nome, batida)]: introducao, A, B, A'
        self.secoes_x = []        # o x em que cada parte comeca: os ATOS do mapa
        self.fim_x = 0.0
        self.duracao = 0.0

    def ato(self, x):
        """
        Em qual parte da musica o ponto `x` do mapa esta (0 = introducao, 1 = A,
        2 = B, 3 = A'). O mapa muda de cara junto com a musica: cada ato tem os
        seus enfeites, os seus tipos de perigo e o seu clima no ceu.
        """
        return max(0, bisect.bisect_right(self.secoes_x, x) - 1)

    def vx_em(self, x):
        """Velocidade horizontal (px/s) de quem esta em `x`."""
        return self.vel_vx[bisect.bisect_right(self.vel_x, x) - 1]

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

    A peca basica e a FRASE (veja `frase`): passos com um obstaculo cada, na
    batida atual. Todo pulo cobre o comprimento L (batidas no ar x tiles por
    batida: 6 nos tres mundos, 8 depois do portal dourado das ilhas) e pousa
    na batida seguinte; o toque rapido so e mais BAIXO (metade da altura).
    Tudo tem de passar saindo ate uma janela BOM cedo ou tarde. Onde fica cada
    obstaculo em relacao a coluna `j` de onde se pula (as propriedades abaixo):

        caco    j + meio       no meio do arco
        torre   j + degrau     bloco solto: o pulo atrasado passa por cima, o
                               adiantado pousa em cima dele
        vao     j + beira ...  buraco ate j + pouso: 3 tiles, ninguem passa
                               correndo
        ilha    o mesmo buraco; a outra margem mais alta fica em j + margem_alta
        sobe    j + degrau     a quina do degrau; 2 tiles so o pulo inteiro sobe
    """

    def __init__(self, fase):
        self.f = fase
        self.b = 0.0
        self.nivel = LINHA_CHAO
        self.s = fase.tiles_batida        # tiles por batida agora (muda nos portais)
        self._x0, self._b0 = 0.0, 0.0     # onde (tiles) e quando a velocidade mudou
        self._desceu = False              # o ultimo pulo desceu e o proximo vem logo
        self._ditas = set()               # as mecanicas que ja ganharam legenda
        self._eco = True                  # os pulos ganham eco no arco (nao nas rotas duplas)
        # na versao alpha o chao e uma RETA: degrau, buraco e ilha viram caco no
        # chao, descida vira chao -- nas mesmas batidas
        self.plano = fase.alpha
        # chao atras da largada: na tela de espera o Leo esta NO mundo, e nao
        # na beira de um penhasco
        self.piso(-10, 0)

    # ------------------------------------------------------------ primitivas
    @property
    def L(self):
        """Comprimento do pulo INTEIRO (botao segurado), em tiles, na velocidade de agora."""
        return int(round(self.f.batidas_pulo * self.s))

    @property
    def janela(self):
        """Quantos tiles o Leo anda dentro da janela BOM: a folga de sair cedo ou tarde."""
        return JANELA_BOM * self.s

    # Onde cada obstaculo fica, em tiles a frente da coluna de onde se pula,
    # para passar tanto o pulo baixo quanto o inteiro, saindo cedo ou tarde.
    # Os dois pousam no mesmo lugar (L a frente): o baixo so e mais baixo.
    @property
    def meio(self):
        """O caco: no meio do arco."""
        return max(2, int(round(self.L / 2)))

    @property
    def beira(self):
        """
        Onde um buraco comeca: depois de onde sai quem pula atrasado -- mesmo
        com o pouso de antes atrasado por um degrau abaixo.
        """
        return max(2, math.ceil(self.janela + 0.6))

    @property
    def pouso(self):
        """Onde um buraco acaba: antes de onde pousa quem saiu adiantado."""
        return max(self.beira + 2, int(self.L - self.janela + 0.3))

    @property
    def degrau(self):
        """
        A face de algo mais alto que o chao (bloco solto, degrau, muro): logo
        depois do meio do arco, onde o pulo atrasado ja esta por cima dela e o
        adiantado ainda nao desceu. 1 tile o pulo baixo passa; 2, so o inteiro.
        """
        return self.L // 2 + 1

    @property
    def margem_alta(self):
        """A outra margem de um buraco, 1 ou 2 tiles acima (o buraco tem 2 tiles ou mais)."""
        return max(self.beira + 2, self.degrau)

    def _x(self, batida):
        return self._x0 + (batida - self._b0) * self.s

    def col(self, batida):
        return int(round(self._x(batida)))

    def velocidade(self, tiles_por_batida):
        """
        Portal de velocidade: da batida atual em diante o Leo corre
        `tiles_por_batida`. O pulo continua durando as mesmas batidas -- so fica
        mais longo (ou mais curto). Poe o portal num trecho de chao, sem pulo
        atravessando a troca.
        """
        x = self._x(self.b)
        rapido = tiles_por_batida > self.s
        self._x0, self._b0, self.s = x, self.b, tiles_por_batida
        self.f.vel_x.append(x * TILE)
        self.f.vel_vx.append(tiles_por_batida * TILE / self.f.dur_batida)
        self.f.portais.append((x * TILE, self.nivel * TILE, rapido))
        return self

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

    def caco(self, tx, ty=None, quantidade=1, fatal=False):
        n = self.nivel if ty is None else ty
        self.f.perigos.append(Perigo(tx * TILE, (n - 1) * TILE, TILE, TILE, quantidade, fatal))

    def marca(self, batida, eco=True, y=None):
        """Registra uma acao exigida e a guia visual na coluna dela."""
        self.f.acoes.append(round(batida, 3))
        self.f.marcas.append((self.col(batida) * TILE, self.nivel * TILE if y is None else y))
        if eco and self._eco:
            self.f.saltos.append((batida, self._x(batida) * TILE, self.nivel * TILE))

    def _dica(self, chave, x, y, texto):
        """A primeira vez de cada mecanica na fase ganha uma legenda no mundo."""
        if chave not in self._ditas:
            self._ditas.add(chave)
            self.f.dicas.append((x, y, texto))

    def _mola(self, batidas, opcao, atraso=0):
        """
        A MOLA: o pulo que sai dela e o salto grande -- 2 batidas no ar, o
        dobro do comprimento (2L) e MOLA_ALTURA tiles de altura. O toque e na
        batida, como em todo pulo; quem nao toca e lancado no fim da mola.

            opcao None     por cima de uma torre de 3 blocos com um caco no alto
            "vao"          por cima de um abismo largo (2L - 4 tiles)
            -1 a -4        para o alto de um paredao dessa altura
            "orbe"         a mola nao alcanca o paredao de 6 tiles: no alto do
                           arco ha um ORBE, e o toque nele (uma batida depois
                           da mola) e um pulo novo, no ar, que chega la
        """
        f, L, n = self.f, self.L, self.nivel
        if batidas < 2 * f.batidas_pulo - 1e-9:
            raise ValueError(f"'mola' com {batidas} batidas na batida {self.b}: o salto dura "
                             f"{2 * f.batidas_pulo}")
        j, fim = self.col(self.b), self.col(self.b + batidas)
        x = self._x(self.b) * TILE
        chao = n * TILE
        self._dica("mola", x, chao - 2.2 * TILE, "MOLA: TOQUE NA BATIDA")
        if opcao == "orbe":
            self._dica("orbe", x + L * TILE, chao - (MOLA_ALTURA + 1.6) * TILE, "ORBE: TOQUE NO AR")
        self.marca(self.b, eco=False)
        # a mola vai de onde sai quem toca adiantado ate um pouco depois de
        # onde sai quem toca atrasado
        # (`atraso`: quem vem de um degrau abaixo pousa 1 tile mais longe)
        f.molas.append((x - (self.janela + 0.15) * TILE,
                        x + (self.janela + 0.25 + atraso) * TILE, chao))
        arco = lambda k: MOLA_ALTURA * (1.0 - (k - 1.0) ** 2)     # altura a k*L da saida
        ecos = [0.5, 1.0, 1.5]
        if opcao is None:
            self.piso(j, fim)
            for k in range(3):
                self.bloco(j + L, n - 1 - k)
            self.caco(j + L, n - 3)
            ecos = [0.5, 1.5]
        elif opcao == "vao":
            self.piso(j, j + 2 + atraso)
            self._fosso(j + 2 + atraso, j + 2 * L - 2, n + 3)
            self.piso(j + 2 * L - 2, fim)
        elif opcao == "orbe":
            face = j + L + L // 2
            self.piso(j, face)
            self.nivel -= 6
            self.piso(face, fim)
            alcance = (self.janela + 0.25) * TILE
            f.orbes.append((x + L * TILE + JOGADOR_TAM * 0.5,
                            chao - MOLA_ALTURA * TILE - JOGADOR_TAM * 0.5, alcance, 1.35 * TILE))
            self.marca(self.b + f.batidas_pulo, eco=False, y=chao - (MOLA_ALTURA - 1.5) * TILE)
            ecos = [0.5]
            f.brilhos_extra.append((x + 1.5 * L * TILE, chao - (MOLA_ALTURA + 3.5) * TILE, True))
        else:
            face = j + L + 2
            self.piso(j, face)
            self.nivel += opcao
            self.piso(face, fim)
            ecos = [0.5, 1.0]
        for k in ecos:
            f.brilhos_extra.append((x + k * L * TILE, chao - arco(k) * TILE, True))
        self.b += batidas

    def secao(self, nome):
        """Marca onde comeca uma parte da musica (introducao, A, B, A')."""
        self.f.secoes.append((nome, self.b))
        self.f.secoes_x.append(self.col(self.b) * TILE)
        return self

    # ----------------------------------------------------------------- frase
    def frase(self, *passos):
        """
        Uma frase ritmica. Cada passo e (tipo, batidas) ou (tipo, batidas,
        opcao): poe um obstaculo na batida atual e anda `batidas` ate o
        proximo passo.

            "caco"   caco no alto do arco; opcao: 2 ou 3 pontas        pulo
            "torre"  bloco solto de 1 tile no caminho                   pulo
            "vao"    fosso no meio do arco; opcao: largura em tiles     pulo
            "ilha"   o mesmo fosso, e a outra margem mais alta (opcao
                     -1 ou -2 tiles) ou mais baixa (+1, +2)             pulo
            "sobe"   degrau para cima; opcao: 1 ou 2 tiles              pulo
            "mola"   o salto grande, de 2 batidas (veja `_mola`); opcao:
                     nada (torre alta), "vao", -1 a -4 (paredao), "orbe" pulo
            "enxame" chao plano com um enxame no ar a cada batida:
                     quem pula ali se fere                              NAO pular
            "pingente" caco, e cristais de gelo pendurados no alto do
                     arco: so o pulo BAIXO passa                        TOQUE curto
            "desce"  degrau para baixo, logo no comeco; opcao: tiles    de graca
            "pausa"  chao plano                                         de graca

        Um passo com pulo precisa de pelo menos `batidas_pulo` batidas: antes
        disso o Leo ainda esta no ar.

        Tudo cabe no pulo BAIXO (o toque rapido) e no INTEIRO, com a folga da
        janela BOM para os dois lados: nenhum passo pede o botao segurado. Por
        isso nao se sobe 2 tiles de uma vez (o pulo baixo nao alcanca).

        Quem desce um nivel pousa um pouco depois da batida: se o passo
        seguinte vem uma batida depois, o buraco dele comeca 1 tile mais longe.
        """
        for passo in passos:
            tipo, batidas = passo[0], passo[1]
            opcao = passo[2] if len(passo) > 2 else None
            if tipo == "mola" and not self.plano:
                self._mola(batidas, opcao, 1 if self._desceu else 0)
                self._desceu = False
                continue
            if tipo == "mola":
                tipo, opcao = "caco", None
            if self.plano and tipo in ("sobe", "desce", "ilha", "vao"):
                tipo, opcao = {"sobe": "caco", "desce": "pausa", "ilha": "caco", "vao": "caco"}[tipo], None
            if tipo == "enxame" and self.plano:
                tipo = "pausa"
            if tipo == "pingente" and self.plano:
                tipo = "caco"
            if tipo == "pingente":
                if batidas < self.f.batidas_pulo - 1e-9:
                    raise ValueError(f"'pingente' com {batidas} batidas na batida {self.b}")
                self._pingente(batidas, opcao or 1)
                self.b += batidas
                self._desceu = False
                continue
            pula = tipo not in ("pausa", "desce", "enxame")
            if pula and batidas < self.f.batidas_pulo - 1e-9:
                raise ValueError(f"'{tipo}' com {batidas} batidas na batida {self.b}: o pulo "
                                 f"dura {self.f.batidas_pulo} e o Leo ainda estaria no ar")
            if (tipo == "sobe" and (opcao or 1) > 1) or (tipo == "ilha" and (opcao or 0) < -1):
                raise ValueError(f"'{tipo}' subindo {opcao} tiles na batida {self.b}: o pulo "
                                 f"baixo (um toque) so sobe 1 tile")
            j, fim = self.col(self.b), self.col(self.b + batidas)
            q1 = self.beira + (1 if self._desceu else 0)
            # as batidas vazias deste passo: o Leo ja pousou (o pulo dura
            # `batidas_pulo`) e o proximo pulo vem uma batida depois, pelo menos.
            # So em chao plano no mesmo nivel, fora das rotas duplas e nunca
            # logo depois de uma descida (ali o pouso atrasa)
            if (tipo in ("caco", "torre", "vao", "pausa") and not self._desceu and self._eco
                    and not self.f.so_toques):
                k = 0.0 if tipo == "pausa" else self.f.batidas_pulo
                while k <= batidas - 1.0 + 1e-9:
                    if abs(k - round(k)) < 1e-9:
                        x = (self._x(self.b + k) + self.L * 0.5) * TILE + JOGADOR_TAM * 0.5
                        self.f.folgas.append((self.b + k, x, self.nivel * TILE))
                    k += 1.0
            # um salto sobre um caco ou sobre um vao sem mudar de altura: o toque
            # rapido passa igual (o pulo baixo pousa onde o inteiro pousa)
            nivelado = tipo in ("caco", "vao") or (tipo == "ilha" and not opcao)
            if (nivelado and not self._desceu and self._eco and self.f.cancao in NOME_PINGENTE
                    and batidas >= self.f.batidas_pulo - 1e-9):
                x = (self._x(self.b) + self.L * 0.5) * TILE + JOGADOR_TAM * 0.5
                self.f.toques.append((self.b, x, self.nivel * TILE))
            self._desceu = (pula and batidas <= self.f.batidas_pulo + 1e-9 and
                            tipo == "ilha" and (opcao or 0) > 0)
            if pula:
                self.marca(self.b)             # a guia fica na altura de onde se pula
            if tipo == "desce":
                self.nivel += opcao or 1
            if tipo in ("caco", "torre", "vao", "pausa", "desce", "enxame"):
                self.piso(j, fim)
            if tipo == "enxame":
                self._enxame(batidas)
            if tipo == "caco":
                self.caco(j + self.meio, quantidade=opcao or 1)
            elif tipo == "torre":
                self.bloco(j + self.degrau, self.nivel - 1)
            elif tipo == "vao":
                self._fosso(j + q1, j + (q1 + opcao if opcao else self.pouso), self.nivel + 3)
            elif tipo == "ilha":
                desnivel = opcao or 0
                q3 = self.margem_alta if desnivel < 0 else self.pouso
                self.piso(j, j + q1)
                self._fosso(j + q1, j + q3, max(self.nivel, self.nivel + desnivel) + 3)
                self.nivel += desnivel
                self.piso(j + q3, fim)
            elif tipo == "sobe":
                q3 = self.degrau
                self.piso(j, j + q3)
                self.nivel -= opcao or 1
                self.piso(j + q3, fim)
            self.b += batidas
        return self

    def _enxame(self, batidas):
        """
        Um enxame por batida do passo, no ar, onde estaria o alto do arco de
        quem pulasse naquela batida. Quem vem do pulo anterior ja pousou antes
        dele e quem sai para o proximo ainda nao decolou -- mesmo na beira da
        janela BOM: so se fere quem pula onde a musica pede silencio (ou quem
        segura o botao e deixa o Leo pular de novo sozinho).
        """
        f = self.f
        larg, pe, topo = ENXAME
        chao = self.nivel * TILE
        for k in range(int(batidas + 1e-9)):
            x = (self._x(self.b + k) + self.L * 0.5) * TILE + JOGADOR_TAM * 0.5
            f.voadores.append((x - larg * 0.5, chao - topo, larg, topo - pe, "enxame"))
            f.guardas.append(self.b + k)
        self._dica("enxame", (self._x(self.b) + self.L * 0.5) * TILE, chao - topo - 0.9 * TILE,
                   f"{NOME_ENXAME.get(f.cancao, 'ENXAME')}: NAO PULE")

    def _pingente(self, batidas, quantidade):
        """
        Um salto sobre um caco com os cristais pendurados no alto do arco. Quem
        segura o botao (o pulo inteiro) bate neles; o toque rapido passa por
        baixo. O eco do salto e o BAIXO: o premio de quem soltou a tempo.
        """
        f = self.f
        j, fim = self.col(self.b), self.col(self.b + batidas)
        self.piso(j, fim)
        self.caco(j + self.meio, quantidade=quantidade)
        self.marca(self.b, eco=False)
        f.curtos.add(round(self.b, 3))
        larg, pe, topo = PINGENTE
        chao = self.nivel * TILE
        x = (self._x(self.b) + self.L * 0.5) * TILE + JOGADOR_TAM * 0.5
        f.voadores.append((x - larg * 0.5, chao - topo, larg, topo - pe, "pingente"))
        f.guardas.append(self.b)
        f.brilhos_extra.append((x - JOGADOR_TAM * 0.5, chao - f.altura_pulo * PULO_MINIMO, False))
        self._dica("pingente", x, chao - topo - 0.9 * TILE,
                   f"{NOME_PINGENTE.get(f.cancao, 'PINGENTE')}: SO UM TOQUE")

    def _fosso(self, c0, c1, ty):
        """
        Buraco nas colunas [c0, c1), com cacos cravados no fundo (linha ty).
        Quem cai la nao volta: os cacos do fundo sao fatais.
        """
        self.abrir(c0, c1)
        for tx in range(c0, c1):
            self.caco(tx, ty, fatal=True)

    def dupla(self, *passos, altura=2):
        """
        DOIS CAMINHOS: a frase `passos` (so "caco", "torre" e "pausa", e
        terminando numa pausa) corre no chao, e por cima dela, `altura` tiles
        acima, vai uma PASSARELA feita de pedacos, com um vao sob o alto de
        cada pulo. Sobe-se segurando o botao: o pulo inteiro atravessa a
        passarela por baixo e pousa nela; o toque rapido passa por baixo e
        segue pelo chao. La em cima os pulos sao nas mesmas batidas, de pedaco
        em pedaco; quem perde um pulo cai de volta ao chao. Os ecos se dividem
        entre os dois caminhos. No fim a passarela acaba e o Leo desce sozinho.
        """
        if self.plano:
            return self.frase(*passos)
        f = self.f
        if passos[-1][0] != "pausa" or any(p[0] not in ("caco", "torre", "pausa") for p in passos):
            raise ValueError("dupla: so caco, torre e pausa, terminando em pausa")
        saltos, b = [], self.b
        for p in passos:
            if p[0] != "pausa":
                saltos.append((self.col(b), self._x(b) * TILE))
            b += p[1]
        topo = self.nivel - altura
        if not f.so_toques:
            self._dica("dupla", saltos[0][1] + self.L * TILE * 0.5, (topo - 1.6) * TILE,
                       "SEGURE: CAMINHO DE CIMA")
        f.duplas.append((self.b, self.b + sum(p[1] for p in passos)))
        self._eco = False
        self.frase(*passos)
        self._eco = True
        vaos = set()
        for j, _ in saltos[1:]:
            vaos.update(range(j + self.beira, j + self.pouso))
        for tx in range(saltos[0][0] + self.pouso, saltos[-1][0] + self.L + 2):
            if tx not in vaos:
                f.pontes.add((tx, topo))
        # os ecos se dividem: em cima (o caminho seguro), um a cada dois pulos;
        # embaixo (o dos perigos), um eco baixo em todo pulo -- cada caminho
        # paga do seu jeito, e segurar sempre deixa de ser a melhor escolha
        for k, (j, x) in enumerate(saltos[1:]):
            if k % 2 == 0 or f.so_toques:
                f.brilhos_extra.append((x + self.L * TILE * 0.5,
                                        topo * TILE - f.altura_pulo, True))
        for j, x in () if f.so_toques else saltos:
            f.brilhos_extra.append((x + self.L * TILE * 0.5,
                                    self.nivel * TILE - f.altura_pulo * PULO_MINIMO, False))
        return self

    # --------------------------------------------------------------- trechos
    def _repetir(self, tipo, batidas, intervalo, opcao=None):
        """`tipo` a cada `intervalo` batidas ate encher `batidas`; o que sobra e chao."""
        n = int(batidas / intervalo + 1e-9)
        self.frase(*[(tipo, intervalo, opcao)] * n)
        return self.descanso(batidas - n * intervalo)

    def descanso(self, batidas):
        return self.frase(("pausa", batidas)) if batidas > 1e-9 else self

    def cacos(self, batidas, intervalo=2, quantidade=1):
        """Um salto a cada `intervalo` batidas, sobre um caco de `quantidade` pontas."""
        return self._repetir("caco", batidas, intervalo, quantidade)

    def sincopado(self, batidas, quantidade=1):
        """
        O ritmo pontuado: um salto a cada pulo e MEIA batida (1,5 no bosque,
        2,5 nas outras), entao um salto sim, um nao, cai no contratempo.
        """
        return self._repetir("caco", batidas, self.f.batidas_pulo + 0.5, quantidade)

    def vaos(self, batidas, intervalo=2):
        """Buracos no chao, com cacos no fundo."""
        return self._repetir("vao", batidas, intervalo)

    def torres(self, batidas, intervalo=2):
        """Um bloco solto no topo do arco do pulo: atrasar e bater de frente nele."""
        return self._repetir("torre", batidas, intervalo)

    def ilhas(self, desniveis, intervalo=2):
        """Arquipelago: um salto por ilha; cada desnivel e a altura da proxima (-1 sobe)."""
        return self.frase(*[("ilha", intervalo, d) for d in desniveis])

    # ---------------------------------------------------------------- relevo
    def subir(self, degraus, intervalo=2, altura=1):
        """Sobe `altura` tiles por salto (2 tiles pedem o pulo inteiro)."""
        return self.frase(*[("sobe", intervalo, altura)] * degraus)

    def descer(self, degraus):
        """
        Desce um tile por batida, de graca: descer nunca custa um pulo. O degrau
        fica no COMECO da batida, para sobrar chao plano antes da proxima marca.
        """
        return self.frase(*[("desce", 1)] * degraus)

    def colina(self, altura, *topo):
        """Sobe `altura` degraus, faz a frase `topo` la em cima e desce de graca."""
        self.subir(altura)
        self.frase(*topo)
        return self.descer(altura)

    def zigue_zague(self, pares, intervalo=2):
        """Sobe um degrau e desce outro: o chao vira uma onda."""
        if self.plano:
            return self.frase(*[("caco", intervalo)] * (pares * 2))
        for k in range(pares * 2):
            subindo = k % 2 == 0
            j = self.col(self.b)
            # subindo, a quina de um degrau; descendo, a beirada passa sob o
            # alto do arco (quem so pousasse antes dela cairia na hora do pulo)
            corte = self.degrau if subindo else self.meio
            self.piso(j, j + corte)
            self.marca(self.b)
            self.nivel += -1 if subindo else 1
            self.piso(j + corte, self.col(self.b + intervalo))
            self.b += intervalo
        self._desceu = intervalo <= self.f.batidas_pulo + 1e-9
        return self

    # ----------------------------------------------------------- finalizacao
    def _silencios(self):
        """
        Poe um enxame nas batidas vazias, o minimo para que segurar o botao,
        de qualquer acao, encontre um "nao pule" em ate SILENCIO batidas
        (veja SILENCIO). Escolhe sempre a folga mais distante que ainda cabe.
        """
        f = self.f
        if f.so_toques or self.plano or not f.acoes:
            return
        guardas = sorted(f.guardas)
        folgas = sorted(f.folgas)
        ultimo, fim = min(f.acoes), max(f.acoes)
        while ultimo + SILENCIO < fim:
            limite = ultimo + SILENCIO
            ja = [g for g in guardas if ultimo < g <= limite]
            if ja:
                ultimo = ja[-1]
                continue
            cabem = [p for p in folgas if ultimo < p[0] <= limite]
            altos = [p for p in f.toques if ultimo < p[0] <= limite]
            if cabem:
                ultimo = self._enxame_em(*cabem[-1])
            elif altos:
                ultimo = self._pendurar(*altos[-1])
            else:
                # nada cabe nesta janela (uma rota dupla, uma escada): a primeira
                # coisa que servir depois dela, para o trecho ficar o menor possivel
                depois = sorted([(p[0], 0, p) for p in folgas if p[0] > limite] +
                                [(p[0], 1, p) for p in f.toques if p[0] > limite] +
                                [(g, 2, None) for g in guardas if g > limite])
                if not depois:
                    break
                b, qual, p = depois[0]
                ultimo = (self._enxame_em(*p) if qual == 0 else
                          self._pendurar(*p) if qual == 1 else b)
            guardas.append(ultimo)
            guardas.sort()

    def _enxame_em(self, b, x, chao):
        """Um enxame na batida vazia `b` (veja _enxame)."""
        larg, pe, topo = ENXAME
        self.f.voadores.append((x - larg * 0.5, chao - topo, larg, topo - pe, "enxame"))
        self._dica("enxame", x, chao - topo - 0.9 * TILE,
                   f"{NOME_ENXAME.get(self.f.cancao, 'ENXAME')}: NAO PULE")
        return b

    def _pendurar(self, b, x, chao):
        """O caco do salto da batida `b` ganha o pingente no alto do arco (veja _pingente)."""
        f = self.f
        larg, pe, topo = PINGENTE
        f.voadores.append((x - larg * 0.5, chao - topo, larg, topo - pe, "pingente"))
        f.curtos.add(round(b, 3))
        f.saltos = [s for s in f.saltos if abs(s[0] - b) > 1e-6]
        f.brilhos_extra.append((x - JOGADOR_TAM * 0.5, chao - f.altura_pulo * PULO_MINIMO, False))
        self._dica("pingente", x, chao - topo - 0.9 * TILE,
                   f"{NOME_PINGENTE.get(f.cancao, 'PINGENTE')}: SO UM TOQUE")
        return b

    def fim(self, batidas=6):
        f = self.f
        self._silencios()
        c1 = self.col(self.b + batidas)
        self.piso(self.col(self.b), c1 + 40)
        self.b += batidas
        f.fim_x = c1 * TILE
        f.duracao = self.b * f.dur_batida
        f.acoes.sort()
        f.celulas_bloco = set(f.blocos)
        f.pontes_col = {}
        for tx, ty in f.pontes:
            f.pontes_col.setdefault(tx, []).append(ty)
        f.molas.sort()
        f.molas_x = [m[0] for m in f.molas]
        for p in f.perigos:
            f.col_perigos.setdefault(int(p.x // TILE), []).append(p)
        f.voadores.sort()
        for v in f.voadores:
            for tx in range(int(v[0] // TILE), int((v[0] + v[2]) // TILE) + 1):
                f.col_voadores.setdefault(tx, []).append(v)
        # o portal de volta e so cenario: solido, mataria o jogador na chegada
        f.decos.append(Deco("portal", c1 * TILE, (self.nivel - 4) * TILE,
                            TILE * 2, TILE * 4))
        self._brilhos()
        self._decorar()
        return f

    def _brilhos(self):
        """
        Os ECOS: brilhos soltos no ar, no alto do arco de um pulo. Sao a
        escolha do jogador dentro do ritmo: o eco ALTO so pega quem segura o
        botao (o pulo inteiro), o BAIXO so quem da o toque rapido -- e nenhum
        dos dois e obrigatorio, valem pontos. Vem em frases de dois compassos
        (altos, baixos, altos, nada, baixos), para se ler como uma melodia.
        No mundo so de toques o pulo e sempre o inteiro: la sao todos altos.
        """
        f = self.f
        if f.alpha:
            return
        desenho = ("alto", "baixo", "alto", None, "baixo")
        for batida, x, y in f.saltos:
            tipo = desenho[(int(batida // 8) + f.semente) % len(desenho)]
            if tipo is None:
                continue
            alto = tipo == "alto" or f.so_toques
            meio = f.vx_em(x + 1.0) * f.duracao_pulo * 0.5
            sobe = f.altura_pulo * (1.0 if alto else PULO_MINIMO)
            f.brilhos.append((x + meio, y - sobe, alto))
        f.brilhos.extend(f.brilhos_extra)
        f.brilhos.sort()

    def _decorar(self):
        """
        Enfeites de chao plano, longe dos obstaculos: uma coluna a cada tantas
        colunas nas ilhas e na cidadela; arvores e moitas no bosque.
        """
        f = self.f
        espaco, chance = ARVOREDO if f.cancao == "bosque" else COLUNAS.get(f.cancao, COLUNAS_PADRAO)
        ocupadas = {int(p.x // TILE) for p in f.perigos}
        ocupadas |= {int(x // TILE) for x, _ in f.marcas}
        # o portal de casa e o fim da fase: nenhuma coluna plantada na frente dele
        ocupadas |= {int(d.x // TILE) + k for d in f.decos if d.tipo == "portal"
                     for k in range(int(d.w // TILE))}
        # nem atravessando um bloco solto
        ocupadas |= {tx for tx, _ in f.blocos}
        # ...nem perto de nada que o jogador precisa LER: perigo no chao, bloco,
        # e mola ficam com 2 tiles limpos de cada lado
        ler = {int(p.x // TILE) for p in f.perigos if not p.fatal}
        ler |= {tx for tx, _ in f.blocos}
        ler |= {int(a // TILE) + k for a, b, _ in f.molas for k in range(int((b - a) // TILE) + 2)}
        ocupadas |= {tx + k for tx in ler for k in range(-2, 3)}
        ocupadas |= {tx for tx, _ in f.pontes}        # nada atravessando uma passarela
        # ...nem atras de um enxame: ele precisa do ceu limpo para ser lido
        ocupadas |= {tx + k for tx in f.col_voadores for k in range(-1, 2)}
        for tx, n in f.chao_col.items():
            plano = f.chao_col.get(tx - 1) == n == f.chao_col.get(tx + 1)
            sorteio = (tx * 2654435761 >> 7) % 100        # fixo por coluna
            if (tx % espaco == espaco // 2 and plano and tx not in ocupadas
                    and sorteio < chance):
                if f.cancao == "bosque":
                    # a copa e larga: a caixa tem 3 tiles, com a arvore no meio
                    f.decos.append(Deco("arvore", (tx - 1) * TILE, (n - 4) * TILE, 3 * TILE,
                                        4 * TILE, variante=sorteio % 7))
                    continue
                # (as colunas de pedra sairam do caminho: de pe na linha do chao,
                # liam-se como obstaculo. Ficam so os enfeites miudos, abaixo.)
        # os enfeites miudos (lampiao, tocha, ruina...): noutra cadencia, no chao
        # plano que sobrou, nunca colados numa coluna ou arvore
        tomadas = {int(d.x // TILE) + k for d in f.decos for k in range(max(1, int(d.w // TILE)))}
        for tx, n in f.chao_col.items():
            plano = f.chao_col.get(tx - 1) == n == f.chao_col.get(tx + 1)
            sorteio = (tx * 2246822519 >> 9) % 100
            if (tx % ENFEITES[0] == 1 and plano and tx not in ocupadas and tx not in tomadas
                    and sorteio < ENFEITES[1]):
                f.decos.append(Deco("enfeite", tx * TILE, (n - 2) * TILE, TILE, 2 * TILE,
                                    variante=(tx * 40503 >> 4) % 97))
                f.decos[-1].ato = f.ato(tx * TILE)


# ---------------------------------------------------------------- partituras
# Cada fase segue o GDD: INTRODUCAO, PARTE A, PARTE B e a repeticao variada da
# parte A (A'), com as partes em cima das partes da propria musica (os
# compassos anotados sao os da faixa). Cada mundo tem o seu MAPA: o bosque e
# chao corrido com colinas, as ilhas sao um arquipelago, a cidadela e escada,
# muralha e torre.

def _fase1():
    """
    Bosque dos Ecos: o chao da floresta. Colinas que sobem e descem, riachos
    (vaos), troncos caidos (torres) e ravinas cruzadas de pedra em pedra.
    Muito chao firme e respiro: e a fase que ensina, so com toques -- nada
    aqui pede o botao segurado. Musica lo-fi a 84 BPM, pulo de uma batida.

    E a primeira fase, entao e CURTA (cerca de 1min30): cada coisa aparece uma
    vez, a quebra nao vira espera e o fim e o clímax, nao uma repeticao. A
    faixa e uma edicao da original (ferramentas/geradores/editar_musica.py):
    intro (1 compasso), A (12), a primeira metade da quebra (8) e os ultimos
    8 compassos do A'.
    """
    c = Construtor(Fase(0, "BOSQUE DOS ECOS", "FACIL", "bosque"))
    # INTRODUCAO (compasso 2 da faixa): um compasso de corrida e o primeiro caco
    c.secao("introducao")
    c.frase(("pausa", 2), ("caco", 2))
    # PARTE A (3-14, o grave entra): uma coisa nova a cada frase
    c.secao("A")
    c.frase(("caco", 2), ("torre", 2))
    c.colina(2, ("caco", 2), ("caco", 2))
    c.frase(("mola", 4), ("pausa", 2))             # a primeira mola: por cima do tronco alto
    c.dupla(("caco", 2), ("torre", 2), ("caco", 2, 2), ("pausa", 2))   # a ponte de troncos
    c.frase(("vao", 2), ("caco", 2), ("vao", 2), ("vao", 2))           # o riacho e a ravina
    # o morro do contratempo: um salto a cada batida e meia, la em cima
    c.colina(1, ("torre", 2), ("caco", 1.5), ("caco", 1.5), ("caco", 1.5), ("caco", 1.5))
    c.descanso(1)
    # PARTE B (19-26, a quebra sem grave): a serra -- saltos largos, mas com
    # o ritmo variando (4, 2, 2...) em vez de um salto igual a cada compasso
    c.secao("B")
    c.frase(("pausa", 2), ("vao", 4), ("mola", 4, -3))     # a mola sobe o paredao
    c.frase(("caco", 2), ("caco", 2), ("ilha", 4, -1), ("torre", 2), ("torre", 2))
    c.frase(("ilha", 4, 1), ("vao", 2), ("desce", 1, 3), ("pausa", 3))
    # PARTE A' (43-50, o grave de novo e o fim): a onda, a rajada, o portal
    # dourado e o grande salto sobre o rio
    c.secao("A'")
    c.zigue_zague(2)
    c.cacos(6, intervalo=1)
    c.descanso(1)
    c.velocidade(8)                                # o portal dourado: a corrida para casa
    c.descanso(1)
    c.frase(("caco", 2), ("vao", 2), ("caco", 2, 2), ("vao", 2))
    c.frase(("mola", 4, "vao"), ("caco", 2), ("caco", 2))  # o grande salto sobre o rio
    return c.fim(6)


def _fase_dunas():
    """
    Dunas do Chocalho: o deserto de dia, entre o bosque e as ilhas. O andamento
    sobe para 96 BPM, as guias somem e o botao segurado ja vale -- mas quase
    tudo ainda vem de duas em duas batidas, com rajadas curtas de uma. O que e
    daqui: os ENXAMES. Pairam sobre o chao plano nas pausas da musica e so
    ferem quem pula: a fase ensina que o silencio tambem e nota (e que segurar
    o botao a toa custa caro). Trilha original, escrita na grade da fase.

    Cerca de 1min40: introducao de 4 compassos, A e A' de 12 e a quebra
    inteira (12), que e o coracao da fase. Cada desenho aparece uma vez.
    """
    c = Construtor(Fase(3, "DUNAS DO CHOCALHO", "MODERADO", "dunas"))
    # INTRODUCAO (compassos 0-3: chocalho e bordao; o alaude chega no 1)
    c.secao("introducao")
    c.frase(("pausa", 2), ("caco", 2), ("caco", 2))
    c.frase(("enxame", 4))                                   # o primeiro: so correr por baixo
    c.frase(("torre", 2), ("caco", 1), ("caco", 1), ("pausa", 2))           # a virada
    # PARTE A (4-15: a levada inteira; a flauta entra no 8)
    c.secao("A")
    c.frase(("caco", 2), ("caco", 2, 2), ("vao", 2), ("enxame", 2))
    c.frase(("sobe", 2), ("sobe", 2), ("caco", 1), ("caco", 1), ("pausa", 2))  # a duna
    c.frase(("torre", 2), ("enxame", 2), ("desce", 1), ("desce", 1), ("vao", 2))
    c.frase(("mola", 4), ("caco", 2), ("caco", 2, 2))        # por cima do obelisco
    c.frase(("ilha", 2, 0), ("ilha", 2, -1), ("ilha", 2, 1), ("enxame", 2))    # as mesas
    c.frase(("vao", 2), ("vao", 2), ("caco", 1), ("caco", 1), ("caco", 1), ("pausa", 1))
    # PARTE B (16-27: a quebra, so pandeiro e flauta grave): a mesa alta, saltos
    # largos, e o jogo de nota e silencio -- pula, nao pula, pula, nao pula
    c.secao("B")
    c.frase(("pausa", 2), ("mola", 4, -3), ("pausa", 2))     # a mola sobe o paredao
    c.frase(("ilha", 4, 0), ("ilha", 4, -1))
    c.frase(("enxame", 2), ("caco", 2), ("enxame", 2), ("caco", 2))
    c.frase(("ilha", 2, 1), ("torre", 2), ("ilha", 2, 1), ("pausa", 2))
    # a subida (24-27): o tremolo do alaude sobe a duna; no ultimo compasso a
    # musica PARA -- e o Leo cruza o desfiladeiro no silencio, para pousar no golpe
    c.frase(("sobe", 2), ("caco", 2), ("sobe", 2), ("caco", 2))
    c.frase(("caco", 1), ("caco", 1), ("caco", 1), ("caco", 1), ("enxame", 2), ("mola", 2, "vao"))
    # PARTE A' (28-39: tudo de novo, oitava acima, com palmas): a descida da
    # mesa aos saltos, o pula-nao-pula, a ponte da caravana, o ritmo pontuado
    # e o rufo
    c.secao("A'")
    c.frase(("caco", 1), ("caco", 1, 2), ("desce", 1), ("caco", 1), ("caco", 1), ("caco", 1, 2),
            ("desce", 1), ("caco", 1))
    c.frase(("caco", 1), ("caco", 1), ("enxame", 2), ("caco", 1), ("caco", 1, 2), ("enxame", 2))
    c.dupla(("caco", 2), ("caco", 2, 2), ("caco", 2), ("pausa", 2))            # a ponte da caravana
    c.frase(("caco", 1.5), ("caco", 1.5), ("caco", 1), ("caco", 1.5), ("caco", 1.5), ("caco", 1))
    c.frase(("ilha", 1, 1), ("ilha", 1, 0), ("ilha", 2, 1), ("torre", 1), ("torre", 1), ("pausa", 2))
    # o rufo final: cinco saltos seguidos e a mola sobre o ultimo desfiladeiro,
    # para pousar em cima do gongo
    c.frase(("caco", 1), ("caco", 1), ("caco", 1, 2), ("caco", 1), ("caco", 1, 3), ("pausa", 1),
            ("mola", 2, "vao"))
    return c.fim(6)


def _saltos(*desniveis):
    """Uma ilha por batida: a corrida de pedra em pedra do arquipelago."""
    return [("ilha", 1, d) for d in desniveis]


def _fase2():
    """
    Ilhas Suspensas: o chao e um arquipelago sobre o vazio. Quase todo salto
    cruza um vao de 3 tiles e cai numa ilha de outra altura, com cacos nas
    ilhas e o ritmo pontuado. Os PORTAIS DE VELOCIDADE mudam o jogo: o dourado
    acelera a corrida nos dois drops da musica, o azul devolve a velocidade
    normal na quebra. 110 BPM, pulo de uma batida.

    A corrida e em CHAMADA E RESPOSTA: tres ou quatro ilhas de uma batida e
    uma ilha maior, onde o pe toca o chao por uma batida -- no maximo 8 saltos
    iguais seguidos. As revoadas (nao pule) caem nos breques da musica e os
    cristais (so um toque) nas notas curtas. Cerca de 1min40: a faixa e uma
    edicao da original sem o "balanco" depois do primeiro drop
    (ferramentas/geradores/editar_musica.py), e a fase entra no compasso 12.
    """
    c = Construtor(Fase(1, "ILHAS SUSPENSAS", "NORMAL", "ilhas"))
    # INTRODUCAO (compassos 12-15 da faixa, o fim da subida): uma ilha a cada
    # duas batidas, a primeira revoada, a mola de vento e o portal dourado
    c.secao("introducao")
    c.descanso(2)
    c.ilhas((0, -1, 1))
    c.frase(("enxame", 2), ("mola", 4, "vao"))                    # a mola de vento: a ilha distante
    c.descanso(1)
    c.velocidade(8)                                # o portal dourado: o drop
    c.descanso(1)
    # PARTE A (16-31, o primeiro drop): a corrida pelas ilhas, em respostas
    c.secao("A")
    c.frase(("ilha", 1, 0), ("ilha", 1, -1), ("ilha", 2, 1), ("ilha", 1, 0), ("ilha", 1, -1),
            ("ilha", 2, 1))
    c.frase(("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1),
            ("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1))       # o ritmo pontuado
    c.frase(("caco", 2), ("enxame", 2), ("caco", 1), ("ilha", 1, -1), ("ilha", 2, 1))  # o breque
    c.frase(*_saltos(0, -1, 0, 1), ("ilha", 1, -1), ("ilha", 1, 0), ("ilha", 2, 1))
    c.frase(("pingente", 2), ("ilha", 1, -1), ("ilha", 1, 1), ("pingente", 2), ("ilha", 2, 0))
    c.dupla(("caco", 2), ("caco", 1, 2), ("pausa", 1))                 # as lajes no ar
    c.frase(("caco", 2), ("enxame", 2))
    c.frase(("ilha", 1.5, -1), ("ilha", 1.5, 1), ("ilha", 1, 0), ("caco", 1), ("caco", 1, 2),
            ("ilha", 2, 0))
    c.frase(*_saltos(0, -1, 1), ("mola", 4, "vao"))
    c.velocidade(6)                                # o azul: a quebra anda devagar
    c.descanso(1)
    # PARTE B (40-47 da original, a quebra): ilhas de duas batidas, a ilha mais
    # alta pelo orbe, e a subida que prepara o segundo drop
    c.secao("B")
    c.frase(("ilha", 2, -1), ("ilha", 2, 0), ("ilha", 2, 1), ("enxame", 2))
    # a ilha mais alta: a mola nao chega, o ORBE no alto do arco leva ate la
    c.frase(("mola", 3, "orbe"), ("desce", 1, 3), ("pausa", 1), ("desce", 1, 3), ("ilha", 2, 0))
    c.frase(*_saltos(1, 0), ("caco", 1, 2), ("ilha", 1, 0), ("ilha", 1.5, -1), ("ilha", 1.5, 1),
            ("ilha", 1, 0))
    c.frase(("caco", 2), ("enxame", 2), ("ilha", 1, -1), ("ilha", 1, 1))   # o breque da subida
    c.descanso(1)
    c.velocidade(8)
    c.descanso(1)
    # PARTE A' (48-63 da original, o segundo drop): outra corrida, ate o salto
    # final sobre o vazio, que pousa no fim do drop
    c.secao("A'")
    c.frase(*_saltos(0, -1, 0, 1), ("caco", 2), ("enxame", 2))
    c.frase(("ilha", 1, -1), ("ilha", 1, 0), ("ilha", 1.5, 1), ("ilha", 1.5, -1), ("ilha", 1, 1),
            ("caco", 1, 3), ("caco", 1))
    c.frase(("caco", 1), ("caco", 1, 2), ("ilha", 1, -1), ("pingente", 2), ("ilha", 1, 1),
            ("ilha", 2, 0))
    c.frase(("ilha", 1.5, -1), ("ilha", 1.5, -1), ("ilha", 1, 1),
            ("ilha", 1.5, 0), ("ilha", 1.5, 1), ("ilha", 1, 0))
    c.frase(("caco", 2), ("enxame", 2), ("pingente", 2), ("enxame", 2))   # pula, nao, toque, nao
    c.frase(*_saltos(0, 0, -1, 0, 1, 0), ("ilha", 2, 0))
    c.frase(("caco", 1), ("ilha", 1, -1), ("caco", 1), ("ilha", 1, 0),
            ("caco", 1, 2), ("ilha", 1, 1), ("ilha", 2, 0))
    c.dupla(("caco", 1, 3), ("caco", 1), ("pausa", 2))
    c.frase(("mola", 4, "vao"))                    # o ultimo salto, sobre o vazio
    return c.fim(6)


def _fase_geleira():
    """
    Geleira da Aurora: a noite de gelo entre as ilhas e a cidadela. 128 BPM,
    quase tudo a uma batida por pulo, ilhas de gelo, escadas, telhados de neve
    -- e os PINGENTES: cristais pendurados no alto do arco, sobre um caco. Ali
    so o toque rapido passa; quem segura o botao bate neles. Depois de quatro
    mundos em que segurar era opcional, a altura do pulo vira parte do ritmo.
    Trilha original (um trance de cristal), escrita na grade da fase.

    Cerca de 1min40: a introducao inteira, A de 16 compassos, a quebra de 12 e
    o A' de 16. No A' a altura do pulo segue o SINO: nota aguda e caco (pode
    pular alto), nota grave e cristal (so o toque). No maximo 12 saltos iguais
    seguidos.
    """
    c = Construtor(Fase(4, "GELEIRA DA AURORA", "AVANCADO", "geleira"))
    # INTRODUCAO (compassos 0-7: o pad e o arpejo; o bumbo chega no 4)
    c.secao("introducao")
    c.descanso(2)
    c.frase(("caco", 2), ("caco", 2), ("torre", 2), ("caco", 2))
    c.frase(("pingente", 4))                                 # o primeiro, com folga
    c.frase(("caco", 2), ("pingente", 2), ("caco", 2), ("pingente", 2))
    c.frase(("ilha", 2, 0), ("ilha", 2, -1), ("ilha", 2, 1), ("caco", 1), ("caco", 1))
    c.descanso(2)
    # PARTE A (8-23: a levada inteira; o sino canta a partir do 16)
    c.secao("A")
    c.frase(*_saltos(0, -1, 0, 1))
    c.frase(("caco", 1), ("pingente", 1), ("caco", 1), ("pingente", 1))     # alto, baixo, alto, baixo
    c.frase(("sobe", 1), ("caco", 1), ("sobe", 1), ("caco", 1, 2))
    c.descer(2)
    c.descanso(2)
    c.torres(4, intervalo=1)
    c.frase(("caco", 2), ("enxame", 2))                      # o breque: os morcegos
    c.zigue_zague(2, intervalo=1)
    c.frase(("vao", 1), ("vao", 1), ("caco", 1), ("pingente", 1))
    c.descanso(1)
    c.velocidade(7)                                          # o portal dourado: o sino entra
    c.descanso(1)
    c.frase(*_saltos(0, -1, 0, 1), ("ilha", 1, 0), ("ilha", 1, -1), ("ilha", 2, 1))
    c.frase(("caco", 1), ("caco", 1, 2), ("pingente", 1), ("ilha", 1, -1), ("caco", 1),
            ("pingente", 1, 2), ("ilha", 1, 1), ("caco", 1))
    c.frase(("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1),
            ("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1))   # o ritmo pontuado
    c.dupla(("caco", 2), ("caco", 1, 2), ("caco", 1, 3), ("pausa", 1))   # a ponte de gelo
    c.velocidade(6)                                          # o azul: a quebra anda devagar
    c.descanso(1)
    # PARTE B (24-35: a quebra, sem bumbo): saltos largos entre os blocos de
    # gelo, a torre do orbe, e a subida (32-35) que aperta ate o drop
    c.secao("B")
    c.frase(("ilha", 2, -1), ("ilha", 2, 0), ("ilha", 2, 1), ("pingente", 2))
    c.frase(("mola", 3, "orbe"), ("desce", 1, 3), ("pausa", 1), ("desce", 1, 3), ("ilha", 2, 0))
    c.frase(("caco", 2), ("pingente", 2), ("caco", 2, 2), ("pingente", 2))
    c.frase(("ilha", 2, -1), ("torre", 2), ("ilha", 2, 1), ("pingente", 2))
    c.frase(("caco", 1), ("caco", 1), ("pingente", 1), ("caco", 1), ("caco", 1), ("caco", 2, 2),
            ("pingente", 1))
    c.frase(("caco", 1), ("caco", 1), ("caco", 1), ("pingente", 1), ("caco", 1), ("caco", 1, 2))
    c.descanso(1)                                            # o respiro antes do drop
    c.velocidade(7)
    c.descanso(1)
    # PARTE A' (36-51: o drop, o sino uma oitava acima). Os 8 primeiros
    # compassos cantam o sino com o pulo: aguda e caco, grave e cristal
    c.secao("A'")
    c.frase(("caco", 2), ("pingente", 1), ("caco", 1))               # Fa#  .  Mi  Fa#
    c.frase(("caco", 2), ("caco", 2))                                # Si      Fa#
    c.frase(("caco", 1), ("caco", 1), ("pingente", 1), ("pingente", 1))   # La Fa# Mi Re
    c.frase(("pingente", 2), ("pingente", 1), ("pingente", 1))       # Mi      Do# Mi
    c.frase(("caco", 2), ("pingente", 1), ("caco", 1))               # Fa#  .  Mi  Fa#
    c.frase(("sobe", 1), ("sobe", 1), ("caco", 2))                   # Si Do# Re: a subida
    c.frase(("caco", 1), ("caco", 1), ("caco", 1), ("caco", 1))      # Do# Si La Fa#
    c.frase(("pingente", 2), ("pingente", 1), ("desce", 1, 2))       # Mi     Do#  e desce
    # e o fim: a ponte com os cristais por baixo, o paredao, e o salto final
    # por cima da fenda, pousando no golpe
    c.dupla(("caco", 2, 2), ("caco", 2, 2), ("caco", 2, 2), ("pausa", 2))
    c.frase(("mola", 2, -3))                                 # o paredao da geleira, pela mola
    c.frase(("caco", 1), ("pingente", 1), ("caco", 1, 2), ("pausa", 1))
    c.descer(3)
    c.descanso(1)
    c.frase(*_saltos(0, -1, 0, 1))
    c.frase(("caco", 1), ("pingente", 1), ("caco", 1, 2), ("pingente", 1))
    c.frase(("ilha", 1, -1), ("ilha", 1, 0), ("ilha", 2, 1))
    c.frase(("mola", 2, "vao"))                              # o ultimo salto, sobre a fenda
    return c.fim(6)


def _fase3():
    """
    Cidadela do Eclipse: arquitetura sombria, e a prova final. Ameias (um bloco
    por batida no alto da muralha), escadarias subidas a cada batida, fossos de
    3 tiles em fila e telhados em zigue-zague, sob o eclipse -- a 150 BPM e na
    corrida mais rapida do jogo (7 tiles por batida).

    Cerca de 1min45, e com CURVA: a introducao aquece de duas em duas batidas,
    o A mostra cada bloco da cidadela uma vez, a quebra anda de verdade mais
    devagar (cerca de 60 acoes por minuto), e o A' e a PROVA DOS MUNDOS -- o
    enxame do deserto, as ilhas, os espetos da geleira e a mola do bosque -- ate
    o eclipse total. A faixa e uma edicao da original sem o pos-drop do
    primeiro drop (ferramentas/geradores/editar_musica.py).
    """
    c = Construtor(Fase(2, "CIDADELA DO ECLIPSE", "DIFICIL", "eclipse"))
    # INTRODUCAO (compassos 32-39 da faixa, a descida que prepara o drop): a
    # muralha de fora, de duas em duas batidas; aperta no fim
    c.secao("introducao")
    c.descanso(2)
    c.frase(("torre", 2), ("torre", 2), ("mola", 4))       # a torre de vigia: so a mola passa
    c.subir(2)
    c.frase(("caco", 2), ("torre", 2), ("caco", 2, 2), ("pausa", 2))
    c.descer(2)
    c.frase(("vao", 2), ("caco", 2), ("caco", 1), ("caco", 1), ("pausa", 2))
    # PARTE A (40-55, o primeiro drop): cada bloco da cidadela uma vez -- as
    # ameias, a escadaria, o ritmo pontuado, os fossos, a muralha pela mola,
    # os telhados
    c.secao("A")
    c.torres(6, intervalo=1)
    c.frase(("torre", 2))
    c.frase(("sobe", 1), ("caco", 1), ("sobe", 1), ("caco", 1, 2), ("vao", 1), ("vao", 1),
            ("sobe", 1), ("sobe", 1))
    c.descer(4)
    c.descanso(1)
    # longa e curta: a 7 tiles por batida, uma meia batida cai entre dois tiles
    # (o caco ficaria meio tile fora do arco), entao a cidadela nao tem
    # contratempo antes do eclipse total
    c.frase(("caco", 1), ("caco", 2, 2), ("caco", 1), ("caco", 2, 2), ("caco", 1), ("caco", 1),
            ("caco", 2, 3), ("caco", 1), ("caco", 1))
    c.frase(("vao", 1), ("vao", 1), ("caco", 1, 2), ("vao", 1), ("vao", 1), ("caco", 1, 3),
            ("vao", 1), ("vao", 1))
    c.frase(("mola", 2, -4), ("pausa", 2))         # a muralha de uma vez, pela mola
    c.zigue_zague(2, intervalo=1)                  # os telhados, la em cima
    c.descer(4)
    c.descanso(1)
    c.frase(("vao", 1), ("vao", 1), ("vao", 1), ("vao", 1), ("mola", 4, "vao"))
    c.descanso(1)
    c.velocidade(5)                                # o portal azul: a quebra anda devagar
    c.descanso(1)
    # PARTE B (a quebra): saltos de duas batidas, o adarve, e a torre de
    # menagem no silencio da musica -- a mola, e o ORBE no alto do arco
    c.secao("B")
    c.frase(("vao", 2), ("vao", 2), ("caco", 2, 2), ("pausa", 2))
    c.dupla(("caco", 2), ("caco", 2, 2), ("pausa", 2))                 # o adarve
    c.frase(("sobe", 2), ("caco", 2), ("sobe", 2), ("enxame", 2))
    c.frase(("caco", 2), ("torre", 2), ("desce", 1), ("desce", 1), ("vao", 2))
    c.frase(("caco", 1), ("caco", 1), ("pausa", 2), ("caco", 1), ("caco", 2, 2), ("caco", 1))
    c.frase(("vao", 2), ("caco", 2, 3), ("enxame", 2))
    c.frase(("sobe", 2), ("caco", 2, 2), ("mola", 3, "orbe"), ("pausa", 2))
    c.frase(("desce", 1, 4), ("desce", 1, 3), ("pausa", 1))        # e o salto la de cima
    c.frase(("caco", 2), ("caco", 2), ("caco", 1), ("caco", 1))    # a subida para o drop
    c.descanso(1)
    c.velocidade(7)                                # de volta a corrida da cidadela
    c.descanso(1)
    # PARTE A' (o ultimo drop): o adarve com as lancas por baixo, e a PROVA
    # DOS MUNDOS -- o enxame das dunas, as ilhas, os espetos da geleira, a mola
    # do bosque, e tudo junto
    c.secao("A'")
    c.dupla(("caco", 2, 2), ("caco", 2, 2), ("caco", 2, 2), ("pausa", 2))
    c.frase(("caco", 1), ("caco", 1), ("enxame", 2))                # as dunas
    c.frase(("ilha", 1, 0), ("ilha", 1, -1), ("ilha", 2, 1))        # as ilhas
    c.frase(("caco", 1), ("pingente", 1), ("caco", 1), ("pingente", 1))   # a geleira
    c.frase(("mola", 4, "vao"))                                     # o bosque
    c.frase(("caco", 1), ("pingente", 1), ("enxame", 2), ("ilha", 1, -1), ("ilha", 1, 0),
            ("ilha", 2, 1))                                         # e tudo junto
    # a escadaria da torre, as ameias la no alto, e os fossos
    c.frase(("sobe", 1), ("sobe", 1), ("sobe", 1), ("caco", 1), ("sobe", 1), ("caco", 1, 2),
            ("pausa", 2))
    c.torres(6, intervalo=1)
    c.descanso(2)
    c.descer(4)
    c.frase(("vao", 1), ("caco", 1), ("vao", 1), ("caco", 1, 2), ("vao", 1), ("caco", 1, 3),
            ("vao", 1), ("vao", 1))
    c.frase(("caco", 2), ("enxame", 1))
    c.velocidade(8)                                # o eclipse total: a corrida final
    c.descanso(1)
    c.sincopado(12, quantidade=2)
    c.cacos(8, intervalo=1, quantidade=2)
    c.descanso(1)
    c.zigue_zague(2, intervalo=1)
    c.frase(("pingente", 1), ("caco", 1))
    c.frase(("vao", 1), ("caco", 1), ("mola", 3, "vao"))   # o ultimo salto, sobre o fosso todo
    return c.fim(8)


# em ordem de dificuldade: e a ordem da tela de fases e do "proxima fase"
_CONSTRUTORES = (_fase1, _fase_dunas, _fase2, _fase_geleira, _fase3)
_cache = {}


def carregar(indice):
    """Devolve a fase `indice` (construida uma unica vez)."""
    if indice not in _cache:
        _cache[indice] = _CONSTRUTORES[indice]()
        _cache[indice].ident = indice
    return _cache[indice]


def do_mundo(cancao):
    """A fase do mundo `cancao` ("bosque", "dunas"...), onde quer que esteja na ordem."""
    return next(f for f in todas() if f.cancao == cancao)


def todas():
    return [carregar(i) for i in range(len(_CONSTRUTORES))]
