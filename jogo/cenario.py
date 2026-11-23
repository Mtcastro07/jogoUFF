"""
O fundo de cada mundo, em pixel art: ceu em degrade, sol ou lua, estrelas e
duas camadas de colinas em parallax.

Tudo e desenhado numa superficie pequena (320x180) e ampliado 4x sem
suavizacao no fim -- e isso que deixa o fundo pixelado como o resto do jogo.

    bosque    lua cheia e estrelas
    ilhas     sol baixo, sem estrelas
    eclipse   o sol eclipsado, com a coroa de luz
"""

import math
import random

import pygame

from . import arte
from .config import LARGURA, ALTURA

ESCALA = 4
W, H = LARGURA // ESCALA, ALTURA // ESCALA

# Onde as pecas de objetos/cenario/<fase>/ sao semeadas. O vao entre duas
# pecas nunca e o mesmo: `passo` da o compasso e `jitter` tira a regularidade,
# para a mata parecer plantada e nao enfileirada.
#   prefixo -> (passo, jitter, afundar, flutua)
#
#   afundar  enterra a peca na colina: a mata de fundo e uma linha de COPAS, nao
#            de arvores inteiras -- o que a mantem atras da faixa em que o
#            jogador le os obstaculos que vem chegando.
#   flutua   None: a peca nasce na linha da colina. (a, b): a peca PAIRA entre
#            a e b px acima da base da camada, sem seguir o relevo -- e o que faz
#            uma ilha parecer suspensa. A altura de cada uma e sorteada.
SEMEADURA = {
    "longe": (46, 17, 6, None),
    "perto": (72, 26, 14, None),
    "nuvem": (58, 24, 0, None),
}
SEMEADURA_FASE = {
    # a geleira: pinheiros nevados afundados nos morros, e as agulhas de gelo
    "geleira": {
        "longe": (40, 16, 5, None),
        "perto": (84, 30, 10, None),
    },
    # o deserto e vazio: poucas pecas, bem espacadas, de pe na crista das dunas
    "dunas": {
        "longe": (96, 34, 3, None),
        "perto": (132, 44, 5, None),
        "nuvem": (120, 40, 0, None),
    },
    # a cidadela e de pedra: as construcoes afundam pouco na colina, para as
    # ameias e as janelas acesas aparecerem
    "eclipse": {
        "longe": (46, 17, 4, None),
        "perto": (78, 28, 6, None),
    },
    # ilhas sao largas: vao generoso entre elas, ou o ceu vira um teto de pedra.
    # As distantes descem ate perto do mar de nuvens: e o que da profundidade.
    "ilhas": {
        "longe": (74, 30, 0, (14, 56)),
        "perto": (150, 50, 0, (40, 54)),
        "nuvem": (76, 32, 0, None),
    },
}
# Perspectiva do ar: a peca distante se desfaz no ceu atras dela -- (cor, quanto).
# As ilhas longe vieram quase pretas, mais escuras que as de perto: sem a nevoa
# elas pareciam buracos no por do sol, e nao ilhas ao longe.
NEVOA = {
    # o frio azul apaga o que esta longe -- e recua o de perto, para o gelo
    # do fundo nao disputar com a faixa em que o jogador le os perigos
    "geleira": {"longe": ((34, 54, 104), 0.42), "perto": ((30, 50, 96), 0.32)},
    "dunas": {"longe": ((176, 204, 186), 0.42)},        # o mormaco apaga o que esta longe
    "ilhas": {"longe": ((150, 92, 118), 0.5)},
}
VAO = W * 16             # a semeadura se repete so depois disso: nunca, na pratica
MARGEM = 64              # mais larga que qualquer peca: quem cruza a borda esquerda
                         # sai de cena aos poucos, em vez de sumir de uma vez

# Ceu com mais de dois tons (altura 0 = topo da tela, 1 = pe). As ilhas pedem o
# por do sol do GDD: roxo em cima, malva no meio, pessego rente as nuvens.
CEUS = {
    # a noite mais funda do jogo: quase preta em cima, azul de gelo no horizonte
    "geleira": ((0.0, (6, 10, 30)), (0.5, (18, 32, 72)), (1.0, (56, 90, 140))),
    # o unico ceu de dia: azul fundo em cima, turquesa, e a poeira clara no horizonte
    "dunas": ((0.0, (26, 78, 126)), (0.42, (58, 140, 168)), (0.56, (150, 200, 190)),
              (1.0, (236, 208, 156))),
    "ilhas": ((0.0, (58, 36, 82)), (0.55, (138, 82, 108)), (1.0, (224, 148, 128))),
}

# Onde as outras fases tem colinas, as ilhas tem um MAR DE NUVENS la embaixo:
# o chao e uma ilha, e embaixo dela nao ha terra. Cada camada:
# (altura da base, parallax, raio minimo e maximo das bolhas, cor do topo, do corpo)
MAR_DE_NUVENS = {
    "ilhas": ((0.80, 0.06, 4, 10, (196, 132, 140), (170, 110, 126)),
              (0.93, 0.13, 6, 14, (222, 160, 156), (192, 128, 138))),
}

# Onde as outras fases tem colinas, a cidadela tem MURALHAS com ameias: uma
# por camada, e as torres e castelos gerados ficam de pe em cima delas. A
# muralha de perto fica ACIMA do chao de jogo -- entre as duas aparece a face
# da muralha, e o castelo nao parece plantado no caminho do jogador.
# camada -> (altura do topo da muralha, fracao de H; cor da janela acesa)
MURALHAS = {
    "eclipse": {"longe": (0.50, (96, 62, 50)), "perto": (0.575, (150, 92, 58))},
}

# Onde as outras fases tem colinas, o deserto tem DUNAS, em tres camadas: crista
# em quina, a face de tras (a esquerda, de costas para o sol) na sombra e a
# espinha da duna descendo em diagonal para perto de quem olha. Cada camada:
# (pecas plantadas nela ou None, parallax, base em fracao da tela, peso do
#  balanco da camera, altura, vao entre cristas, corpo, sombra, crista)
DUNAS = {
    "dunas": (("longe", 0.10, 0.515, 2.0, 15, 118, (228, 194, 150), (198, 162, 138), (248, 228, 186)),
              (None, 0.17, 0.585, 2.5, 13, 150, (226, 174, 120), (186, 134, 104), (252, 220, 156)),
              ("perto", 0.25, 0.660, 3.0, 15, 190, (214, 148, 92), (162, 102, 76), (253, 212, 138))),
}
CRISTAS_POR_VOLTA = 6    # a tira de cada camada se repete depois de tantas dunas

# O astro anda devagar para a esquerda com a camera (parallax de 1%). Numa fase
# longa isso o levaria para fora da tela -- a cidadela tem mais de 110 mil px --
# entao, depois de DERIVA_LIVRE px de caminho, ele desacelera suave e para antes
# de chegar na borda (DERIVA_MAX). O bosque inteiro cabe no trecho livre.
DERIVA_LIVRE, DERIVA_MAX = 150.0, 190.0

_ceus = {}

# O CLIMA de cada ato (introducao, A, B, A'): o fundo inteiro e multiplicado
# pela primeira cor e somado a segunda. Nao muda a faixa em que o jogador le os
# obstaculos (o chao e os perigos nao sao tingidos) -- so diz, pelo ceu, que a
# musica entrou noutra parte.
NEUTRO = ((255, 255, 255), (0, 0, 0))
CLIMA = {
    # a noite fica violeta nas ruinas e ganha o verde da aurora no final
    "bosque": (NEUTRO, NEUTRO, ((176, 190, 255), (20, 8, 40)), ((214, 255, 236), (0, 24, 22))),
    # na quebra o vento levanta a areia e o dia fica ocre; no final ele limpa
    "dunas": (NEUTRO, NEUTRO, ((255, 244, 230), (18, 6, 0)), ((255, 252, 248), (4, 6, 8))),
    # a nevasca embranquece a quebra; no drop a aurora tinge tudo de verde
    "geleira": (NEUTRO, NEUTRO, ((206, 220, 250), (44, 50, 66)), ((220, 255, 240), (0, 22, 22))),
    # o por do sol cai no crepusculo e volta num ultimo clarao dourado
    "ilhas": (NEUTRO, NEUTRO, ((176, 160, 232), (8, 0, 30)), ((255, 232, 200), (30, 10, 0))),
    # o eclipse sangra na parte B e esfria num azul de aco no final
    "eclipse": (NEUTRO, NEUTRO, ((255, 176, 184), (38, 0, 6)), ((196, 208, 255), (4, 8, 40))),
}
# O astro muda de tamanho de ato em ato: a lua incha sobre as ruinas, o sol das
# ilhas cresce no ultimo clarao e o eclipse toma o ceu no final.
ESCALA_ASTRO = {
    "bosque": (1.0, 1.0, 1.3, 1.1),
    "dunas": (1.0, 1.0, 0.85, 1.25),
    "ilhas": (1.0, 1.0, 0.9, 1.4),
    "geleira": (1.0, 1.0, 0.85, 1.2),
    "eclipse": (1.0, 1.0, 1.35, 1.8),
}
# nas ilhas o crepusculo da parte B traz as estrelas (0 = nenhuma, 1 = todas)
NOITE = {"geleira": (1.0, 1.0, 0.45, 1.0), "dunas": (0.0, 0.0, 0.0, 0.0), "ilhas": (0.0, 0.0, 1.0, 0.0), "bosque": (1.0, 1.0, 1.0, 1.0), "eclipse": (1.0, 1.0, 1.0, 1.0)}
PASSAGEM_CLIMA = 900.0        # px de mapa que a troca de clima leva (uns 19 tiles)


def clima(fase, x):
    """((multiplica), (soma)) do fundo no ponto `x` do mapa, passando suave entre os atos."""
    atos = CLIMA.get(fase.tema.nome)
    if not atos or not fase.secoes_x:
        return None
    i = min(fase.ato(x), len(atos) - 1)
    atual = atos[i]
    if i > 0:
        k = (x - fase.secoes_x[i]) / PASSAGEM_CLIMA
        if k < 1.0:
            k = max(0.0, k) ** 2 * (3.0 - 2.0 * max(0.0, k))
            antes = atos[i - 1]
            atual = tuple(tuple(int(a + (b - a) * k) for a, b in zip(ca, cb))
                          for ca, cb in zip(antes, atual))
    return None if atual == NEUTRO else atual


def _entre_atos(fase, x, valores):
    """O valor do ato de `x`, passando suave a partir do valor do ato anterior."""
    if not fase.secoes_x:
        return valores[0]
    i = min(fase.ato(x), len(valores) - 1)
    v = valores[i]
    if i > 0:
        k = max(0.0, min(1.0, (x - fase.secoes_x[i]) / PASSAGEM_CLIMA))
        v = valores[i - 1] + (v - valores[i - 1]) * k * k * (3.0 - 2.0 * k)
    return v


def cena(fase, x):
    """Tudo o que o fundo precisa saber do ponto `x` do mapa: clima, astro e noite."""
    nome = fase.tema.nome
    return {"clima": clima(fase, x),
            "astro": round(_entre_atos(fase, x, ESCALA_ASTRO.get(nome, (1.0,))) * 20) / 20,
            "noite": _entre_atos(fase, x, NOITE.get(nome, (1.0,))),
            "aurora": _entre_atos(fase, x, AURORA_DO_ATO.get(nome, (1.0,)))}


_escalados = {}


def _escalado(img, k):
    """`img` ampliada `k` vezes (em passos de 5%), em cache."""
    if abs(k - 1.0) < 0.01:
        return img
    chave = (id(img), k)
    ent = _escalados.get(chave)
    if ent is None or ent[0] is not img:
        ent = _escalados[chave] = (img, pygame.transform.scale(
            img, (max(1, round(img.get_width() * k)), max(1, round(img.get_height() * k)))))
    return ent[1]


# A serra distante: (pe da serra em fracao da tela, altura da tira, corpo, face
# acesa, cume, nevoa). No bosque o cume e neve ao luar; na cidadela, pedra
# lambida pela coroa do eclipse.
PERIODO_SERRA = 640
SERRAS = {
    "bosque": (0.50, 46, (26, 40, 70), (44, 62, 96), (170, 190, 214), (22, 34, 66)),
    "eclipse": (0.50, 52, (30, 16, 44), (56, 32, 66), (150, 100, 84), (20, 9, 34)),
    # nas dunas, a cordilheira azulada do outro lado do deserto, quase da cor do ceu
    "dunas": (0.52, 40, (104, 150, 166), (134, 176, 180), (214, 222, 200), (150, 200, 190)),
    # na geleira, os picos nevados, com a neve acesa pela lua
    "geleira": (0.50, 56, (34, 54, 98), (62, 90, 140), (226, 238, 255), (20, 34, 74)),
}
# quem voa no ceu, e de que cor: passaros nas ilhas (a cor das ilhas distantes:
# sao longe) e morcegos na cidadela, mais claros que a noite para aparecerem
REVOADA = {"dunas": (40, 62, 92), "ilhas": (88, 54, 84), "eclipse": (70, 44, 98)}

# Raios em volta do astro: (cor, quantos, raio de dentro, raio de fora, alfa).
# Giram devagar, fora da batida; na cidadela e a coroa do eclipse, que estoura
# junto com o astro. Sao luz, nao desenho: quase transparentes.
RAIOS = {
    "dunas": ((255, 246, 204), 10, 14, 42, 12),
    "ilhas": ((255, 214, 150), 9, 15, 44, 10),
    "eclipse": ((255, 190, 110), 12, 16, 34, 13),
}
QUADROS_RAIOS = 12
# halo da lua: (cor, raio) de fora para dentro, por cima do ceu
HALO_LUA = {"bosque": (((24, 37, 70), 21), ((28, 42, 77), 17))}
# bruma entre os morros do bosque: (altura em fracao da tela, cor, alfa)
BRUMA = {"bosque": ((0.515, (86, 124, 132), 46), (0.60, (70, 112, 112), 38)),
         "geleira": ((0.53, (110, 146, 200), 40), (0.62, (150, 184, 226), 30))}
PERIODO_BRUMA = 200
# estrela cadente: de quantos em quantos segundos, e quanto dura
CADENTE = {"bosque": (11.0, 0.7), "geleira": (13.0, 0.7), "eclipse": (17.0, 0.6)}

# A AURORA da geleira: cortinas de luz ondulando devagar no alto do ceu, fora
# da batida (o ceu respira, nao pisca). Cada cortina: (altura da borda acesa em
# fracao da tela, comprimento da franja em px, cor da borda, cor do alto, alfa,
# velocidade). A forca muda de ato em ato (AURORA_DO_ATO): fraca na introducao,
# some na nevasca e explode no drop.
AURORA = {
    "geleira": ((0.30, 40, (120, 255, 196), (70, 170, 255), 120, 1.0),
                (0.20, 30, (110, 200, 255), (150, 120, 255), 70, -0.7)),
}
AURORA_DO_ATO = {"geleira": (0.6, 1.0, 0.25, 1.6)}


_raios_prontos = {}


def _raios(chave, cor, n, r0, r1, alfa):
    """
    [QUADROS_RAIOS superficies]: `n` raios em cunha saindo do astro, um longo e
    um curto alternados, cada quadro um pouco mais girado -- uma volta do
    desenho leva so 1/n de volta, entao 12 quadros ja giram sem pulo.
    """
    if chave not in _raios_prontos:
        quadros = []
        lado = (r1 + 2) * 2
        for q in range(QUADROS_RAIOS):
            s = pygame.Surface((lado, lado), pygame.SRCALPHA)
            c = lado / 2
            for i in range(n):
                a = math.tau * (i + q / QUADROS_RAIOS) / n
                fim = r1 if i % 2 == 0 else r0 + (r1 - r0) * 0.6
                meia = math.tau / n * 0.2
                pontos = [(c + r0 * math.cos(a - meia), c + r0 * math.sin(a - meia)),
                          (c + fim * math.cos(a - meia * 0.5), c + fim * math.sin(a - meia * 0.5)),
                          (c + fim * math.cos(a + meia * 0.5), c + fim * math.sin(a + meia * 0.5)),
                          (c + r0 * math.cos(a + meia), c + r0 * math.sin(a + meia))]
                pygame.draw.polygon(s, (*cor, alfa), pontos)
                # o miolo do raio e mais forte, e mais curto
                curto = r0 + (fim - r0) * 0.55
                pygame.draw.polygon(s, (*cor, alfa + 8), [
                    pontos[0], (c + curto * math.cos(a), c + curto * math.sin(a)), pontos[3]])
            quadros.append(s)
        _raios_prontos[chave] = quadros
    return _raios_prontos[chave]


_brumas_prontas = {}


def _bruma(chave, cor, alfa):
    """Uma tira de bruma que se repete: fiapos compridos, mais densos no meio da altura."""
    if chave not in _brumas_prontas:
        s = pygame.Surface((PERIODO_BRUMA, 13), pygame.SRCALPHA)
        rnd = random.Random(chave)
        for _ in range(26):
            larg = rnd.randint(14, 54)
            x, y = rnd.randrange(PERIODO_BRUMA), rnd.randint(1, 11)
            forca = int(alfa * (1.0 - abs(y - 6) / 7.0))
            for xx in (x, x - PERIODO_BRUMA):
                s.fill((*cor, forca), (xx, y, larg, 1))
                s.fill((*cor, forca // 2), (xx + 3, y - 1, larg - 8, 1))
        _brumas_prontas[chave] = s
    return _brumas_prontas[chave]


def _deriva_astro(cx):
    """Quantos px do fundo o astro ja andou para a esquerda com a camera em `cx`."""
    d = cx * 0.01
    if d <= DERIVA_LIVRE:
        return d
    folga = DERIVA_MAX - DERIVA_LIVRE
    return DERIVA_LIVRE + folga * (1.0 - math.exp(-(d - DERIVA_LIVRE) / folga))


def ceu(tema):
    """Degrade vertical do ceu. Um por tema, em cache."""
    s = _ceus.get(tema.nome)
    if s is None:
        s = _ceus[tema.nome] = pygame.Surface((W, H))
        paradas = CEUS.get(tema.nome)
        if paradas is None:
            topo, base = arte.escurecer(tema.ceu, 0.35), arte.clarear(tema.ceu, 0.25)
            paradas = ((0.0, topo), (1.0, base))
        for y in range(0, H, 2):
            t = y / H
            for (t0, c0), (t1, c1) in zip(paradas, paradas[1:]):
                if t <= t1:
                    k = (t - t0) / (t1 - t0)
                    break
            cor = tuple(int(c0[i] * (1 - k) + c1[i] * k) for i in range(3))
            s.fill(cor, (0, y, W, 2))
    return s


def _bolhas(semente, r0, r1):
    """
    A linha de bolhas de uma camada de nuvens baixas: [(x, raio, subida)] num
    periodo. Tamanho e altura variam de bolha para bolha, ou o topo vira um
    babado de desenho animado.
    """
    rnd = random.Random(semente)
    bolhas, x = [], 0
    while x < W * 4:
        r = rnd.randint(r0, r1)
        bolhas.append((x, r, rnd.randint(0, r // 2)))
        x += rnd.randint(r // 2 + 2, r + r // 2)
    return bolhas


def _altura(u, base, amp, freq):
    """Altura da colina na coordenada `u` do mundo daquela camada."""
    t = u * 0.008 * freq
    return base - amp * (0.6 + 0.4 * math.sin(t) + 0.25 * math.sin(t * 2.7 + 1.0))


def _regra(fase, prefixo):
    return SEMEADURA_FASE.get(fase, {}).get(prefixo, SEMEADURA[prefixo])


def _pecas(fase, prefixo):
    """[(normal, espelhada)] das pecas <prefixo>_1..12 que existirem."""
    achadas = []
    for i in range(1, 13):
        img = arte.png("objetos", "cenario", fase, f"{prefixo}_{i}.png")
        if img is not None:
            nevoa = NEVOA.get(fase, {}).get(prefixo)
            if nevoa:
                img = arte.recuar(img, *nevoa)
            achadas.append((img, pygame.transform.flip(img, True, False)))
    return achadas


def _semear(fase, prefixo, n_pecas):
    """[(u, indice, espelhada, altitude)] ao longo de VAO, estavel entre partidas."""
    if not n_pecas:
        return []
    passo, jitter, _, flutua = _regra(fase, prefixo)
    rnd = random.Random(f"{fase}/{prefixo}")
    slots, u, anterior = [], 0.0, -1
    while u < VAO:
        # a mesma peca nunca aparece duas vezes seguidas
        i = rnd.randrange(n_pecas)
        if n_pecas > 1 and i == anterior:
            i = (i + 1 + rnd.randrange(n_pecas - 1)) % n_pecas
        anterior = i
        espelhada = rnd.random() < 0.5
        # so sorteia altitude quem flutua: o bosque mantem a mesma sequencia
        altitude = rnd.uniform(*flutua) if flutua else 0.0
        slots.append((u, i, espelhada, altitude))
        u += passo + rnd.uniform(-jitter, jitter)
    return slots


class Cenario:
    def __init__(self, tema):
        self.tema = tema
        self.buf = pygame.Surface((W, H))
        rnd = random.Random(len(tema.nome))
        self.estrelas = [(rnd.uniform(0, W * 2), rnd.uniform(0, H * 0.6),
                          rnd.uniform(0, math.tau)) for _ in range(50)]
        self.pecas = {p: _pecas(tema.nome, p) for p in SEMEADURA}
        self.slots = {p: _semear(tema.nome, p, len(v)) for p, v in self.pecas.items()}
        self.mar = [(camada, _bolhas(f"{tema.nome}/mar{i}", camada[2], camada[3]))
                    for i, camada in enumerate(MAR_DE_NUVENS.get(tema.nome, ()))]
        if any(_regra(tema.nome, p)[3] for p in ("longe", "perto")):
            self._clarear_o_sol()
        astro = (arte.png("objetos", "cenario", tema.nome, "astro_4f.png"), 4)
        if astro[0] is None:
            astro = (arte.png("objetos", "cenario", tema.nome, "astro_3f.png"), 3)
        self.astro = arte.tira(astro[0], astro[1]) if astro[0] else None
        regra = RAIOS.get(tema.nome)
        self.raios = _raios(tema.nome, *regra) if regra else None
        self.raios_fortes = _raios(tema.nome + "+", regra[0], regra[1], regra[2], regra[3] + 6,
                                   regra[4] + 7) if regra else None
        self.brumas = [(_bruma(f"{tema.nome}/{i}", cor, alfa), frac)
                       for i, (frac, cor, alfa) in enumerate(BRUMA.get(tema.nome, ()))]
        baleia = arte.png("objetos", "cenario", tema.nome, "baleia_2f.png")
        self.baleia = arte.tira(baleia, 2) if baleia else None

    def _clarear_o_sol(self):
        """
        Na tela da largada o sol (que pulsa na batida) aparece inteiro: some a
        ilha que ficaria na frente dele nessa camera. Durante a fase elas ainda
        passam na frente dele de vez em quando -- e so o parallax.
        """
        from .mundo import ANCORA_X
        cx = -LARGURA * ANCORA_X / ESCALA
        sol_x, sol_y, raio = W * 0.74 - _deriva_astro(cx), H * 0.22, 22
        for prefixo, parallax, base in (("longe", 0.12, H * 0.52), ("perto", 0.25, H * 0.64)):
            pecas, desloc = self.pecas[prefixo], cx * parallax
            fica = []
            for u, i, espelhada, altitude in self.slots[prefixo]:
                img = pecas[i][0]
                x = (u - desloc + MARGEM) % VAO - MARGEM
                embaixo = base - altitude
                if (x < sol_x + raio and x + img.get_width() > sol_x - raio and
                        embaixo - img.get_height() < sol_y + raio and embaixo > sol_y - raio):
                    continue
                fica.append((u, i, espelhada, altitude))
            self.slots[prefixo] = fica

    def desenhar(self, tela, cam_x, cam_y, tempo, pulso, simples=False, clima=None, astro=1.0,
                 noite=None, aurora=1.0):
        """
        `pulso` vai de 1 (na batida) a 0 (entre batidas). `simples`: a versao
        alpha -- um fundo PARADO: o ceu, o astro e os morros lisos, sem nada
        se mexer (nem acompanhando a camera).
        """
        tema, b = self.tema, self.buf
        cx = cam_x / ESCALA
        dy = -cam_y / ESCALA * 0.08
        b.blit(ceu(tema), (0, 0))
        if simples:
            sx, sy = int(W * 0.74), int(H * 0.22)
            if self.astro is not None:
                b.blit(self.astro[0], (sx - self.astro[0].get_width() // 2,
                                       sy - self.astro[0].get_height() // 2))
            else:
                pygame.draw.circle(b, tema.sol, (sx, sy), 12)
            self._colinas(b, 0.0, H * 0.52, 28, 0.9, arte.escurecer(tema.montanha, 0.35))
            self._colinas(b, 0.0, H * 0.64, 18, 1.7, tema.montanha)
            tela.blit(pygame.transform.scale(b, (LARGURA, ALTURA)), (0, 0))
            return

        if noite is None:
            noite = NOITE.get(tema.nome, (1.0,))[0]
        if noite > 0.02:
            cor = arte.clarear(tema.ceu, 0.7)
            # anoitecendo, as estrelas acendem uma a uma
            for x, y, fase in self.estrelas[:int(len(self.estrelas) * noite)]:
                sx = (x - cx * 0.05) % (W * 2)
                if sx < W and math.sin(tempo * 2.0 + fase) > -0.3:   # piscam
                    b.fill(cor, (int(sx), int(y + dy), 1, 1))

        if tema.nome in AURORA:
            self._aurora(b, cx, dy, tempo, aurora)

        # sol / lua, respirando junto com a batida
        sx = int(W * 0.74 - _deriva_astro(cx))
        sy = int(H * 0.22 + dy)
        for cor, raio in HALO_LUA.get(tema.nome, ()):
            pygame.draw.circle(b, cor, (sx, sy), int(raio * astro) + (1 if pulso > 0.6 else 0))
        if self.raios:
            q = self.raios[int(tempo * 2.5) % len(self.raios)]
            if tema.nome == "eclipse" and pulso > 0.6:
                q = self.raios_fortes[int(tempo * 2.5) % len(self.raios)]
            q = _escalado(q, astro)
            b.blit(q, (sx - q.get_width() // 2, sy - q.get_height() // 2))
        if self.astro is not None:
            # 0 em repouso, 1 estourado na batida, 2 voltando
            q = _escalado(self.astro[1 if pulso > 0.6 else 2 if pulso > 0.2 else 0], astro)
            b.blit(q, (sx - q.get_width() // 2, sy - q.get_height() // 2))
        else:
            raio = 12 + int(2 * pulso)
            pygame.draw.circle(b, arte.escurecer(tema.sol, 0.55), (sx, sy), raio + 4)
            pygame.draw.circle(b, tema.sol, (sx, sy), raio)
            if tema.nome == "eclipse":
                pygame.draw.circle(b, arte.escurecer(tema.ceu, 0.5), (sx - 1, sy), raio - 2)

        cadente = CADENTE.get(tema.nome)
        if cadente:
            self._cadente(b, tempo, dy, cadente, arte.clarear(tema.ceu, 0.85))

        serra = SERRAS.get(tema.nome)
        if serra:
            # a serra la longe: quase nao anda, e o que da tamanho ao mundo
            img = self._serra(tema.nome, serra)
            x0 = -int(cx * 0.04) % PERIODO_SERRA
            y0 = int(H * serra[0] + dy) - img.get_height()
            b.blit(img, (x0 - PERIODO_SERRA, y0))
            b.blit(img, (x0, y0))
        if tema.nome in REVOADA:
            self._revoada(b, cx, dy, tempo, REVOADA[tema.nome])
        if self.baleia:
            self._baleia(b, cx, dy, tempo)

        self._apoiar(b, "nuvem", cx * 0.08, H * 0.34 + dy, 10, 0.7)

        longe = (cx * 0.12, H * 0.52 + dy * 2, 28, 0.9)
        perto = (cx * 0.25, H * 0.64 + dy * 3, 18, 1.7)
        muralhas = MURALHAS.get(tema.nome)
        if muralhas:
            # cidadela: muralha distante, suas torres, muralha de perto, seus castelos
            for prefixo, parallax, k_dy, cor in (("longe", 0.12, 2, arte.escurecer(tema.montanha, 0.35)),
                                                 ("perto", 0.25, 3, tema.montanha)):
                frac, janela = muralhas[prefixo]
                topo = int(H * frac + dy * k_dy)
                self._muralha(b, cx * parallax, topo, cor, janela)
                self._apoiar(b, prefixo, cx * parallax, topo, 0, 0)
        elif tema.nome in DUNAS:
            self._camadas_de_dunas(b, cx, dy)
        elif self.mar:
            # ilhas: as distantes, o mar de nuvens la embaixo, e as proximas
            self._apoiar(b, "longe", *longe)
            for camada, bolhas in self.mar:
                self._mar(b, camada, bolhas, cx, dy)
            self._apoiar(b, "perto", *perto)
        else:
            brumas = self.brumas
            self._morro(b, *longe, arte.escurecer(tema.montanha, 0.35), capim=False)
            self._apoiar(b, "longe", *longe)
            if brumas:
                self._bruma(b, brumas[0], cx * 0.16 + tempo * 2.0, dy * 2)
            self._morro(b, *perto, tema.montanha, capim=True)
            self._apoiar(b, "perto", *perto)
            if len(brumas) > 1:
                self._bruma(b, brumas[1], cx * 0.3 - tempo * 3.0, dy * 3)

        if clima:
            b.fill(clima[0], special_flags=pygame.BLEND_RGB_MULT)
            b.fill(clima[1], special_flags=pygame.BLEND_RGB_ADD)
        tela.blit(pygame.transform.scale(b, (LARGURA, ALTURA)), (0, 0))

    def _apoiar(self, b, prefixo, desloc, base, amp, freq, altura=None):
        """
        Planta as pecas de `prefixo` com a BASE na linha da colina daquela
        camada -- e por isso que elas andam no parallax certo sem conta
        nenhuma: a colina e funcao de (x + desloc), e a peca le a mesma conta.
        """
        pecas = self.pecas[prefixo]
        if not pecas:
            return
        _, _, afundar, flutua = _regra(self.tema.nome, prefixo)
        for u, i, espelhada, altitude in self.slots[prefixo]:
            x = (u - desloc + MARGEM) % VAO - MARGEM
            if x > W:
                continue
            img = pecas[i][1 if espelhada else 0]
            if x + img.get_width() <= 0:
                continue
            if flutua:
                b.blit(img, (int(x), int(base - altitude) - img.get_height()))
                continue
            if altura is not None:
                y = altura(x + img.get_width() * 0.5 + desloc)     # o relevo proprio da camada
            else:
                y = _altura(x + desloc, base, amp, freq) if amp else base
            b.blit(img, (int(x), int(y) - img.get_height() + afundar))

    _franjas = {}

    @classmethod
    def _franja(cls, comprimento, borda, alto, alfa):
        """[surfaces 1 x comprimento]: a franja da cortina, em 6 niveis de brilho."""
        chave = (comprimento, borda, alto, alfa)
        if chave not in cls._franjas:
            niveis = []
            for n in range(6):
                s = pygame.Surface((1, comprimento), pygame.SRCALPHA)
                for y in range(comprimento):
                    t = y / (comprimento - 1)                 # 0 no alto, 1 na borda acesa
                    cor = tuple(int(a + (b - a) * t ** 1.6) for a, b in zip(alto, borda))
                    a = alfa * (n + 1) / 6.0 * (t ** 2.2 if t < 0.93 else 1.0)
                    s.set_at((0, y), (*cor, int(a)))
                niveis.append(s)
            cls._franjas[chave] = niveis
        return cls._franjas[chave]

    def _aurora(self, b, cx, dy, tempo, forca):
        """As cortinas da aurora: uma franja por coluna do ceu, ondulando."""
        if forca <= 0.02:
            return
        for frac, comprimento, borda, alto, alfa, vel in AURORA[self.tema.nome]:
            niveis = self._franja(comprimento, borda, alto, alfa)
            base = H * frac + dy
            t = tempo * vel
            for x in range(W):
                u = x + cx * 0.02
                y = base + 9.0 * math.sin(u * 0.019 + t * 0.21) + 5.0 * math.sin(u * 0.047 - t * 0.37)
                luz = (0.5 + 0.5 * math.sin(u * 0.083 + t * 0.6)) * (0.6 + 0.4 * math.sin(u * 0.011 - t * 0.15))
                n = int(min(5.0, luz * forca * 5.5))
                if n > 0:
                    b.blit(niveis[n], (x, int(y) - comprimento))

    _serras = {}

    @classmethod
    def _serra(cls, nome, regra):
        """
        A serra, desenhada uma vez numa tira que se repete: picos em dente, a
        face virada para o astro (a direita) acesa, o cume com neve ou brasa, e
        a base sumindo na cor do ceu -- a nevoa da distancia.
        """
        img = cls._serras.get(nome)
        if img is not None:
            return img
        _, alto, corpo, luz, cume, nevoa = regra
        img = cls._serras[nome] = pygame.Surface((PERIODO_SERRA, alto), pygame.SRCALPHA)

        def tri(x, periodo, fase=0.0):
            t = (x / periodo + fase) % 1.0
            return 1.0 - abs(2.0 * t - 1.0)

        def topo(x):
            k = 0.55 * tri(x, PERIODO_SERRA / 4, 0.1) + 0.3 * tri(x, PERIODO_SERRA / 10, 0.4) \
                + 0.15 * tri(x, PERIODO_SERRA / 32)
            return int(alto - 4 - k * (alto - 6))
        for x in range(PERIODO_SERRA):
            y, depois = topo(x), topo((x + 1) % PERIODO_SERRA)
            antes = topo((x - 1) % PERIODO_SERRA)
            virada = depois > y or (depois == y and antes < y)      # desce para a direita
            for yy in range(y, alto):
                fundo = (yy - y) / max(1, alto - y)
                cor = luz if virada and yy - y < 7 + (x % 3) else corpo
                if yy - y < 3 and y < alto * 0.45:
                    cor = cume                                      # so os picos altos
                elif yy - y < 5 and y < alto * 0.3 and virada:
                    cor = cume
                # pontilhado da encosta e a nevoa embaixo
                if cor is corpo and (x + yy * 2) % 7 == 0 and fundo < 0.6:
                    cor = arte.escurecer(corpo, 0.18)
                if fundo > 0.55:
                    k = (fundo - 0.55) / 0.45
                    cor = tuple(int(c + (n - c) * k * 0.8) for c, n in zip(cor, nevoa))
                img.set_at((x, yy), cor)
        return img

    @staticmethod
    def _bruma(b, bruma, desloc, dy):
        img, frac = bruma
        x0 = -int(desloc) % PERIODO_BRUMA
        y = int(H * frac + dy)
        for x in range(x0 - PERIODO_BRUMA, W, PERIODO_BRUMA):
            b.blit(img, (x, y))

    @staticmethod
    def _cadente(b, tempo, dy, regra, cor):
        """Uma estrela cadente de vez em quando: um risco curto que se apaga na cauda."""
        cada, dura = regra
        n, t = divmod(tempo + cada * 0.6, cada)
        if t > dura:
            return
        k = t / dura
        x0 = 40 + (int(n) * 97) % (W - 110)
        y0 = 8 + (int(n) * 41) % 34
        x, y = x0 + k * 46, y0 + k * 17 + dy
        for i in range(7):
            if k * 46 - i * 2 < 0:
                break
            tom = tuple(max(0, c - i * 30) for c in cor)
            b.fill(tom, (int(x - i * 2), int(y - i * 0.74), 2 if i < 2 else 1, 1))

    def _baleia(self, b, cx, dy, tempo):
        """
        A baleia do ceu das ilhas: la longe, devagar, subindo e descendo. Cruza
        a tela de tempos em tempos e passa a maior parte do tempo fora dela.
        """
        q = self.baleia[int(tempo * 1.2) % 2]
        volta = W + 520
        x = W + 30 - (tempo * 7.0 + cx * 0.05 + 60) % volta
        if x > W or x < -q.get_width():
            return
        b.blit(q, (int(x), int(H * 0.40 + math.sin(tempo * 0.5) * 3 + dy)))

    @staticmethod
    def _revoada(b, cx, dy, tempo, cor):
        """Passaros em V cruzando o ceu, devagar, batendo asa cada um no seu tempo."""
        for n, (x0, y0, vel) in enumerate(((40, 0.30, 5.0), (230, 0.42, 3.5))):
            lider = (x0 - tempo * vel - cx * 0.06) % (W + 80) - 40
            for k, (dx, dyy) in enumerate(((0, 0), (5, 3), (10, 6), (6, -3), (12, -6))):
                x, y = int(lider + dx), int(H * y0 + dyy + dy)
                asa = int(tempo * 5 + k * 0.7 + n) % 2
                b.fill(cor, (x, y, 1, 1))
                b.fill(cor, (x - 1, y - 1 + asa, 1, 1))
                b.fill(cor, (x + 1, y - 1 + asa, 1, 1))
                if not asa:
                    b.fill(cor, (x - 2, y - 2, 1, 1))
                    b.fill(cor, (x + 2, y - 2, 1, 1))

    def _morro(self, b, desloc, base, amp, freq, cor, capim):
        """
        A colina detalhada: faixas mais escuras que seguem o relevo para baixo
        (a terra vai ficando funda), o cume aceso pela lua -- mais na encosta
        virada para ela, a direita -- e, na de perto, tufos de capim no alto.
        """
        self._colinas(b, desloc, base, amp, freq, cor)
        for desce, k in ((5, 0.12), (12, 0.24), (22, 0.36)):
            escura = arte.escurecer(cor, k)
            self._colinas(b, desloc, base + desce, amp, freq, escura)
            # a borda de cada faixa e pontilhada: a passagem nao vira um degrau liso
            for x in range(0, W, 2):
                y = int(_altura(x + desloc, base + desce, amp, freq))
                b.fill(escura, (x + (y % 2), y - 1, 1, 1))
        luar = arte.clarear(cor, 0.35)
        luar_forte = arte.clarear(cor, 0.6)
        capim_cor = arte.clarear(cor, 0.45)
        anterior = int(_altura(desloc - 1, base, amp, freq))
        for x in range(W):
            u = x + desloc
            y = int(_altura(u, base, amp, freq))
            # descendo para a direita, a encosta olha para a lua
            b.fill(luar_forte if y > anterior else luar, (x, y, 1, 1))
            anterior = y
            if capim:
                n = (int(u) * 2654435761 >> 7) & 31
                if n < 4:
                    b.fill(capim_cor, (x, y - 1 - (n & 1), 1, 1 + (n & 1)))   # um tufo
                elif n == 4:
                    b.fill(luar_forte, (x, y + 3, 1, 1))                      # uma pedrinha

    _dunas = {}

    @classmethod
    def _duna(cls, chave, amp, vao, corpo, sombra, crista):
        """
        (tira, alturas): uma volta inteira de dunas da camada, desenhada uma vez.
        O vento sopra da direita: cada duna sobe comprida e suave pela direita
        (a encosta do sol, com as ondulacoes do vento) e cai curta e ingreme pela
        esquerda -- a face de tras, numa sombra que acompanha a encosta e se
        desfaz em pontilhado. `alturas[u]` e quanto o relevo sobe acima da base
        em cada x da tira (as pecas se apoiam nele).
        """
        pronto = cls._dunas.get(chave)
        if pronto is not None:
            return pronto
        rnd = random.Random(chave)
        volta = vao * CRISTAS_POR_VOLTA
        cristas = [(k * vao + rnd.uniform(-0.22, 0.22) * vao, amp * rnd.uniform(0.5, 1.0),
                    vao * rnd.uniform(0.30, 0.42), vao * rnd.uniform(1.1, 1.6))
                   for k in range(CRISTAS_POR_VOLTA)]
        alto = amp + 12
        tira = pygame.Surface((volta, alto), pygame.SRCALPHA)
        meio_tom = tuple((a + b) // 2 for a, b in zip(corpo, sombra))
        ondula = tuple((3 * a + b) // 4 for a, b in zip(corpo, sombra))
        luz = tuple((a + b) // 2 for a, b in zip(corpo, crista))
        alturas = []
        for u in range(volta):
            melhor = (0.0, None)
            for uc, h, esq, dir_ in cristas:
                d = (u - uc + volta / 2) % volta - volta / 2      # a tira da a volta
                if d < 0:
                    t = -d / esq
                    sobe = h * (1.0 - t ** 1.7) if t < 1.0 else 0.0
                else:
                    t = d / dir_
                    sobe = h * (0.5 + 0.5 * math.cos(math.pi * t)) if t < 1.0 else 0.0
                if sobe > melhor[0]:
                    melhor = (sobe, (d, h, esq))
            sobe, dona = melhor
            alturas.append(sobe)
            y = alto - 1 - int(round(sobe))
            tira.fill(corpo, (u, y, 1, alto - y))
            if dona is None:
                continue
            d, h, esq = dona
            if d < 0:
                # a face de tras: uma faixa de sombra que segue a encosta
                fundo = 6 + int(5 * (1.0 + d / esq)) + ((u * 2654435761 >> 9) & 1)
                fundo = min(fundo, alto - y)
                tira.fill(sombra, (u, y, 1, fundo))
                for k in range(3):                               # e some em pontilhado
                    if (u + k) % (k + 2) == 0 and y + fundo + k < alto:
                        tira.set_at((u, y + fundo + k), meio_tom)
            else:
                tira.set_at((u, y), crista)
                if d < h * 1.2:
                    tira.set_at((u, y + 1), luz)                 # o sol pega o ombro da crista
                # as ondulacoes do vento, paralelas a encosta
                for prof in (5, 10, 15):
                    if y + prof < alto and ((u + prof * 2) // 4) % 3 == 0:
                        tira.set_at((u, y + prof), ondula)
        pronto = cls._dunas[chave] = (tira, alturas)
        return pronto

    def _camadas_de_dunas(self, b, cx, dy):
        """As tres camadas do deserto, da mais distante para a mais proxima, com as pecas."""
        for i, (pecas, parallax, frac, k_dy, amp, vao, corpo, sombra, crista) in enumerate(
                DUNAS[self.tema.nome]):
            tira, alturas = self._duna(f"{self.tema.nome}/{i}", amp, vao, corpo, sombra, crista)
            volta = tira.get_width()
            desloc = cx * parallax
            base = int(H * frac + dy * k_dy)
            x0 = -int(desloc) % volta
            for x in (x0 - volta, x0):
                if x < W and x + volta > 0:
                    b.blit(tira, (x, base + 1 - tira.get_height()))
            b.fill(corpo, (0, base, W, H - base))
            if pecas:
                self._apoiar(b, pecas, desloc, base, 0, 0,
                             altura=lambda u: base - alturas[int(u) % volta])

    _tijolos = {}

    @classmethod
    def _textura_muralha(cls, cor):
        """Os tijolos do paredao, uma vez por cor: fiadas de 4 px, juntas a cada 8."""
        t = cls._tijolos.get(cor)
        if t is None:
            t = cls._tijolos[cor] = pygame.Surface((W + 8, H))
            t.fill(cor)
            rejunte = arte.escurecer(cor, 0.22)
            for y in range(0, H, 4):
                t.fill(rejunte, (0, y, W + 8, 1))
                for x in range(4 if (y // 4) % 2 else 0, W + 8, 8):
                    t.fill(rejunte, (x, y + 1, 1, 3))
            # o pe do paredao escurece em faixas
            for i, y in enumerate(range(int(H * 0.8), H, 6)):
                sombra = pygame.Surface((W + 8, 6))
                sombra.fill((0, 0, 0))
                sombra.set_alpha(30 + 18 * i)
                t.blit(sombra, (0, y))
        return t

    @classmethod
    def _muralha(cls, b, desloc, topo, cor, janela):
        """Paredao ate o pe da tela, com ameias no topo e umas janelas acesas."""
        d0 = int(desloc)
        b.blit(cls._textura_muralha(cor), (-(d0 % 8), topo), (0, 0, W + 8, H - topo))
        b.fill(arte.clarear(cor, 0.25), (0, topo, W, 1))           # o parapeito aceso
        d = int(desloc)
        for x in range(-(d % 10), W, 10):
            b.fill(cor, (x, topo - 4, 6, 4))                      # as ameias
            b.fill(arte.clarear(cor, 0.25), (x, topo - 4, 6, 1))  # com o alto aceso
            b.fill(arte.escurecer(cor, 0.25), (x, topo - 3, 1, 3))
        luz = arte.escurecer(cor, 0.45)
        b.fill(luz, (0, topo + 2, W, 1))                          # a sombra do parapeito
        for x in range(-(d % 14), W, 14):
            u = (x + d) // 14
            if (u * 2654435761 >> 9) % 7 == 0:                     # poucas janelas acesas
                b.fill(janela, (x + 3, topo + 7 + (u % 3) * 5, 1, 2))

    @staticmethod
    def _mar(b, camada, bolhas, cx, dy):
        """Nuvens baixas: bolhas redondas com o topo aceso pelo sol baixo."""
        base_frac, parallax, _, _, cor_topo, cor_corpo = camada
        base = int(H * base_frac + dy * 3)
        desloc = cx * parallax
        b.fill(cor_corpo, (0, base, W, H - base))
        periodo = W * 4
        brilho = arte.clarear(cor_topo, 0.3)
        for x, r, subida in bolhas:
            sx = int((x - desloc) % periodo)
            for xx in (sx, sx - periodo):
                if -r <= xx <= W + r:
                    cy = base - subida
                    pygame.draw.circle(b, cor_topo, (xx, cy), r)
                    # a quina da bolha virada para o sol (a direita) pega mais luz
                    pygame.draw.circle(b, brilho, (xx + r // 3, cy - r // 3), max(1, r // 3))
                    pygame.draw.circle(b, cor_topo, (xx + r // 3 - 1, cy - r // 3 + 1), max(1, r // 3))
                    pygame.draw.circle(b, cor_corpo, (xx, cy + 2), r)
        # mais para baixo o mar fica mais denso e mais escuro, em faixas pontilhadas
        for i, desce in enumerate((7, 13)):
            escura = arte.escurecer(cor_corpo, 0.08 * (i + 1))
            y = base + desce
            b.fill(escura, (0, y + 1, W, H - y))
            for xx in range(-(int(desloc) % 2), W, 2):
                b.fill(escura, (xx, y, 1, 1))

    @staticmethod
    def _colinas(b, desloc, base, amp, freq, cor):
        pontos = [(0, H)]
        for x in range(0, W + 8, 8):
            pontos.append((x, int(_altura(x + desloc, base, amp, freq))))
        pontos.append((W + 8, H))
        pygame.draw.polygon(b, cor, pontos)
