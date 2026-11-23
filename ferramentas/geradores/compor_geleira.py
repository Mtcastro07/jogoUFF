"""
Compoe, por sintese, a trilha ORIGINAL da Geleira da Aurora: 128 BPM cravados,
Si menor (Bm - G - D - A), um trance de cristal: bumbo reto, baixo no
contratempo, serras desafinadas, arpejo de vidro e um sino em FM no lugar da voz.

    python3 ferramentas/geradores/compor_geleira.py      (precisa de numpy e ffmpeg)

A faixa e escrita na mesma grade de batidas da fase: a batida 0 cai em
ENTRADA segundos do arquivo (audio.TRILHAS["geleira"].offset).

    batidas   0- 32   introducao   o pad e o arpejo abafado; o bumbo chega no 16
             32- 96   A            a levada inteira; o sino canta a partir do 64
             96-144   B            a quebra: sem bumbo, o sino sozinho; a subida (128)
            144-208   A'           o drop, com o sino uma oitava acima
            208       o golpe final

A faixa ja teve 288 batidas (8+24+16+24 compassos); o A e o A' cairam para 16
compassos e a quebra para 12, para a fase durar cerca de 1min40.
"""

import os
import subprocess
import sys

import numpy as np

SR = 44100
BPM = 128.0
BATIDA = 60.0 / BPM
ENTRADA = 0.100
TOTAL_BATIDAS = 208
# onde cada parte comeca, em batidas
A, B, SUBIDA, A2, GOLPE = 32, 96, 128, 144, 208
FIM = ENTRADA + (TOTAL_BATIDAS + 12) * BATIDA + 2.0
N = int(FIM * SR)
rnd = np.random.default_rng(128)

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAIDA = os.path.join(RAIZ, "assets", "music", "geleira.mp3")


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
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    m = np.ones_like(f)
    if baixo:
        m *= 1.0 / (1.0 + (baixo / np.maximum(f, 1e-6)) ** (2.0 / suave))
    if alto:
        m *= 1.0 / (1.0 + (f / alto) ** (2.0 / suave))
    return np.fft.irfft(X * m, len(x))


def serra(f, t, fase=0.0):
    """Dente de serra com poucos harmonicos (sem o chiado do aliasing)."""
    x = np.zeros_like(t)
    for h in range(1, int(min(40, 9000 / f)) + 1):
        x += np.sin(2 * np.pi * f * h * t + fase * h) / h
    return x * 0.6


# ------------------------------------------------------------- instrumentos
def bumbo(forca=1.0):
    n = int(0.36 * SR)
    t = np.arange(n) / SR
    f = 48.0 + 150.0 * np.exp(-t / 0.028)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.15)
    x += filtro(rnd.standard_normal(n), 1500, 6000) * np.exp(-t / 0.004) * 0.4
    return np.tanh(x * 1.6) * forca


def palma(forca=1.0):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for atraso in (0.0, 0.009, 0.018, 0.026):
        k = int(atraso * SR)
        x[k:] += filtro(rnd.standard_normal(n), 1100, 5200)[:n - k] * np.exp(-t[:n - k] / 0.045)
    return x * forca * 0.45


def chimbal(forca=1.0, aberto=False):
    n = int((0.22 if aberto else 0.05) * SR)
    t = np.arange(n) / SR
    x = filtro(rnd.standard_normal(n), 7500, 16000, 0.4)
    return x * np.exp(-t / (0.07 if aberto else 0.012)) * forca


def caixa(forca=1.0):
    n = int(0.18 * SR)
    t = np.arange(n) / SR
    tom = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04)
    x = filtro(rnd.standard_normal(n), 1800, 9000) * np.exp(-t / 0.05)
    return (tom * 0.5 + x) * forca * 0.5


def baixo(midi, dur):
    n = int((dur * BATIDA + 0.03) * SR)
    t = np.arange(n) / SR
    f = hz(midi)
    x = serra(f, t) * 0.7 + np.sin(2 * np.pi * f * t) * 0.8
    e = np.minimum(1.0, t / 0.004) * np.exp(-t / 0.18)
    e *= np.where(t > dur * BATIDA, np.exp(-(t - dur * BATIDA) / 0.01), 1.0)
    return np.tanh(x * e * 1.3)


def sub(midi, dur):
    n = int((dur * BATIDA + 0.05) * SR)
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / 0.01) * np.where(t > dur * BATIDA, np.exp(-(t - dur * BATIDA) / 0.02), 1.0)
    return np.sin(2 * np.pi * hz(midi) * t) * e


_pads = {}


def pad(notas, dur):
    """Serras desafinadas (7 por nota), abafadas: o gelo que respira."""
    chave = (tuple(notas), dur)
    if chave in _pads:
        return _pads[chave]
    n = int((dur * BATIDA + 0.4) * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in notas:
        for k, des in enumerate((-0.11, -0.07, -0.03, 0.0, 0.03, 0.07, 0.11)):
            x += serra(hz(m + des), t, k * 1.7)
    x = filtro(x, 120, 3200, 0.4) / (len(notas) * 4.0)
    e = np.minimum(1.0, t / 0.25) * np.where(t > dur * BATIDA, np.exp(-(t - dur * BATIDA) / 0.15), 1.0)
    _pads[chave] = x * e
    return _pads[chave]


def pluck(midi, forca=1.0, brilho=1.0):
    """O arpejo de vidro: serra curta com o filtro fechando depressa."""
    n = int(0.32 * SR)
    t = np.arange(n) / SR
    f = hz(midi)
    x = np.zeros(n)
    for h in range(1, 14):
        corte = np.exp(-t / (0.03 + 0.05 * brilho)) * 14 + 1.2
        x += np.sin(2 * np.pi * f * h * t) / h * np.clip(corte - h, 0.0, 1.0)
    return x * np.exp(-t / 0.13) * forca * 0.5


def sino(midi, dur, forca=1.0):
    """O sino em FM: o ataque de vidro, e o corpo que canta a nota."""
    n = int((dur * BATIDA + 0.6) * SR)
    t = np.arange(n) / SR
    f = hz(midi)
    indice = 2.6 * np.exp(-t / 0.18) + 0.5
    x = np.sin(2 * np.pi * f * t + indice * np.sin(2 * np.pi * f * 3.5 * t))
    x += 0.35 * np.sin(2 * np.pi * f * 2 * t + 0.8 * np.sin(2 * np.pi * f * t))
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1.0, t / 0.4)
    x += 0.25 * np.sin(2 * np.pi * f * vib * np.arange(n) / SR)
    e = np.minimum(1.0, t / 0.005) * (0.55 * np.exp(-t / 0.35) + 0.45)
    e *= np.where(t > dur * BATIDA, np.exp(-(t - dur * BATIDA) / 0.18), 1.0)
    return x * e * forca * 0.32


def subida(batidas):
    """O ruido que sobe ate o drop."""
    n = int(batidas * BATIDA * SR)
    k = np.linspace(0.0, 1.0, n)
    x = rnd.standard_normal(n)
    partes = []
    pedaco = n // 8
    for i in range(8):
        a, b = i * pedaco, (i + 1) * pedaco if i < 7 else n
        partes.append(filtro(x[a:b], 300 + 900 * i, 1500 + 1800 * i, 0.5))
    return np.concatenate(partes) * k ** 2


def impacto():
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    f = 34.0 + 70.0 * np.exp(-t / 0.08)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)
    x += filtro(rnd.standard_normal(n), 200, 5000) * np.exp(-t / 0.5) * 0.25
    return x


# ------------------------------------------------------------------ a faixa
ritmo, grave, harmonia, arpejo, voz, fundo = (Pista() for _ in range(6))

ACORDES = ((59, 62, 66), (55, 59, 62), (57, 62, 66), (57, 61, 64))      # Bm G D A
RAIZES = (35, 31, 38, 33)

MELODIA = (
    ((0, 1.5, 78), (1.5, 0.5, 74), (2, 1, 76), (3, 1, 78)),
    ((0, 1.5, 83), (1.5, 0.5, 81), (2, 2, 78)),
    ((0, 1, 81), (1, 1, 78), (2, 1, 76), (3, 1, 74)),
    ((0, 2, 76), (2, 1, 73), (3, 1, 76)),
    ((0, 1.5, 78), (1.5, 0.5, 74), (2, 1, 76), (3, 1, 78)),
    ((0, 1, 83), (1, 1, 85), (2, 2, 86)),
    ((0, 1, 85), (1, 1, 83), (2, 1, 81), (3, 1, 78)),
    ((0, 1.5, 76), (1.5, 0.5, 78), (2, 2, 73)),
)
MELODIA_B = (
    ((0, 3, 74), (3, 1, 73)), ((0, 4, 71),), ((0, 3, 69), (3, 1, 71)), ((0, 4, 73),),
    ((0, 3, 78), (3, 1, 76)), ((0, 4, 74),), ((0, 2, 73), (2, 2, 76)), ((0, 4, 78),),
)


def bumbos(b0, compassos, forca=1.0):
    for c in range(compassos):
        for k in range(4):
            ritmo.por(bumbo(forca), b0 + c * 4 + k)


def levada(b0, compassos, forca=1.0, aberto=True):
    for c in range(compassos):
        b = b0 + c * 4
        ritmo.por(palma(), b + 1, forca, 0.05)
        ritmo.por(palma(), b + 3, forca, -0.05)
        for s in range(16):
            if s % 4 == 2 and aberto:
                ritmo.por(chimbal(0.55, True), b + s * 0.25, forca, 0.25)
            elif s % 2 == 1:
                ritmo.por(chimbal(0.42), b + s * 0.25, forca, 0.3)
            else:
                ritmo.por(chimbal(0.2), b + s * 0.25, forca, -0.2)


def baixos(b0, compassos, forca=1.0):
    for c in range(compassos):
        r = RAIZES[c % 4]
        for k in range(4):
            grave.por(baixo(r + 12, 0.42), b0 + c * 4 + k + 0.5, forca)
            grave.por(sub(r, 0.45), b0 + c * 4 + k + 0.5, forca * 0.6)


def pads(b0, compassos, forca=1.0):
    for c in range(compassos):
        ac = ACORDES[c % 4]
        harmonia.por(pad(ac + (ac[0] + 12,), 4), b0 + c * 4, forca)


def arpejos(b0, compassos, forca=1.0, brilho=1.0, oitava=12):
    padrao = (0, 1, 2, 3, 2, 1, 2, 3, 0, 1, 2, 3, 4, 3, 2, 1)
    for c in range(compassos):
        ac = ACORDES[c % 4]
        tons = (ac[0], ac[1], ac[2], ac[0] + 12, ac[1] + 12)
        for s, i in enumerate(padrao):
            arpejo.por(pluck(tons[i] + oitava, 1.0, brilho), b0 + c * 4 + s * 0.25,
                       forca * (1.0 if s % 4 == 0 else 0.75), -0.35 + 0.7 * ((s * 5) % 16) / 15.0)


def melodia(b0, linhas, forca, oitava=0):
    for c, linha in enumerate(linhas):
        for ini, dur, m in linha:
            voz.por(sino(m + oitava, dur * 0.95), b0 + c * 4 + ini, forca, 0.15)


def bombear(pista, b0, b1, fundo_=0.35):
    """O 'sidechain': cada bumbo afunda o resto e ele volta antes da proxima batida."""
    for b in range(b0, b1):
        a, z = pos(b), min(N, pos(b + 1))
        t = np.arange(z - a) / SR
        k = 1.0 - (1.0 - fundo_) * np.exp(-t / 0.09)
        pista.e[a:z] *= k
        pista.d[a:z] *= k


# INTRODUCAO (0-32): o pad e o arpejo abafado; o bumbo chega no 16
pads(0, 8, 0.8)
arpejos(0, 8, 0.32, brilho=0.25)
bumbos(16, 4, 0.8)
for c in range(4):
    ritmo.por(chimbal(0.4, True), 16 + c * 4 + 2.5, 1.0, 0.3)
fundo.por(subida(8), 24, 0.25)

# PARTE A (16 compassos): a levada inteira; o sino entra no nono
bumbos(A, 16)
levada(A, 16)
baixos(A, 16)
pads(A, 16, 0.55)
arpejos(A, 16, 0.40, brilho=1.0)
melodia(A + 32, MELODIA, 0.95)
fundo.por(impacto(), A, 0.55)
fundo.por(subida(4), B - 4, 0.22)

# PARTE B (12 compassos): a quebra, sem bumbo; o sino sozinho sobre o pad
pads(B, 12, 0.9)
arpejos(B, 8, 0.24, brilho=0.4, oitava=24)
melodia(B, MELODIA_B, 0.85)
fundo.por(impacto(), B, 0.4)
for c in range(4):
    grave.por(sub(RAIZES[c % 4], 7.5), B + c * 8, 0.55)
# a subida (4 compassos): a caixa aperta, o arpejo abre, o ruido cresce; o respiro no fim
for c in range(4):
    b = SUBIDA + c * 4
    passo = (1.0, 0.5, 0.25, 0.125)[c]
    k = 0
    while k * passo < 4 - (1.0 if c == 3 else 0.0):
        ritmo.por(caixa(0.4 + 0.15 * c + 0.1 * (k * passo / 4)), b + k * passo, 1.0, 0.1)
        k += 1
arpejos(SUBIDA, 3, 0.36, brilho=1.2)
melodia(SUBIDA, MELODIA_B[4:7], 0.8, oitava=12)
fundo.por(subida(15), SUBIDA, 0.42)

# PARTE A' (16 compassos): o drop, o sino uma oitava acima; na segunda volta,
# dobrado nas duas oitavas
bumbos(A2, 16, 1.05)
levada(A2, 16, 1.05)
baixos(A2, 16, 1.05)
pads(A2, 16, 0.6)
arpejos(A2, 16, 0.42, brilho=1.2)
melodia(A2, MELODIA, 0.85, oitava=12)
melodia(A2 + 32, MELODIA, 0.9)
melodia(A2 + 32, MELODIA, 0.55, oitava=12)
fundo.por(impacto(), A2, 0.7)
fundo.por(subida(4), GOLPE - 4, 0.25)

# o golpe final e a cauda
fundo.por(impacto(), GOLPE, 0.9)
ritmo.por(bumbo(1.2), GOLPE)
ritmo.por(palma(1.0), GOLPE)
ritmo.por(chimbal(0.8, True), GOLPE)
harmonia.por(pad((59, 62, 66, 71), 7), GOLPE, 0.9)
voz.por(sino(83, 5), GOLPE, 0.8)
voz.por(sino(78, 5), GOLPE + 0.02, 0.5)
grave.por(sub(35, 6), GOLPE, 0.8)

# o bombeado das partes com bumbo
for pista in (grave, harmonia, arpejo):
    bombear(pista, 16, A, 0.6)
    bombear(pista, A, B)
    bombear(pista, A2, GOLPE)


# -------------------------------------------------------------------- mixagem
def eco(x, molhado, cauda=0.55, pre=0.02):
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    ri = filtro(rnd.standard_normal(n), 300, 7000, 0.5) * np.exp(-t / cauda)
    ri[:int(pre * SR)] = 0.0
    ri /= np.sqrt(np.sum(ri ** 2))
    tam = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, tam) * np.fft.rfft(ri, tam), tam)[:len(x)]
    return x + y * molhado


def atraso(x, batidas, volta=0.35):
    """O eco em colcheia pontuada do arpejo e do sino."""
    k = int(batidas * BATIDA * SR)
    y = x.copy()
    for i in range(1, 4):
        y[k * i:] += x[:-k * i] * volta ** i
    return y


def somar():
    canais = []
    for lado, outro in (("e", "d"), ("d", "e")):
        arp = atraso(getattr(arpejo, lado), 0.75) * 0.8 + atraso(getattr(arpejo, outro), 0.75) * 0.2
        x = (getattr(ritmo, lado) * 0.80
             + getattr(grave, lado) * 0.62
             + eco(getattr(harmonia, lado), 0.6, 0.9) * 0.62
             + eco(arp, 0.4) * 1.0
             + eco(atraso(getattr(voz, lado), 0.75, 0.25), 0.6, 0.8) * 0.95
             + eco(getattr(fundo, lado), 0.4) * 0.9)
        canais.append(x)
    x = np.stack([filtro(c, 25, None) for c in canais], axis=1)
    x /= np.percentile(np.abs(x), 99.9)
    x = np.tanh(x * 1.5) / np.tanh(1.5)
    x *= 0.89 / np.max(np.abs(x))
    f = int(1.5 * SR)
    x[-f:] *= np.linspace(1.0, 0.0, f)[:, None]
    return x


def main():
    x = somar()
    bruto = SAIDA[:-4] + ".tmp.raw"
    (x * 32767.0).astype("<i2").tofile(bruto)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2",
                    "-i", bruto, "-af", "volume=-2.5dB", "-codec:a", "libmp3lame", "-b:a", "192k",
                    "-metadata", "title=Aurora de Cristal", "-metadata", "artist=Rhythm Striker",
                    SAIDA], check=True)
    os.remove(bruto)
    print(f"{SAIDA}  {len(x) / SR:.1f}s  batida 0 em {ENTRADA:.3f}s  {BPM:g} BPM")


if __name__ == "__main__":
    sys.exit(main())
