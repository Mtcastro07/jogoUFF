"""Pinta os enfeites de mapa (props sem colisao) de cada mundo.
Desenhados em pixels logicos e ampliados 2x (o mesmo "pixel" do chao do bosque)."""
import os, shutil
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init(); pygame.display.set_mode((8, 8))
J = "/home/matheus/Documentos/jogoUFF/assets/art/objetos/jogo/"
BRUTO = "/home/matheus/Documentos/jogoUFF/assets/art/objetos 2/cenario/"


class C:
    def __init__(self, w, h):
        self.s = pygame.Surface((w, h), pygame.SRCALPHA)
        self.w, self.h = w, h

    def r(self, x0, y0, x1, y1, cor):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.p(x, y, cor)

    def p(self, x, y, cor):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.s.set_at((x, y), cor if len(cor) == 4 else (*cor, 255))

    def halo(self, cx, cy, raio, cor, alfa):
        """Brilho: so pinta onde ainda esta vazio."""
        for y in range(int(cy - raio), int(cy + raio) + 1):
            for x in range(int(cx - raio), int(cx + raio) + 1):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if d <= raio and 0 <= x < self.w and 0 <= y < self.h and self.s.get_at((x, y)).a == 0:
                    self.s.set_at((x, y), (*cor, int(alfa * (1 - d / (raio + 0.5)))))

    def contorno(self, cor):
        """1 px escuro em volta do que e opaco (nao em volta do brilho)."""
        op = [[self.s.get_at((x, y)).a == 255 for x in range(self.w)] for y in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                if not op[y][x] and any(0 <= x + dx < self.w and 0 <= y + dy < self.h and op[y + dy][x + dx]
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.s.set_at((x, y), (*cor, 255))


def salvar(fase, nome, quadros):
    w, h = quadros[0].w, quadros[0].h
    tira = pygame.Surface((w * len(quadros), h), pygame.SRCALPHA)
    for i, q in enumerate(quadros):
        tira.blit(q.s, (i * w, 0))
    tira = pygame.transform.scale_by(tira, 2)
    sufixo = f"_{len(quadros)}f" if len(quadros) > 1 else ""
    pygame.image.save(tira, f"{J}{fase}/{nome}{sufixo}.png")


# =================================================================== bosque
MAD_E, MAD, MAD_L = (52, 40, 38), (84, 64, 52), (122, 96, 70)
CONT_B = (18, 26, 30)
LUZ, LUZ_F = (255, 226, 170), (255, 246, 214)


def lampiao(k):
    c = C(20, 40)
    c.r(8, 8, 9, 37, MAD); c.r(9, 8, 9, 37, MAD_L); c.r(8, 20, 8, 37, MAD_E)        # o poste
    c.r(8, 7, 15, 8, MAD); c.r(8, 7, 15, 7, MAD_L)                                    # o braco
    c.p(10, 9, MAD_E); c.p(11, 10, MAD_E)                                             # a escora
    c.r(6, 38, 11, 39, (66, 86, 82)); c.r(7, 37, 10, 37, (94, 114, 106))              # pedras no pe
    c.p(14, 9, (40, 34, 40))                                                          # a corrente
    c.r(12, 10, 16, 10, (40, 34, 40)); c.r(12, 16, 16, 16, (40, 34, 40))              # a lanterna
    c.r(12, 11, 12, 15, (40, 34, 40)); c.r(16, 11, 16, 15, (40, 34, 40))
    c.r(13, 11, 15, 15, LUZ)
    c.r(14, 12 + (k % 2), 14, 14, LUZ_F)                                              # a chama treme
    c.p(13 + (k == 2), 13, LUZ_F)
    c.contorno(CONT_B)
    c.halo(14, 13, 6.5 + (0.8 if k in (1, 2) else 0), LUZ, 110 if k != 3 else 90)
    return c


def toco():
    c = C(24, 16)
    c.r(6, 6, 17, 15, MAD); c.r(6, 6, 8, 15, MAD_E); c.r(15, 6, 17, 15, MAD_L)
    for x in (9, 12, 14):
        c.r(x, 8, x, 15, MAD_E)                                                       # a casca
    c.r(6, 4, 17, 6, (150, 126, 92)); c.r(7, 3, 16, 3, (150, 126, 92))                # o corte
    c.r(9, 4, 14, 5, (118, 94, 68)); c.r(11, 4, 12, 4, (150, 126, 92))                # os aneis
    c.r(4, 14, 5, 15, MAD_E); c.r(18, 14, 19, 15, MAD); c.p(3, 15, MAD_E); c.p(20, 15, MAD)
    c.r(6, 13, 9, 13, (92, 140, 70)); c.r(13, 14, 16, 14, (58, 94, 60))               # musgo
    COG, COG_L, CAULE = (110, 220, 170), (190, 255, 226), (196, 206, 196)
    for mx, my, larg in ((3, 10, 3), (19, 9, 3), (12, 0, 4)):
        c.r(mx, my, mx + larg - 1, my, COG_L); c.r(mx - 1, my + 1, mx + larg, my + 1, COG)
        c.r(mx + larg // 2, my + 2, mx + larg // 2, my + 3 if my else my + 2, CAULE)
    c.contorno(CONT_B)
    for mx, my in ((4, 10), (20, 9), (13, 1)):
        c.halo(mx, my, 3.5, (150, 255, 200), 80)
    return c


def placa():
    c = C(22, 26)
    c.r(10, 9, 11, 25, MAD); c.r(11, 9, 11, 25, MAD_L)
    c.r(2, 3, 17, 10, MAD_L); c.r(2, 9, 17, 10, MAD); c.r(2, 3, 17, 3, (160, 130, 96))
    for y in (4, 5, 6, 7, 8):                                                         # a ponta da seta
        c.r(18, y, 18 + (2 - abs(y - 6)), y, MAD_L)
    c.r(2, 6, 17, 6, MAD) if False else None
    c.r(5, 6, 13, 7, (50, 36, 34))                                                    # a seta entalhada
    for d in (1, 2):
        c.p(13 - d + 2, 6 - d, (50, 36, 34)); c.p(13 - d + 2, 7 + d, (50, 36, 34))
    c.r(14, 6, 15, 7, (50, 36, 34))
    c.p(3, 4, (200, 190, 150)); c.p(3, 9, (200, 190, 150))                            # os pregos
    c.r(8, 24, 13, 25, (58, 94, 60)); c.p(7, 25, (92, 140, 70)); c.p(14, 25, (92, 140, 70))
    c.contorno(CONT_B)
    return c


# ==================================================================== ilhas
CR_F, CR_E, CR, CR_L, CR_B = (58, 84, 150), (90, 146, 200), (148, 219, 250), (212, 244, 255), (255, 255, 255)
RO_F, RO_E, RO, RO_L, RO_T = (46, 33, 61), (69, 50, 87), (86, 66, 106), (105, 79, 120), (128, 100, 139)
CONT_I = (40, 26, 52)


def cristais(k):
    c = C(22, 20)
    for x0, x1, topo in ((2, 6, 11), (8, 13, 3), (15, 19, 8)):
        meio = (x0 + x1) // 2
        c.r(x0, topo + 2, x1, 19, CR); c.r(x0, topo + 2, meio - 1, 19, CR_E)
        c.r(x0 + 1, topo + 1, x1 - 1, topo + 1, CR); c.r(x0 + 2, topo, x1 - 2, topo, CR_L)
        c.r(x0, topo + 2, x0, 19, CR_F)
        c.r(meio, topo + 1, meio, 19, CR_L)                                           # a aresta
        c.r(x1, topo + 3, x1, 19, CR_L)
        c.r(x0, 18, x1, 19, CR_E)
    c.r(1, 19, 20, 19, RO); c.r(4, 18, 7, 18, RO_L); c.r(13, 18, 15, 18, RO_L)        # o cascalho
    if k:
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            c.p(11 + dx, 5 + dy, CR_B)
        c.p(17, 10, CR_B)
    else:
        c.p(11, 5, CR_B); c.p(4, 13, CR_B)
    c.contorno(CONT_I)
    c.halo(10, 9, 9, (148, 219, 250), 46 + 26 * k)
    return c


def arco():
    c = C(34, 34)
    def bloco(x0, y0, x1, y1):
        c.r(x0, y0, x1, y1, RO); c.r(x0, y0, x1, y0, RO_T); c.r(x1, y0, x1, y1, RO_L)
        c.r(x0, y1, x1, y1, RO_E); c.r(x0, y0 + 1, x0, y1, RO_E)
    for y in range(9, 33, 6):                                                         # o pilar inteiro
        bloco(3, y, 9, y + 5)
    bloco(2, 6, 10, 8)
    for y in range(21, 33, 6):                                                        # o pilar quebrado
        bloco(24, y, 30, y + 5)
    c.r(24, 19, 27, 20, RO); c.r(24, 19, 27, 19, RO_T); c.p(29, 20, RO)
    bloco(8, 2, 14, 6); bloco(14, 0, 20, 4); bloco(20, 2, 24, 5)                      # o arco, ate onde sobrou
    c.p(25, 4, RO); c.p(25, 5, RO_E)
    for x in (4, 6, 8):                                                               # gelo no alto
        c.p(x, 6, CR_L)
    c.r(14, 0, 19, 0, CR_L); c.r(9, 2, 12, 2, CR)
    c.p(16, 5, CR); c.p(16, 6, CR); c.p(16, 7, CR_E)                                  # um pingente
    c.r(1, 33, 11, 33, RO_E); c.r(23, 33, 31, 33, RO_E)
    c.p(13, 33, RO); c.p(20, 32, RO); c.r(19, 33, 21, 33, RO_E)                       # pedras caidas
    c.contorno(CONT_I)
    return c


def orbe(k):
    c = C(16, 34)
    c.r(5, 22, 10, 33, RO); c.r(5, 22, 6, 33, RO_E); c.r(10, 22, 10, 33, RO_L)        # o pedestal
    c.r(4, 20, 11, 21, RO_T); c.r(4, 21, 11, 21, RO); c.r(3, 32, 12, 33, RO_E)
    c.r(7, 25, 8, 29, CR_E); c.p(7, 26, CR); c.p(8, 28, CR)                           # a runa
    dy = (0, -1, -2, -1)[k]
    cy = 11 + dy
    for y in range(-3, 4):
        larg = 3 if abs(y) < 2 else (2 if abs(y) == 2 else 1)
        c.r(8 - larg, cy + y, 7 + larg, cy + y, CR)
    c.r(6, cy - 1, 7, cy, CR_L); c.p(6, cy - 2, CR_B); c.r(8, cy + 2, 9, cy + 2, CR_E)
    c.contorno(CONT_I)
    c.halo(7.5, cy, 7, (148, 219, 250), 90)
    c.p(7, 18 + (k % 2), (212, 244, 255, 150)); c.p(8, 16 + (k // 2), (212, 244, 255, 110))   # a poeira que sobe
    return c


# ================================================================== eclipse
FE_E, FE, FE_L = (30, 20, 46), (58, 42, 84), (96, 76, 130)
OURO, OURO_E = (255, 206, 120), (176, 116, 70)
FOGO_E, FOGO, FOGO_L = (140, 92, 224), (206, 168, 255), (248, 238, 255)
CONT_E = (12, 6, 20)
CHAMAS = (
    ((0, 3), (-1, 2), (0, 2), (-1, 1), (0, 1), (1, 1), (-1, 0), (0, 0), (1, 0), (0, 4), (1, 5)),
    ((0, 3), (0, 2), (1, 2), (-1, 1), (0, 1), (1, 1), (-1, 0), (0, 0), (1, 0), (1, 4), (0, 5), (0, 6)),
    ((0, 3), (-1, 2), (0, 2), (1, 2), (-1, 1), (0, 1), (1, 1), (-1, 0), (0, 0), (1, 0), (-1, 3), (-1, 4), (0, 5)),
    ((0, 3), (0, 2), (-1, 1), (0, 1), (1, 1), (-1, 0), (0, 0), (1, 0), (1, 2), (1, 3), (0, 4), (-1, 6)),
)


def chama(c, cx, base, k):
    """A chama do eclipse e lavanda (a cor do chao: nada a ver com o perigo, que e brasa)."""
    for dx, dy in CHAMAS[k]:
        cor = FOGO_L if dy <= 1 and dx == 0 else (FOGO if dy <= 3 else FOGO_E)
        c.p(cx + dx, base - dy, cor)
        c.p(cx + dx + 1, base - dy, cor if dy <= 2 else FOGO_E) if dy <= 2 else None


def tocha(k):
    c = C(16, 40)
    c.r(7, 14, 8, 37, FE); c.r(8, 14, 8, 37, FE_L); c.r(7, 26, 7, 37, FE_E)
    c.r(5, 38, 10, 39, FE); c.r(5, 38, 10, 38, FE_L)
    c.r(6, 24, 9, 24, OURO_E)                                                         # um anel
    c.r(5, 11, 10, 13, OURO); c.r(5, 13, 10, 13, OURO_E); c.r(6, 14, 9, 14, OURO_E)   # a taca
    c.p(4, 10, OURO); c.p(11, 10, OURO)
    chama(c, 7, 10, k)
    c.contorno(CONT_E)
    c.halo(7.5, 7, 7 + (k % 2) * 0.7, (206, 168, 255), 100)
    return c


def estandarte(k):
    c = C(20, 42)
    PANO, PANO_E, PANO_L = (104, 46, 134), (66, 26, 92), (140, 78, 176)
    c.r(3, 3, 4, 41, FE); c.r(4, 3, 4, 41, FE_L)
    c.r(2, 0, 5, 2, OURO); c.p(3, 0, (255, 240, 190)); c.r(2, 2, 5, 2, OURO_E)        # a ponta
    c.r(3, 5, 16, 5, OURO_E); c.p(17, 5, OURO)                                        # a travessa
    for y in range(6, 28):
        dx = (1 if (k and y > 16) else 0) + (1 if (k and y > 23) else 0)
        fim = 15 if y < 24 else None
        for x in range(6, 16):
            if y >= 24 and abs(x - 10.5) < (y - 23) * 1.0:                            # o rabo de andorinha
                continue
            cor = PANO_L if x >= 13 else (PANO if x >= 8 else PANO_E)
            if x in (6, 15):
                cor = OURO_E
            c.p(x + dx, y, cor)
    dx = 1 if k else 0
    for x, y in ((9, 12), (10, 11), (11, 11), (12, 12), (12, 13), (12, 14), (11, 15), (10, 15), (9, 14), (9, 13)):
        c.p(x + (dx if y > 16 else 0), y, OURO)                                       # o anel do eclipse
    c.r(10, 12, 11, 14, (20, 10, 34))
    c.r(7, 19, 14, 19, OURO_E)
    c.r(2, 40, 5, 41, FE_E)
    c.contorno(CONT_E)
    return c


def braseiro(k):
    c = C(22, 26)
    c.r(4, 12, 17, 14, FE); c.r(4, 12, 17, 12, FE_L); c.r(5, 15, 16, 15, FE_E); c.r(7, 16, 14, 16, FE_E)
    c.r(3, 11, 18, 11, OURO); c.p(3, 12, OURO_E); c.p(18, 12, OURO_E)
    for i in range(9):                                                                # o tripe
        c.p(6 - i // 3, 17 + i, FE); c.p(15 + i // 3, 17 + i, FE_L)
    c.r(10, 17, 11, 25, FE_E)
    c.r(8, 21, 13, 21, FE)
    for x in range(5, 17):                                                            # as brasas
        c.p(x, 10, FOGO if (x + k) % 3 else FOGO_L)
    chama(c, 8, 9, k); chama(c, 12, 9, (k + 2) % 4)
    c.p(6 + k, 4 - k % 2, FOGO_L); c.p(15 - k, 3 + k % 2, FOGO)                       # fagulhas
    c.contorno(CONT_E)
    c.halo(10.5, 7, 9, (206, 168, 255), 90)
    return c


def gargula(k):
    c = C(26, 36)
    PE, P, PL = (44, 32, 62), (72, 58, 96), (108, 92, 136)
    c.r(6, 24, 19, 35, (51, 32, 74)); c.r(6, 24, 19, 24, (99, 61, 122)); c.r(5, 22, 20, 23, (89, 50, 113))
    c.r(5, 22, 20, 22, (140, 100, 170))
    for y in (27, 31):
        c.r(6, y, 19, y, (24, 11, 40))
    for x, y in ((10, 25), (15, 28), (9, 32), (16, 32)):
        c.r(x, y, x, y + 2, (24, 11, 40))
    c.r(8, 12, 17, 21, P); c.r(8, 12, 10, 21, PE); c.r(15, 12, 17, 21, PL)            # o corpo agachado
    c.r(7, 18, 9, 21, P); c.r(16, 18, 18, 21, PL); c.r(7, 21, 18, 21, PE)             # as patas
    c.r(10, 6, 15, 11, P); c.r(10, 6, 11, 11, PE); c.r(14, 6, 15, 10, PL)             # a cabeca
    c.p(9, 4, P); c.p(9, 5, P); c.p(10, 5, P); c.p(16, 4, PL); c.p(16, 5, PL); c.p(15, 5, PL)   # os chifres
    c.r(11, 10, 14, 11, PE); c.p(12, 11, PL)                                          # o focinho
    for i in range(7):                                                                # as asas
        c.r(7 - i // 2 - 1, 8 + i, 7, 8 + i, PE if i % 2 else P)
        c.r(18, 8 + i, 18 + i // 2 + 1, 8 + i, PL if i % 2 == 0 else P)
    c.p(3, 7, P); c.p(22, 7, PL)
    olho = FOGO_L if k else FOGO
    c.p(11, 8, olho); c.p(14, 8, olho)
    c.contorno(CONT_E)
    if k:
        c.halo(12.5, 8, 4, (206, 168, 255), 90)
    return c


for f in ("bosque", "ilhas", "eclipse"):
    for velho in os.listdir(J + f):
        if velho.startswith("enfeite_"):
            os.remove(J + f + "/" + velho)
salvar("bosque", "enfeite_1", [lampiao(k) for k in range(4)])
salvar("bosque", "enfeite_2", [toco()])
salvar("bosque", "enfeite_3", [placa()])
# duas ruinas que ja estavam na arte bruta do projeto e nunca tinham entrado no jogo
shutil.copy(BRUTO + "bosque/Pixel_art_game_asset_for_a_2D (18).png", J + "bosque/enfeite_4.png")
shutil.copy(BRUTO + "bosque/Pixel_art_game_asset_for_a_2D (19).png", J + "bosque/enfeite_5.png")
salvar("ilhas", "enfeite_1", [cristais(k) for k in range(2)])
salvar("ilhas", "enfeite_2", [arco()])
salvar("ilhas", "enfeite_3", [orbe(k) for k in range(4)])
salvar("eclipse", "enfeite_1", [tocha(k) for k in range(4)])
salvar("eclipse", "enfeite_2", [estandarte(k) for k in range(2)])
salvar("eclipse", "enfeite_3", [braseiro(k) for k in range(4)])
salvar("eclipse", "enfeite_4", [gargula(k) for k in range(2)])
print("ok")
