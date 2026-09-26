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
VAO = W * 16             # a semeadura se repete so depois disso: nunca, na pratica
MARGEM = 64              # mais larga que qualquer peca: quem cruza a borda esquerda
                         # sai de cena aos poucos, em vez de sumir de uma vez

# Ceu com mais de dois tons (altura 0 = topo da tela, 1 = pe). As ilhas pedem o
# por do sol do GDD: roxo em cima, malva no meio, pessego rente as nuvens.
CEUS = {
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

_ceus = {}


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

    def _clarear_o_sol(self):
        """
        Na tela da largada o sol (que pulsa na batida) aparece inteiro: some a
        ilha que ficaria na frente dele nessa camera. Durante a fase elas ainda
        passam na frente dele de vez em quando -- e so o parallax.
        """
        from .mundo import ANCORA_X
        cx = -LARGURA * ANCORA_X / ESCALA
        sol_x, sol_y, raio = W * 0.74 - cx * 0.01, H * 0.22, 22
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

    def desenhar(self, tela, cam_x, cam_y, tempo, pulso, simples=False):
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

        if tema.nome != "ilhas":
            cor = arte.clarear(tema.ceu, 0.7)
            for x, y, fase in self.estrelas:
                sx = (x - cx * 0.05) % (W * 2)
                if sx < W and math.sin(tempo * 2.0 + fase) > -0.3:   # piscam
                    b.fill(cor, (int(sx), int(y + dy), 1, 1))

        # sol / lua, respirando junto com a batida
        sx = int(W * 0.74 - cx * 0.01) % (W * 3)
        sy = int(H * 0.22 + dy)
        if self.astro is not None:
            # 0 em repouso, 1 estourado na batida, 2 voltando
            q = self.astro[1 if pulso > 0.6 else 2 if pulso > 0.2 else 0]
            b.blit(q, (sx - q.get_width() // 2, sy - q.get_height() // 2))
        else:
            raio = 12 + int(2 * pulso)
            pygame.draw.circle(b, arte.escurecer(tema.sol, 0.55), (sx, sy), raio + 4)
            pygame.draw.circle(b, tema.sol, (sx, sy), raio)
            if tema.nome == "eclipse":
                pygame.draw.circle(b, arte.escurecer(tema.ceu, 0.5), (sx - 1, sy), raio - 2)

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
        elif self.mar:
            # ilhas: as distantes, o mar de nuvens la embaixo, e as proximas
            self._apoiar(b, "longe", *longe)
            for camada, bolhas in self.mar:
                self._mar(b, camada, bolhas, cx, dy)
            self._apoiar(b, "perto", *perto)
        else:
            self._colinas(b, *longe, arte.escurecer(tema.montanha, 0.35))
            self._apoiar(b, "longe", *longe)
            self._colinas(b, *perto, tema.montanha)
            self._apoiar(b, "perto", *perto)

        tela.blit(pygame.transform.scale(b, (LARGURA, ALTURA)), (0, 0))

    def _apoiar(self, b, prefixo, desloc, base, amp, freq):
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
            y = _altura(x + desloc, base, amp, freq) if amp else base
            b.blit(img, (int(x), int(y) - img.get_height() + afundar))

    @staticmethod
    def _muralha(b, desloc, topo, cor, janela):
        """Paredao ate o pe da tela, com ameias no topo e umas janelas acesas."""
        b.fill(cor, (0, topo, W, H - topo))
        d = int(desloc)
        for x in range(-(d % 10), W, 10):
            b.fill(cor, (x, topo - 4, 6, 4))                      # as ameias
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
        for x, r, subida in bolhas:
            sx = int((x - desloc) % periodo)
            for xx in (sx, sx - periodo):
                if -r <= xx <= W + r:
                    pygame.draw.circle(b, cor_topo, (xx, base - subida), r)
                    pygame.draw.circle(b, cor_corpo, (xx, base - subida + 2), r)

    @staticmethod
    def _colinas(b, desloc, base, amp, freq, cor):
        pontos = [(0, H)]
        for x in range(0, W + 8, 8):
            pontos.append((x, int(_altura(x + desloc, base, amp, freq))))
        pontos.append((W + 8, H))
        pygame.draw.polygon(b, cor, pontos)
