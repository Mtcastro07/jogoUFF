"""Mixa o audio do trailer: trechos das musicas, efeitos do jogo e sons de trailer sintetizados.
Uso: mix.py timeline.json saida.wav"""
import json, subprocess, sys, wave
import numpy as np
SR = 44100
tl = json.load(open(sys.argv[1]))
N = int(tl["dur"] * SR)
mix = np.zeros((N + SR * 3, 2), np.float32)
rng = np.random.default_rng(3)


def decode(path, ss=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{ss:.4f}", "-i", path]
    if dur:
        cmd += ["-t", f"{dur:.4f}"]
    cmd += ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()


def por(a, t, ganho=1.0):
    i = max(0, int(round(t * SR)))
    k = min(len(a), len(mix) - i)
    if k > 0:
        mix[i:i + k] += a[:k] * ganho


def caixa(x, n):
    c = np.cumsum(np.concatenate([np.zeros(1, x.dtype), x]))
    y = (c[n:] - c[:-n]) / n
    return np.pad(y, (0, len(x) - len(y)))


def estereo(m, pan=None):
    if pan is None:
        return np.stack([m, m], 1).astype(np.float32)
    return np.stack([m * np.sqrt(1 - pan), m * np.sqrt(pan)], 1).astype(np.float32)


def riser(dur):
    n = int(dur * SR); t = np.arange(n) / SR; k = t / dur
    ruido = rng.standard_normal(n).astype(np.float32)
    r = caixa(ruido, 48) * (1 - k) * 2.2 + (ruido - caixa(ruido, 6)) * k * 0.8
    f = 180 * (8 ** k)
    tom = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35 + np.sin(4 * np.pi * np.cumsum(f) / SR) * 0.12
    return estereo((r * 0.22 + tom) * k ** 2.2)


def boom(dur=1.8):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 72 * np.exp(-t * 7) + 38
    corpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    estalo = rng.standard_normal(n) * np.exp(-t * 60) * 0.6
    cauda = caixa(rng.standard_normal(n).astype(np.float32), 30) * np.exp(-t * 3.5) * 1.2
    return estereo(np.tanh((corpo * 1.3 + estalo + cauda) * 1.4))


def whoosh(dur):
    n = int(dur * SR); k = np.arange(n) / n
    ruido = rng.standard_normal(n).astype(np.float32)
    banda = caixa(ruido, 4) - caixa(ruido, 40)
    return estereo(banda * np.sin(np.pi * k) ** 2 * 0.9, pan=0.15 + 0.7 * k)


def glitch(dur):
    n = int(dur * SR); s = np.zeros(n, np.float32); i = 0
    while i < n:
        m = min(int(rng.uniform(0.015, 0.05) * SR), n - i)
        tt = np.arange(m) / SR
        if rng.random() < 0.55:
            s[i:i + m] = np.sign(np.sin(2 * np.pi * rng.uniform(180, 2400) * tt)) * 0.35
        elif rng.random() < 0.7:
            s[i:i + m] = np.round(rng.standard_normal(m) * 2) / 4 * 0.5
        i += m
    return estereo(s * np.linspace(1, 0.4, n))


def tick():
    n = int(0.03 * SR); t = np.arange(n) / SR
    r = rng.standard_normal(n).astype(np.float32)
    r = r - caixa(r, 5)
    return estereo(r * np.exp(-t * 260) * 0.7 + np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 400) * 0.3)


def coracao():
    n = int(0.6 * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for t0, a in ((0.0, 1.0), (0.2, 0.7)):
        d = np.clip(t - t0, 0, None)
        s += (t >= t0) * np.sin(2 * np.pi * (48 + 30 * np.exp(-d * 30)) * d) * np.exp(-d * 14) * a
    return estereo(np.tanh(s * 1.6))


def drone(dur):
    n = int(dur * SR); t = np.arange(n) / SR; k = t / dur
    s = np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t + 1) + 0.3 * np.sin(2 * np.pi * 110.7 * t)
    s *= 0.75 + 0.25 * np.sin(2 * np.pi * 3.1 * t)
    r = rng.standard_normal(n).astype(np.float32)
    s += (r - caixa(r, 3)) * 0.08
    return estereo(s * np.minimum(1, k / 0.1) * np.minimum(1, (1 - k) / 0.15) * 0.4)


def estatica(dur):
    """O chiado de TV fora do ar: ruido branco, um pouco aspero, que entra e sai rapido."""
    n = int(dur * SR); k = np.arange(n) / n
    r = rng.standard_normal(n).astype(np.float32)
    env = np.minimum(1, k / 0.05) * np.minimum(1, (1 - k) / 0.15)
    return estereo((r - caixa(r, 2)) * env * 0.6)


def abafar(a, vezes=3, n=14):
    """Passa-baixa simples (media movel repetida): o som que sai do alto-falante da TV."""
    for _ in range(vezes):
        a = np.stack([caixa(a[:, 0], n), caixa(a[:, 1], n)], 1)
    return a.astype(np.float32)


SINT = {"drone": lambda e: drone(e["dur"]), "riser": lambda e: riser(e["dur"]), "boom": lambda e: boom(),
        "whoosh": lambda e: whoosh(e["dur"]), "glitch": lambda e: glitch(e["dur"]), "tick": lambda e: tick(),
        "coracao": lambda e: coracao(), "estatica": lambda e: estatica(e["dur"])}
NIVEL = {"drone": 0.5, "riser": 0.5, "boom": 0.75, "whoosh": 0.35, "glitch": 0.3, "tick": 0.35, "coracao": 0.9, "estatica": 0.3}

for c in tl["musica"]:
    ts = c.get("tapestop", 0.0)
    a = decode(c["arquivo"], c["origem"], c["dur"] + ts)
    if c.get("abafado"):
        a = abafar(a)
    corpo = a[: int(c["dur"] * SR)]
    k = len(corpo)
    env = np.ones(k, np.float32)
    fi, fo = int(c["ent"] * SR), int(c["sai"] * SR)
    if 0 < fi <= k:
        env[:fi] = np.linspace(0, 1, fi)
    if 0 < fo <= k and not ts:
        env[k - fo:] *= np.linspace(1, 0, fo)
    corpo = corpo * env[:, None]
    if ts:
        m = int(ts * SR); i = np.arange(m)
        resto = a[k:] if len(a) - k > 2 else np.zeros((m, 2), np.float32)
        pos = np.clip(i - i ** 2 / (2 * m), 0, len(resto) - 2)
        j = pos.astype(int); fr = (pos - j)[:, None]
        freio = (resto[j] * (1 - fr) + resto[j + 1] * fr) * (np.linspace(1, 0, m)[:, None] ** 0.7)
        corpo = np.concatenate([corpo, freio.astype(np.float32)])
    por(corpo, c["t"], 0.78 * c.get("ganho", 1.0))

cache = {}
for t, nome in tl["sfx"]:
    if nome not in cache:
        cache[nome] = decode(f'{tl["sfx_dir"]}/{nome}.wav')
    por(cache[nome], t, 0.38)
for e in tl["synth"]:
    por(SINT[e["tipo"]](e), e["t"], NIVEL[e["tipo"]] * e.get("ganho", 1.0))

mix = mix[:N]
acima = np.abs(mix) > 0.8
mix[acima] = np.sign(mix[acima]) * (0.8 + 0.2 * np.tanh((np.abs(mix[acima]) - 0.8) / 0.2))
mix *= 0.89 / np.abs(mix).max()
j = int(0.25 * SR)
rms = np.sqrt((mix[: N // j * j].reshape(-1, j, 2) ** 2).mean(axis=(1, 2)))
print("trechos mudos (s):", [i * 0.25 for i, v in enumerate(rms) if 20 * np.log10(v + 1e-9) < -45])
w = wave.open(sys.argv[2], "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype("<i2").tobytes()); w.close()
