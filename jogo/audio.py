"""
Audio: a trilha de cada fase e os efeitos sonoros.

As faixas sao da NCS (NoCopyrightSounds) e ficam em assets/music/. A fase e
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
EFEITOS = ("pulo", "perfeito", "bom", "erro", "ponte", "quebra",
           "vitoria", "morte", "clique", "navegar")


class Trilha:
    """Uma faixa da NCS: creditos, andamento e onde a fase entra nela."""

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
    # A fase 1 roda na metade do andamento (75 em vez de 150) para o tutorial
    # ter quase um segundo entre pulos. Como e divisao exata, continua no ritmo.
    "bosque": Trilha("About You", "Ascence", bpm=150, offset=0.023,
                     bpm_grade=75, compasso_inicial=9),
    "ilhas": Trilha("Heroes Tonight (feat. Johnning)", "Janji", bpm=128,
                    offset=0.651, bpm_grade=128, compasso_inicial=24),
    "eclipse": Trilha("Nekozilla", "Different Heaven", bpm=128, offset=0.081,
                      bpm_grade=128, compasso_inicial=20),
}


class Audio:
    def __init__(self):
        self.ligado = False
        self.sons = {}
        self.tocando = False

    def iniciar(self):
        try:
            SoundManager.inicializar()
            self.ligado = pygame.mixer.get_init() is not None
        except pygame.error as erro:
            print(f"[audio] sem mixer ({erro}); o jogo roda em silencio")
            return
        for nome in EFEITOS:
            som = Sound(os.path.join(DIR_SFX, f"{nome}.wav"))
            som.set_volume(VOLUME_SFX * 100)
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
        pygame.mixer.music.set_volume(VOLUME_MUSICA)
        pygame.mixer.music.play(start=TRILHAS[cancao].inicio)
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
