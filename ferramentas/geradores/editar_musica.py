"""
Edita uma faixa licenciada para uma fase mais curta: corta compassos inteiros
e emenda o resto, sem mexer no andamento.

    ./.venv/bin/python ferramentas/geradores/editar_musica.py bosque

A faixa original fica em ferramentas/musica_fonte/<cancao>.mp3 (copiada de
assets/music na primeira vez) e a editada vai para assets/music/<cancao>.mp3,
que e a que o jogo toca.

Cada corte e um intervalo de compassos da faixa original [de, ate) que sai.
Os cortes caem exatamente na batida forte, e cada emenda tem uma transicao
de 12 ms antes dela (o trecho que sai some enquanto o que entra aparece).
Como se tiram compassos inteiros, a grade de batidas segue exata depois de
cada emenda: o offset e o andamento em jogo/audio.py continuam valendo, e
`compasso_inicial` continua contado na faixa editada.

Os compassos sao os do ARQUIVO. O jogo abre o audio a 44,1 kHz; uma faixa de
48 kHz e convertida pelo SDL e toca um pouco mais rapido (a Cruising: 84 BPM
no arquivo, 84,105 em jogo -- o andamento de jogo/audio.py e o medido em
jogo). Por isso a velocidade e medida como o jogo toca (`_velocidade`) e os
cortes caem na grade do arquivo: andamento do jogo / velocidade.

Nao precisa de numpy: o audio passa como PCM de 16 bits pelo ffmpeg.
"""

import array
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from jogo.audio import TRILHAS  # noqa: E402

FONTE = os.path.join(RAIZ, "ferramentas", "musica_fonte")
SAIDA = os.path.join(RAIZ, "assets", "music")
CANAIS = 2
TRANSICAO = 0.012          # segundos

# os compassos (da faixa ORIGINAL) que saem: [de, ate)
CORTES = {
    # Cruising: intro 0-2, A 3-18, B 19-34, A' 35-50. Ficam a intro, 12
    # compassos do A (3-14), metade da quebra (19-26) e o fim do A' (43-50)
    "bosque": ((15, 19), (27, 43)),
    # Castle: a subida 8-15, o drop 16-31, o balanco 32-39, a quebra 40-47, o
    # segundo drop 48-63 e o fim. Sai o balanco (a corrida sem o portal)
    "ilhas": ((32, 40),),
    # Ark: a levada 16-32, a descida 33-39, o primeiro drop 40-55, o pos-drop
    # 56-63, a quebra 64-79, o segundo drop 80-95, o pos-drop 96-103. Sai o
    # primeiro pos-drop
    "eclipse": ((56, 64),),
}


def _taxa(caminho):
    """
    A taxa de amostragem da faixa. A editada fica NA MESMA taxa da original:
    o conversor de taxa do SDL nao e exato (cerca de 0,05%), e uma faixa
    convertida escorrega dezenas de milissegundos da grade ao longo da fase.
    """
    return int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                               "stream=sample_rate", "-of", "csv=p=0", caminho],
                              capture_output=True, check=True, text=True).stdout.strip())


def _velocidade(caminho):
    """Quanto mais rapido que o arquivo a faixa toca no jogo (mixer de 44,1 kHz, como o PPlay abre)."""
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", caminho], capture_output=True, check=True,
                               text=True).stdout)
    return dur / pygame.mixer.Sound(caminho).get_length()


def _pcm(caminho, taxa):
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", caminho, "-f", "s16le", "-ac", str(CANAIS),
                            "-ar", str(taxa), "-"], capture_output=True, check=True).stdout
    return array.array("h", bruto)


def editar(cancao):
    os.makedirs(FONTE, exist_ok=True)
    original = os.path.join(FONTE, f"{cancao}.mp3")
    if not os.path.exists(original):
        shutil.copy2(os.path.join(SAIDA, f"{cancao}.mp3"), original)
    tr = TRILHAS[cancao]
    velocidade = _velocidade(original)
    compasso = 4 * 60.0 / (tr.bpm / velocidade)       # no tempo do ARQUIVO
    # a ancora e onde a fase comeca no arquivo (trilha.inicio, o compasso
    # `compasso_inicial`); dali, a grade do arquivo
    no_arquivo = lambda n: tr.inicio + (n - tr.compasso_inicial) * compasso   # noqa: E731
    taxa = _taxa(original)
    pcm = _pcm(original, taxa)
    quadros = len(pcm) // CANAIS
    _amostra = lambda segundo: int(round(segundo * taxa))   # noqa: E731 -- o quadro mais proximo
    d = _amostra(TRANSICAO)

    # os trechos que ficam, em quadros: [0, corte1) [fim1, corte2) ... [fimN, fim)
    trechos, a = [], 0
    for de, ate in CORTES[cancao]:
        trechos.append((a, _amostra(no_arquivo(de))))
        a = _amostra(no_arquivo(ate))
    trechos.append((a, quadros))

    saida = array.array("h")
    for k, (q0, q1) in enumerate(trechos):
        ini = q0 if k == 0 else q0          # o trecho entra inteiro na batida forte
        fim = q1 if k == len(trechos) - 1 else q1 - d
        saida.extend(pcm[ini * CANAIS:fim * CANAIS])
        if k < len(trechos) - 1:
            # a transicao: o fim deste trecho sai, os 12 ms antes do proximo entram
            p0 = trechos[k + 1][0] - d
            for i in range(d):
                w = (i + 0.5) / d
                for c in range(CANAIS):
                    x = pcm[(fim + i) * CANAIS + c] * (1 - w) + pcm[(p0 + i) * CANAIS + c] * w
                    saida.append(max(-32768, min(32767, int(round(x)))))

    destino = os.path.join(SAIDA, f"{cancao}.mp3")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(taxa), "-ac", str(CANAIS),
                    "-i", "-", "-codec:a", "libmp3lame", "-b:a", "320k", destino],
                   input=saida.tobytes(), check=True)
    tirados = sum(ate - de for de, ate in CORTES[cancao])
    print(f"{cancao}: {quadros / taxa:.1f}s -> {len(saida) // CANAIS / taxa:.1f}s "
          f"({tirados} compassos a menos, {taxa} Hz, toca a {velocidade:.5f}x)  {destino}")


if __name__ == "__main__":
    for nome in sys.argv[1:] or list(CORTES):
        editar(nome)
