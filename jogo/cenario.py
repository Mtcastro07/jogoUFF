import math
import random

import pygame

from . import arte
from .camera import ONDE_LEO_FICA_X
from .config import LARG_TELA, ALT_TELA
from .paralaxe import Fundinho, FundoQueAnda, OndeTaOFundo, ImagemRepetida

ESCALA = 4
W, H = LARG_TELA // ESCALA, ALT_TELA // ESCALA

SEMEADURA = {
    "longe": (46, 17, 6, None),
    "perto": (72, 26, 14, None),
    "nuvem": (58, 24, 0, None),
}
SEMEADURA_FASE = {
    "geleira": {
        "longe": (40, 16, 5, None),
        "perto": (84, 30, 10, None),
    },
    "dunas": {
        "longe": (96, 34, 3, None),
        "perto": (132, 44, 5, None),
        "nuvem": (120, 40, 0, None),
    },
    "eclipse": {
        "longe": (46, 17, 4, None),
        "perto": (78, 28, 6, None),
    },
    "ilhas": {
        "longe": (74, 30, 0, (14, 56)),
        "perto": (150, 50, 0, (40, 54)),
        "nuvem": (76, 32, 0, None),
    },
}
NEVOA = {
    "geleira": {"longe": ((34, 54, 104), 0.42), "perto": ((30, 50, 96), 0.32)},
    "dunas": {"longe": ((176, 204, 186), 0.42)},
    "ilhas": {"longe": ((150, 92, 118), 0.5)},
}
VAO = W * 16
MARGENZINHA = 64

CEUS = {
    "geleira": ((0.0, (6, 10, 30)), (0.5, (18, 32, 72)), (1.0, (56, 90, 140))),
    "dunas": ((0.0, (26, 78, 126)), (0.42, (58, 140, 168)), (0.56, (150, 200, 190)),
              (1.0, (236, 208, 156))),
    "ilhas": ((0.0, (58, 36, 82)), (0.55, (138, 82, 108)), (1.0, (224, 148, 128))),
}

MAR_DE_NUVENS = {
    "ilhas": ((0.80, 0.06, 4, 10, (196, 132, 140), (170, 110, 126)),
              (0.93, 0.13, 6, 14, (222, 160, 156), (192, 128, 138))),
}

MURALHAS = {
    "eclipse": {"longe": (0.50, (96, 62, 50)), "perto": (0.575, (150, 92, 58))},
}

DUNAS = {
    "dunas": (("longe", 0.10, 0.515, 2.0, 15, 118, (228, 194, 150), (198, 162, 138), (248, 228, 186)),
              (None, 0.17, 0.585, 2.5, 13, 150, (226, 174, 120), (186, 134, 104), (252, 220, 156)),
              ("perto", 0.25, 0.660, 3.0, 15, 190, (214, 148, 92), (162, 102, 76), (253, 212, 138))),
}
CRISTAS_POR_VOLTA = 6

DERIVA_LIVRE, DERIVA_MAX = 150.0, 190.0

ceus_prontos = {}

NEUTRO = ((255, 255, 255), (0, 0, 0))
CLIMA_DE_CADA_ATO = {
    "bosque": (NEUTRO, NEUTRO, ((176, 190, 255), (20, 8, 40)), ((214, 255, 236), (0, 24, 22))),
    "dunas": (NEUTRO, NEUTRO, ((255, 244, 230), (18, 6, 0)), ((255, 252, 248), (4, 6, 8))),
    "geleira": (NEUTRO, NEUTRO, ((206, 220, 250), (44, 50, 66)), ((220, 255, 240), (0, 22, 22))),
    "ilhas": (NEUTRO, NEUTRO, ((176, 160, 232), (8, 0, 30)), ((255, 232, 200), (30, 10, 0))),
    "eclipse": (NEUTRO, NEUTRO, ((255, 176, 184), (38, 0, 6)), ((196, 208, 255), (4, 8, 40))),
}
TAMANHO_DO_SOL = {
    "bosque": (1.0, 1.0, 1.3, 1.1),
    "dunas": (1.0, 1.0, 0.85, 1.25),
    "ilhas": (1.0, 1.0, 0.9, 1.4),
    "geleira": (1.0, 1.0, 0.85, 1.2),
    "eclipse": (1.0, 1.0, 1.35, 1.8),
}
NOITE = {
    "bosque": (1.0, 1.0, 1.0, 1.0),
    "dunas": (0.0, 0.0, 0.0, 0.0),
    "ilhas": (0.0, 0.0, 1.0, 0.0),
    "geleira": (1.0, 1.0, 0.45, 1.0),
    "eclipse": (1.0, 1.0, 1.0, 1.0),
}
TEMPO_PRA_MUDAR_CLIMA = 900.0


def clima(fase, x):
    atos = CLIMA_DE_CADA_ATO[fase.cores_da_fase.nome]
    i = min(fase.ato(x), len(atos) - 1)
    atual = atos[i]
    if i > 0:
        k = (x - fase.x_das_partes[i]) / TEMPO_PRA_MUDAR_CLIMA
        if k < 1.0:
            k = max(0.0, k)
            k = k ** 2 * (3.0 - 2.0 * k)
            mult, soma = atos[i - 1]
            atual = (cor_no_meio(mult, atual[0], k), cor_no_meio(soma, atual[1], k))
    if atual == NEUTRO:
        return None
    return atual


def cor_no_meio(uma_cor, outra_cor, k):
    return tuple(int(a + (b - a) * k) for a, b in zip(uma_cor, outra_cor))


def mistura_dos_atos(fase, x, valores):
    i = min(fase.ato(x), len(valores) - 1)
    v = valores[i]
    if i > 0:
        k = max(0.0, min(1.0, (x - fase.x_das_partes[i]) / TEMPO_PRA_MUDAR_CLIMA))
        v = valores[i - 1] + (v - valores[i - 1]) * k * k * (3.0 - 2.0 * k)
    return v


def cena(fase, x):
    nome = fase.cores_da_fase.nome
    return {"clima": clima(fase, x),
            "astro": round(mistura_dos_atos(fase, x, TAMANHO_DO_SOL[nome]) * 20) / 20,
            "noite": mistura_dos_atos(fase, x, NOITE[nome]),
            "aurora": mistura_dos_atos(fase, x, AURORA_DO_ATO)}


tamanhos_prontos = {}


def no_tamanho_certo(img, k):
    if abs(k - 1.0) < 0.01:
        return img
    chave = (id(img), k)
    if chave not in tamanhos_prontos:
        w = max(1, round(img.get_width() * k))
        h = max(1, round(img.get_height() * k))
        tamanhos_prontos[chave] = (img, pygame.transform.scale(img, (w, h)))
    return tamanhos_prontos[chave][1]


PERIODO_SERRA = 640
SERRAS = {
    "bosque": (0.50, 46, (26, 40, 70), (44, 62, 96), (170, 190, 214), (22, 34, 66)),
    "eclipse": (0.50, 52, (30, 16, 44), (56, 32, 66), (150, 100, 84), (20, 9, 34)),
    "dunas": (0.52, 40, (104, 150, 166), (134, 176, 180), (214, 222, 200), (150, 200, 190)),
    "geleira": (0.50, 56, (34, 54, 98), (62, 90, 140), (226, 238, 255), (20, 34, 74)),
}
REVOADA = {"dunas": (40, 62, 92), "ilhas": (88, 54, 84), "eclipse": (70, 44, 98)}

RAIOS = {
    "dunas": ((255, 246, 204), 10, 14, 42, 12),
    "ilhas": ((255, 214, 150), 9, 15, 44, 10),
    "eclipse": ((255, 190, 110), 12, 16, 34, 13),
}
QUADROS_RAIOS = 12
HALO_LUA = {"bosque": (((24, 37, 70), 21), ((28, 42, 77), 17))}
BRUMA = {"bosque": ((0.515, (86, 124, 132), 46), (0.60, (70, 112, 112), 38)),
         "geleira": ((0.53, (110, 146, 200), 40), (0.62, (150, 184, 226), 30))}
PERIODO_BRUMA = 200
CADENTE = {"bosque": (11.0, 0.7), "geleira": (13.0, 0.7), "eclipse": (17.0, 0.6)}

AURORA = {
    "geleira": ((0.30, 40, (120, 255, 196), (70, 170, 255), 120, 1.0),
                (0.20, 30, (110, 200, 255), (150, 120, 255), 70, -0.7)),
}
AURORA_DO_ATO = (0.6, 1.0, 0.25, 1.6)


raios_prontos = {}


def faz_raios(chave, cor, n, r0, r1, alfa):
    if chave not in raios_prontos:
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
                curto = r0 + (fim - r0) * 0.55
                pygame.draw.polygon(s, (*cor, alfa + 8), [
                    pontos[0], (c + curto * math.cos(a), c + curto * math.sin(a)), pontos[3]])
            quadros.append(s)
        raios_prontos[chave] = quadros
    return raios_prontos[chave]


neblinas_prontas = {}


def faz_neblina(chave, cor, alfa):
    if chave not in neblinas_prontas:
        s = pygame.Surface((PERIODO_BRUMA, 13), pygame.SRCALPHA)
        dado = random.Random(chave)
        for _ in range(26):
            larg = dado.randint(14, 54)
            x, y = dado.randrange(PERIODO_BRUMA), dado.randint(1, 11)
            forca = int(alfa * (1.0 - abs(y - 6) / 7.0))
            for xx in (x, x - PERIODO_BRUMA):
                s.fill((*cor, forca), (xx, y, larg, 1))
                s.fill((*cor, forca // 2), (xx + 3, y - 1, larg - 8, 1))
        neblinas_prontas[chave] = s
    return neblinas_prontas[chave]


def sol_andando(cx):
    d = cx * 0.01
    if d <= DERIVA_LIVRE:
        return d
    folga = DERIVA_MAX - DERIVA_LIVRE
    return DERIVA_LIVRE + folga * (1.0 - math.exp(-(d - DERIVA_LIVRE) / folga))


def ceu(cores_da_fase):
    if cores_da_fase.nome not in ceus_prontos:
        s = pygame.Surface((W, H))
        if cores_da_fase.nome in CEUS:
            paradas = CEUS[cores_da_fase.nome]
        else:
            paradas = ((0.0, arte.escurece_cor(cores_da_fase.ceu, 0.35)),
                       (1.0, arte.clareia(cores_da_fase.ceu, 0.25)))
        for y in range(0, H, 2):
            t = y / H
            for (t0, c0), (t1, c1) in zip(paradas, paradas[1:]):
                if t <= t1:
                    k = (t - t0) / (t1 - t0)
                    break
            cor = tuple(int(c0[i] * (1 - k) + c1[i] * k) for i in range(3))
            s.fill(cor, (0, y, W, 2))
        ceus_prontos[cores_da_fase.nome] = s
    return ceus_prontos[cores_da_fase.nome]


VOLTA_MAR = W * 4


def faz_bolhas(semente, r0, r1):
    dado = random.Random(semente)
    bolhas, x = [], 0
    while x < VOLTA_MAR:
        r = dado.randint(r0, r1)
        bolhas.append((x, r, dado.randint(0, r // 2)))
        x += dado.randint(r // 2 + 2, r + r // 2)
    return bolhas


def altura_do_morro(u, base, sobe_quanto, freq):
    t = u * 0.008 * freq
    return base - sobe_quanto * (0.6 + 0.4 * math.sin(t) + 0.25 * math.sin(t * 2.7 + 1.0))


def qual_regra(fase, prefixo):
    return SEMEADURA_FASE.get(fase, {}).get(prefixo, SEMEADURA[prefixo])


def carrega_pecas(fase, prefixo):
    achadas = []
    for i in range(1, 13):
        img = arte.pega_png("objetos", "cenario", fase, f"{prefixo}_{i}.png")
        if img is not None:
            nevoa = NEVOA.get(fase, {}).get(prefixo)
            if nevoa:
                img = arte.recuar(img, *nevoa)
            achadas.append((img, pygame.transform.flip(img, True, False)))
    return achadas


def espalha_coisas(fase, prefixo, quantas_pecas):
    if not quantas_pecas:
        return []
    passo, jitter, _, ta_flutuando = qual_regra(fase, prefixo)
    dado = random.Random(f"{fase}/{prefixo}")
    slots, u, o_de_antes = [], 0.0, -1
    while u < VAO:
        i = dado.randrange(quantas_pecas)
        if quantas_pecas > 1 and i == o_de_antes:
            i = (i + 1 + dado.randrange(quantas_pecas - 1)) % quantas_pecas
        o_de_antes = i
        espelhada = dado.random() < 0.5
        altitude = dado.uniform(*ta_flutuando) if ta_flutuando else 0.0
        slots.append((u, i, espelhada, altitude))
        u += passo + dado.uniform(-jitter, jitter)
    return slots


def faz_colinas(b, andou, base, sobe_quanto, freq, cor):
    pontos = [(0, H)]
    for x in range(0, W + 8, 8):
        pontos.append((x, int(altura_do_morro(x + andou, base, sobe_quanto, freq))))
    pontos.append((W + 8, H))
    pygame.draw.polygon(b, cor, pontos)


franjas_prontas = {}


def faz_franja(tamanho_da_linha, borda, alto, alfa):
    chave = (tamanho_da_linha, borda, alto, alfa)
    if chave not in franjas_prontas:
        niveis = []
        for n in range(6):
            s = pygame.Surface((1, tamanho_da_linha), pygame.SRCALPHA)
            for y in range(tamanho_da_linha):
                t = y / (tamanho_da_linha - 1)
                cor = tuple(int(a + (b - a) * t ** 1.6) for a, b in zip(alto, borda))
                a = alfa * (n + 1) / 6.0 * (t ** 2.2 if t < 0.93 else 1.0)
                s.set_at((0, y), (*cor, int(a)))
            niveis.append(s)
        franjas_prontas[chave] = niveis
    return franjas_prontas[chave]


serras_prontas = {}


def faz_serra(nome, regra):
    img = serras_prontas.get(nome)
    if img is not None:
        return img
    _, alto, corpo, luz, cume, nevoa = regra
    img = serras_prontas[nome] = pygame.Surface((PERIODO_SERRA, alto), pygame.SRCALPHA)

    def tri(x, de_quanto_em_quanto, fase=0.0):
        t = (x / de_quanto_em_quanto + fase) % 1.0
        return 1.0 - abs(2.0 * t - 1.0)

    def topo(x):
        k = 0.55 * tri(x, PERIODO_SERRA / 4, 0.1) + 0.3 * tri(x, PERIODO_SERRA / 10, 0.4) \
            + 0.15 * tri(x, PERIODO_SERRA / 32)
        return int(alto - 4 - k * (alto - 6))
    for x in range(PERIODO_SERRA):
        y, depois = topo(x), topo((x + 1) % PERIODO_SERRA)
        antes = topo((x - 1) % PERIODO_SERRA)
        ta_virada = depois > y or (depois == y and antes < y)
        for yy in range(y, alto):
            fundo = (yy - y) / max(1, alto - y)
            cor = luz if ta_virada and yy - y < 7 + (x % 3) else corpo
            if yy - y < 3 and y < alto * 0.45:
                cor = cume
            elif yy - y < 5 and y < alto * 0.3 and ta_virada:
                cor = cume
            if cor is corpo and (x + yy * 2) % 7 == 0 and fundo < 0.6:
                cor = arte.escurece_cor(corpo, 0.18)
            if fundo > 0.55:
                k = (fundo - 0.55) / 0.45
                cor = tuple(int(c + (n - c) * k * 0.8) for c, n in zip(cor, nevoa))
            img.set_at((x, yy), cor)
    return img


dunas_prontas = {}


def faz_duna(chave, sobe_quanto, vao, corpo, sombra, crista):
    pronto = dunas_prontas.get(chave)
    if pronto is not None:
        return pronto
    dado = random.Random(chave)
    volta = vao * CRISTAS_POR_VOLTA
    cristas = [(k * vao + dado.uniform(-0.22, 0.22) * vao, sobe_quanto * dado.uniform(0.5, 1.0),
                vao * dado.uniform(0.30, 0.42), vao * dado.uniform(1.1, 1.6))
               for k in range(CRISTAS_POR_VOLTA)]
    alto = sobe_quanto + 12
    tira = pygame.Surface((volta, alto), pygame.SRCALPHA)
    meia_cor = tuple((a + b) // 2 for a, b in zip(corpo, sombra))
    ondula = tuple((3 * a + b) // 4 for a, b in zip(corpo, sombra))
    luz = tuple((a + b) // 2 for a, b in zip(corpo, crista))
    alturas = []
    for u in range(volta):
        melhor = (0.0, None)
        for uc, h, esq, dir_ in cristas:
            d = (u - uc + volta / 2) % volta - volta / 2
            if d < 0:
                t = -d / esq
                sobe = h * (1.0 - t ** 1.7) if t < 1.0 else 0.0
            else:
                t = d / dir_
                sobe = h * (0.5 + 0.5 * math.cos(math.pi * t)) if t < 1.0 else 0.0
            if sobe > melhor[0]:
                melhor = (sobe, (d, h, esq))
        sobe, de_quem_e = melhor
        alturas.append(sobe)
        y = alto - 1 - int(round(sobe))
        tira.fill(corpo, (u, y, 1, alto - y))
        if de_quem_e is None:
            continue
        d, h, esq = de_quem_e
        if d < 0:
            fundo = 6 + int(5 * (1.0 + d / esq)) + ((u * 2654435761 >> 9) & 1)
            fundo = min(fundo, alto - y)
            tira.fill(sombra, (u, y, 1, fundo))
            for k in range(3):
                if (u + k) % (k + 2) == 0 and y + fundo + k < alto:
                    tira.set_at((u, y + fundo + k), meia_cor)
        else:
            tira.set_at((u, y), crista)
            if d < h * 1.2:
                tira.set_at((u, y + 1), luz)
            for prof in (5, 10, 15):
                if y + prof < alto and ((u + prof * 2) // 4) % 3 == 0:
                    tira.set_at((u, y + prof), ondula)
    pronto = dunas_prontas[chave] = (tira, alturas)
    return pronto


tijolos_prontos = {}


def textura_do_muro(cor):
    t = tijolos_prontos.get(cor)
    if t is None:
        t = tijolos_prontos[cor] = pygame.Surface((W + 8, H))
        t.fill(cor)
        rejunte = arte.escurece_cor(cor, 0.22)
        for y in range(0, H, 4):
            t.fill(rejunte, (0, y, W + 8, 1))
            for x in range(4 if (y // 4) % 2 else 0, W + 8, 8):
                t.fill(rejunte, (x, y + 1, 1, 3))
        for i, y in enumerate(range(int(H * 0.8), H, 6)):
            sombra = pygame.Surface((W + 8, 6))
            sombra.fill((0, 0, 0))
            sombra.set_alpha(30 + 18 * i)
            t.blit(sombra, (0, y))
    return t


def faz_bolha(b, x, cy, r, topo, brilho, corpo):
    pygame.draw.circle(b, topo, (x, cy), r)
    pygame.draw.circle(b, brilho, (x + r // 3, cy - r // 3), max(1, r // 3))
    pygame.draw.circle(b, topo, (x + r // 3 - 1, cy - r // 3 + 1), max(1, r // 3))
    pygame.draw.circle(b, corpo, (x, cy + 2), r)


mares_prontos = {}


def faz_mar(bolhas, cores):
    chave = (tuple(bolhas), cores)
    if chave not in mares_prontos:
        tem_em_cima = max(r + subida for _, r, subida in bolhas) + 1
        abaixo = max(r - subida for _, r, subida in bolhas) + 3
        tira = pygame.Surface((VOLTA_MAR, tem_em_cima + abaixo), pygame.SRCALPHA)
        for x, r, subida in bolhas:
            for xx in (x - VOLTA_MAR, x, x + VOLTA_MAR):
                faz_bolha(tira, xx, tem_em_cima - subida, r, *cores)
        mares_prontos[chave] = tira, tem_em_cima
    return mares_prontos[chave]


class Estrelas(Fundinho):
    def __init__(self, cores_da_fase):
        super().__init__(0.05)
        dado = random.Random(len(cores_da_fase.nome))
        self.estrelas = [(dado.uniform(0, W * 2), dado.uniform(0, H * 0.6),
                          dado.uniform(0, math.tau)) for _ in range(50)]
        self.cor = arte.clareia(cores_da_fase.ceu, 0.7)

    def draw(self):
        q = self.fundo.agora_ta
        if q.noite <= 0.02:
            return
        andou = self.quanto_andou()
        for x, y, fase in self.estrelas[:int(len(self.estrelas) * q.noite)]:
            sx = (x - andou) % (W * 2)
            if sx < W and math.sin(q.tempo * 2.0 + fase) > -0.3:
                q.tela.fill(self.cor, (int(sx), int(y + q.dy), 1, 1))


class Aurora(Fundinho):
    def __init__(self, cortininhas):
        super().__init__(0.02)
        self.cortininhas = cortininhas

    def draw(self):
        q = self.fundo.agora_ta
        b, tempo, forca, andou = q.tela, q.tempo, q.aurora, self.quanto_andou()
        if forca <= 0.02:
            return
        for altura_na_tela, tamanho_da_linha, borda, alto, alfa, vel in self.cortininhas:
            niveis = faz_franja(tamanho_da_linha, borda, alto, alfa)
            base = H * altura_na_tela + q.dy
            t = tempo * vel
            for x in range(W):
                u = x + andou
                y = base + 9.0 * math.sin(u * 0.019 + t * 0.21) + 5.0 * math.sin(u * 0.047 - t * 0.37)
                luz = (0.5 + 0.5 * math.sin(u * 0.083 + t * 0.6)) * (0.6 + 0.4 * math.sin(u * 0.011 - t * 0.15))
                n = int(min(5.0, luz * forca * 5.5))
                if n > 0:
                    b.blit(niveis[n], (x, int(y) - tamanho_da_linha))


class SolOuLua(Fundinho):
    def __init__(self, cores_da_fase, imagem):
        super().__init__(0.01, 0.22)
        self.cores_da_fase, self.astro = cores_da_fase, imagem
        self.raios = None
        if cores_da_fase.nome in RAIOS:
            cor, n, r0, r1, alfa = RAIOS[cores_da_fase.nome]
            self.raios = faz_raios(cores_da_fase.nome, cor, n, r0, r1, alfa)
            self.raios_fortes = faz_raios(cores_da_fase.nome + "+", cor, n, r0, r1 + 6, alfa + 7)

    def draw(self):
        q, cores_da_fase = self.fundo.agora_ta, self.cores_da_fase
        b, pulso = q.tela, q.pulso
        sx = int(W * 0.74 - sol_andando(q.cx))
        sy = int(self.base())
        for cor, raio in HALO_LUA.get(cores_da_fase.nome, ()):
            raio = int(raio * q.astro)
            if pulso > 0.6:
                raio += 1
            pygame.draw.circle(b, cor, (sx, sy), raio)
        if self.raios:
            img = self.raios[int(q.tempo * 2.5) % len(self.raios)]
            if cores_da_fase.nome == "eclipse" and pulso > 0.6:
                img = self.raios_fortes[int(q.tempo * 2.5) % len(self.raios)]
            img = no_tamanho_certo(img, q.astro)
            b.blit(img, (sx - img.get_width() // 2, sy - img.get_height() // 2))
        if pulso > 0.6:
            self.astro.set_curr_frame(1)
        elif pulso > 0.2:
            self.astro.set_curr_frame(2)
        else:
            self.astro.set_curr_frame(0)
        img = no_tamanho_certo(self.astro.imagem_dele(), q.astro)
        b.blit(img, (sx - img.get_width() // 2, sy - img.get_height() // 2))


class EstrelaCadente(Fundinho):
    def __init__(self, cada, dura, cor):
        super().__init__()
        self.cada, self.dura, self.cor = cada, dura, cor

    def draw(self):
        q = self.fundo.agora_ta
        n, t = divmod(q.tempo + self.cada * 0.6, self.cada)
        if t > self.dura:
            return
        k = t / self.dura
        x0 = 40 + (int(n) * 97) % (W - 110)
        y0 = 8 + (int(n) * 41) % 34
        x, y = x0 + k * 46, y0 + k * 17 + q.dy
        for i in range(7):
            if k * 46 - i * 2 < 0:
                break
            tom = tuple(max(0, c - i * 30) for c in self.cor)
            q.tela.fill(tom, (int(x - i * 2), int(y - i * 0.74), 2 if i < 2 else 1, 1))


class NotasVoando(Fundinho):
    def __init__(self, cor):
        super().__init__(0.06)
        self.cor = cor

    def draw(self):
        q = self.fundo.agora_ta
        b, tempo, cor, andou = q.tela, q.tempo, self.cor, self.quanto_andou()
        for n, (x0, y0, vel) in enumerate(((40, 0.30, 5.0), (230, 0.42, 3.5))):
            o_primeiro = (x0 - tempo * vel - andou) % (W + 80) - 40
            for k, (dx, dyy) in enumerate(((0, 0), (5, 3), (10, 6), (6, -3), (12, -6))):
                x, y = int(o_primeiro + dx), int(H * y0 + dyy + q.dy)
                asa = int(tempo * 5 + k * 0.7 + n) % 2
                b.fill(cor, (x, y, 1, 1))
                b.fill(cor, (x - 1, y - 1 + asa, 1, 1))
                b.fill(cor, (x + 1, y - 1 + asa, 1, 1))
                if not asa:
                    b.fill(cor, (x - 2, y - 2, 1, 1))
                    b.fill(cor, (x + 2, y - 2, 1, 1))


class Baleia(Fundinho):
    def __init__(self, animacao):
        super().__init__(0.05)
        self.animacao = animacao

    def draw(self):
        q, baleia = self.fundo.agora_ta, self.animacao
        baleia.set_curr_frame(q.tempo * 1.2)
        volta = W + 520
        x = W + 30 - (q.tempo * 7.0 + self.quanto_andou() + 60) % volta
        if x > W or x < -baleia.width:
            return
        q.tela.blit(baleia.imagem_dele(),
                    (int(x), int(H * 0.40 + math.sin(q.tempo * 0.5) * 3 + q.dy)))


class CoisasDoFundo(Fundinho):
    def __init__(self, cenario, prefixo, velocidade, altura_na_tela, peso=1, sobe_quanto=0, freq=0.0,
                 reta=False, altura_do_lugar=None):
        super().__init__(velocidade, altura_na_tela, peso)
        self.prefixo, self.sobe_quanto, self.freq = prefixo, sobe_quanto, freq
        self.reta, self.altura_do_lugar = reta, altura_do_lugar
        self.pecas, self.slots = cenario.pecas[prefixo], cenario.slots[prefixo]
        _, _, self.afunda, self.ta_flutuando = qual_regra(cenario.cores_da_fase.nome, prefixo)

    def draw(self):
        if not self.pecas:
            return
        b, andou, base = self.fundo.agora_ta.tela, self.quanto_andou(), self.base()
        if self.reta:
            base = int(base)
        for u, i, espelhada, altitude in self.slots:
            x = (u - andou + MARGENZINHA) % VAO - MARGENZINHA
            if x > W:
                continue
            img = self.pecas[i][1 if espelhada else 0]
            if x + img.get_width() <= 0:
                continue
            y = base
            if self.ta_flutuando:
                y -= altitude
            elif self.altura_do_lugar is not None:
                y -= self.altura_do_lugar(x + img.get_width() * 0.5 + andou)
            elif self.sobe_quanto:
                y = altura_do_morro(x + andou, base, self.sobe_quanto, self.freq)
            b.blit(img, (int(x), int(y) - img.get_height() + self.afunda))


class Serra(ImagemRepetida):
    def __init__(self, nome, regra):
        super().__init__(0.04, faz_serra(nome, regra), regra[0])


class Neblina(ImagemRepetida):
    def __init__(self, velocidade, vento, imagem, altura_na_tela, peso):
        dupla = pygame.Surface((PERIODO_BRUMA * 2, imagem.get_height()), pygame.SRCALPHA)
        for x in (0, PERIODO_BRUMA):
            dupla.blit(imagem, (x, 0))
        super().__init__(velocidade, dupla, altura_na_tela, peso)
        self.vento = vento

    def passo(self):
        return int(self.quanto_andou() + self.fundo.agora_ta.tempo * self.vento)

    def topo(self):
        return int(self.base())


class Morro(Fundinho):
    def __init__(self, velocidade, altura_na_tela, peso, sobe_quanto, freq, cor, capim):
        super().__init__(velocidade, altura_na_tela, peso)
        self.sobe_quanto, self.freq, self.cor, self.capim = sobe_quanto, freq, cor, capim

    def draw(self):
        b, andou, base = self.fundo.agora_ta.tela, self.quanto_andou(), self.base()
        sobe_quanto, freq, cor = self.sobe_quanto, self.freq, self.cor
        faz_colinas(b, andou, base, sobe_quanto, freq, cor)
        for desce, k in ((5, 0.12), (12, 0.24), (22, 0.36)):
            cor_escura = arte.escurece_cor(cor, k)
            faz_colinas(b, andou, base + desce, sobe_quanto, freq, cor_escura)
            for x in range(0, W, 2):
                y = int(altura_do_morro(x + andou, base + desce, sobe_quanto, freq))
                b.fill(cor_escura, (x + (y % 2), y - 1, 1, 1))
        luzinha_da_lua = arte.clareia(cor, 0.35)
        luzona_da_lua = arte.clareia(cor, 0.6)
        capim_cor = arte.clareia(cor, 0.45)
        o_de_antes = int(altura_do_morro(andou - 1, base, sobe_quanto, freq))
        for x in range(W):
            u = x + andou
            y = int(altura_do_morro(u, base, sobe_quanto, freq))
            b.fill(luzona_da_lua if y > o_de_antes else luzinha_da_lua, (x, y, 1, 1))
            o_de_antes = y
            if self.capim:
                n = (int(u) * 2654435761 >> 7) & 31
                if n < 4:
                    b.fill(capim_cor, (x, y - 1 - (n & 1), 1, 1 + (n & 1)))
                elif n == 4:
                    b.fill(luzona_da_lua, (x, y + 3, 1, 1))


class Duna(ImagemRepetida):
    def __init__(self, velocidade, altura_na_tela, peso, tira, alturas, corpo):
        super().__init__(velocidade, tira, altura_na_tela, peso)
        self.alturas, self.corpo = alturas, corpo

    def topo(self):
        return int(self.base()) + 1 - self.altura

    def altura_do_lugar(self, u):
        return self.alturas[int(u) % self.largura]

    def draw(self):
        super().draw()
        base = int(self.base())
        self.fundo.agora_ta.tela.fill(self.corpo, (0, base, W, H - base))


class Muralha(ImagemRepetida):
    def __init__(self, velocidade, altura_na_tela, peso, cor, janela):
        super().__init__(velocidade, textura_do_muro(cor), altura_na_tela, peso)
        self.cor, self.janela = cor, janela

    def topo(self):
        return int(self.base())

    def draw(self):
        super().draw()
        b, topo, d, cor = self.fundo.agora_ta.tela, self.topo(), self.passo(), self.cor
        b.fill(arte.clareia(cor, 0.25), (0, topo, W, 1))
        for x in range(-(d % 10), W, 10):
            b.fill(cor, (x, topo - 4, 6, 4))
            b.fill(arte.clareia(cor, 0.25), (x, topo - 4, 6, 1))
            b.fill(arte.escurece_cor(cor, 0.25), (x, topo - 3, 1, 3))
        luz = arte.escurece_cor(cor, 0.45)
        b.fill(luz, (0, topo + 2, W, 1))
        for x in range(-(d % 14), W, 14):
            u = (x + d) // 14
            if (u * 2654435761 >> 9) % 7 == 0:
                b.fill(self.janela, (x + 3, topo + 7 + (u % 3) * 5, 1, 2))


class MarDeNuvem(ImagemRepetida):
    def __init__(self, nome, i, camada):
        altura_na_tela, velocidade, r0, r1, topo, self.cor = camada
        self.bolhas = faz_bolhas(f"{nome}/mar{i}", r0, r1)
        self.cores = (topo, arte.clareia(topo, 0.3), self.cor)
        tira, self.tem_em_cima = faz_mar(self.bolhas, self.cores)
        super().__init__(velocidade, tira, altura_na_tela, 3)

    def passo(self):
        return math.ceil(self.quanto_andou())

    def topo(self):
        return int(self.base()) - self.tem_em_cima

    def draw(self):
        b, base, cor, andou = self.fundo.agora_ta.tela, int(self.base()), self.cor, self.quanto_andou()
        b.fill(cor, (0, base, W, H - base))
        if 0.0 < abs(andou - round(andou)) < 1e-9:
            for x, r, subida in self.bolhas:
                sx = int((x - andou) % VOLTA_MAR)
                for xx in (sx, sx - VOLTA_MAR):
                    if -r <= xx <= W + r:
                        faz_bolha(b, xx, base - subida, r, *self.cores)
        else:
            super().draw()
        for i, desce in enumerate((7, 13)):
            cor_escura = arte.escurece_cor(cor, 0.08 * (i + 1))
            y = base + desce
            b.fill(cor_escura, (0, y + 1, W, H - y))
            for xx in range(-(int(andou) % 2), W, 2):
                b.fill(cor_escura, (xx, y, 1, 1))


class FundoTodo(FundoQueAnda):
    def __init__(self, cores_da_fase):
        super().__init__()
        self.cores_da_fase = cores_da_fase
        self.telinha = pygame.Surface((W, H))
        self.pecas = {p: carrega_pecas(cores_da_fase.nome, p) for p in SEMEADURA}
        self.slots = {p: espalha_coisas(cores_da_fase.nome, p, len(v)) for p, v in self.pecas.items()}
        if any(qual_regra(cores_da_fase.nome, p)[3] for p in ("longe", "perto")):
            self.clareia_sol()
        self.astro = arte.pega_tira("objetos", "cenario", cores_da_fase.nome, "astro_3f.png", quadros=3)
        self.monta()

    def monta(self):
        cores_da_fase, nome = self.cores_da_fase, self.cores_da_fase.nome
        bota_camada = self.add_layer
        bota_camada(Fundinho(imagem=ceu(cores_da_fase)))
        bota_camada(Estrelas(cores_da_fase))
        if nome in AURORA:
            bota_camada(Aurora(AURORA[nome]))
        bota_camada(SolOuLua(cores_da_fase, self.astro))
        if nome in CADENTE:
            bota_camada(EstrelaCadente(*CADENTE[nome], arte.clareia(cores_da_fase.ceu, 0.85)))
        if nome in SERRAS:
            bota_camada(Serra(nome, SERRAS[nome]))
        if nome in REVOADA:
            bota_camada(NotasVoando(REVOADA[nome]))
        baleia = arte.pega_tira("objetos", "cenario", nome, "baleia_2f.png", quadros=2)
        if baleia:
            bota_camada(Baleia(baleia))
        bota_camada(CoisasDoFundo(self, "nuvem", 0.08, 0.34, 1, 10, 0.7))

        longe, perto = (0.12, 0.52, 2, 28, 0.9), (0.25, 0.64, 3, 18, 1.7)
        cor_la_longe, cor_aqui_perto = arte.escurece_cor(cores_da_fase.montanha, 0.35), cores_da_fase.montanha
        if nome in MURALHAS:
            for prefixo, velocidade, peso, cor in (("longe", 0.12, 2, cor_la_longe),
                                                       ("perto", 0.25, 3, cor_aqui_perto)):
                altura_na_tela, janela = MURALHAS[nome][prefixo]
                bota_camada(Muralha(velocidade, altura_na_tela, peso, cor, janela))
                bota_camada(CoisasDoFundo(self, prefixo, velocidade, altura_na_tela, peso, reta=True))
        elif nome in DUNAS:
            for i, regra in enumerate(DUNAS[nome]):
                prefixo, velocidade, altura_na_tela, peso, sobe_quanto, vao, corpo, sombra, crista = regra
                tira, alturas = faz_duna(f"{nome}/{i}", sobe_quanto, vao, corpo, sombra, crista)
                duna = Duna(velocidade, altura_na_tela, peso, tira, alturas, corpo)
                bota_camada(duna)
                if prefixo:
                    bota_camada(CoisasDoFundo(self, prefixo, velocidade, altura_na_tela, peso,
                                              reta=True, altura_do_lugar=duna.altura_do_lugar))
        elif nome in MAR_DE_NUVENS:
            bota_camada(CoisasDoFundo(self, "longe", *longe))
            for i, camada in enumerate(MAR_DE_NUVENS[nome]):
                bota_camada(MarDeNuvem(nome, i, camada))
            bota_camada(CoisasDoFundo(self, "perto", *perto))
        else:
            bota_camada(Morro(*longe, cor_la_longe, capim=False))
            bota_camada(CoisasDoFundo(self, "longe", *longe))
            altura_na_tela, cor, alfa = BRUMA[nome][0]
            bota_camada(Neblina(0.16, 2.0, faz_neblina(f"{nome}/0", cor, alfa), altura_na_tela, 2))
            bota_camada(Morro(*perto, cor_aqui_perto, capim=True))
            bota_camada(CoisasDoFundo(self, "perto", *perto))
            altura_na_tela, cor, alfa = BRUMA[nome][1]
            bota_camada(Neblina(0.3, -3.0, faz_neblina(f"{nome}/1", cor, alfa), altura_na_tela, 3))

    def clareia_sol(self):
        cx = -LARG_TELA * ONDE_LEO_FICA_X / ESCALA
        x_do_sol, y_do_sol, raio = W * 0.74 - sol_andando(cx), H * 0.22, 22
        for prefixo, parallax, base in (("longe", 0.12, H * 0.52), ("perto", 0.25, H * 0.64)):
            pecas, andou = self.pecas[prefixo], cx * parallax
            fica = []
            for u, i, espelhada, altitude in self.slots[prefixo]:
                img = pecas[i][0]
                x = (u - andou + MARGENZINHA) % VAO - MARGENZINHA
                embaixo = base - altitude
                if (x < x_do_sol + raio and x + img.get_width() > x_do_sol - raio and
                        embaixo - img.get_height() < y_do_sol + raio and embaixo > y_do_sol - raio):
                    continue
                fica.append((u, i, espelhada, altitude))
            self.slots[prefixo] = fica

    def mostra_na_tela(self, tela, cam, tempo, pulso, clima=None, astro=1.0, noite=None, aurora=1.0):
        b = self.telinha
        if noite is None:
            noite = NOITE[self.cores_da_fase.nome][0]
        cx, dy = cam.x / ESCALA, -cam.y / ESCALA * 0.08
        self.pinta_tudo(OndeTaOFundo(b, cx, dy, tempo, pulso, astro, noite, aurora))
        if clima:
            b.fill(clima[0], special_flags=pygame.BLEND_RGB_MULT)
            b.fill(clima[1], special_flags=pygame.BLEND_RGB_ADD)
        tela.blit(pygame.transform.scale(b, (LARG_TELA, ALT_TELA)), (0, 0))
