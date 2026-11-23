"""
Audio: a trilha de cada fase e os efeitos sonoros.

As faixas sao da NCS (NoCopyrightSounds) -- menos as das dunas e da geleira, que
sao originais, compostas para o jogo -- e ficam em assets/music/. A fase e
uma grade de batidas que comeca no tempo 0, mas a musica tem uma introducao:
`offset` e o segundo da primeira batida forte e `compasso_inicial` quantos
compassos de 4 batidas pulamos antes de a fase comecar. A regra e uma so:

    segundo da musica = trilha.inicio + tempo de jogo

Os efeitos sonoros sao arquivos .wav curtos em assets/sfx/.
"""

import os

import pygame
from PPlay.sound import Sound, SoundManager

from .config import DIR_MUSICA, DIR_SFX, VOLUME_MUSICA, VOLUME_SFX

AVISO_NCS = "Music provided by NoCopyrightSounds - ncs.io"
EFEITOS = ("pulo", "perfeito", "bom", "erro", "quebra",
           "vitoria", "morte", "clique", "navegar", "mola", "orbe", "eco")


class Trilha:
    """Uma faixa: creditos, andamento e onde a fase entra nela."""

    def __init__(self, titulo, artista, bpm, offset, bpm_grade, compasso_inicial):
        self.titulo = titulo
        self.artista = artista
        self.bpm = bpm                        # andamento real da faixa
        self.offset = offset                  # segundo da 1a batida forte
        self.bpm_grade = bpm_grade            # andamento em que a fase e escrita
        self.compasso_inicial = compasso_inicial

    @property
    def inicio(self):
        """Segundo da faixa em que a batida 0 da fase acontece."""
        return self.offset + self.compasso_inicial * 4 * 60.0 / self.bpm

    @property
    def creditos(self):
        return f"{self.artista} - {self.titulo}"


TRILHAS = {
    # O bosque (a fase que ensina) e a faixa mais calma possivel: lo-fi a
    # 84,105 BPM (medido: a 84 redondo a batida escorrega meio segundo ate o
    # fim). A faixa do jogo e uma EDICAO da original, para a primeira fase ser
    # curta (ferramentas/geradores/editar_musica.py; a original fica em
    # ferramentas/musica_fonte): sairam os compassos 15-18 e 27-42. Na faixa
    # editada: introducao (2), A com o grave (3-14), a quebra sem grave
    # (15-22) e o fim do A' (23-30). A fase entra no compasso 2.
    # O offset vai 7 ms adiante do medido (2,831): `inicio` conta os 2 compassos
    # a 84,105, e no arquivo eles sao de 84 (a faixa e de 48 kHz e toca 0,13%
    # mais rapido no mixer de 44,1 kHz).
    "bosque": Trilha("Cruising", "Dosi & Aisake", bpm=84.105, offset=2.838,
                     bpm_grade=84.105, compasso_inicial=2),
    # As dunas (96 BPM, entre o bosque e as ilhas) tem trilha ORIGINAL, composta
    # por sintese na mesma grade da fase (ferramentas/geradores/compor_dunas.py):
    # a batida 0 cai em 0,100 s do arquivo e o andamento e cravado. Introducao
    # (compassos 0-3), A com a levada inteira (4-15), B na quebra (16-27), A'
    # com palmas (28-39) e o golpe final na batida 160.
    "dunas": Trilha("Chocalho das Dunas", "Trilha original", bpm=96, offset=0.100,
                    bpm_grade=96, compasso_inicial=0),
    # As ilhas (110 BPM, a fase media do GDD) tocam uma EDICAO da faixa, sem o
    # "balanco" depois do primeiro drop (compassos 32-39 da original; veja
    # ferramentas/geradores/editar_musica.py). Na faixa editada: a fase entra
    # no fim da subida (compasso 12), A no primeiro drop (16), B na quebra
    # (32) e A' no segundo drop (40).
    "ilhas": Trilha("Castle", "Clarx & Harddope", bpm=110, offset=0.530,
                    bpm_grade=110, compasso_inicial=12),
    # A geleira (128 BPM, entre as ilhas e a cidadela) tambem tem trilha
    # ORIGINAL (ferramentas/geradores/compor_geleira.py), um trance de cristal
    # na grade da fase: introducao (compassos 0-7), A (8-23), B na quebra sem
    # bumbo (24-35, com a subida no 32), A' no drop (36-51), golpe na batida 208.
    "geleira": Trilha("Aurora de Cristal", "Trilha original", bpm=128, offset=0.100,
                      bpm_grade=128, compasso_inicial=0),
    # A cidadela (150 BPM, a final) e sombria e epica. A faixa do jogo e uma
    # EDICAO da original sem o pos-drop do primeiro drop (compassos 56-63; veja
    # ferramentas/geradores/editar_musica.py). Na faixa editada: a fase entra
    # na descida que prepara o drop (compasso 32), A no primeiro drop (40-55),
    # B na quebra (56-71), A' no segundo drop (72-87) e no pos-drop ate o fim.
    "eclipse": Trilha("Ark", "Ship Wrek & Zookeepers", bpm=150, offset=0.078,
                      bpm_grade=150, compasso_inicial=32),
}


class Audio:
    def __init__(self):
        self.ligado = False
        self.sons = {}
        self.tocando = False
        self.vol_musica = 1.0     # 0..1, da tela de opcoes (multiplica o volume da config)
        self.vol_sfx = 1.0        # os efeitos tocam sempre no volume da config
        self.atraso = 0.0         # a musica entra exatamente no inicio da fase

    def aplicar(self, opcoes):
        """Poe em uso a unica opcao do jogador (save.opcoes): o volume da musica.
        Os efeitos e o atraso do audio nao sao mais ajustaveis -- um valor antigo
        que tenha ficado no save e ignorado."""
        self.vol_musica = opcoes["musica"] / 10.0
        if self.ligado:
            pygame.mixer.music.set_volume(VOLUME_MUSICA * self.vol_musica)

    def iniciar(self):
        try:
            SoundManager.inicializar()
            self.ligado = pygame.mixer.get_init() is not None
        except pygame.error as erro:
            print(f"[audio] sem mixer ({erro}); o jogo roda em silencio")
            return
        for nome in EFEITOS:
            caminho = os.path.join(DIR_SFX, f"{nome}.wav")
            if not os.path.exists(caminho):
                continue
            som = Sound(caminho)
            som.set_volume(VOLUME_SFX * self.vol_sfx * 100)
            self.sons[nome] = som

    def tocar(self, nome):
        if nome in self.sons:
            self.sons[nome].play()

    def tocar_musica(self, cancao):
        """Toca a faixa da fase a partir do instante em que a fase comeca."""
        self.tocando = False
        caminho = os.path.join(DIR_MUSICA, f"{cancao}.mp3")
        if not self.ligado or not os.path.exists(caminho):
            return
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.set_volume(VOLUME_MUSICA * self.vol_musica)
        pygame.mixer.music.play(start=max(0.0, TRILHAS[cancao].inicio + self.atraso))
        self.tocando = True

    def parar_musica(self):
        if self.tocando:
            pygame.mixer.music.fadeout(300)
        self.tocando = False

    def pausar_musica(self):
        if self.tocando:
            pygame.mixer.music.pause()

    def retomar_musica(self):
        if self.tocando:
            pygame.mixer.music.unpause()


audio = Audio()
