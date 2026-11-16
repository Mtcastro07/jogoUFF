"""Pinta as variantes dos cacos (v2, v3) de cada mundo. A silhueta de cada variante
fica DENTRO da do caco original (conferido aqui): nunca mais dificil."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init(); pygame.display.set_mode((8, 8))
J = "/home/matheus/Documentos/jogoUFF/assets/art/objetos/jogo/"
H = W = 48


def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def ruido(x, y, s=0):
    return ((x * 73856093) ^ (y * 19349663) ^ (s * 83492791)) & 1023


def carregar(caminho):
    img = pygame.image.load(caminho)
    return [[img.get_at((x, y)).a >= 128 for x in range(W)] for y in range(H)]


def pontas(m):
    op = lambda x, y: 0 <= x < W and 0 <= y < H and m[y][x]
    topo = [next((y for y in range(H) if m[y][x]), H) for x in range(W)]
    picos, x = [], 0
    while x < W:
        if topo[x] >= H:
            x += 1; continue
        x2 = x
        while x2 + 1 < W and topo[x2 + 1] == topo[x]:
            x2 += 1
        e = topo[x - 1] if x > 0 else H
        d = topo[x2 + 1] if x2 + 1 < W else H
        if e > topo[x] and d > topo[x]:
            picos.append(((x + x2) // 2, topo[x]))
        x = x2 + 1
    bons = []
    for i, (px, py) in enumerate(picos):
        e = max(topo[q] for q in range(0 if i == 0 else picos[i - 1][0], px + 1))
        d = max(topo[q] for q in range(px, W if i == len(picos) - 1 else picos[i + 1][0] + 1))
        if min(e, d) - py >= 6:
            bons.append((px, py))
    picos = bons or sorted(picos, key=lambda p: p[1])[:1]
    res = []
    for i, (px, py) in enumerate(picos):
        if i == 0:
            esq = 0
        else:
            a = picos[i - 1][0]
            esq = max(range(a, px + 1), key=lambda q: (topo[q], -abs(q - (a + px) / 2))) + 1
        if i == len(picos) - 1:
            dir_ = W - 1
        else:
            b = picos[i + 1][0]
            dir_ = max(range(px, b + 1), key=lambda q: (topo[q], -abs(q - (px + b) / 2)))
        res.append((px, py, esq, dir_))
    return res


def pintar(origem, recorte, estilo, semente):
    m = carregar(origem)
    novo = [[False] * W for _ in range(H)]
    espinhos = []
    for k, (px, py, esq, dir_) in enumerate(pontas(m)):
        linhas = {}
        for y in range(py, H):
            xs = [x for x in range(esq, dir_ + 1) if m[y][x]]
            if xs:
                linhas[y] = (xs[0], xs[-1])
        linhas = recorte(dict(linhas), px, py, k + semente)
        for y, (a, b) in linhas.items():
            for x in range(a, b + 1):
                novo[y][x] = m[y][x]            # nunca fora da silhueta original
        espinhos.append((px, py, linhas, k + semente))
    op = lambda x, y: 0 <= x < W and 0 <= y < H and novo[y][x]
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    for px, py, linhas, sem in espinhos:
        alt = max(1, H - 1 - py)
        for y, (xl, xr) in linhas.items():
            crista = (xl + xr) / 2 * 0.5 + px * 0.5
            v = (y - py) / alt
            for x in range(xl, xr + 1):
                if not novo[y][x]:
                    continue
                borda = any(not op(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, -1))) or \
                        (y + 1 < H and not op(x, y + 1))
                lado = (x - crista) / max(1.0, (xr - xl) / 2)
                s.set_at((x, y), (*estilo(x, y, v, lado, crista, borda, xl, xr, sem, op), 255))
    return s


# ------------------------------------------------------------- recortes
def inteiro(linhas, px, py, s):
    return linhas


def serrilha(linhas, px, py, s):
    """Espinheiro: a cada 5 linhas a borda recua 2 px e volta -- farpas."""
    for y, (a, b) in list(linhas.items()):
        f = (y - py) % 5
        rec = 2 if f in (3, 4) else (1 if f == 2 else 0)
        if b - a > 6 + 2 * rec:
            linhas[y] = (a + rec, b - rec)
    return linhas


def degraus(linhas, px, py, s):
    """Cristal em camadas: a largura so muda de 5 em 5 linhas (um zigurate)."""
    ys = sorted(linhas)
    for y in ys:
        y0 = py + ((y - py) // 5) * 5
        linhas[y] = linhas[max(y0, ys[0])] if y0 in linhas else linhas[y]
    return linhas


def lascado(linhas, px, py, s):
    """Basalto: lascas arrancadas de um lado e do outro."""
    for y, (a, b) in list(linhas.items()):
        if b - a < 8:
            continue
        bloco = (y - py) // 6
        r = ruido(bloco, s, 7) % 4
        if r == 0:
            linhas[y] = (a + 2, b)
        elif r == 1:
            linhas[y] = (a, b - 2)
    return linhas


def lanca(linhas, px, py, s):
    """Lanca: lamina em cima, haste fina embaixo, e um pe largo no chao."""
    ys = sorted(linhas)
    alt = ys[-1] - py
    corte = py + int(alt * 0.62)
    for y in ys:
        a, b = linhas[y]
        if corte + 2 < y < ys[-1] - 2:
            meio = (linhas[corte][0] + linhas[corte][1]) // 2
            larg = max(2, min(3, (b - a) // 4))
            linhas[y] = (max(a, meio - larg), min(b, meio + larg))
    return linhas


# -------------------------------------------------------------- estilos
def espinheiro(x, y, v, lado, crista, borda, xl, xr, s, op):
    if borda:
        # as farpas acendem em rosa na ponta de cada dente
        if not op(x - 1, y - 1) and not op(x + 1, y - 1) and v > 0.2:
            return (255, 150, 200)
        return (22, 16, 30)
    if v < 0.2:
        return (255, 236, 246) if v < 0.07 else ((255, 150, 200) if lado > -0.2 else (214, 80, 140))
    esc, med, cla = (44, 30, 40), (76, 54, 56), (118, 88, 76)
    c = cla if lado > 0.25 else (med if lado > -0.35 else esc)
    d = (x + y * 2 + s * 5) % 11                          # o cipo que sobe em espiral
    if d < 2:
        c = (58, 118, 74) if d == 0 else (96, 164, 96)
    if v < 0.34:
        c = mix(c, (240, 110, 160), (0.34 - v) / 0.16)   # a madeira ja vai ficando rosa
    if v > 0.86 and ruido(x, y, s) % 3 == 0:
        c = (70, 130, 80)
    return c


def estaca(x, y, v, lado, crista, borda, xl, xr, s, op):
    if borda:
        return (26, 18, 26)
    if v < 0.26:                                             # a ponta pintada de eco
        if v < 0.07:
            return (255, 240, 248)
        return (250, 140, 186) if lado > -0.1 else (206, 74, 132)
    if 0.26 <= v < 0.3:
        return (60, 30, 50)                                  # a borda da pintura
    esc, med, cla = (78, 56, 48), (118, 88, 64), (160, 126, 88)
    c = cla if lado > 0.3 else (med if lado > -0.3 else esc)
    if (x + s) % 4 == 0 and ruido(x, y // 5, s) % 3:
        c = mix(c, (50, 34, 34), 0.45)                       # o veio da madeira
    if 0.58 < v < 0.68:                                      # a corda
        c = (214, 200, 150) if (x + y) % 3 else (150, 132, 96)
        if v > 0.65:
            c = (96, 80, 62)
    if v > 0.9 and ruido(x, y, s) % 3 == 0:
        c = (66, 124, 78)
    return c


def rubi(x, y, v, lado, crista, borda, xl, xr, s, op):
    if borda:
        return (255, 196, 206) if (not op(x, y - 1) and lado > -0.2) else (54, 16, 46)
    esc, med, cla, cume = (118, 28, 70), (186, 48, 92), (238, 94, 122), (255, 190, 204)
    c = cume if abs(x - crista) < 0.8 else (cla if lado > 0 else (med if lado > -0.5 else esc))
    # cada camada escurece para baixo e tem o alto aceso
    f = (y - int(v * 0) ) % 5
    if not op(x, y - 1) or (op(x, y - 1) and not (op(x - 1, y - 1) and op(x + 1, y - 1))):
        c = mix(c, (255, 220, 226), 0.5)
    if v < 0.1:
        c = (255, 240, 244)
    if 0.3 < v < 0.5 and int(crista + 2) == x:
        c = (255, 255, 255)
    return c


def basalto(x, y, v, lado, crista, borda, xl, xr, s, op):
    if borda:
        return (30, 18, 40)
    esc, med, cla = (58, 42, 72), (88, 68, 102), (124, 100, 136)
    c = cla if lado > 0.2 else (med if lado > -0.35 else esc)
    if ruido(x // 2, y // 3, s) % 7 == 0:
        c = mix(c, (40, 28, 54), 0.5)
    # o veio em ziguezague, quente
    zig = crista + ((y // 4) % 2 * 2 - 1) * 1.5 + (ruido(y // 4, s) % 3 - 1)
    if v > 0.14:
        d = abs(x - zig)
        if d < 0.9:
            c = (255, 214, 190) if v < 0.6 else (255, 150, 140)
        elif d < 2.0:
            c = (255, 106, 118)
        elif d < 3.2 and ruido(x, y, s) % 2:
            c = (150, 54, 84)
    else:
        c = (255, 244, 236) if v < 0.06 else (255, 140, 134)
    return c


def ferro(x, y, v, lado, crista, borda, xl, xr, s, op):
    if borda:
        return (18, 12, 28)
    if v < 0.24:                                             # a ponta em brasa
        return mix((255, 248, 210), (255, 128, 96), v / 0.24) if lado > -0.3 else mix((255, 190, 120), (200, 70, 60), v / 0.24)
    if 0.56 <= v <= 0.66:                                    # a guarda dourada
        return (255, 226, 150) if v < 0.6 else ((255, 206, 120) if lado > -0.2 else (190, 130, 70))
    if v > 0.66:                                             # a haste e o pe
        return (96, 76, 110) if lado > 0 else (58, 42, 76)
    esc, med, cla, cume = (72, 64, 98), (124, 116, 156), (180, 174, 210), (240, 236, 255)
    if abs(x - crista) < 0.8:
        return (52, 44, 78)                                  # o sulco da lamina
    c = cla if lado > 0 else (med if lado > -0.55 else esc)
    if lado > 0 and abs(x - crista - 2) < 0.6:
        c = cume
    if v < 0.36:
        c = mix(c, (255, 128, 96), (0.36 - v) / 0.14)
    return c


def presa(x, y, v, lado, crista, borda, xl, xr, s, op):
    if borda:
        return (36, 16, 30)
    esc, med, cla = (150, 112, 122), (216, 194, 180), (252, 242, 222)
    c = cla if lado > 0.1 else (med if lado > -0.45 else esc)
    if ruido(x, y // 6, s) % 9 == 0 and 0.2 < v < 0.8:
        c = mix(c, (110, 80, 96), 0.6)                       # trincas do osso
    if v < 0.16:
        c = mix((255, 110, 84), c, v / 0.16)                 # a ponta suja de brasa
    if v > 0.74:
        c = mix(c, (220, 84, 60), (v - 0.74) / 0.3)          # a gengiva de brasa
    if v > 0.93:
        c = (120, 34, 40)
    return c


TRABALHO = {
    "bosque": ((serrilha, espinheiro), (inteiro, estaca)),
    "ilhas": ((degraus, rubi), (lascado, basalto)),
    "eclipse": ((lanca, ferro), (inteiro, presa)),
}
for fase, variantes in TRABALHO.items():
    for q in (1, 2, 3):
        for n, (recorte, estilo) in enumerate(variantes, start=2):
            img = pintar(f"{J}{fase}/caco{q}.png", recorte, estilo, q * 3 + n)
            pygame.image.save(img, f"{J}{fase}/caco{q}v{n}.png")
print("ok")
