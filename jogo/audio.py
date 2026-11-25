import os

import pygame
from PPlay.sound import Music, Sound, SoundManager

from .config import PASTA_MUSICAS, PASTA_SONS, VOLUME_DAS_MUSICAS, VOLUME_DOS_SONS

SONS_DO_JOGO = ("pulo", "perfeito", "bom", "erro", "quebra",
                "vitoria", "morte", "clique", "navegar", "mola", "orbe", "eco")


class InfoDaMusica:
    def __init__(self, titulo, quem_canta, bpm_da_musica, offset, bpm_do_jogo, compasso_de_inicio):
        self.titulo = titulo
        self.quem_canta = quem_canta
        self.bpm_da_musica = bpm_da_musica
        self.offset = offset
        self.bpm_do_jogo = bpm_do_jogo
        self.compasso_de_inicio = compasso_de_inicio
        self.inicio = offset + compasso_de_inicio * 4 * 60.0 / bpm_da_musica
        self.creditos = f"{quem_canta} - {titulo}"


AS_MUSICAS = {
    "bosque": InfoDaMusica("Cruising", "Dosi & Aisake", bpm_da_musica=84.105, offset=2.838,
                           bpm_do_jogo=84.105, compasso_de_inicio=2),
    "dunas": InfoDaMusica("Chocalho das Dunas", "Trilha original", bpm_da_musica=96, offset=0.100,
                          bpm_do_jogo=96, compasso_de_inicio=0),
    "ilhas": InfoDaMusica("Castle", "Clarx & Harddope", bpm_da_musica=110, offset=0.530,
                          bpm_do_jogo=110, compasso_de_inicio=12),
    "geleira": InfoDaMusica("Aurora de Cristal", "Trilha original", bpm_da_musica=128, offset=0.100,
                            bpm_do_jogo=128, compasso_de_inicio=0),
    "eclipse": InfoDaMusica("Ark", "Ship Wrek & Zookeepers", bpm_da_musica=150, offset=0.078,
                            bpm_do_jogo=150, compasso_de_inicio=32),
}


class Musica(Music):
    def __init__(self, nome_da_musica):
        super().__init__(os.path.join(PASTA_MUSICAS, f"{nome_da_musica}.mp3"))
        self.inicio = AS_MUSICAS[nome_da_musica].inicio

    def play(self, volume, pula=0.0):
        pygame.mixer.music.load(self.caminho)
        SoundManager.set_music_volume(volume)
        pygame.mixer.music.play(start=max(0.0, self.inicio + pula))


class Barulho:
    def __init__(self):
        self.ta_ligado = False
        self.sons = {}
        self.musicas = {}
        self.musica = None
        self.volume_da_musica = 1.0

    def ta_tocando(self):
        return self.musica is not None

    def aplica(self, opcoes):
        self.volume_da_musica = opcoes["musica"] / 10.0
        self.volume()

    def volume_de_verdade(self):
        return VOLUME_DAS_MUSICAS * self.volume_da_musica * 100

    def volume(self, quanto=1.0):
        if self.ta_ligado:
            SoundManager.set_music_volume(self.volume_de_verdade() * quanto)

    def liga(self):
        try:
            SoundManager.inicializar()
            self.ta_ligado = pygame.mixer.get_init() is not None
        except pygame.error as erro:
            print(f"[audio] sem som: {erro}")
            return
        SoundManager.set_sfx_volume(VOLUME_DOS_SONS * 100)
        for nome in SONS_DO_JOGO:
            self.sons[nome] = Sound(os.path.join(PASTA_SONS, f"{nome}.wav"))
        for nome_da_musica in AS_MUSICAS:
            self.musicas[nome_da_musica] = Musica(nome_da_musica)

    def toca(self, nome):
        if nome in self.sons:
            self.sons[nome].play()

    def toca_musica(self, nome_da_musica):
        self.musica = None
        if nome_da_musica in self.musicas:
            self.musica = self.musicas[nome_da_musica]
            self.musica.play(self.volume_de_verdade())

    def acerta_musica(self, tempo):
        if self.musica:
            self.musica.play(self.volume_de_verdade(), tempo)

    def para_musica(self):
        if self.musica:
            self.musica.stop(300)
        self.musica = None

    def pausa_musica(self):
        if self.musica:
            self.musica.pause()

    def volta_musica(self):
        if self.musica:
            self.musica.unpause()


audio = Barulho()
