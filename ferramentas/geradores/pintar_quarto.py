"""
O quarto do Leo, onde o trailer final comeca e termina (o enredo do GDD: ele joga
de madrugada e e sugado pela tela no instante em que aperta START).

    ./.venv/bin/python ferramentas/geradores/pintar_quarto.py

Sai em assets/art/trailer/, em pixels logicos de 320x180 (o trailer amplia 4x):

    quarto_noite.png   03:12, a lua na janela, so a TV acesa
    quarto_manha.png   06:00, o sol nascendo: ele voltou
    brilho_tv.png      a luz da TV em tons de cinza: o trailer tinge com a cor da tela e soma
    foto.png           o porta-retrato da familia, para o plano de memoria

A TV fica em TELA = (232, 88, 57, 32): ali o trailer desenha o jogo de verdade.
"""
import math
import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
from pintar_arte import C, mist  # noqa: E402

PASTA = os.path.join(RAIZ, "assets", "art", "trailer")
W, H = 320, 180
TELA = (232, 88, 57, 32)          # a tela da TV: x, y, largura, altura (16:9)
CHAO = 150

DIGITOS = {
    "0": ("111", "101", "101", "101", "111"), "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"), "3": ("111", "001", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"), "5": ("111", "100", "111", "001", "111"),
    ":": ("0", "1", "0", "1", "0"),
}

NOITE = dict(
    parede=(30, 28, 58), listra=(34, 32, 64), rodape=(18, 16, 34), chao=(38, 28, 44),
    tabua=(28, 20, 34), chao_luz=(48, 38, 56),
    ceu_alto=(10, 14, 40), ceu_baixo=(34, 38, 88), predio=(14, 14, 32), janela_acesa=(255, 206, 120),
    moldura=(62, 54, 92), cortina=(66, 38, 88), cortina_sombra=(48, 26, 66), cortina_luz=(90, 56, 112),
    madeira=(60, 42, 46), madeira_luz=(78, 56, 58), madeira_sombra=(40, 28, 34),
    coberta=(56, 64, 122), coberta_luz=(74, 84, 148), coberta_sombra=(40, 46, 92), fronha=(150, 150, 186),
    tv=(44, 44, 58), tv_luz=(68, 68, 86), tv_sombra=(28, 28, 38),
    tapete=(64, 34, 58), tapete_borda=(96, 52, 84),
    relogio="03:12", luz_janela=(110, 130, 220, 34),
)
MANHA = dict(
    parede=(92, 70, 92), listra=(100, 76, 98), rodape=(52, 38, 56), chao=(98, 70, 70),
    tabua=(80, 56, 60), chao_luz=(122, 90, 84),
    ceu_alto=(120, 116, 176), ceu_baixo=(255, 178, 120), predio=(72, 56, 86), janela_acesa=None,
    moldura=(150, 126, 150), cortina=(150, 88, 130), cortina_sombra=(118, 64, 104), cortina_luz=(186, 120, 160),
    madeira=(122, 84, 74), madeira_luz=(150, 108, 90), madeira_sombra=(90, 60, 58),
    coberta=(98, 110, 180), coberta_luz=(130, 142, 206), coberta_sombra=(74, 84, 146), fronha=(226, 220, 236),
    tv=(70, 66, 82), tv_luz=(102, 96, 116), tv_sombra=(46, 42, 56),
    tapete=(128, 66, 96), tapete_borda=(170, 98, 128),
    relogio="06:00", luz_janela=(255, 196, 140, 52),
)


def ret(c, x0, y0, x1, y1, cor):
    pygame.draw.rect(c.s, (*cor[:3], 255), (x0, y0, x1 - x0 + 1, y1 - y0 + 1))


def digitos(c, x, y, texto, cor):
    for ch in texto:
        for j, linha in enumerate(DIGITOS[ch]):
            for i, b in enumerate(linha):
                if b == "1":
                    c.p(x + i, y + j, cor)
        x += len(DIGITOS[ch][0]) + 1


def quarto(P, manha):
    c = C(W, H)
    rnd = random.Random(3)
    # parede com listras finas e o rodape
    ret(c, 0, 0, W - 1, CHAO - 1, P["parede"])
    for x in range(4, W, 12):
        ret(c, x, 0, x + 1, CHAO - 5, P["listra"])
    for y in range(0, 10):                                   # o teto escurece
        ret(c, 0, y, W - 1, y, mist(P["parede"], (0, 0, 0), 0.5 * (1 - y / 10)))
    ret(c, 0, CHAO - 4, W - 1, CHAO - 1, P["rodape"])
    # o chao de tabuas
    ret(c, 0, CHAO, W - 1, H - 1, P["chao"])
    for y in range(CHAO + 4, H, 7):
        ret(c, 0, y, W - 1, y, P["tabua"])
        off = (y * 13) % 40
        for x in range(off, W, 40):
            ret(c, x, y - 6, x, y - 1, P["tabua"])
    ret(c, 0, CHAO, W - 1, CHAO, P["chao_luz"])

    # a janela: ceu, lua ou sol, a cidade
    jx0, jy0, jx1, jy1 = 26, 26, 92, 90
    for y in range(jy0, jy1 + 1):
        k = (y - jy0) / (jy1 - jy0)
        ret(c, jx0, y, jx1, y, mist(P["ceu_alto"], P["ceu_baixo"], k ** 1.4))
    if manha:
        for r, a in ((16, 40), (11, 80)):
            for y in range(jy0, jy1 + 1):
                for x in range(jx0, jx1 + 1):
                    d = math.hypot(x - 70, y - 80)
                    if d < r:
                        c.p(x, y, mist(c.s.get_at((x, y))[:3], (255, 226, 160), a / 100 * (1 - d / r)))
        c.disco(70, 80, 6.5, (255, 232, 170))
    else:
        for _ in range(26):
            x, y = rnd.randint(jx0 + 1, jx1 - 1), rnd.randint(jy0 + 1, jy0 + 40)
            c.p(x, y, mist((255, 255, 240), P["ceu_alto"], rnd.random() * 0.6))
        for y in range(28, 50):
            for x in range(60, 86):
                d = math.hypot(x - 76, y - 38)
                if 6 < d < 11:
                    c.p(x, y, mist(c.s.get_at((x, y))[:3], (150, 160, 230), 0.25 * (1 - (d - 6) / 5)))
        c.disco(76, 38, 6, (238, 232, 204))
        c.disco(74, 37, 1.2, (214, 206, 176)); c.disco(78, 41, 1, (214, 206, 176))
    # a cidade: predios recortados, umas janelas acesas de madrugada
    x = jx0
    while x <= jx1:
        larg, alto = rnd.randint(6, 12), rnd.randint(10, 26)
        ret(c, x, jy1 - alto, min(jx1, x + larg), jy1, P["predio"])
        if P["janela_acesa"]:
            for wy in range(jy1 - alto + 3, jy1 - 1, 4):
                for wx in range(x + 2, min(jx1, x + larg) - 1, 3):
                    if rnd.random() < 0.18:
                        c.p(wx, wy, P["janela_acesa"])
        x += larg + 1
    # moldura e travessas
    for (a, b, cc, d) in ((jx0 - 3, jy0 - 3, jx1 + 3, jy0 - 1), (jx0 - 3, jy1 + 1, jx1 + 3, jy1 + 4),
                          (jx0 - 3, jy0 - 3, jx0 - 1, jy1 + 4), (jx1 + 1, jy0 - 3, jx1 + 3, jy1 + 4),
                          ((jx0 + jx1) // 2 - 1, jy0, (jx0 + jx1) // 2, jy1), (jx0, 57, jx1, 58)):
        ret(c, a, b, cc, d, P["moldura"])
    ret(c, jx0 - 5, jy1 + 4, jx1 + 5, jy1 + 6, mist(P["moldura"], (255, 255, 255), 0.15))   # o peitoril
    # cortinas, com dobras
    for x0, x1 in ((12, 25), (93, 106)):
        ret(c, x0, 18, x1, 104, P["cortina"])
        for x in range(x0 + 2, x1, 4):
            ret(c, x, 19, x, 103, P["cortina_sombra"])
            ret(c, x + 1, 19, x + 1, 103, P["cortina_luz"])
        for y in range(98, 105):                                  # a barra ondula
            if (y + x0) % 3 == 0:
                ret(c, x0, y, x1, y, P["cortina_sombra"])
    ret(c, 8, 16, 110, 17, mist(P["moldura"], (0, 0, 0), 0.2))

    # o poster: um equalizador, a musica ja estava no quarto
    px0, py0, px1, py1 = 124, 30, 156, 74
    ret(c, px0, py0, px1, py1, mist(P["parede"], (0, 0, 0), 0.45))
    alturas = (8, 14, 22, 30, 18, 26, 12, 20, 9)
    for i, a in enumerate(alturas):
        x = px0 + 3 + i * 3
        for y in range(py1 - 6 - a, py1 - 5):
            k = min(1.0, (py1 - 5 - y) / 31)
            c.p(x, y, mist((80, 235, 255), (255, 70, 190), k))
            c.p(x + 1, y, mist((80, 235, 255), (255, 70, 190), k))
    ret(c, px0 + 4, py0 + 4, px1 - 4, py0 + 5, (255, 206, 120))
    for x, y in ((px0, py0), (px1 - 2, py0), (px0, py1 - 2), (px1 - 2, py1 - 2)):
        ret(c, x, y, x + 2, y + 2, (214, 208, 186))

    # a cama, a esquerda
    ret(c, 0, 116, 70, CHAO + 2, P["madeira_sombra"])
    ret(c, 0, 112, 66, 132, P["coberta"])
    for x in range(6, 66, 9):
        ret(c, x, 114, x + 1, 132, P["coberta_sombra"])
    ret(c, 0, 112, 66, 113, P["coberta_luz"])
    ret(c, 2, 104, 24, 113, P["fronha"])
    ret(c, 2, 112, 24, 113, mist(P["fronha"], (0, 0, 0), 0.25))
    ret(c, 66, 104, 70, CHAO + 2, P["madeira"])
    ret(c, 66, 104, 70, 105, P["madeira_luz"])

    # a estante sobre a TV: livros, a foto da familia, o relogio, a planta
    ret(c, 210, 52, 308, 54, P["madeira"])
    ret(c, 210, 52, 308, 52, P["madeira_luz"])
    ret(c, 214, 55, 306, 56, P["madeira_sombra"])
    x = 214
    for cor, alto in (((150, 60, 70), 15), ((60, 110, 150), 13), ((200, 170, 90), 16), ((90, 140, 90), 12),
                      ((120, 80, 140), 14)):
        ret(c, x, 52 - alto, x + 3, 51, cor if not manha else mist(cor, (255, 230, 200), 0.15))
        ret(c, x, 52 - alto, x, 51, mist(cor, (255, 255, 255), 0.25))
        x += 5
    foto = porta_retrato(manha)
    c.s.blit(foto.s, (244, 36))
    ret(c, 268, 43, 291, 51, (16, 14, 20))
    ret(c, 268, 43, 291, 43, (40, 36, 46))
    digitos(c, 270, 45, P["relogio"], (255, 70, 60))
    ret(c, 296, 46, 303, 51, (150, 90, 70))
    for dx, dy in ((-2, -4), (0, -7), (2, -5), (4, -3), (-1, -2), (3, -8)):
        ret(c, 299 + dx, 46 + dy, 300 + dx, 47 + dy, (70, 140, 80) if not manha else (100, 170, 100))

    # o movel e a TV de tubo
    ret(c, 220, 126, 302, CHAO + 4, P["madeira"])
    ret(c, 220, 126, 302, 127, P["madeira_luz"])
    ret(c, 224, 132, 260, CHAO, P["madeira_sombra"])
    ret(c, 264, 132, 298, CHAO, P["madeira_sombra"])
    ret(c, 228, 138, 254, 145, (26, 24, 30))                     # o console, na prateleira
    ret(c, 228, 138, 254, 138, (52, 50, 60))
    c.p(251, 141, (80, 255, 120))
    for x, y in ((242, 145), (246, 148), (252, 151), (262, 154), (276, 158)):  # o fio do controle
        c.p(x, y, (20, 18, 24))
    tx, ty, tw, th = TELA
    ret(c, tx - 7, ty - 6, tx + tw + 7, ty + th + 9, P["tv_sombra"])
    ret(c, tx - 6, ty - 6, tx + tw + 6, ty + th + 8, P["tv"])
    ret(c, tx - 6, ty - 6, tx + tw + 6, ty - 5, P["tv_luz"])
    ret(c, tx - 2, ty - 2, tx + tw + 1, ty + th + 1, P["tv_sombra"])
    ret(c, tx - 1, ty - 1, tx + tw, ty + th, (8, 8, 12))
    for i in range(5):
        c.p(tx + tw - 10 + i * 3, ty + th + 5, P["tv_luz"])
    c.p(tx + 2, ty + th + 5, (255, 60, 60) if not manha else (90, 255, 140))
    c.linha((tx + tw // 2 - 4, ty - 6), (tx + tw // 2 - 16, ty - 24), P["tv_luz"])
    c.linha((tx + tw // 2 + 4, ty - 6), (tx + tw // 2 + 14, ty - 26), P["tv_luz"])

    # o tapete, no meio do quarto
    for y in range(156, 172):
        k = abs(y - 164) / 8
        meio = int(64 * math.sqrt(max(0.0, 1 - k * k)))
        ret(c, 172 - meio, y, 172 + meio, y, P["tapete_borda"] if y in (156, 171) else P["tapete"])
    for x in range(120, 226, 6):
        c.p(x, 164, P["tapete_borda"])

    # a luz da janela no chao (lua ou sol)
    luz = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.polygon(luz, P["luz_janela"], [(40, CHAO + 1), (104, CHAO + 1), (150, H), (60, H)])
    c.s.blit(luz, (0, 0))
    if manha:                                            # o feixe do sol atravessa o quarto
        feixe = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(feixe, (255, 200, 150, 22), [(30, 28), (92, 28), (200, H), (100, H)])
        c.s.blit(feixe, (0, 0))
    return c


def porta_retrato(manha):
    """A familia do Leo: pai, mae e ele, pequenos, num dia de sol."""
    c = C(18, 15)
    ret(c, 0, 0, 17, 14, (170, 140, 86))
    ret(c, 1, 1, 16, 13, (122, 96, 58))
    for y in range(2, 13):
        ret(c, 2, y, 15, y, mist((140, 200, 240), (200, 232, 250), (y - 2) / 10))
    ret(c, 2, 11, 15, 12, (110, 170, 100))
    for x, alto, roupa, cabelo in ((5, 7, (200, 80, 90), (60, 40, 30)), (9, 7, (70, 110, 170), (40, 30, 26)),
                                   (13, 5, (140, 150, 200), (110, 70, 40))):
        ret(c, x - 1, 12 - alto + 2, x + 1, 12, roupa)
        ret(c, x - 1, 12 - alto, x + 1, 12 - alto + 1, (240, 196, 160))
        ret(c, x - 1, 12 - alto - 1, x + 1, 12 - alto - 1, cabelo)
    return c


def brilho_tv():
    """A luz da TV: um halo em volta da tela e um cone no chao, a frente dela."""
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    tx, ty, tw, th = TELA
    cx, cy = tx + tw / 2, ty + th / 2
    for y in range(H):
        for x in range(W):
            d = math.hypot((x - cx) / 1.3, (y - cy) / 1.0)
            a = max(0.0, 1 - d / 110) ** 2 * 150
            if y > CHAO and x < cx:                      # no chao a luz espicha para o quarto
                a = max(a, max(0.0, 1 - math.hypot((x - cx + 40) / 2.4, (y - CHAO - 12) / 0.9) / 60) ** 1.5 * 90)
            v = int(min(255, a))
            s.set_at((x, y), (v, v, v, 255))       # a intensidade na propria cor: soma direto
    return s


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(PASTA, exist_ok=True)
    for nome, P, manha in (("quarto_noite", NOITE, False), ("quarto_manha", MANHA, True)):
        pygame.image.save(quarto(P, manha).s, os.path.join(PASTA, nome + ".png"))
        print(f"  trailer/{nome}.png  {W}x{H}")
    pygame.image.save(brilho_tv(), os.path.join(PASTA, "brilho_tv.png"))
    pygame.image.save(porta_retrato(False).s, os.path.join(PASTA, "foto.png"))
    print("  trailer/brilho_tv.png, trailer/foto.png")


if __name__ == "__main__":
    main()
