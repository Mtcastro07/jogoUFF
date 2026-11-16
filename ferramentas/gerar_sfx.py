"""
Gera os efeitos sonoros da mola, do orbe e do eco (assets/sfx/*.wav), so com a
biblioteca padrao: ondas simples com um envelope, no estilo 8 bits do jogo.

    ./.venv/bin/python ferramentas/gerar_sfx.py
"""

import math
import os
import struct
import wave

TAXA = 44100
DESTINO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "assets", "sfx")


def quadrada(fase, largura=0.5):
    return 1.0 if fase % 1.0 < largura else -1.0


def triangular(fase):
    return 4.0 * abs(fase % 1.0 - 0.5) - 1.0


def gravar(nome, dur, freq_de, onda, volume=0.5, ataque=0.005):
    """`freq_de(t)` da a frequencia no instante t (0..dur); o som some ate o fim."""
    n = int(dur * TAXA)
    fase, quadros = 0.0, bytearray()
    for i in range(n):
        t = i / TAXA
        fase += freq_de(t) / TAXA
        env = min(1.0, t / ataque) * (1.0 - t / dur) ** 1.6
        quadros += struct.pack("<h", int(32767 * volume * env * onda(fase)))
    with wave.open(os.path.join(DESTINO, f"{nome}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(bytes(quadros))


if __name__ == "__main__":
    # a mola: uma subida rapida de uma oitava e meia, um "boing" para cima
    gravar("mola", 0.26, lambda t: 220.0 * 2.0 ** (min(t, 0.16) / 0.16 * 1.6),
           lambda f: 0.6 * quadrada(f, 0.25) + 0.4 * triangular(f), 0.45)
    # o orbe: um sino de duas notas (quinta acima), limpo
    gravar("orbe", 0.30, lambda t: 880.0 if t < 0.06 else 1318.5, triangular, 0.55)
    # o eco: um pingo curto e agudo, que nao briga com o PERFEITO
    gravar("eco", 0.09, lambda t: 1760.0 if t < 0.03 else 2349.3, triangular, 0.35)
    print("ok")
