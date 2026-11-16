"""
Pinta, por codigo, a arte da segunda rodada: obstaculos de outros TIPOS (nao so
o mesmo espinho), blocos variados, enfeites de mapa e pecas novas de paisagem.

    ./.venv/bin/python ferramentas/pintar_arte.py

Tudo sai em assets/art/objetos/ com os nomes que o jogo ja procura sozinho:

    jogo/<fase>/caco{1,2,3}v{4,5}[_4f].png   os tipos novos de perigo
    jogo/<fase>/bloco_v{2,3}.png             os blocos variados
    jogo/<fase>/enfeite_N[_Kf].png           os enfeites de mapa
    cenario/<fase>/{perto,longe}_N.png       as pecas da paisagem

As pecas de jogo sao desenhadas em pixels logicos e ampliadas 2x (o "pixel" do
chao); as de paisagem ja nascem na escala do fundo (320x180). Rodar de novo
regrava os mesmos arquivos: nada aqui e sorteado.
"""

import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(RAIZ, "assets", "art", "objetos")


class C:
    """Uma tela pequena de pixels logicos."""

    def __init__(self, w, h):
        self.s = pygame.Surface((w, h), pygame.SRCALPHA)
        self.w, self.h = w, h

    def p(self, x, y, cor):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.s.set_at((x, y), cor if len(cor) == 4 else (*cor, 255))

    def r(self, x0, y0, x1, y1, cor):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.p(x, y, cor)

    def poli(self, pontos, cor):
        pygame.draw.polygon(self.s, (*cor, 255), [(int(x), int(y)) for x, y in pontos])

    def linha(self, a, b, cor):
        pygame.draw.line(self.s, (*cor, 255), (int(a[0]), int(a[1])), (int(b[0]), int(b[1])))

    def disco(self, cx, cy, raio, cor):
        for y in range(int(cy - raio) - 1, int(cy + raio) + 2):
            for x in range(int(cx - raio) - 1, int(cx + raio) + 2):
                if (x - cx) ** 2 + (y - cy) ** 2 <= raio * raio + 0.3:
                    self.p(x, y, cor)

    def cheio(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.s.get_at((int(x), int(y))).a == 255

    def halo(self, cx, cy, raio, cor, alfa):
        """Brilho: so pinta onde ainda esta vazio (e nunca conta na colisao)."""
        for y in range(int(cy - raio), int(cy + raio) + 1):
            for x in range(int(cx - raio), int(cx + raio) + 1):
                d = math.hypot(x - cx, y - cy)
                if d <= raio and 0 <= x < self.w and 0 <= y < self.h and self.s.get_at((x, y)).a == 0:
                    self.s.set_at((x, y), (*cor, min(120, int(alfa * (1 - d / (raio + 0.5))))))

    def contorno(self, cor):
        """1 px escuro em volta do que e opaco (nao em volta do brilho)."""
        op = [[self.s.get_at((x, y)).a == 255 for x in range(self.w)] for y in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                if not op[y][x] and any(0 <= x + dx < self.w and 0 <= y + dy < self.h and op[y + dy][x + dx]
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.s.set_at((x, y), (*cor, 255))

    def sombrear(self, fn):
        """Troca a cor de cada pixel opaco por fn(x, y, cor)."""
        for y in range(self.h):
            for x in range(self.w):
                c = self.s.get_at((x, y))
                if c.a == 255:
                    self.s.set_at((x, y), (*fn(x, y, (c.r, c.g, c.b)), 255))


def mist(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def salvar(pasta, nome, quadros, escala=2):
    """Grava `quadros` (um C ou uma lista deles) como PNG; varios viram tira `_Nf`."""
    quadros = quadros if isinstance(quadros, list) else [quadros]
    w, h = quadros[0].w, quadros[0].h
    tira = pygame.Surface((w * len(quadros), h), pygame.SRCALPHA)
    for i, q in enumerate(quadros):
        tira.blit(q.s, (i * w, 0))
    if escala != 1:
        tira = pygame.transform.scale_by(tira, escala)
    sufixo = f"_{len(quadros)}f" if len(quadros) > 1 else ""
    caminho = os.path.join(OBJ, pasta, f"{nome}{sufixo}.png")
    # a peca pode ter mudado de parada para animada (ou o contrario)
    for velho in os.listdir(os.path.dirname(caminho)):
        base = velho[:-4]
        if velho.endswith(".png") and (base == nome or (base.startswith(nome + "_") and base.endswith("f")
                                                         and base[len(nome) + 1:-1].isdigit())):
            os.remove(os.path.join(os.path.dirname(caminho), velho))
    pygame.image.save(tira, caminho)
    print(f"  {pasta}/{nome}{sufixo}.png  {tira.get_width()}x{tira.get_height()}")


# ================================================================== PERIGOS
# Cada tipo novo e desenhado por UNIDADE (uma ponta), repetida 1, 2 ou 3 vezes
# no tile, com a ponta na mesma altura do caco original da fase: a colisao segue
# o desenho, e o robo de ferramentas/validar_fases.py confirma que continua justo.
L = 24      # um tile em pixels logicos


def pontas_da_base(fase, quantidade):
    """[(centro, topo)] de cada ponta do caco original da fase, em pixels logicos."""
    img = pygame.image.load(os.path.join(OBJ, "jogo", fase, f"caco{quantidade}.png")).convert_alpha()
    uw = 48 // quantidade
    saida = []
    for i in range(quantidade):
        melhor = (i * uw + uw // 2, 47)
        for x in range(i * uw, (i + 1) * uw):
            for y in range(48):
                if img.get_at((x, y)).a > 128:
                    if y < melhor[1]:
                        melhor = (x, y)
                    break
        saida.append((min(max(melhor[0] // 2, i * (L // quantidade) + 2), (i + 1) * (L // quantidade) - 3),
                      melhor[1] // 2 + 1))
    return saida


def molde(fase, quantidade):
    """
    Onde um perigo novo PODE ter tinta para caber, com contorno e tudo, dentro
    do que os desenhos ja validados da fase ocupam (caco, v2 e v3): a uniao das
    silhuetas deles, encolhida 1 px logico. Na cidadela, a 150 BPM, a folga do
    pulo e curta e um desenho mais largo que isso fere quem tocou na janela BOM.
    """
    dentro = [[False] * L for _ in range(L)]
    for v in ("", "v2", "v3"):
        img = pygame.image.load(os.path.join(OBJ, "jogo", fase, f"caco{quantidade}{v}.png")).convert_alpha()
        for x in range(48):
            for y in range(48):
                if img.get_at((x, y)).a > 128:
                    dentro[y // 2][x // 2] = True
    # so vale a coluna inteira dali para baixo (a colisao e por perfil)
    for x in range(L):
        topo = next((y for y in range(L) if dentro[y][x]), L)
        for y in range(L):
            dentro[y][x] = y > topo
    return [[dentro[y][x] and (x == 0 or dentro[y][x - 1]) and (x == L - 1 or dentro[y][x + 1])
             for x in range(L)] for y in range(L)]


def perigo(fase, variante, unidade, quadros=1, cont=(20, 12, 28), caber=False):
    for q in (1, 2, 3):
        pontas = pontas_da_base(fase, q)
        cabe = molde(fase, q) if caber else None
        tiras = []
        for k in range(quadros):
            c = C(L, L)
            for i, (cx, topo) in enumerate(pontas):
                unidade(c, cx, L // q, topo, k, i)
            if cabe:
                for y in range(L):
                    for x in range(L):
                        if not cabe[y][x]:
                            c.s.set_at((x, y), (0, 0, 0, 0))
            c.contorno(cont)
            tiras.append(c)
        # o brilho vem depois do contorno: fica por fora dele, solto no ar
        for k, c in enumerate(tiras):
            for i, (cx, topo) in enumerate(pontas):
                brilho = getattr(unidade, "brilho", None)
                if brilho:
                    brilho(c, cx, L // q, topo, k, i)
        salvar(f"jogo/{fase}", f"caco{q}v{variante}", tiras)


def _lasca(c, cx, topo, a, pe, escura, media, clara, luz, inclina=0):
    """Um cristal facetado: ponta em (cx, topo), meia largura `a`, ate o pe."""
    ombro = topo + max(2, a * 2)
    for y in range(int(topo), pe + 1):
        larg = a if y >= ombro else max(0, int(round(a * (y - topo) / max(1, ombro - topo))))
        desvio = int(round(inclina * (pe - y) / max(1, pe - topo)))
        for x in range(-larg, larg + 1):
            cor = escura if x < 0 else (media if x == 0 or x < larg else clara)
            if x == larg and larg > 0:
                cor = clara
            c.p(cx + x + desvio, y, cor)
        if y < topo + (pe - topo) * 0.55 and larg > 0:
            c.p(cx + desvio, y, luz)                         # a aresta acesa
    c.p(cx + int(round(inclina)), topo, luz)


def faz_cristal(pal, pedra):
    escura, media, clara, luz = pal

    def unidade(c, cx, uw, topo, k, i):
        h = L - topo
        a = {24: 4, 12: 2, 8: 1}[uw]
        if uw >= 12:
            lado = uw * 0.3
            _lasca(c, cx - lado, topo + h * 0.52, max(1, a - 2), 21, escura, media, clara, luz, -1 if uw == 24 else 0)
            _lasca(c, cx + lado, topo + h * 0.64, max(1, a - 2), 21, escura, media, clara, luz, 1 if uw == 24 else 0)
        _lasca(c, cx, topo, a, 21, escura, media, clara, luz)
        # o cascalho de onde ele brota
        m = min(uw // 2 - 1, a + (5 if uw == 24 else 2 if uw == 12 else 1))
        c.r(cx - m, 21, cx + m, 23, pedra[1])
        c.r(cx - m, 23, cx + m, 23, pedra[0])
        c.r(cx - m + 1, 20, cx + m - 1, 20, pedra[1]) if uw == 24 else None
        for x in range(int(cx - m), int(cx + m) + 1, 3):
            c.p(x, 21, pedra[2])
        # lasquinhas no cascalho
        if uw == 24:
            c.p(cx - 9, 20, clara); c.p(cx - 9, 19, luz); c.p(cx + 10, 20, media)
    return unidade


def faz_cogumelo(chapeu, pe_cor, pinta):
    """Cogumelo de ruido: chapeu de bruxa, pontudo -- no bosque so o perigo e pontudo."""
    escura, media, clara, luz = chapeu

    def um(c, cx, topo, raio, pe):
        aba = pe - max(3, int((pe - topo) * 0.36))
        for y in range(int(topo), aba + 1):
            t = (y - topo) / max(1, aba - topo)
            larg = int(round(raio * t ** 1.25))
            for x in range(-larg, larg + 1):
                cor = escura if x < -larg * 0.35 else (clara if x > larg * 0.45 else media)
                c.p(cx + x, y, cor)
        c.p(cx, topo, luz); c.p(cx, topo + 1, luz)
        c.r(cx - raio, aba + 1, cx + raio, aba + 1, escura)             # a aba, por baixo
        if raio >= 4:
            c.p(cx + raio * 0.35, topo + (aba - topo) * 0.6, pinta)
            c.p(cx - raio * 0.4, aba - 1, pinta); c.p(cx + raio * 0.6, aba - 1, pinta)
            c.p(cx - 1, topo + (aba - topo) * 0.38, pinta)
        g = 1 if raio >= 4 else 0
        c.r(cx - g, aba + 2, cx + g, pe, pe_cor[1])
        c.r(cx - g, aba + 2, cx - g, pe, pe_cor[0]) if g else None
        c.p(cx + g, aba + 3, pe_cor[2])

    def unidade(c, cx, uw, topo, k, i):
        raio = {24: 9, 12: 5, 8: 3}[uw]
        if uw == 24:
            um(c, cx - 8, 15, 3, 23)
            um(c, cx + 9, 17, 2, 23)
        um(c, cx, topo, raio, 23)
        if uw >= 12:
            c.r(cx - raio + 1, 23, cx + raio - 1, 23, (58, 94, 60))    # o musgo no pe
            c.p(cx - 2, 22, (92, 140, 70)); c.p(cx + 3, 22, (92, 140, 70))
    return unidade


def faz_pararaios(ferro, ponta, raio_cor):
    """Haste de ferro com a ponta em brasa; a faisca corre solta (4 quadros)."""
    def unidade(c, cx, uw, topo, k, i):
        abre = {24: 5, 12: 3, 8: 2}[uw]
        c.r(cx, topo + 4, cx, 23, ferro[1])
        for y in range(topo + 5, 22, 2):
            c.p(cx, y, ferro[2] if (y // 2) % 2 else ferro[1])
        for j in range(abre + 1):                                       # o tripe
            c.p(cx - j, 23 - (abre - j), ferro[0]); c.p(cx + j, 23 - (abre - j), ferro[1])
        c.r(cx - abre, 23, cx + abre, 23, ferro[0])
        if uw >= 12:
            c.r(cx - 2, topo + 9, cx + 2, topo + 9, ferro[1])           # os isoladores
            c.r(cx - 1, topo + 13, cx + 1, topo + 13, ferro[1])
            c.p(cx - 2, topo + 9, ferro[2]); c.p(cx + 2, topo + 9, ferro[2])
        if uw == 24:
            # sozinho no tile, ele e uma antena: travessa larga e duas pontas menores
            c.r(cx - 7, topo + 13, cx + 7, topo + 13, ferro[1])
            c.r(cx - 7, topo + 14, cx + 7, topo + 14, ferro[0])
            for lado in (-7, 7):
                c.r(cx + lado, topo + 8, cx + lado, topo + 13, ferro[1])
                c.p(cx + lado, topo + 5, ponta[2]); c.p(cx + lado, topo + 6, ponta[1])
                c.p(cx + lado, topo + 7, ponta[0])
            c.linha((cx - 6, 22), (cx - 3, topo + 15), ferro[0])
            c.linha((cx + 6, 22), (cx + 3, topo + 15), ferro[1])
        # a ponta: um losango em brasa
        c.p(cx, topo, ponta[2]); c.p(cx, topo + 1, ponta[2])
        c.r(cx - 1, topo + 2, cx + 1, topo + 3, ponta[1]); c.p(cx, topo + 2, ponta[2])
        c.p(cx, topo + 4, ponta[0]); c.p(cx - 1, topo + 3, ponta[0])

    def brilho(c, cx, uw, topo, k, i):
        f = (k + i) % 4
        c.halo(cx, topo + 2, 4.5 if f % 2 else 3.5, ponta[1], 110)
        zig = {1: ((-2, 1), (-3, 3), (-2, 5), (-3, 7)), 3: ((2, 0), (3, 2), (2, 4), (4, 6))}.get(f, ())
        for dx, dy in zig:
            if not c.cheio(cx + dx, topo + dy):
                c.s.set_at((int(cx + dx), int(topo + dy)), (*raio_cor, 255)) \
                    if 0 <= cx + dx < c.w and topo + dy >= 0 else None
    unidade.brilho = brilho
    return unidade


def faz_chama(fora, meio, dentro, ferro, ouro):
    """Lingua de fogo saindo de um braseiro de ferro (4 quadros, fora da batida)."""
    def unidade(c, cx, uw, topo, k, i):
        f = (k + i * 2) % 4
        gordo = {24: 6, 12: 3, 8: 2}[uw]
        base = 19
        puxa = (0, 1, 0, -1)[f]
        encolhe = (0, 1, 0, 1)[f] if k else 0
        t0 = topo + encolhe
        for y in range(int(t0), base + 1):
            t = (y - t0) / max(1, base - t0)
            # gota: estreita em cima, barriga a 70%, fecha no braseiro
            larg = gordo * (math.sin(min(1.0, t / 0.72) * math.pi / 2) ** 1.6) * (1.0 if t < 0.72 else 1.0 - (t - 0.72) * 0.9)
            balanco = puxa * (1.0 - t) * (1.5 if uw == 24 else 1.0)
            for x in range(-int(round(larg)), int(round(larg)) + 1):
                d = abs(x) / (larg + 0.01)
                cor = fora
                if d < 0.62 and t > 0.3:
                    cor = meio
                if d < 0.3 and t > 0.55:
                    cor = dentro
                c.p(cx + x + int(round(balanco)), y, cor)
        c.p(cx + int(round(puxa * 1.5)), t0, meio)
        if uw == 24:                                                    # as linguas de lado
            for lado, alto in ((-1, 10 + (f % 2)), (1, 12 - (f % 2))):
                for y in range(alto, base + 1):
                    c.p(cx + lado * (gordo + 1 - (y - alto) // 5), y, fora)
        # o braseiro
        m = min(uw // 2 - 1, gordo + 2)
        c.r(cx - m, 20, cx + m, 20, ouro)
        c.r(cx - m + 1, 21, cx + m - 1, 22, ferro[1])
        c.r(cx - m + 1, 21, cx - m + 1, 22, ferro[0])
        c.p(cx + m - 1, 21, ferro[2])
        c.r(cx - max(1, m - 2), 23, cx + max(1, m - 2), 23, ferro[0])

    def brilho(c, cx, uw, topo, k, i):
        c.halo(cx, 14, {24: 11, 12: 7, 8: 5}[uw], fora, 70)
    unidade.brilho = brilho
    return unidade


def faz_lancas(haste, ponta, ouro):
    """Lancas de ferro fincadas, com a ponta em brasa."""
    def lanca(c, x, topo, pe, inclina):
        for y in range(int(topo) + 5, pe + 1):
            dx = int(round(inclina * (y - topo) / max(1, pe - topo)))
            c.p(x - dx, y, haste[1] if y % 4 else haste[2])
        dx = 0
        c.p(x + dx, topo, ponta[2]); c.p(x + dx, topo + 1, ponta[2])
        c.r(x + dx - 1, topo + 2, x + dx + 1, topo + 3, ponta[1]); c.p(x + dx, topo + 2, ponta[2])
        c.p(x + dx, topo + 3, ponta[2])
        c.p(x + dx, topo + 4, ponta[0])
        c.r(x + dx - 1, topo + 5, x + dx + 1, topo + 5, ouro)

    def unidade(c, cx, uw, topo, k, i):
        topo += 2 if uw == 24 else 3          # a ponta larga precisa caber no molde
        if uw == 24:
            # um feixe: as de lado fincadas longe e inclinadas para dentro
            lanca(c, cx - 3, topo + 6, 22, -4)
            lanca(c, cx + 3, topo + 8, 22, 4)
            c.r(cx - 5, 18, cx + 5, 18, haste[1]); c.r(cx - 5, 19, cx + 5, 19, haste[0])   # a amarra
            c.p(cx - 5, 18, ouro); c.p(cx + 5, 18, ouro); c.p(cx, 18, ouro)
        elif uw == 12:
            c.r(cx - 3, 19, cx + 3, 19, haste[1]); c.p(cx - 3, 19, ouro); c.p(cx + 3, 19, ouro)
        lanca(c, cx, topo, 22, 0)
        m = {24: 9, 12: 4, 8: 2}[uw]
        c.r(cx - m, 22, cx + m, 23, haste[0])
        c.r(cx - m, 22, cx + m, 22, haste[1])

    def brilho(c, cx, uw, topo, k, i):
        c.halo(cx, topo + 5, 3.5, ponta[1], 90)
    unidade.brilho = brilho
    return unidade


def pintar_perigos():
    print("perigos de outros tipos:")
    # bosque: cristal de ruido rosa e cogumelo de chapeu pontudo
    rosa = ((150, 48, 104), (240, 110, 160), (248, 146, 190), (255, 214, 236))
    pedra_b = ((40, 52, 60), (62, 80, 84), (94, 114, 112))
    perigo("bosque", 4, faz_cristal(rosa, pedra_b), cont=(26, 18, 36))
    perigo("bosque", 5, faz_cogumelo(rosa, ((150, 150, 140), (214, 214, 196), (240, 240, 226)), (255, 236, 244)),
           cont=(26, 18, 36))
    # ilhas: cristal rubro com a aresta de gelo, e o para-raios
    rubro = ((176, 58, 84), (228, 96, 112), (255, 148, 140), (150, 226, 255))
    pedra_i = ((46, 33, 61), (86, 66, 106), (128, 100, 139))
    perigo("ilhas", 4, faz_cristal(rubro, pedra_i), cont=(58, 26, 58))
    perigo("ilhas", 5, faz_pararaios(((46, 33, 61), (98, 91, 130), (176, 180, 214)),
                                     ((176, 58, 84), (255, 106, 118), (255, 214, 214)), (212, 244, 255)),
           quadros=4, cont=(40, 22, 52))
    # eclipse: a chama do braseiro e as lancas em brasa
    perigo("eclipse", 4, faz_chama((255, 128, 96), (255, 190, 90), (255, 240, 180),
                                   ((14, 6, 20), (62, 32, 64), (150, 88, 116)), (255, 206, 120)),
           quadros=4, cont=(70, 22, 30), caber=True)
    perigo("eclipse", 5, faz_lancas(((30, 16, 44), (104, 58, 92), (150, 88, 116)),
                                    ((150, 52, 40), (255, 140, 60), (255, 236, 160)), (255, 206, 120)),
           cont=(14, 6, 20), caber=True)


# =================================================================== BLOCOS
def _moldura(c, escura, media, clara):
    c.r(0, 0, 23, 23, media)
    c.r(0, 0, 23, 0, clara); c.r(0, 0, 0, 23, clara)
    c.r(0, 23, 23, 23, escura); c.r(23, 0, 23, 23, escura)


def bloco_caixote(tabua, ferro, musgo=None):
    """Caixote de tabuas com cantoneiras de ferro e a travessa em X."""
    e, m, cl = tabua
    c = C(24, 24)
    _moldura(c, e, m, cl)
    for x in (6, 12, 18):
        c.r(x, 1, x, 22, e)
    for x, y in ((3, 5), (9, 14), (15, 8), (20, 17), (3, 18), (15, 19)):
        c.p(x, y, e); c.p(x, y + 1, e)                                  # os veios
    for i in range(3, 21):                                              # o X
        c.p(i, i, cl); c.p(i + 1, i, m); c.p(i, 23 - i, cl); c.p(i + 1, 23 - i, e)
    c.r(1, 1, 22, 2, m); c.r(1, 21, 22, 22, m); c.r(1, 1, 2, 22, m); c.r(21, 1, 22, 22, m)   # o quadro
    c.r(1, 3, 22, 3, e); c.r(3, 20, 20, 20, cl)
    for x0, y0 in ((0, 0), (20, 0), (0, 20), (20, 20)):                 # as cantoneiras
        c.r(x0, y0, x0 + 3, y0 + 3, ferro[1])
        c.p(x0 + 1, y0 + 1, ferro[2]); c.p(x0 + 2, y0 + 2, ferro[0])
    c.r(0, 23, 23, 23, ferro[0])
    if musgo:
        for x, n in ((1, 3), (4, 2), (7, 4), (11, 2), (14, 3), (18, 2), (21, 3)):
            c.r(x, 0, x + 1, 0, musgo[1]); c.r(x, 0, x, n - 2, musgo[0])
        c.r(0, 0, 23, 0, musgo[1]); c.p(3, 0, musgo[2]); c.p(12, 0, musgo[2]); c.p(19, 0, musgo[2])
    return c


def bloco_ecos(pedra, luz, luz_forte):
    """Pedra entalhada com os aneis de um eco: o som que virou marca na rocha."""
    e, m, cl = pedra
    c = C(24, 24)
    _moldura(c, e, m, cl)
    for x, y in ((3, 3), (19, 5), (5, 19), (17, 18), (10, 2), (2, 12), (21, 13)):
        c.p(x, y, e)
    for raio, cor in ((9, luz), (6, luz), (3, luz_forte)):
        for a in range(0, 360, 4):
            # aneis abertos em baixo a esquerda: um eco que vai sumindo
            if raio == 9 and 130 < a < 230:
                continue
            x = 11.5 + raio * math.cos(math.radians(a)); y = 11.5 + raio * math.sin(math.radians(a))
            c.p(x, y, cor)
    c.r(11, 11, 12, 12, luz_forte)
    c.r(1, 22, 22, 22, e)
    return c


def bloco_gelo(pal):
    """Bloco de cristal das ilhas: facetas claras e um nucleo de luz."""
    f, e, m, cl, br = pal
    c = C(24, 24)
    c.r(0, 0, 23, 23, m)
    c.poli([(0, 0), (23, 0), (16, 7), (7, 7)], cl)
    c.poli([(0, 0), (7, 7), (7, 16), (0, 23)], e)
    c.poli([(23, 0), (23, 23), (16, 16), (16, 7)], m)
    c.poli([(0, 23), (7, 16), (16, 16), (23, 23)], f)
    c.r(7, 7, 16, 16, e); c.r(8, 8, 15, 15, m)
    c.linha((8, 13), (13, 8), cl); c.linha((10, 15), (15, 10), cl)
    c.p(9, 9, br); c.p(10, 9, br); c.p(9, 10, br)
    c.r(0, 0, 23, 0, br); c.r(0, 0, 0, 23, cl); c.r(23, 1, 23, 23, f); c.r(0, 23, 23, 23, f)
    c.p(2, 2, br); c.p(20, 3, cl); c.p(3, 20, m)
    return c


def bloco_emblema(pedra, ouro, miolo, anel=None):
    """Pedra lavrada com um emblema: o sol das ilhas, ou o disco do eclipse."""
    e, m, cl = pedra
    c = C(24, 24)
    _moldura(c, e, m, cl)
    c.r(2, 2, 21, 21, e); c.r(3, 3, 21, 21, m); c.r(3, 3, 20, 20, mist(m, cl, 0.35))
    for x, y in ((4, 4), (19, 4), (4, 19), (19, 19)):                   # os cravos
        c.p(x, y, ouro[1]); c.p(x, y + 1, ouro[0])
    if anel:
        c.disco(11.5, 11.5, 6.6, anel)
        c.disco(11.5, 11.5, 5.2, ouro[1])
        c.disco(11, 11.5, 4.3, miolo)
        c.p(16, 8, ouro[2]); c.p(17, 9, ouro[2])
    else:
        for a in range(0, 360, 45):                                     # os raios
            for d in (7, 8):
                c.p(11.5 + d * math.cos(math.radians(a)), 11.5 + d * math.sin(math.radians(a)), ouro[1])
        c.disco(11.5, 11.5, 5.2, ouro[0])
        c.disco(11.5, 11.5, 4.2, ouro[1])
        c.disco(12.2, 10.8, 2.4, miolo)
    return c


def pintar_blocos():
    print("blocos variados:")
    musgo = ((58, 94, 60), (76, 168, 116), (140, 214, 150))
    salvar("jogo/bosque", "bloco_v2", bloco_caixote(((52, 40, 38), (96, 74, 58), (134, 106, 78)),
                                                     ((30, 46, 48), (66, 92, 86), (124, 150, 138)), musgo))
    salvar("jogo/bosque", "bloco_v3", bloco_ecos(((30, 46, 48), (58, 84, 82), (95, 122, 111)),
                                                 (76, 168, 116), (150, 255, 200)))
    salvar("jogo/ilhas", "bloco_v2", bloco_gelo(((58, 84, 150), (90, 146, 200), (148, 219, 250),
                                                 (212, 244, 255), (255, 255, 255))))
    salvar("jogo/ilhas", "bloco_v3", bloco_emblema(((45, 44, 85), (86, 82, 125), (130, 125, 170)),
                                                   ((165, 110, 70), (255, 200, 130), (255, 236, 200)),
                                                   (255, 240, 210)))
    salvar("jogo/eclipse", "bloco_v2", bloco_caixote(((24, 12, 40), (58, 36, 92), (96, 76, 130)),
                                                      ((120, 80, 50), (255, 206, 120), (255, 240, 190))))
    salvar("jogo/eclipse", "bloco_v3", bloco_emblema(((30, 16, 50), (58, 36, 76), (96, 76, 130)),
                                                     ((176, 116, 70), (255, 206, 120), (255, 240, 190)),
                                                     (12, 6, 20), anel=(176, 116, 70)))


# ================================================================= ENFEITES
MAD_E, MAD, MAD_L = (52, 40, 38), (84, 64, 52), (122, 96, 70)
CONT_B = (18, 26, 30)
PED_E, PED, PED_L = (42, 60, 58), (66, 86, 82), (94, 114, 106)
LUZ, LUZ_F = (255, 226, 170), (255, 246, 214)
MINT, MINT_L = (110, 220, 170), (190, 255, 226)


def lanterna_de_pedra(k):
    """Bosque: a lanterna de pedra dos caminhos antigos, com musgo e a luz tremendo."""
    c = C(22, 34)
    c.r(6, 31, 15, 33, PED); c.r(6, 31, 15, 31, PED_L); c.r(6, 33, 15, 33, PED_E)      # a base
    c.r(8, 29, 13, 30, PED); c.r(8, 29, 13, 29, PED_L)
    c.r(9, 19, 12, 28, PED); c.r(9, 19, 9, 28, PED_E); c.r(12, 19, 12, 28, PED_L)      # o fuste
    c.p(10, 23, PED_E); c.p(11, 26, PED_E)
    c.r(6, 17, 15, 18, PED); c.r(6, 17, 15, 17, PED_L)                                 # a mesa
    c.r(7, 10, 14, 16, PED); c.r(7, 10, 7, 16, PED_E)                                  # a caixa da luz
    c.r(9, 11, 12, 15, LUZ); c.r(10, 12 + (k % 2), 11, 14, LUZ_F)
    c.r(10, 11, 10, 15, PED_E) if k == 1 else None                                     # a grade
    c.r(4, 8, 17, 9, PED); c.r(4, 8, 17, 8, PED_L); c.r(4, 9, 17, 9, PED_E)            # o telhado, largo
    c.r(6, 6, 15, 7, PED); c.r(7, 5, 14, 5, PED_L)
    c.r(9, 3, 12, 4, PED); c.r(10, 2, 11, 2, PED_L)                                    # a bola de cima
    for x, y in ((5, 8), (6, 7), (7, 5), (8, 5), (16, 8), (6, 31), (7, 31), (14, 30)):
        c.p(x, y, (92, 140, 70))
    c.p(5, 9, (58, 94, 60)); c.p(5, 10, (58, 94, 60)); c.p(8, 6, (58, 94, 60))
    c.contorno(CONT_B)
    c.halo(10.5, 13, 8 + (0.7 if k else 0), LUZ, 96 if k else 80)
    return c


def cerca():
    """Bosque: um lance de cerca velha, torta, com musgo."""
    c = C(30, 16)
    for x, topo in ((3, 3), (14, 2), (25, 4)):
        c.r(x, topo, x + 2, 15, MAD); c.r(x, topo, x, 15, MAD_E); c.r(x + 2, topo + 1, x + 2, 15, MAD_L)
        c.r(x, topo, x + 2, topo, MAD_L)
    for y, d in ((6, 0), (11, 1)):
        for x in range(1, 29):
            yy = y + d * (1 if x > 16 else 0) + (1 if x > 24 else 0)
            c.p(x, yy, MAD_L); c.p(x, yy + 1, MAD)
    c.p(8, 6, MAD_E); c.p(20, 12, MAD_E); c.p(9, 11, MAD_E)
    for x in (3, 4, 14, 26):
        c.p(x, 15, (58, 94, 60))
    c.r(13, 2, 15, 2, (92, 140, 70)); c.p(4, 3, (92, 140, 70)); c.p(27, 4, (92, 140, 70))
    c.r(18, 13, 19, 13, (92, 140, 70))
    c.contorno(CONT_B)
    return c


def cogumelos_de_luz(k):
    """Bosque: os cogumelos que brilham, redondos e grandes (os do perigo sao pontudos e rosa)."""
    c = C(26, 20)
    for cx, topo, raio in ((7, 9, 4), (16, 3, 6), (22, 12, 3)):
        c.r(cx - 1, topo + 2, cx, 19, (196, 206, 196)); c.r(cx - 1, topo + 2, cx - 1, 19, (140, 156, 150))
        for dy in range(0, raio // 2 + 2):
            larg = raio - (0 if dy else 1) if dy < raio // 2 + 1 else raio - 1
            larg = int(round(raio * math.sin(math.pi / 2 * min(1.0, (dy + 1) / (raio / 2 + 1)))))
            c.r(cx - larg, topo + dy, cx + larg - 1, topo + dy, MINT)
        c.r(cx - raio, topo + raio // 2 + 2, cx + raio - 1, topo + raio // 2 + 2, mist(MINT, (20, 40, 40), 0.45))
        c.p(cx - raio // 2, topo + 1, MINT_L); c.p(cx - raio // 2 + 1, topo + 1, MINT_L)
        if raio > 4:
            c.p(cx + 2, topo + 2, MINT_L); c.p(cx - 3, topo + 3, (255, 255, 255) if k else MINT_L)
    c.r(3, 19, 24, 19, (58, 94, 60)); c.p(5, 18, (92, 140, 70)); c.p(12, 18, (92, 140, 70)); c.p(20, 18, (92, 140, 70))
    c.contorno(CONT_B)
    for cx, topo, raio in ((7, 9, 4), (16, 3, 6), (22, 12, 3)):
        c.halo(cx, topo + 2, raio + 3 + (1 if k else 0), (150, 255, 200), 80 if k else 60)
    return c


CR_F, CR_E, CR, CR_L, CR_B = (58, 84, 150), (90, 146, 200), (148, 219, 250), (212, 244, 255), (255, 255, 255)
RO_F, RO_E, RO, RO_L, RO_T = (46, 33, 61), (69, 50, 87), (86, 66, 106), (105, 79, 120), (128, 100, 139)
CONT_I = (40, 26, 52)
OURO_E, OURO, OURO_L = (176, 116, 70), (255, 200, 130), (255, 236, 200)


def catavento(k):
    """Ilhas: um catavento de papel girando no vento do por do sol."""
    c = C(22, 38)
    c.r(10, 12, 11, 35, RO_L); c.r(10, 12, 10, 35, RO_E)
    c.r(7, 36, 14, 37, RO); c.r(8, 35, 13, 35, RO_T); c.r(7, 37, 14, 37, RO_E)
    cx, cy = 10.5, 9.5
    for j in range(4):
        a = math.radians(j * 90 + k * 22.5)
        ponta = (cx + 9 * math.cos(a), cy + 9 * math.sin(a))
        lado = (cx + 5.5 * math.cos(a + 0.9), cy + 5.5 * math.sin(a + 0.9))
        c.poli([(cx, cy), ponta, lado], OURO if j % 2 == 0 else CR)
        c.linha((cx, cy), ponta, OURO_L if j % 2 == 0 else CR_L)
    c.disco(cx, cy, 1.2, CR_B)
    c.contorno(CONT_I)
    return c


def balao(k):
    """Ilhas: uma lanterna de papel presa por um fio, subindo e descendo no ar."""
    c = C(18, 44)
    sobe = (0, 1, 2, 1)[k]
    y0 = 3 + sobe
    c.r(5, 40, 12, 43, RO); c.r(6, 39, 11, 39, RO_T); c.r(5, 43, 12, 43, RO_E)        # a pedra que segura
    for y in range(y0 + 15, 40):                                                       # o fio
        c.p(8.5 + math.sin((y + k * 2) * 0.5) * 0.8, y, (128, 100, 139, 255))
    for dy in range(13):                                                               # o balao
        larg = int(round(5.4 * math.sin(math.pi * (dy + 0.8) / 14.2) ** 0.7))
        for x in range(-larg, larg + 1):
            cor = OURO if x > -larg * 0.3 else (228, 150, 100)
            if x > larg * 0.4 and dy < 7:
                cor = OURO_L
            c.p(8.5 + x + 0.5, y0 + dy, cor)
    c.r(7, y0, 10, y0, OURO_E); c.r(7, y0 + 12, 10, y0 + 13, OURO_E)
    for x in (6, 9, 12):
        c.r(x, y0 + 2, x, y0 + 10, (228, 150, 100))                                    # as varetas
    c.r(8, y0 + 5, 9, y0 + 8, (255, 250, 230))                                         # a vela
    c.contorno(CONT_I)
    c.halo(8.5, y0 + 6, 9, (255, 220, 150), 100)
    return c


def arvore_do_ceu():
    """Ilhas: arvore baixa de copa azul-gelo, tronco torto de pedra-roxa."""
    c = C(34, 36)
    for y in range(18, 36):
        x = 16 + int(round(math.sin((y - 18) * 0.35) * 1.5))
        c.r(x - 1, y, x + 1, y, RO); c.p(x - 1, y, RO_E); c.p(x + 1, y, RO_T)
    c.linha((16, 24), (10, 18), RO); c.linha((17, 22), (23, 16), RO_L)
    c.r(13, 35, 20, 35, RO_E)
    bolas = ((16, 10, 8), (8, 14, 6), (25, 13, 6), (12, 6, 5), (21, 5, 5))
    for x, y, r in bolas:
        c.disco(x, y, r, CR_F)
    for x, y, r in bolas:
        c.disco(x + 1, y - 1, r - 1.5, CR_E)
    for x, y, r in bolas:
        c.disco(x + r * 0.35, y - r * 0.35, r * 0.5, CR)
        c.p(x + r * 0.4, y - r * 0.6, CR_L); c.p(x + r * 0.4 + 1, y - r * 0.6, CR_L)
    for x, y in ((6, 22), (27, 24), (13, 26)):                                         # folhas caindo
        c.p(x, y, CR)
    c.contorno(CONT_I)
    return c


FE_F, FE_E, FE, FE_L = (12, 6, 20), (30, 20, 46), (58, 42, 84), (96, 76, 130)
LAV, LAV_L, ROXO_V = (206, 168, 255), (248, 238, 255), (140, 92, 224)
BRZ_E, BRZ, BRZ_L = (120, 80, 50), (176, 116, 70), (255, 206, 120)
CONT_E = (12, 6, 20)


def gaiola(k):
    """Cidadela: lanterna de gaiola pendurada num gancho de ferro, com a chama lavanda."""
    c = C(22, 42)
    c.r(5, 6, 6, 39, FE); c.r(5, 6, 5, 39, FE_E); c.r(6, 12, 6, 39, FE_L)
    c.r(3, 40, 8, 41, FE); c.r(3, 41, 8, 41, FE_E); c.r(4, 39, 7, 39, FE_L)
    c.r(5, 4, 15, 5, FE); c.r(5, 4, 15, 4, FE_L); c.p(7, 6, FE_E); c.p(8, 7, FE_E)     # o braco
    c.p(16, 5, FE); c.p(16, 6, FE)
    c.r(15, 7, 15, 9, FE_E)                                                            # a corrente
    c.r(12, 10, 18, 10, BRZ); c.r(13, 9, 17, 9, BRZ_L)
    c.r(12, 18, 18, 19, BRZ); c.r(12, 19, 18, 19, BRZ_E)
    for x in (12, 15, 18):
        c.r(x, 11, x, 17, FE_E)
    c.r(13, 11, 14, 17, ROXO_V); c.r(16, 11, 17, 17, ROXO_V)
    c.r(13, 13 - (k % 2), 14, 17, LAV); c.r(16, 13 + (k % 2), 17, 17, LAV)
    c.p(14, 15, LAV_L); c.p(16, 16, LAV_L)
    c.contorno(CONT_E)
    c.halo(15, 14, 8 + (0.8 if k else 0), LAV, 96 if k else 76)
    return c


def sino():
    """Cidadela: o sino de bronze da muralha, no seu cavalete."""
    c = C(32, 36)
    for x in (4, 25):
        c.r(x, 6, x + 2, 33, FE); c.r(x, 6, x, 33, FE_E); c.r(x + 2, 8, x + 2, 33, FE_L)
        c.r(x - 1, 34, x + 3, 35, FE); c.r(x - 1, 35, x + 3, 35, FE_E)
    c.r(2, 3, 29, 5, FE); c.r(2, 3, 29, 3, FE_L); c.r(2, 5, 29, 5, FE_E)
    c.p(7, 7, FE_E); c.p(8, 6, FE_E); c.p(24, 7, FE_E); c.p(23, 6, FE_E)
    c.r(15, 6, 16, 8, FE_E)
    for dy in range(15):                                                               # o sino
        larg = 4 + dy * 0.28 + (2.2 if dy > 11 else 0)
        for x in range(-int(larg), int(larg) + 1):
            cor = BRZ_E if x < -larg * 0.4 else (BRZ_L if x > larg * 0.35 else BRZ)
            c.p(15.5 + x + 0.5, 9 + dy, cor)
    c.r(9, 23, 22, 23, BRZ_E); c.r(11, 15, 20, 15, BRZ_E); c.r(11, 20, 20, 20, BRZ_E)
    c.r(14, 9, 17, 9, BRZ_L)
    c.r(15, 24, 16, 26, BRZ_E); c.p(15, 27, BRZ); c.p(16, 27, BRZ)                     # o badalo
    c.contorno(CONT_E)
    return c


def vitral(k):
    """Cidadela: um arco de janela que sobrou de pe, com o vitral ainda aceso."""
    c = C(30, 44)
    def arco(x0, x1, topo, cor):
        meio, raio = (x0 + x1) / 2, (x1 - x0) / 2
        for x in range(x0, x1 + 1):
            sobe = topo + raio - math.sqrt(max(0.0, raio * raio - (x - meio) ** 2))
            c.r(x, sobe, x, 41, cor)
    arco(3, 26, 3, FE)
    for y in range(8, 42, 5):                                                          # as pedras do arco
        c.r(3, y, 7, y, FE_E); c.r(22, y, 26, y, FE_E)
    c.r(3, 14, 3, 41, FE_E); c.r(26, 14, 26, 41, FE_L)
    arco(8, 21, 8, FE_F)
    vidro = (ROXO_V, (96, 154, 227), LAV, (255, 206, 120))
    for x in range(9, 21):
        for y in range(10, 38):
            if c.s.get_at((x, y))[:3] == FE_F and not (x in (14, 15)) and y % 7 != 2:
                cor = vidro[((x > 14) + (y // 7)) % 4]
                c.p(x, y, mist(cor, (255, 255, 255), 0.25) if k and (x + y) % 5 == 0 else cor)
    c.r(8, 38, 21, 41, FE); c.r(8, 38, 21, 38, FE_L)                                   # o peitoril
    c.r(1, 42, 28, 43, FE); c.r(1, 42, 28, 42, FE_L); c.r(1, 43, 28, 43, FE_E)
    c.p(5, 5, FE_L); c.p(6, 4, FE_L); c.p(23, 4, FE_E)
    c.contorno(CONT_E)
    c.halo(14.5, 22, 15, ROXO_V, 50 + 20 * k)
    return c


def pintar_enfeites():
    print("enfeites de mapa:")
    salvar("jogo/bosque", "enfeite_6", [lanterna_de_pedra(k) for k in range(2)])
    salvar("jogo/bosque", "enfeite_7", cerca())
    salvar("jogo/bosque", "enfeite_8", [cogumelos_de_luz(k) for k in range(2)])
    salvar("jogo/ilhas", "enfeite_4", [catavento(k) for k in range(4)])
    salvar("jogo/ilhas", "enfeite_5", [balao(k) for k in range(4)])
    salvar("jogo/ilhas", "enfeite_6", arvore_do_ceu())
    salvar("jogo/eclipse", "enfeite_5", [gaiola(k) for k in range(2)])
    salvar("jogo/eclipse", "enfeite_6", sino())
    salvar("jogo/eclipse", "enfeite_7", [vitral(k) for k in range(2)])


# ================================================================= PAISAGEM
# Na escala do fundo (1 px aqui = 4 px na tela), ja nas cores enevoadas da camada.
def arvore_seca():
    """Bosque, perto: uma arvore velha sem folhas, com uma coruja no galho."""
    e, m, l = (12, 30, 32), (22, 46, 49), (40, 72, 74)
    c = C(34, 44)
    for y in range(14, 44):
        larg = 2 if y < 34 else 2 + (y - 34) // 3
        x = 16 + int(round(math.sin(y * 0.22) * 1.2))
        c.r(x - larg, y, x + larg, y, m); c.p(x - larg, y, e); c.p(x + larg, y, l)
    galhos = (((16, 22), (6, 12)), ((6, 12), (2, 11)), ((6, 12), (5, 5)), ((17, 18), (27, 9)),
              ((27, 9), (32, 8)), ((27, 9), (26, 3)), ((16, 15), (14, 4)), ((14, 4), (10, 1)),
              ((14, 6), (18, 1)), ((17, 26), (25, 20)), ((25, 20), (30, 19)), ((10, 16), (4, 18)))
    for a, b in galhos:
        c.linha(a, b, m)
    for a, b in galhos[:6]:
        c.linha((a[0] + 1, a[1]), (b[0] + 1, b[1]), l) if abs(a[0] - b[0]) > 4 else None
    c.r(21, 12, 23, 15, (45, 84, 88)); c.p(21, 11, (45, 84, 88)); c.p(23, 11, (45, 84, 88))   # a coruja
    c.p(21, 13, (214, 214, 150)); c.p(23, 13, (214, 214, 150))
    c.r(12, 43, 21, 43, e)
    return c


def torre_caida():
    """Bosque, perto: o que sobrou de uma torre de vigia, tomada pela hera, com uma luz acesa."""
    e, m, l, ll = (18, 44, 46), (31, 65, 70), (45, 84, 88), (59, 101, 104)
    c = C(24, 40)
    perfil = (9, 9, 8, 6, 6, 5, 3, 3, 4, 5, 5, 2, 2, 0, 0, 1, 3, 3)
    for i, topo in enumerate(perfil):
        c.r(3 + i, topo, 3 + i, 39, m)
    for y in range(2, 40, 4):
        for x in range(3 + (2 if (y // 4) % 2 else 0), 21, 5):
            if c.cheio(x, y):
                c.p(x, y, e); c.p(x + 1, y, e)
    c.r(3, 9, 3, 39, e); c.r(4, 9, 4, 39, e)
    c.r(20, 4, 20, 39, ll); c.r(19, 6, 19, 39, l)
    for i, topo in enumerate(perfil):
        c.p(3 + i, topo, ll)
    c.r(10, 14, 12, 18, (12, 30, 32)); c.p(11, 13, (12, 30, 32))                       # a janela
    c.r(10, 16, 12, 18, (190, 170, 104)); c.p(11, 15, (190, 170, 104)); c.p(11, 17, (236, 220, 150))
    c.r(9, 30, 13, 39, (12, 30, 32)); c.r(10, 28, 12, 29, (12, 30, 32))                # a porta
    hera = ((38, 78, 62), (60, 104, 76))
    for x, y0, y1 in ((4, 10, 26), (5, 12, 20), (6, 9, 15), (17, 3, 14), (18, 4, 22), (16, 2, 8), (7, 30, 38)):
        for y in range(y0, y1):
            c.p(x + (y % 3 == 0), y, hera[(x + y) % 2])
    c.r(0, 37, 3, 39, m); c.r(1, 36, 2, 36, l); c.r(21, 38, 23, 39, m); c.p(22, 37, l)   # as pedras caidas
    return c


def pinheiro_longe():
    """Bosque, longe: so a silhueta de um pinheiro."""
    e, m, l = (14, 32, 36), (21, 47, 51), (32, 63, 67)
    c = C(15, 28)
    for andar, (y0, larg) in enumerate(((2, 3), (7, 5), (13, 6), (19, 7))):
        for dy in range(7):
            w = int(round(larg * (dy + 1) / 7))
            c.r(7 - w, y0 + dy, 7 + w, y0 + dy, e if dy == 6 else m)
            c.p(7 + w, y0 + dy, l)
    c.r(7, 0, 7, 2, m); c.r(6, 26, 8, 27, e)
    return c


def ilha_do_templo():
    """Ilhas, perto: uma ilha com um templo de cupula, uma arvore e uma cascata."""
    f, e, m, l, t, tt = (42, 28, 58), (60, 42, 80), (67, 48, 86), (86, 64, 107), (115, 88, 130), (138, 108, 156)
    gelo, gelo_l = (176, 212, 238), (214, 236, 250)
    c = C(56, 46)
    topo = 22
    for y in range(topo, 46):
        t_ = (y - topo) / 23.0
        meia = 26 * (1.0 - t_ ** 1.6) + math.sin(y * 1.3) * 1.2
        if meia < 1:
            break
        desvio = math.sin(y * 0.45) * 1.5
        cor = (l, m, m, e, e, f)[min(5, int(t_ * 6.5))]
        c.r(28 - meia + desvio, y, 28 + meia + desvio, y, cor)
        c.p(28 + meia + desvio, y, t if t_ < 0.5 else m)
    for x, y, w in ((8, 26, 7), (30, 28, 9), (16, 32, 8), (36, 34, 6), (22, 38, 6)):   # as camadas da rocha
        c.r(x, y, x + w, y, f)
    c.r(3, topo, 53, topo, gelo); c.r(5, topo - 1, 51, topo - 1, t); c.r(4, topo + 1, 52, topo + 1, tt)
    c.r(3, topo, 6, topo, gelo_l); c.r(40, topo, 46, topo, gelo_l)
    # o templo
    c.r(22, 20, 40, 21, tt); c.r(22, 20, 40, 20, gelo)
    for x in (24, 28, 34, 38):
        c.r(x, 11, x, 19, tt); c.p(x, 11, gelo)
    c.r(29, 12, 33, 19, e); c.r(30, 13, 32, 19, (224, 160, 128))                       # a luz de dentro
    c.r(22, 9, 40, 10, t); c.r(22, 9, 40, 9, tt)
    for dy, w in enumerate((2, 4, 6, 7, 8)):
        c.r(31 - w, 4 + dy, 31 + w, 4 + dy, t)
        c.p(31 + w, 4 + dy, tt); c.p(31 + w - 1, 4 + dy, tt)
    c.r(31, 1, 31, 3, gelo); c.p(31, 0, gelo_l)
    # a arvore
    c.r(11, 14, 12, 21, e)
    for x, y, r in ((11, 10, 5), (7, 13, 3), (15, 12, 3)):
        c.disco(x, y, r, l)
    for x, y, r in ((12, 9, 3), (8, 12, 1.5), (16, 11, 1.5)):
        c.disco(x, y, r, t)
    c.p(13, 7, tt); c.p(14, 8, tt)
    # a cascata, da borda ate sumir no ar
    for y in range(topo, 44):
        c.p(46, y, gelo if y % 3 else gelo_l); c.p(47, y, gelo_l if y < 36 else gelo)
    c.p(45, 44, gelo); c.p(48, 44, gelo); c.p(46, 45, gelo_l)
    return c


def ilha_do_arco():
    """Ilhas, longe: uma ilha pequena com um arco de pedra natural."""
    f, e, m, l = (30, 20, 40), (44, 32, 54), (62, 47, 72), (85, 65, 97)
    c = C(30, 24)
    for y in range(10, 24):
        t_ = (y - 10) / 14.0
        meia = 14 * (1.0 - t_ ** 1.4)
        if meia < 1:
            break
        c.r(15 - meia, y, 15 + meia, y, (m, e, e, f)[min(3, int(t_ * 4))])
    c.r(1, 10, 28, 10, l)
    for x in range(8, 23):                                                             # o arco
        alto = 9 - math.sqrt(max(0.0, 49 - (x - 15) ** 2))
        c.r(x, alto, x, 9, m); c.p(x, alto, l)
    for x in range(11, 20):
        alto = 9 - math.sqrt(max(0.0, 16 - (x - 15) ** 2))
        for y in range(int(alto) + 1, 10):
            c.s.set_at((x, y), (0, 0, 0, 0))
    return c


def catedral():
    """Cidadela, perto: a catedral, com a rosacea acesa e a torre do sino."""
    f, e, m, l, t, tt = (16, 6, 39), (22, 7, 45), (38, 20, 60), (50, 30, 75), (78, 43, 104), (105, 70, 134)
    luz, luz_l = (190, 120, 80), (255, 190, 110)
    c = C(44, 48)

    def parede(x0, y0, x1, y1):
        c.r(x0, y0, x1, y1, m)
        for y in range(y0 + 1, y1, 3):
            c.r(x0, y, x1, y, e)
            for x in range(x0 + (2 if (y // 3) % 2 else 0), x1, 5):
                c.p(x, y + 1, e)
        c.r(x1, y0, x1, y1, l); c.r(x0, y0, x0, y1, f)
    parede(12, 22, 34, 47)                                                             # a nave
    for i in range(12):                                                                # o frontao
        c.r(23 - i, 10 + i, 23 + i, 10 + i, m if i % 3 else e)
        c.p(23 + i, 10 + i, t); c.p(23 - i, 10 + i, l)
    c.p(23, 8, tt); c.p(23, 9, tt); c.p(22, 9, tt); c.p(24, 9, tt)
    c.disco(23, 26, 4.4, f); c.disco(23, 26, 3.4, luz)                                 # a rosacea
    c.p(23, 26, luz_l); c.r(23, 23, 23, 29, f); c.r(20, 26, 26, 26, f); c.p(23, 26, luz_l)
    c.r(20, 38, 26, 47, f); c.r(21, 36, 25, 37, f); c.r(22, 35, 24, 35, f)             # o portal
    c.r(22, 40, 24, 47, e)
    for x in (15, 31):
        c.r(x, 34, x + 1, 39, f); c.p(x, 36, luz)
    parede(0, 8, 10, 47)                                                               # a torre do sino
    for x in (0, 3, 6, 9):
        c.r(x, 5, x + 1, 7, m); c.p(x + 1, 5, l)
    c.r(0, 8, 10, 8, t)
    c.r(3, 12, 7, 18, f); c.r(4, 11, 6, 11, f); c.r(4, 14, 6, 17, (176, 116, 70)); c.p(5, 18, (120, 80, 50))
    c.r(4, 26, 5, 29, f); c.p(4, 27, luz); c.r(4, 36, 5, 39, f)
    parede(35, 26, 43, 47)                                                             # a capela ao lado
    c.r(35, 25, 43, 25, t)
    for x in (35, 38, 41):
        c.r(x, 23, x + 1, 24, m)
    c.r(38, 32, 40, 37, f); c.p(39, 34, luz_l); c.p(39, 35, luz)
    c.r(12, 22, 34, 22, t)
    return c


def torre_do_passadico():
    """Cidadela, longe: uma torre fina com um passadico saindo dela."""
    f, e, m, l = (24, 12, 40), (31, 16, 50), (41, 28, 57), (65, 45, 71)
    luz = (153, 120, 83)
    c = C(22, 32)
    c.r(3, 6, 10, 31, m); c.r(3, 6, 3, 31, f); c.r(10, 6, 10, 31, l)
    for y in range(8, 31, 3):
        c.r(4, y, 9, y, e)
    c.r(2, 3, 11, 5, m); c.r(2, 3, 11, 3, l)
    for x in (2, 5, 8, 11):
        c.r(x, 1, x, 2, m)
    c.p(6, 10, luz); c.p(6, 11, luz); c.p(8, 20, luz); c.p(5, 25, luz)
    c.r(11, 14, 21, 15, m); c.r(11, 14, 21, 14, l)                                     # o passadico
    for x in (13, 16, 19):
        c.r(x, 12, x, 13, m)
    for x in range(11, 22):
        sobe = 16 + int(round(3 - 3 * abs(math.sin((x - 11) / 11 * math.pi))))
        c.r(x, 16, x, sobe, e) if x % 5 else c.r(x, 16, x, 31, e)
    return c


def baleia(k):
    """Ilhas: a baleia do ceu, la longe -- na cor da nevoa, quase uma sombra."""
    e, m, l, v = (92, 58, 92), (110, 70, 104), (132, 88, 118), (160, 112, 132)
    c = C(46, 20)
    for x in range(4, 34):                                                             # o corpo
        t_ = (x - 4) / 30.0
        topo = 9 - 4.5 * math.sin(math.pi * min(1.0, t_ * 1.15)) ** 0.8
        baixo = 10 + 3.6 * math.sin(math.pi * min(1.0, t_ * 1.25)) ** 0.9
        for y in range(int(round(topo)), int(round(baixo)) + 1):
            c.p(x, y, m if y < 10 else v if (y + x) % 3 else l)
        c.p(x, int(round(topo)), l)
    for x in range(33, 41):                                                            # o rabo afina
        c.r(x, 9 - (40 - x) // 4, x, 10 + (40 - x) // 5, m)
    sobe = -2 if k else 0
    for i in range(5):                                                                 # a cauda bate
        c.p(40 + i, 8 + sobe * i // 4 - i // 2, m); c.p(40 + i, 9 + sobe * i // 4 - i // 2, m)
        c.p(40 + i, 10 + sobe * i // 4 + i // 2, m); c.p(40 + i, 9 + sobe * i // 4 + i // 2, e)
    c.r(14, 13, 15, 14 + (1 if k else 2), e); c.r(16, 13, 17, 15 if k else 16, e)       # a nadadeira
    c.p(8, 9, e)                                                                       # o olho
    c.r(5, 11, 12, 11, e)                                                              # a boca
    for x in (12, 16, 20, 24):
        c.p(x, 12, l)
    c.p(20, 2 - (1 if k else 0), l); c.p(19, 3, l); c.p(21, 3, l)                        # o esguicho
    return c


def pintar_paisagem():
    print("paisagem:")
    salvar("cenario/bosque", "perto_5", arvore_seca(), 1)
    salvar("cenario/bosque", "perto_6", torre_caida(), 1)
    salvar("cenario/bosque", "longe_5", pinheiro_longe(), 1)
    salvar("cenario/ilhas", "perto_4", ilha_do_templo(), 1)
    salvar("cenario/ilhas", "longe_5", ilha_do_arco(), 1)
    salvar("cenario/ilhas", "baleia", [baleia(k) for k in range(2)], 1)
    salvar("cenario/eclipse", "perto_4", catedral(), 1)
    salvar("cenario/eclipse", "longe_5", torre_do_passadico(), 1)


def main():
    pygame.init()
    pygame.display.set_mode((8, 8))
    pintar_perigos()
    pintar_blocos()
    pintar_enfeites()
    pintar_paisagem()


if __name__ == "__main__":
    main()
