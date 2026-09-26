"""
As fases: modelo, construtor ritmico e as tres partituras.

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
from .config import (TILE, LINHA_CHAO, TEMAS, ALPHA, FOLGA_CACO, PULO_MINIMO,
                     CORTE_PULO, JANELA_BOM)

PROFUNDIDADE = 8      # linhas de bloco solido abaixo do topo do chao

# O pulo de cada mundo: (batidas no ar, tiles por batida, altura em tiles).
# O pulo dura UMA batida e cobre 6 tiles (7 na cidadela); o que muda e o
# andamento: 84 BPM no bosque (0,7 s no ar), 110 nas ilhas (0,55 s) e 150 na
# cidadela (0,4 s) -- o mundo acelera junto com a musica, como pede o GDD.
PULO = {"bosque": (1, 6, 3.5), "ilhas": (1, 6, 3.5), "eclipse": (1, 7, 3.5)}
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
        self.decos = []
        self.acoes = []           # batidas em que o jogador precisa agir
        self.secoes = []          # [(nome, batida)]: introducao, A, B, A'
        self.fim_x = 0.0
        self.duracao = 0.0

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

    def marca(self, batida):
        """Registra uma acao exigida e a guia visual na coluna dela."""
        self.f.acoes.append(round(batida, 3))
        self.f.marcas.append((self.col(batida) * TILE, self.nivel * TILE))

    def secao(self, nome):
        """Marca onde comeca uma parte da musica (introducao, A, B, A')."""
        self.f.secoes.append((nome, self.b))
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
            if self.plano and tipo in ("sobe", "desce", "ilha", "vao"):
                tipo, opcao = {"sobe": "caco", "desce": "pausa", "ilha": "caco", "vao": "caco"}[tipo], None
            pula = tipo not in ("pausa", "desce")
            if pula and batidas < self.f.batidas_pulo - 1e-9:
                raise ValueError(f"'{tipo}' com {batidas} batidas na batida {self.b}: o pulo "
                                 f"dura {self.f.batidas_pulo} e o Leo ainda estaria no ar")
            if (tipo == "sobe" and (opcao or 1) > 1) or (tipo == "ilha" and (opcao or 0) < -1):
                raise ValueError(f"'{tipo}' subindo {opcao} tiles na batida {self.b}: o pulo "
                                 f"baixo (um toque) so sobe 1 tile")
            j, fim = self.col(self.b), self.col(self.b + batidas)
            q1 = self.beira + (1 if self._desceu else 0)
            self._desceu = (pula and batidas <= self.f.batidas_pulo + 1e-9 and
                            tipo == "ilha" and (opcao or 0) > 0)
            if pula:
                self.marca(self.b)             # a guia fica na altura de onde se pula
            if tipo == "desce":
                self.nivel += opcao or 1
            if tipo in ("caco", "torre", "vao", "pausa", "desce"):
                self.piso(j, fim)
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

    def _fosso(self, c0, c1, ty):
        """
        Buraco nas colunas [c0, c1), com cacos cravados no fundo (linha ty).
        Quem cai la nao volta: os cacos do fundo sao fatais.
        """
        self.abrir(c0, c1)
        for tx in range(c0, c1):
            self.caco(tx, ty, fatal=True)

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
    def fim(self, batidas=6):
        f = self.f
        c1 = self.col(self.b + batidas)
        self.piso(self.col(self.b), c1 + 40)
        self.b += batidas
        f.fim_x = c1 * TILE
        f.duracao = self.b * f.dur_batida
        f.acoes.sort()
        f.celulas_bloco = set(f.blocos)
        for p in f.perigos:
            f.col_perigos.setdefault(int(p.x // TILE), []).append(p)
        # o portal de volta e so cenario: solido, mataria o jogador na chegada
        f.decos.append(Deco("portal", c1 * TILE, (self.nivel - 4) * TILE,
                            TILE * 2, TILE * 4))
        self._decorar()
        return f

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
                alt = TILE * (2 + tx % 2)
                f.decos.append(Deco("coluna", tx * TILE, n * TILE - alt, TILE, alt,
                                    variante=tx // espaco))


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
    """
    c = Construtor(Fase(0, "BOSQUE DOS ECOS", "FACIL", "bosque"))
    # INTRODUCAO (compassos 0-2 da faixa, antes do grave): a clareira
    c.secao("introducao")
    c.descanso(4)
    c.cacos(8, intervalo=4)
    # PARTE A (3-18, o grave entra): a primeira colina e o riacho; depois
    # frases de dois compassos, cada uma com o seu desenho
    c.secao("A")
    c.frase(("caco", 2), ("torre", 2))
    c.colina(2, ("caco", 2), ("caco", 2))
    c.vaos(4)
    c.descanso(2)
    c.frase(("caco", 2), ("torre", 2), ("caco", 2, 2), ("pausa", 2))
    c.frase(("vao", 2), ("caco", 2), ("vao", 2), ("caco", 2, 2))
    c.frase(("vao", 2), ("vao", 2), ("pausa", 2))  # a primeira ravina, pedra a pedra
    c.frase(("caco", 2))
    c.colina(2, ("torre", 2), ("caco", 2), ("caco", 1.5), ("caco", 1.5), ("caco", 1.5),
             ("caco", 1.5))
    c.frase(("caco", 2, 2), ("vao", 2))
    # PARTE B (19-34, a quebra sem grave): saltos longos e respiro
    c.secao("B")
    c.descanso(4)
    c.frase(("vao", 4), ("vao", 4))
    c.cacos(12, intervalo=4)
    c.frase(("caco", 4), ("torre", 4))
    c.frase(("vao", 4), ("caco", 4), ("vao", 4), ("caco", 4, 2))
    c.frase(("torre", 4), ("caco", 4), ("vao", 4), ("pausa", 4))
    # PARTE A' (35-50, o grave de novo): a colina e o riacho, mais altos e mais juntos
    c.secao("A'")
    c.colina(3, ("caco", 2, 2), ("torre", 2))
    c.frase(("pausa", 1), ("vao", 2))
    c.frase(("caco", 2), ("caco", 2))
    c.frase(("vao", 2), ("vao", 2), ("pausa", 2))  # a ultima ravina
    c.frase(("caco", 2))
    c.zigue_zague(2)
    c.cacos(6, intervalo=1)
    c.descanso(2)
    c.frase(("caco", 2), ("vao", 2), ("caco", 2, 2), ("vao", 2))
    c.cacos(8)
    c.descanso(4)
    return c.fim(6)


def _saltos(*desniveis):
    """Uma ilha por batida: a corrida de pedra em pedra do arquipelago."""
    return [("ilha", 1, d) for d in desniveis]


def _fase2():
    """
    Ilhas Suspensas: o chao e um arquipelago sobre o vazio. Quase todo salto
    cruza um vao de 3 tiles e cai numa ilha de outra altura -- quase sempre
    uma ilha por batida, com cacos nas ilhas e o ritmo pontuado. Os PORTAIS
    DE VELOCIDADE mudam o jogo: o dourado acelera a corrida nos dois drops da
    musica, o azul devolve a velocidade normal. 110 BPM, pulo de uma batida.
    """
    c = Construtor(Fase(1, "ILHAS SUSPENSAS", "NORMAL", "ilhas"))
    # INTRODUCAO (compassos 8-15 da faixa, a subida): uma ilha a cada duas
    # batidas, depois a cada batida
    c.secao("introducao")
    c.descanso(2)
    c.ilhas((0, -1, 0, 1, 0, -1))
    c.frase(*_saltos(0, -1, 1, 0))
    c.frase(("ilha", 1.5, -1), ("ilha", 1.5, 1), ("ilha", 1, 0))
    c.frase(*_saltos(0, 0, -1, 1, 0, 0), ("ilha", 2, 0))
    c.descanso(1)
    c.velocidade(8)                                # o portal dourado: o drop
    c.descanso(1)
    # PARTE A (16-31, o primeiro drop): a corrida pelas ilhas
    c.secao("A")
    c.frase(*_saltos(0, -1, 0, 1), ("ilha", 1, -1), *_saltos(-1, 1, 1))
    c.frase(("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1),
            ("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1))       # o ritmo pontuado
    c.frase(("caco", 1), ("ilha", 1, -1), ("caco", 1, 2), ("ilha", 1, 0),
            ("caco", 1, 3), *_saltos(1, 0, 0))
    c.frase(*_saltos(-1, 0, 1, 0), ("ilha", 1, -1), *_saltos(-1, 1, 1))
    c.frase(*_saltos(0, -1, 0, 1, 0, -1, 0, 1))
    c.frase(("ilha", 1, -1), ("caco", 1), ("caco", 1, 2), *_saltos(-1, 1, 1), ("ilha", 2, 0))
    c.frase(("ilha", 1.5, -1), ("ilha", 1.5, 1), ("ilha", 1, 0),
            ("ilha", 1.5, -1), ("ilha", 1.5, 1), ("ilha", 1, 0))
    c.frase(*_saltos(0, -1, 0), ("ilha", 2, 1), ("ilha", 2, 0))
    c.velocidade(6)                                # o azul: de volta ao normal
    c.descanso(1)
    # (32-39) o balanco depois do drop: sem folga
    c.frase(*_saltos(0, -1, 0, 1, 0, -1, 1, 0))
    c.frase(*_saltos(-1, 0), ("caco", 1), ("caco", 1, 2), *_saltos(1, 0), ("caco", 1, 3),
            ("ilha", 1, 0))
    c.frase(("ilha", 1.5, 0), ("ilha", 1.5, -1), ("ilha", 1, 0),
            ("ilha", 1.5, 1), ("ilha", 1.5, 0), ("ilha", 1, 0))
    c.frase(("ilha", 1, -1), *_saltos(0, 1, 0), ("caco", 1), ("caco", 1, 2), ("caco", 1),
            ("pausa", 1))
    # PARTE B (40-47, a quebra): o ritmo quebrado entre ilhas altas, e a
    # subida que prepara o segundo drop
    c.secao("B")
    c.frase(("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1),
            ("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 1))
    c.frase(("ilha", 2.5, -1), ("ilha", 2.5, 1), ("ilha", 1, 0), ("ilha", 2, -1))
    c.frase(*_saltos(1, 0), ("caco", 1, 2), ("ilha", 1, 0), ("ilha", 1.5, -1), ("ilha", 1.5, 1),
            ("ilha", 1, 0))
    c.frase(*_saltos(0, 0, -1, 1, 0, 0))
    c.descanso(1)
    c.velocidade(8)
    c.descanso(1)
    # PARTE A' (48-63, o segundo drop): a corrida de novo, mais longa e mais cheia
    c.secao("A'")
    c.frase(*_saltos(0, -1, 0, 1, 0, -1, 0, 1))
    c.frase(("ilha", 1, -1), ("ilha", 1, 0), ("ilha", 1.5, 1), ("ilha", 1.5, -1),
            ("ilha", 1, 0), ("caco", 1, 3), ("caco", 1))
    c.frase(("caco", 1), ("caco", 1, 2), ("ilha", 1, -1), ("caco", 1), ("ilha", 1, 0),
            ("caco", 1, 3), *_saltos(1, 0))
    c.frase(("ilha", 1.5, -1), ("ilha", 1.5, -1), ("ilha", 1, 1),
            ("ilha", 1.5, 0), ("ilha", 1.5, 1), ("ilha", 1, 0))
    c.frase(*_saltos(0, 0, -1, 0, 1, 0), ("ilha", 1, -1), ("ilha", 1, 0))
    c.frase(*_saltos(1, 0), ("caco", 1, 2), ("caco", 1, 3), ("ilha", 1.5, -1), ("ilha", 1.5, 1),
            ("ilha", 1, 0))
    c.frase(("caco", 1), ("ilha", 1, -1), ("caco", 1), ("ilha", 1, 0),
            ("caco", 1, 2), ("ilha", 1, 1), ("ilha", 1, 0), ("caco", 1, 3))
    c.frase(("ilha", 1, -1), *_saltos(0, 1, 0), ("ilha", 3, 0))
    c.velocidade(6)
    c.descanso(1)
    # (64-69) o fim da faixa, na velocidade normal
    c.frase(*_saltos(0, -1, 1, 0), ("caco", 1), ("caco", 1, 2), ("caco", 1, 3), ("ilha", 1, 0))
    c.frase(("ilha", 1.5, -1), ("ilha", 1.5, 0), ("ilha", 1, 0), ("ilha", 1, -1),
            *_saltos(0, 1, 0))
    c.frase(*_saltos(0, 0, 1, 0), ("caco", 2, 3), ("pausa", 2))
    return c.fim(6)


def _fase3():
    """
    Cidadela do Eclipse: arquitetura sombria, e a prova final. Ameias (um bloco
    por batida no alto da muralha), escadarias subidas a cada batida, fossos de
    3 tiles em fila e telhados em zigue-zague, sob o eclipse -- a 150 BPM e na
    corrida mais rapida do jogo (7 tiles por batida), quase sem respiro.
    """
    c = Construtor(Fase(2, "CIDADELA DO ECLIPSE", "DIFICIL", "eclipse"))
    # INTRODUCAO (compassos 24-39 da faixa, a batida e a subida): a muralha de
    # fora; o ritmo aperta ate o drop
    c.secao("introducao")
    c.descanso(2)
    c.torres(8)
    c.subir(4)
    c.frase(("caco", 1), ("caco", 1), ("torre", 1), ("caco", 1, 2), ("caco", 1), ("torre", 1),
            ("pausa", 2))
    c.descer(4)
    c.cacos(8, intervalo=1, quantidade=2)
    c.zigue_zague(2, intervalo=1)
    c.frase(("vao", 2), ("caco", 1), ("caco", 1), ("vao", 2), ("caco", 1), ("caco", 1))
    c.frase(("sobe", 1), ("sobe", 1), ("torre", 1), ("sobe", 1), ("caco", 1, 2), ("sobe", 1),
            ("caco", 1), ("pausa", 1))
    c.descer(4)
    c.frase(("sobe", 1), ("pausa", 1))
    # PARTE A (40-63, o primeiro drop): as ameias, as escadas e o fosso; depois
    # os telhados
    c.secao("A")
    c.torres(8, intervalo=1)
    c.frase(("sobe", 1), ("caco", 1), ("sobe", 1), ("caco", 1, 2), ("vao", 1), ("vao", 1),
            ("sobe", 1), ("sobe", 1))
    c.descer(5)
    c.descanso(2)
    c.sincopado(12, quantidade=2)
    c.frase(("vao", 1), ("vao", 1), ("caco", 1, 2), ("vao", 1), ("vao", 1), ("caco", 1, 3),
            ("vao", 1), ("vao", 1))
    c.subir(4, intervalo=1)
    c.torres(4, intervalo=1)
    c.frase(("caco", 1, 3), ("sobe", 1), ("caco", 1, 2), ("sobe", 1), ("caco", 1))
    c.descer(6)
    c.descanso(2)
    c.zigue_zague(4, intervalo=1)
    c.descanso(2)
    c.sincopado(12, quantidade=2)
    c.frase(("vao", 1), ("vao", 1), ("vao", 1), ("vao", 1), ("vao", 2), ("vao", 2))
    c.descanso(2)
    # PARTE B (64-79, a quebra): os fossos em fila e a torre de menagem
    c.secao("B")
    c.frase(("vao", 1), ("vao", 1), ("caco", 1, 2), ("vao", 1), ("vao", 1), ("caco", 1, 3),
            ("vao", 1), ("vao", 1), ("pausa", 2))
    c.frase(("caco", 1), ("caco", 1, 2), ("caco", 1), ("caco", 1, 3), ("pausa", 2))
    c.frase(("sobe", 1), ("caco", 1), ("sobe", 1), ("caco", 1, 2), ("desce", 1),
            ("desce", 1), ("vao", 1), ("vao", 1), ("pausa", 2))
    c.frase(("caco", 1), ("caco", 1), ("caco", 1, 2), ("caco", 1), ("caco", 1.5), ("caco", 1.5),
            ("caco", 1, 3))
    c.torres(6, intervalo=1)
    c.descanso(2)
    c.frase(("vao", 1), ("caco", 1, 2), ("vao", 1), ("caco", 1, 3), ("vao", 1), ("vao", 1),
            ("pausa", 2))
    c.frase(("sobe", 1), ("sobe", 1), ("caco", 1, 2), ("caco", 1), ("sobe", 2),
            ("caco", 2, 3))
    c.descer(3)
    c.descanso(3)
    # PARTE A' (80-103, o ultimo drop e o fim da faixa): tudo de novo, mais
    # alto e mais junto, ate o portal de casa
    c.secao("A'")
    c.cacos(8, intervalo=1, quantidade=2)
    c.frase(("sobe", 1), ("sobe", 1), ("sobe", 1), ("caco", 1), ("sobe", 1), ("caco", 1, 2),
            ("pausa", 2))
    c.torres(8, intervalo=1)
    c.frase(("sobe", 1), ("caco", 1), ("sobe", 1), ("caco", 1, 2), ("sobe", 1),
            ("caco", 1, 3), ("caco", 1), ("pausa", 1))
    c.descer(7)
    c.descanso(3)
    c.frase(("vao", 1), ("caco", 1), ("vao", 1), ("caco", 1, 2), ("vao", 1), ("caco", 1, 3),
            ("vao", 1), ("vao", 1))
    c.sincopado(12, quantidade=2)
    c.subir(2, intervalo=1)
    c.torres(6, intervalo=1)
    c.frase(("caco", 1, 3), ("caco", 1, 3), ("sobe", 1), ("caco", 1), ("caco", 1, 2))
    c.descer(3)
    c.descanso(1)
    c.cacos(8, intervalo=1, quantidade=2)
    c.zigue_zague(2, intervalo=1)
    c.frase(("vao", 1), ("caco", 1), ("vao", 1), ("caco", 1, 2), ("vao", 1))
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
