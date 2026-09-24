"""
Constantes do jogo: janela, mundo, fisica, ritmo e cores.

Tudo que precisa ser ajustado "no olho" fica aqui, num lugar so.
"""

import os
from collections import namedtuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_MUSICA = os.path.join(RAIZ, "assets", "music")
DIR_SFX = os.path.join(RAIZ, "assets", "sfx")
SPRITESHEET = os.path.join(RAIZ, "male_hero_free", "male_hero.png")
FONTE = os.path.join(RAIZ, "assets", "fonts", "Silkscreen-Regular.ttf")
ARQUIVO_SAVE = os.path.join(RAIZ, "savegame.json")

# ------------------------------------------------------------------ janela
LARGURA, ALTURA = 1280, 720    # resolucao em que o jogo e DESENHADO (16:9)
TELA_CHEIA = True              # abre ocupando o monitor; F11 alterna com a janela.
                               # A imagem e ampliada sem suavizar para qualquer
                               # tela: 1920x1080 e 1,5x, 2560x1440 e 2x, 4K e 3x.
                               # Fora de 16:9, sobram faixas pretas.
FPS = 60
VOLUME_MUSICA = 0.7            # 0..1
VOLUME_SFX = 0.8

# ------------------------------------------------------------------- mundo
TILE = 48                      # lado de um bloco do grid, em pixels
TILES_POR_BATIDA = 4           # o jogador anda 4 tiles por batida da musica
ALTURA_PULO = 3 * TILE         # apice do pulo
LINHA_CHAO = 10                # linha do grid onde o chao comeca (y = 10 * TILE)
PASSO_FISICA = 1.0 / 240.0     # a fisica anda em passos fixos de 1/240 s

# ----------------------------------------------------------------- jogador
JOGADOR_TAM = 32               # lado da caixa de colisao (o sprite tem 32 px de largura)
HITBOX_PERIGO = 0.5            # fracao da caixa que colide com cacos (raspar nao mata)
COYOTE = 0.08                  # ainda da para pular ate 80 ms depois de sair do chao
BUFFER_PULO = 0.12             # um toque ate 120 ms antes de pousar vale como pulo
VIDAS = 3
INVULNERAVEL = 1.0             # segundos sem levar dano depois de um erro

# ------------------------------------------------------------ ponte de eco
PONTE_ZONA = 2 * TILE          # a zona da ponte comeca 2 tiles antes do abismo
PONTE_GRAVIDADE = 0.45         # gravidade dentro da zona (perdoa o toque atrasado)
PONTE_RESGATE = 2.5 * TILE     # ate quantos px abaixo da linha a ponte ainda segura

# ------------------------------------------------------------------- ritmo
# Janelas de julgamento, em fracao da batida. Sao as maiores janelas em que
# um toque julgado como "bom" ainda passa por cima de todos os obstaculos.
JANELA_PERFEITO = 0.10
JANELA_BOM = 0.20
PONTOS_PERFEITO = 50
PONTOS_BOM = 25
NOTAS = ((0.95, "S"), (0.85, "A"), (0.70, "B"), (0.0, "C"))   # por precisao

# ------------------------------------------------------------------- cores
BRANCO = (240, 240, 250)
CINZA = (150, 155, 185)
FUNDO = (18, 16, 36)
PAINEL = (30, 26, 56)
AMARELO = (255, 214, 92)
VERMELHO = (255, 86, 112)
VERDE = (120, 255, 168)
AZUL = (120, 240, 255)
ROXO = (200, 160, 255)

COR_JULGAMENTO = {"perfeito": VERDE, "bom": AMARELO, "erro": VERMELHO}
COR_DIFICULDADE = {"FACIL": VERDE, "NORMAL": AMARELO, "DIFICIL": VERMELHO}
COR_NOTA = {"S": AMARELO, "A": VERDE, "B": AZUL, "C": ROXO, "-": CINZA}

# Paleta de cada mundo: so cores chapadas.
Tema = namedtuple("Tema", "nome ceu sol montanha chao chao_topo bloco perigo destaque")
TEMAS = {
    "bosque": Tema("bosque", ceu=(22, 34, 66), sol=(255, 226, 170),
                   montanha=(20, 56, 60), chao=(32, 62, 54),
                   chao_topo=(110, 220, 160), bloco=(48, 84, 74),
                   perigo=(240, 110, 160), destaque=(126, 244, 180)),
    "ilhas": Tema("ilhas", ceu=(136, 82, 104), sol=(255, 220, 150),
                  montanha=(86, 60, 112), chao=(58, 50, 92),
                  chao_topo=(150, 226, 255), bloco=(76, 68, 118),
                  perigo=(255, 106, 118), destaque=(255, 200, 130)),
    "eclipse": Tema("eclipse", ceu=(26, 12, 46), sol=(255, 200, 110),
                    montanha=(48, 24, 80), chao=(42, 22, 70),
                    chao_topo=(206, 168, 255), bloco=(64, 36, 100),
                    perigo=(255, 128, 96), destaque=(255, 206, 120)),
}
