"""
Compoe, por sintese, a trilha ORIGINAL das Dunas do Chocalho: 96 BPM cravados,
escala frigia dominante de Re (o "deserto"), darbuka, chocalho, alaude e flauta.

    python3 ferramentas/geradores/compor_dunas.py      (precisa de numpy e ffmpeg)

Como a faixa e escrita na mesma grade de batidas da fase, a sincronia e exata:
a batida 0 cai em ENTRADA segundos do arquivo (audio.TRILHAS["dunas"].offset).

    batidas   0- 16   introducao   bordao, chocalho, o alaude chega
             16- 64   A            a levada inteira (maqsum), a flauta entra
             64-112   B            a quebra: so pandeiro e flauta grave; a subida
            112-160   A'           tudo de novo, oitava acima, com palmas
            160       o golpe final

A faixa ja teve 208 batidas (8+16+12+16 compassos); encurtamos a introducao
para 4 compassos e o A e o A' para 12, para a fase durar cerca de 1min40.
"""

import os
import subprocess
import sys

import numpy as np

SR = 44100
BPM = 96.0
BATIDA = 60.0 / BPM
ENTRADA = 0.100                      # segundos de silencio antes da batida 0
TOTAL_BATIDAS = 160
# onde cada parte comeca, em batidas
INTRO, A, B, SUBIDA, A2, GOLPE = 0, 16, 64, 96, 112, 160
FIM = ENTRADA + (TOTAL_BATIDAS + 10) * BATIDA + 2.5
N = int(FIM * SR)
rnd = np.random.default_rng(96)

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAIDA = os.path.join(RAIZ, "assets", "music", "dunas.mp3")


def hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def pos(batida):
    return int(round((ENTRADA + batida * BATIDA) * SR))


class Pista:
    def __init__(self):
        self.e = np.zeros(N)
        self.d = np.zeros(N)

    def por(self, som, batida, ganho=1.0, pan=0.0):
        i = pos(batida)
        if i >= N or i < 0:
            return
        som = som[:N - i]
        self.e[i:i + len(som)] += som * ganho * (1.0 - max(0.0, pan))
        self.d[i:i + len(som)] += som * ganho * (1.0 + min(0.0, pan))


def filtro(x, baixo=None, alto=None, suave=0.25):
    """Passa-faixa no dominio da frequencia, com bordas suaves."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    m = np.ones_like(f)
    if baixo:
        m *= 1.0 / (1.0 + (baixo / np.maximum(f, 1e-6)) ** (2.0 / suave))
    if alto:
        m *= 1.0 / (1.0 + (f / alto) ** (2.0 / suave))
    return np.fft.irfft(X * m, len(x))


def env(n, ataque, queda):
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(ataque, 1e-4)) * np.exp(-t / queda)


# ------------------------------------------------------------- instrumentos
def dum(forca=1.0):
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 62.0 + 70.0 * np.exp(-t / 0.035)
    corpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    pele = filtro(rnd.standard_normal(n), 300, 1800) * np.exp(-t / 0.012) * 0.6
    return (corpo + pele) * forca


def tek(forca=1.0, agudo=1.0):
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    tom = np.sin(2 * np.pi * 720 * agudo * t) * np.exp(-t / 0.03) * 0.5
    tom += np.sin(2 * np.pi * 1180 * agudo * t) * np.exp(-t / 0.018) * 0.3
    estalo = filtro(rnd.standard_normal(n), 2400, 9000) * np.exp(-t / 0.016)
    return (tom + estalo * 0.9) * forca


def chocalho(forca=1.0, longo=False):
    n = int((0.11 if longo else 0.055) * SR)
    t = np.arange(n) / SR
    graos = filtro(rnd.standard_normal(n), 5200, 13000, 0.4)
    e = np.minimum(1.0, t / 0.006) * np.exp(-t / (0.035 if longo else 0.016))
    return graos * e * forca


def platinela(forca=1.0):
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t + rnd.uniform(0, 6)) for f in (5230, 6890, 8120, 9410, 11300))
    x = x * 0.12 + filtro(rnd.standard_normal(n), 7000, 14000) * 0.5
    return x * np.exp(-t / 0.05) * forca


def palma(forca=1.0):
    n = int(0.2 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for atraso in (0.0, 0.011, 0.021):
        k = int(atraso * SR)
        x[k:] += filtro(rnd.standard_normal(n), 900, 3600)[:n - k] * np.exp(-t[:n - k] / 0.03)
    return x * forca * 0.6


def bumbo(forca=1.0):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    f = 46.0 + 90.0 * np.exp(-t / 0.022)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11) * forca


def alaude(midi, dur, forca=1.0):
    """Corda beliscada (Karplus-Strong), com o ataque duro do alaude."""
    n = int((dur * BATIDA + 0.5) * SR)
    p = max(2, int(round(SR / hz(midi))))
    seg = filtro(rnd.uniform(-1, 1, p * 8), 80, 4200)[:p]
    partes = []
    perda = 0.996 - 0.0009 * (midi - 50) / 12.0
    for _ in range(n // p + 1):
        partes.append(seg)
        seg = (0.5 * seg + 0.5 * np.roll(seg, 1)) * perda
    x = np.concatenate(partes)[:n]
    t = np.arange(n) / SR
    solta = np.where(t > dur * BATIDA, np.exp(-(t - dur * BATIDA) / 0.09), 1.0)
    return x * solta * forca


def baixo(midi, dur, forca=1.0):
    n = int((dur * BATIDA + 0.12) * SR)
    t = np.arange(n) / SR
    f = hz(midi)
    x = np.sin(2 * np.pi * f * t) + 0.42 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.12)
    x += 0.18 * np.sin(6 * np.pi * f * t) * np.exp(-t / 0.06)
    e = np.minimum(1.0, t / 0.006) * np.exp(-t / 0.5)
    e *= np.where(t > dur * BATIDA, np.exp(-(t - dur * BATIDA) / 0.03), 1.0)
    return np.tanh(x * e * 1.4) * forca


def flauta(midi, dur, forca=1.0, de=None):
    """Sopro com vibrato que entra aos poucos; `de` = nota de onde ela escorrega."""
    n = int((dur * BATIDA + 0.18) * SR)
    t = np.arange(n) / SR
    f = np.full(n, hz(midi))
    if de is not None:
        f = hz(midi) + (hz(de) - hz(midi)) * np.exp(-t / 0.035)
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.3 * t) * np.minimum(1.0, t / 0.35)
    fase = 2 * np.pi * np.cumsum(f * vib) / SR
    x = np.sin(fase) + 0.32 * np.sin(2 * fase) + 0.11 * np.sin(3 * fase) + 0.04 * np.sin(4 * fase)
    sopro = filtro(rnd.standard_normal(n), hz(midi) * 1.5, hz(midi) * 6) * 0.10
    e = np.minimum(1.0, t / 0.045) * np.where(
        t > dur * BATIDA, np.exp(-(t - dur * BATIDA) / 0.06), 1.0)
    e *= 0.82 + 0.18 * np.exp(-t / 0.2)
    return (x + sopro) * e * forca * 0.5


def bordao(midi, dur_batidas):
    """O bordao: serras desafinadas, bem abafadas, respirando devagar."""
    n = int(dur_batidas * BATIDA * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for des in (-0.07, 0.0, 0.06):
        f = hz(midi + des)
        for h in range(1, 9):
            x += np.sin(2 * np.pi * f * h * t + des * 40 * h) / h
    x = filtro(x, 50, 700, 0.5)
    return x * (0.8 + 0.2 * np.sin(2 * np.pi * t / (8 * BATIDA)))


def sopro_de_areia(dur_batidas, sobe=True):
    """O vento que anuncia a troca de parte: ruido que cresce (ou some)."""
    n = int(dur_batidas * BATIDA * SR)
    k = np.linspace(0.0, 1.0, n)
    x = filtro(rnd.standard_normal(n), 900, 7000, 0.5)
    return x * (k ** 2.2 if sobe else (1 - k) ** 2.5)


def gongo():
    n = int(4.0 * SR)
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t + rnd.uniform(0, 6)) * np.exp(-t / d) * a
            for f, d, a in ((73.4, 1.6, 1.0), (146.8, 1.3, 0.6), (220.0, 1.0, 0.35),
                            (311.0, 0.7, 0.2), (466.0, 0.5, 0.14), (587.3, 0.4, 0.1)))
    return x


# ------------------------------------------------------------------ a faixa
perc, grave, cordas, sopros, fundo = Pista(), Pista(), Pista(), Pista(), Pista()

DUM, TEK, KA = dum(), tek(), tek(0.55, 1.25)
CHOC, CHOC_L = chocalho(), chocalho(1.0, True)

# o ciclo de 4 compassos: Re, Re, Sol, Mib (que cai de volta em Re)
RAIZES = (38, 38, 43, 39)
R1 = ((0, 2, 62), (2, 1, 57), (3, 1, 62), (4, 2, 63), (6, 2, 62), (8, 2, 66), (10, 1, 63),
      (11, 1, 62), (12, 2, 60), (14, 2, 62))
R2 = ((0, 2, 62), (2, 1, 57), (3, 1, 62), (4, 2, 66), (6, 2, 67), (8, 3, 69), (11, 1, 67),
      (12, 1, 66), (13, 1, 63), (14, 2, 62))
RG = ((0, 2, 67), (2, 1, 62), (3, 1, 67), (4, 2, 69), (6, 2, 70), (8, 2, 69), (10, 1, 67),
      (11, 1, 66), (12, 2, 63), (14, 2, 62))
R3 = ((0, 2, 63), (2, 1, 58), (3, 1, 63), (4, 2, 67), (6, 2, 63), (8, 2, 62), (10, 1, 60),
      (11, 1, 58), (12, 1, 60), (13, 1, 63), (14, 2, 62))
RIFFS = (R1, R2, RG, R3)

MELODIA = (
    ((0, 1.5, 74), (1.5, 0.5, 75), (2, 2, 74)),
    ((0, 1, 78), (1, 1, 79), (2, 1.5, 81), (3.5, 0.5, 79)),
    ((0, 1.5, 82), (1.5, 0.5, 81), (2, 1, 79), (3, 1, 78)),
    ((0, 1, 75), (1, 1, 79), (2, 2, 74)),
    ((0, 0.5, 74), (0.5, 0.5, 75), (1, 0.5, 78), (1.5, 0.5, 79), (2, 2, 81)),
    ((0, 1, 81), (1, 0.5, 82), (1.5, 0.5, 81), (2, 1, 79), (3, 1, 78)),
    ((0, 1.5, 79), (1.5, 0.5, 78), (2, 1, 79), (3, 1, 82)),
    ((0, 1, 79), (1, 1, 75), (2, 2, 74)),
)
MELODIA_B = (
    ((0, 2, 67), (2, 1, 70), (3, 1, 69)), ((0, 3, 67), (3, 1, 66)),
    ((0, 2, 66), (2, 1, 69), (3, 1, 67)), ((0, 3, 69), (3, 1, 67)),
    ((0, 2, 72), (2, 1, 75), (3, 1, 74)), ((0, 3, 72), (3, 1, 70)),
    ((0, 2, 69), (2, 1, 72), (3, 1, 70)), ((0, 4, 69),),
)
ACORDES_B = ((55, 62, 67, 70), (55, 62, 67, 70), (50, 57, 62, 66), (50, 57, 62, 66),
             (48, 55, 60, 63), (48, 55, 60, 63), (50, 57, 62, 66), (50, 57, 62, 66))


def chocalhos(b0, compassos, forca):
    for c in range(compassos):
        for s in range(16):
            acento = 1.0 if s % 4 == 2 else 0.62 if s % 2 == 0 else 0.34
            perc.por(CHOC_L if s % 4 == 2 else CHOC, b0 + c * 4 + s * 0.25,
                     forca * acento * rnd.uniform(0.88, 1.0), 0.35 if s % 2 else -0.2)


def maqsum(b0, compassos, forca=1.0, enfeite=False, bumbo_em=()):
    """D T . T D . T .  -- a levada do deserto, em colcheias."""
    for c in range(compassos):
        b = b0 + c * 4
        for col, som, g in ((0, DUM, 1.0), (1, TEK, 0.8), (3, TEK, 0.9), (4, DUM, 0.9), (6, TEK, 1.0)):
            perc.por(som, b + col * 0.5, forca * g, -0.1 if som is DUM else 0.15)
        if enfeite:
            for s in ((5, 11, 14, 15) if c % 2 else (5, 10, 15)):
                perc.por(KA, b + s * 0.25, forca * 0.5, 0.3)
        for k in bumbo_em:
            grave.por(bumbo(0.9), b + k, forca)


def virada(b0, forca=1.0):
    """Um compasso de rufo que cresce ate a parte seguinte."""
    for s in range(16):
        k = s / 15.0
        perc.por(TEK if s % 2 else KA, b0 + s * 0.25, forca * (0.35 + 0.65 * k), -0.4 + 0.8 * k)
    for s in range(8, 16, 2):
        perc.por(DUM, b0 + s * 0.25, forca * 0.7)
    fundo.por(sopro_de_areia(4), b0, 0.20 * forca)


def riffs(b0, compassos, forca, oitava=0, de=0):
    for c in range(compassos):
        for s, d, m in RIFFS[(de + c) % 4]:
            cordas.por(alaude(m + oitava, d * 0.25, 1.0), b0 + c * 4 + s * 0.25, forca,
                       -0.25)


def linha_de_baixo(b0, compassos, forca):
    for c in range(compassos):
        r = RAIZES[c % 4]
        for col, m in ((0, r), (3, r), (4, r + 7 if c % 4 != 3 else 38), (7, r + 12 if c % 2 else r)):
            grave.por(baixo(m, 0.5 if col != 0 else 0.9), b0 + c * 4 + col * 0.5, forca)


def melodia(b0, linhas, forca, oitava=0, dobra=False):
    antes = None
    for c, linha in enumerate(linhas):
        for ini, dur, m in linha:
            sopros.por(flauta(m + oitava, dur * 0.96, 1.0, antes), b0 + c * 4 + ini, forca, 0.2)
            if dobra:
                sopros.por(flauta(m + oitava - 12, dur * 0.96, 0.6), b0 + c * 4 + ini, forca, -0.3)
            antes = m + oitava


# o bordao atravessa a faixa (Re e La), mais baixo quando a levada esta cheia
for b0, dur, g in ((INTRO, A - INTRO, 1.0), (A, B - A, 0.55), (B, A2 - B, 0.9), (A2, GOLPE - A2, 0.55)):
    fundo.por(bordao(38, dur), b0, 0.085 * g)
    fundo.por(bordao(45, dur), b0, 0.05 * g, 0.3)

# INTRODUCAO (4 compassos): chocalho e pandeiro; o alaude chega no segundo,
# e o rufo do ultimo leva a levada
chocalhos(INTRO, 4, 0.30)
for c in range(4):
    perc.por(DUM, INTRO + c * 4, 0.75)
    perc.por(DUM, INTRO + c * 4 + 2, 0.5)
    if c >= 1:
        perc.por(KA, INTRO + c * 4 + 1, 0.5, 0.2)
        perc.por(KA, INTRO + c * 4 + 3, 0.6, 0.2)
        perc.por(platinela(0.35), INTRO + c * 4 + 3.5, 1.0, 0.3)
riffs(INTRO + 4, 2, 0.34)
virada(A - 4, 0.9)

# PARTE A (12 compassos): a levada inteira; a flauta entra no quinto
chocalhos(A, 12, 0.36)
maqsum(A, 12, 1.0, enfeite=False, bumbo_em=(0, 2))
for c in range(12):
    for k in range(4):
        perc.por(platinela(0.26), A + c * 4 + k + 0.5, 1.0, 0.35)
riffs(A, 12, 0.36)
linha_de_baixo(A, 12, 0.50)
melodia(A + 16, MELODIA, 0.30)
fundo.por(gongo(), A, 0.20)
virada(B - 4, 0.8)

# PARTE B (12 compassos): a quebra. So o pandeiro marca; flauta grave e arpejos
chocalhos(B, 8, 0.22)
for c in range(8):
    b = B + c * 4
    perc.por(DUM, b, 0.85)
    perc.por(KA, b + 1.5, 0.55, 0.25)
    perc.por(DUM, b + 2, 0.45)
    perc.por(TEK, b + 3, 0.6, 0.2)
    ac = ACORDES_B[c]
    for k, i in enumerate((0, 1, 2, 3, 1, 2, 3, 2)):
        cordas.por(alaude(ac[i], 0.5), b + k * 0.5, 0.26, -0.25 + 0.06 * k)
    grave.por(baixo(ac[0] - 12, 1.8), b, 0.42)
    grave.por(baixo(ac[0] - 12, 0.9), b + 2.5, 0.30)
melodia(B, MELODIA_B, 0.34)
fundo.por(gongo(), B, 0.16)
# a subida (4 compassos): o alaude em tremolo sobe a escala, o chocalho aperta,
# e a ultima batida e silencio -- o Leo cruza o desfiladeiro e pousa no golpe
for c, m in enumerate((63, 67, 69, 70)):
    b = SUBIDA + c * 4
    for s in range(16):
        if c == 3 and s >= 12:
            break                                  # o respiro antes do golpe
        cordas.por(alaude(m if s % 4 else m + 12, 0.25), b + s * 0.25,
                   0.20 + 0.05 * c + (0.06 if s % 4 == 0 else 0.0), -0.2)
    for k in range(4 if c < 2 else 8):
        if not (c == 3 and k >= 6):
            perc.por(DUM, b + k * (1.0 if c < 2 else 0.5), 0.5 + 0.1 * c)
    grave.por(baixo((39, 39, 38, 38)[c], 3.6), b, 0.42)
chocalhos(SUBIDA, 4, 0.34)
sopros.por(flauta(74, 11.0, 1.0), SUBIDA + 4, 0.16, 0.2)
fundo.por(sopro_de_areia(12), SUBIDA + 3, 0.24)

# PARTE A' (12 compassos): tudo de novo, oitava acima, com palmas e a darbuka
# solta; a melodia inteira e, nos 4 ultimos compassos, a sua resposta
chocalhos(A2, 12, 0.40)
maqsum(A2, 12, 1.05, enfeite=True, bumbo_em=(0, 1, 2, 3))
for c in range(12):
    b = A2 + c * 4
    perc.por(palma(), b + 1, 0.9, 0.1)
    perc.por(palma(), b + 3, 1.0, -0.1)
    for k in range(4):
        perc.por(platinela(0.30), b + k + 0.5, 1.0, 0.35)
riffs(A2, 12, 0.36)
riffs(A2 + 16, 8, 0.17, oitava=12)
linha_de_baixo(A2, 12, 0.54)
melodia(A2, MELODIA, 0.27, dobra=True)
melodia(A2 + 32, MELODIA[4:], 0.29, oitava=0, dobra=True)
fundo.por(gongo(), A2, 0.26)
virada(GOLPE - 4, 1.0)

# o golpe final e a cauda
fundo.por(gongo(), GOLPE, 0.5)
perc.por(DUM, GOLPE, 1.3)
perc.por(palma(), GOLPE, 1.0)
grave.por(baixo(26, 6.0), GOLPE, 0.6)
cordas.por(alaude(50, 6.0), GOLPE, 0.5)
cordas.por(alaude(62, 6.0), GOLPE + 0.02, 0.4, 0.2)
sopros.por(flauta(74, 5.0), GOLPE, 0.26)
for s in range(24):
    perc.por(CHOC, GOLPE + 0.5 + s * 0.25, 0.3 * (1 - s / 24.0) ** 1.5, 0.3)


# -------------------------------------------------------------------- mixagem
def eco_de_sala(x, molhado):
    """Reverberacao curta: convolucao com um ruido que decai."""
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    ri = filtro(rnd.standard_normal(n), 250, 6000, 0.5) * np.exp(-t / 0.42)
    ri[:int(0.012 * SR)] = 0.0
    ri /= np.sqrt(np.sum(ri ** 2))
    tam = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, tam) * np.fft.rfft(ri, tam), tam)[:len(x)]
    return x + y * molhado


def somar():
    canais = []
    for lado in ("e", "d"):
        x = (getattr(perc, lado) * 0.62
             + getattr(grave, lado) * 0.56
             + eco_de_sala(getattr(cordas, lado), 0.30) * 1.9
             + eco_de_sala(getattr(sopros, lado), 0.55) * 1.0
             + eco_de_sala(getattr(fundo, lado), 0.35) * 0.8
             + eco_de_sala(getattr(perc, lado), 1.0) * 0.07)
        canais.append(x)
    x = np.stack(canais, axis=1)
    x = filtro(x[:, 0], 28, None), filtro(x[:, 1], 28, None)
    x = np.stack(x, axis=1)
    x /= np.percentile(np.abs(x), 99.9)
    x = np.tanh(x * 1.5) / np.tanh(1.5)            # o limitador: cola a mixagem
    x *= 0.89 / np.max(np.abs(x))
    # fade no fim da cauda
    f = int(1.5 * SR)
    x[-f:] *= np.linspace(1.0, 0.0, f)[:, None]
    return x


def main():
    x = somar()
    wav = SAIDA[:-4] + ".tmp.raw"
    (x * 32767.0).astype("<i2").tofile(wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2",
                    "-i", wav, "-codec:a", "libmp3lame", "-b:a", "192k",
                    "-metadata", "title=Chocalho das Dunas", "-metadata", "artist=Rhythm Striker",
                    SAIDA], check=True)
    os.remove(wav)
    print(f"{SAIDA}  {len(x) / SR:.1f}s  batida 0 em {ENTRADA:.3f}s  {BPM:g} BPM")


if __name__ == "__main__":
    sys.exit(main())
