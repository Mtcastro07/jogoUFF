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
EFEITOS = ("pulo", "perfeito", "bom", "erro", "quebra",
           "vitoria", "morte", "clique", "navegar", "mola", "orbe", "eco")


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
    # O bosque (a fase que ensina) e a faixa mais calma possivel: lo-fi a
    # 84,105 BPM (medido: a 84 redondo a batida escorrega meio segundo ate o
    # fim). A fase entra no primeiro compasso: introducao (0-2), A com o
    # grave (3-18), B na quebra sem grave (19-34), A' com o grave de novo.
    "bosque": Trilha("Cruising", "Dosi & Aisake", bpm=84.105, offset=2.831,
                     bpm_grade=84.105, compasso_inicial=0),
    # As ilhas (110 BPM, a fase media do GDD) entram na subida da introducao
    # (compasso 8) e vao ate o fim da faixa: A no primeiro drop (compasso 16),
    # B na quebra (40), A' no segundo drop (48).
    "ilhas": Trilha("Castle", "Clarx & Harddope", bpm=110, offset=0.530,
                    bpm_grade=110, compasso_inicial=8),
    # A cidadela (150 BPM, a final) e sombria e epica: entra na segunda metade
    # da batida (compasso 24), A no primeiro drop (40), B na quebra (64), A'
    # no ultimo drop (80) e no fim da faixa.
    "eclipse": Trilha("Ark", "Ship Wrek & Zookeepers", bpm=150, offset=0.078,
                      bpm_grade=150, compasso_inicial=24),
}


class Audio:
    def __init__(self):
        self.ligado = False
        self.sons = {}
        self.tocando = False
        self.vol_musica = 1.0     # 0..1, da tela de opcoes (multiplica o volume da config)
        self.vol_sfx = 1.0
        self.atraso = 0.0         # segundos que o som demora a chegar ao ouvido

    def aplicar(self, opcoes):
        """Poe em uso as opcoes do jogador (save.opcoes): volumes e atraso do audio."""
        self.vol_musica = opcoes["musica"] / 10.0
        self.vol_sfx = opcoes["sfx"] / 10.0
        self.atraso = opcoes["atraso"] / 1000.0
        for som in self.sons.values():
            som.set_volume(VOLUME_SFX * self.vol_sfx * 100)
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
        # com o som chegando atrasado (fone sem fio, TV), a faixa entra adiantada
        # o mesmo tanto: o que se OUVE cai em cima do que se ve
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
